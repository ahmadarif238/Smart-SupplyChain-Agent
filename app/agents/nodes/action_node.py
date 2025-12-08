# app/agents/nodes/action_node.py
from app.models.database import SessionLocal
from app.models import schemas
from sqlalchemy.orm import Session
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import json

logger = logging.getLogger("action_node")


class ActionNode:
    """
    Action node executes decisions by creating orders and alerts.
    
    Uses new decision data structure with urgency levels and cost analysis.
    """
    
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def _get_priority_from_urgency(self, urgency_level: str) -> int:
        """Convert urgency level to priority (1=highest, 5=lowest)"""
        urgency_priority = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
            "deferred": 5,
            "obsolete": 5
        }
        return urgency_priority.get(urgency_level, 3)

    def execute(self, decision: dict) -> dict:
        """
        Execute decision: create order and alert if reorder required.
        
        Args:
            decision: Dict from intelligent decision node with:
              - reorder_required (bool)
              - order_quantity (int)
              - urgency_level (str)
              - reason (str)
              - details (dict)
              - cost_analysis (dict)
              - sku (str)
              - product_name (str)
        
        Returns:
            Dict with execution results
        """
        db: Session = self.session_factory()
        try:
            if not decision.get("reorder_required"):
                return {
                    "executed": False,
                    "message": "No reorder required",
                    "urgency": decision.get("urgency_level", "low")
                }

            sku = decision.get("sku", "UNKNOWN")
            qty = int(decision.get("order_quantity", 0))
            urgency = decision.get("urgency_level", "medium")
            reason = decision.get("reason", "Automatic reorder")

            # Fetch product details
            product = db.query(schemas.Inventory).filter(schemas.Inventory.sku == sku).first()
            product_name = product.product_name if product else sku
            supplier = product.supplier if product and hasattr(product, "supplier") else "Default"

            # Check for approval requirement
            requires_approval = decision.get("requires_approval", False)
            approval_reason = decision.get("approval_reason", "")
            
            status = "Needs Approval" if requires_approval else "Pending"
            
            # Prepare detailed alert message with decision metrics
            details = decision.get("details", {})
            cost_analysis = decision.get("cost_analysis", {})

            alert_parts = [
                f"🚀 AutoPO: {product_name} ({sku})",
                f"Qty: {qty} units",
                f"Supplier: {supplier}",
                f"Urgency: {urgency.upper()}",
                f"Reason: {reason[:100]}",  # Truncate reason
            ]
            
            if requires_approval:
                alert_parts.insert(0, f"⚠️ APPROVAL NEEDED: {approval_reason}")

            # Add supply chain details if available
            if details:
                if "lead_time_days" in details:
                    alert_parts.append(f"Lead Time: {details['lead_time_days']}d")
                if "reorder_point" in details:
                    alert_parts.append(f"ROP: {details['reorder_point']} | Stock: {details.get('current_stock', '?')}")
                if "daily_avg_demand" in details:
                    alert_parts.append(f"Avg Demand: {details['daily_avg_demand']}/day")

            # Add cost analysis if available
            if cost_analysis:
                cost_per_unit = cost_analysis.get("cost_per_unit", 0)
                if cost_per_unit > 0:
                    alert_parts.append(f"Cost/Unit: ${cost_per_unit:.2f}")

            alert_msg = "\n".join(alert_parts)

            # Create order record with urgency priority
            priority = self._get_priority_from_urgency(urgency)
            
            order = schemas.Orders(
                sku=sku,
                quantity=qty,
                order_date=datetime.utcnow(),
                status=status,
                # Store decision details for audit trail
                notes=json.dumps({
                    "urgency": urgency,
                    "reason": reason,
                    "requires_approval": requires_approval,
                    "approval_reason": approval_reason,
                    "details": {k: str(v) for k, v in details.items()},
                    "cost_analysis": {k: float(v) if isinstance(v, (int, float)) else str(v) 
                                     for k, v in cost_analysis.items()}
                })
            )
            db.add(order)

            # Create alert record with urgency level
            alert = schemas.Alerts(
                message=alert_msg,
                type="AutoOrder",
                sku=sku,
                # Store structured data
                priority=priority
            )
            db.add(alert)

            db.commit()
            db.refresh(order)

            # SIMULATION: Immediate replenishment for demo purposes
            # In a real system, this would happen on "Receive"
            if product:
                product.quantity += qty
                db.add(product)
                db.commit()
                logger.info(f"📦 Immediate replenishment: {sku} stock increased by {qty} to {product.quantity}")

            logger.info(
                f"Order created: {order.id} for {sku}, qty {qty}, urgency {urgency}"
            )

            # Calculate total cost
            unit_price = product.unit_price if product and product.unit_price else 0.0
            total_cost = qty * unit_price

            return {
                "executed": True,
                "order_id": order.id,
                "sku": sku,
                "quantity": qty,
                "urgency": urgency,
                "alert": alert_msg,
                "supplier": supplier,
                "cost_per_unit": unit_price,
                "total_cost": total_cost
            }

        except Exception as e:
            logger.error(f"Action execution error: {str(e)}", exc_info=True)
            return {
                "executed": False,
                "error": str(e),
                "sku": decision.get("sku", "UNKNOWN")
            }
        finally:
            db.close()
