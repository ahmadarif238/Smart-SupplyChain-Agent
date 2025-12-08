# app/agents/nodes/fetch_data_node.py
"""LangGraph node: Fetch inventory, sales, and orders data."""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models import schemas
from app.utils.common import serialize_model
from app.agents.state import CycleState

logger = logging.getLogger("fetch_data_node")

def fetch_data_node(state: CycleState) -> CycleState:
    """
    LangGraph node: Fetch inventory, sales, and orders data.
    
    Input: CycleState with empty data fields
    Output: CycleState with populated inventory_data, sales_data, sales_by_sku
    """
    
    db: Session = SessionLocal()
    try:
        logger.info(f"[{state.cycle_id}] Fetching inventory and sales data...")
        
        # Fetch all inventory
        inventory = db.query(schemas.Inventory).all()
        state.inventory_data = {
            item.sku: {
                "sku": item.sku,
                "product_name": item.product_name,
                "quantity": item.quantity or 0,
                "threshold": item.threshold or 10,
                "reorder_cost": item.reorder_cost if item.reorder_cost is not None else 50.0,
                "unit_price": item.unit_price if item.unit_price is not None else 0.0,
                "holding_cost_percent": item.holding_cost_percent if item.holding_cost_percent is not None else 0.15,
                "lead_time_days": item.lead_time_days or 7,
                "safety_stock": item.safety_stock or 5
            }
            for item in inventory
        }

        # Inject semantic memory
        from app.agents.langgraph_workflow import _memory_manager
        for sku, data in state.inventory_data.items():
            facts = _memory_manager.retrieve_relevant_facts(sku)
            if facts:
                data["semantic_memory"] = facts
                logger.info(f"[{state.cycle_id}] Loaded {len(facts)} facts for {sku}")
        
        logger.info(f"[{state.cycle_id}] Fetched {len(state.inventory_data)} SKUs")
        logger.info(f"[{state.cycle_id}] Inventory SKUs: {list(state.inventory_data.keys())}")
        
        # Fetch recent sales (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        sales = db.query(schemas.Sales).filter(
            schemas.Sales.date >= seven_days_ago
        ).order_by(schemas.Sales.date.desc()).all()
        
        state.sales_data = [serialize_model(s) for s in sales]
        
        # Group sales by SKU for volatility calculation
        state.sales_by_sku = {}
        total_revenue = 0.0
        
        # Create price lookup map
        price_map = {item.sku: (item.unit_price or 0.0) for item in inventory}
        
        for sale in sales:
            sku = sale.sku
            if sku not in state.sales_by_sku:
                state.sales_by_sku[sku] = []
            state.sales_by_sku[sku].append(serialize_model(sale))
            
            # Calculate revenue
            price = price_map.get(sku, 0.0)
            total_revenue += sale.sold_quantity * price
            
        state.recent_sales_revenue = total_revenue
        logger.info(f"[{state.cycle_id}] Fetched {len(state.sales_data)} sales records. Revenue (7d): ${total_revenue:.2f}")
        
        # Fetch recent orders
        orders = db.query(schemas.Orders).order_by(schemas.Orders.order_date.desc()).limit(500).all()
        state.orders_data = [serialize_model(o) for o in orders]
        
        # Calculate pending orders by SKU and check for overdue
        state.pending_orders_by_sku = {}
        state.overdue_orders = []
        now = datetime.utcnow().replace(tzinfo=None)  # Make timezone-naive for comparison
        
        for order in orders:
            if order.status == "Pending":
                state.pending_orders_by_sku[order.sku] = state.pending_orders_by_sku.get(order.sku, 0) + order.quantity
                
                # Check if overdue
                # Get lead time for this SKU
                sku_data = state.inventory_data.get(order.sku, {})
                lead_time = sku_data.get("lead_time_days", 7)
                
                # Expected delivery date
                order_date_naive = order.order_date.replace(tzinfo=None) if order.order_date.tzinfo else order.order_date
                expected_delivery = order_date_naive + timedelta(days=lead_time)
                
                # If expected delivery was yesterday or earlier, it's overdue
                if expected_delivery < now:
                    days_overdue = (now - expected_delivery).days
                    state.overdue_orders.append({
                        "order_id": order.id,
                        "sku": order.sku,
                        "days_overdue": days_overdue,
                        "supplier": sku_data.get("supplier", "Unknown")
                    })
                    logger.warning(f"⚠️ Order #{order.id} for {order.sku} is overdue by {days_overdue} days!")
        
        # Fetch recent alerts
        alerts = db.query(schemas.Alerts).order_by(schemas.Alerts.created_at.desc()).limit(200).all()
        state.alerts_data = [serialize_model(a) for a in alerts]
        
        return state
        
    except Exception as e:
        logger.error(f"[{state.cycle_id}] Error fetching data: {str(e)}")
        state.add_error("DATA_FETCH", str(e))
        return state
    finally:
        db.close()
