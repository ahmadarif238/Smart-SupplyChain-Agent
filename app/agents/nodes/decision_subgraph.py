# app/agents/nodes/decision_subgraph.py
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from datetime import datetime

from app.agents.state import CycleState
from app.agents.nodes.intelligent_decision_node import IntelligentDecisionNode, UrgencyLevel, DecisionResult

logger = logging.getLogger("decision_subgraph")

# Initialize the engine
_engine = IntelligentDecisionNode()

def analyze_trends_node(state: CycleState) -> CycleState:
    """
    Step 1: Analyze trends and calculate metrics for all SKUs.
    """
    logger.info(f"[{state.cycle_id}] 📊 Subgraph: Analyzing trends for {len(state.forecast_results)} SKUs...")
    logger.info(f"[{state.cycle_id}] 📋 Forecast SKUs: {[f['sku'] for f in state.forecast_results]}")
    
    analyzed_skus = []
    
    def process_metrics(forecast_item):
        sku = forecast_item['sku']
        try:
            inventory_item = state.inventory_data.get(sku, {})
            recent_sales = state.sales_by_sku.get(sku, [])
            
            # Extract metrics using the engine
            metrics = _engine.extract_metrics(
                sku_item=inventory_item,
                forecast=forecast_item['forecast'],
                recent_sales=recent_sales
            )
            
            # Convert to dict for state storage
            metrics_dict = metrics.__dict__.copy()
            
            # Pre-calculate utility here to ensure it's available even if optimization fails later (though it shouldn't)
            utility_score = _engine.calculate_utility_score(metrics)
            
            return {
                "sku": sku,
                "product_name": forecast_item['product_name'],
                "metrics": metrics_dict,
                "forecast_item": forecast_item,
                "inventory_item": inventory_item,
                "utility_score": utility_score
            }
        except Exception as e:
            logger.error(f"Metric extraction failed for {sku}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_metrics, item) for item in state.forecast_results]
        for future in as_completed(futures):
            result = future.result()
            if result:
                analyzed_skus.append(result)
                
    state.analyzed_skus = analyzed_skus
    return state


def check_constraints_node(state: CycleState) -> CycleState:
    """
    Step 2: Check constraints (confidence, thresholds, active status).
    """
    logger.info(f"[{state.cycle_id}] 🚧 Subgraph: Checking constraints for {len(state.analyzed_skus)} SKUs...")
    
    constrained_skus = []
    
    for item in state.analyzed_skus:
        sku = item['sku']
        metrics = item['metrics']
        inventory_item = item['inventory_item']
        
        # Check if active
        if not inventory_item.get("is_active", True):
            logger.info(f"[{state.cycle_id}] ⏸️ {sku}: Skipped (inactive)")
            continue # Skip inactive
            
        # Check confidence constraint
        if metrics['forecast_confidence'] < _engine.min_confidence_to_order:
            # Low confidence logic
            threshold = inventory_item.get("threshold", 10)
            current_stock = metrics['current_stock']
            
            logger.info(f"[{state.cycle_id}] 🔍 {sku}: Low confidence ({metrics['forecast_confidence']:.2f}). Stock={current_stock}, Threshold={threshold}")
            
            if current_stock < threshold:
                #  Fallback trigger
                fallback_qty = max(metrics['min_order_qty'], int(threshold * 2) - current_stock)
                item['constraint_decision'] = "fallback"
                item['fallback_qty'] = fallback_qty
                logger.info(f"[{state.cycle_id}] ✅ {sku}: Fallback triggered. Qty={fallback_qty}")
            else:
                # Hold
                logger.info(f"[{state.cycle_id}] ⏸️  {sku}: Holding (stock >= threshold despite low confidence)")
                continue 
        else:
            item['constraint_decision'] = "proceed"
            logger.info(f"[{state.cycle_id}] ✅ {sku}: Proceeding (good confidence)")
            
        constrained_skus.append(item)
        
    logger.info(f"[{state.cycle_id}] 🎯 Constraint check complete. {len(constrained_skus)}/{len(state.analyzed_skus)} passed.")
    state.constrained_skus = constrained_skus
    return state


def optimize_cost_node(state: CycleState) -> CycleState:
    """
    Step 3: Optimize cost (EOQ, ROP) and generate final decisions.
    """
    logger.info(f"[{state.cycle_id}] 💎 Subgraph: Optimizing cost for {len(state.constrained_skus)} SKUs...")
    
    decisions = []
    
    def process_optimization(item):
        sku = item['sku']
        metrics_dict = item['metrics']
        
        # Reconstruct metrics object
        from app.agents.nodes.intelligent_decision_node import InventoryMetrics
        metrics = InventoryMetrics(**metrics_dict)
        
        try:
            # SIMPLE OVERRIDE: If stock < threshold, ALWAYS reorder (regardless of forecast/ROP)
            inventory_item = item['inventory_item']
            threshold = inventory_item.get("threshold", 10)
            current_stock = inventory_item.get("quantity", 0)
            
            if current_stock < threshold:
                target_stock = int(threshold * 2)
                order_qty = max(metrics_dict.get('min_order_qty', 1), target_stock - current_stock)
                
                logger.info(f"[OVERRIDE] {sku}: Stock {current_stock} < Threshold {threshold} → Ordering {order_qty} units")
                
                return {
                    "sku": sku,
                    "product_name": item['product_name'],
                    "reorder_required": True,
                    "order_quantity": order_qty,
                    "urgency_level": UrgencyLevel.HIGH,
                    "reason": f"Stock {current_stock} < Threshold {threshold}. Ordering to {target_stock}.",
                    "details": {
                        "type": "threshold_override",
                        "threshold": threshold,
                        "target_stock": target_stock,
                        "unit_price": metrics.unit_cost
                    },
                    "cost_analysis": {
                        "purchasing_cost_per_unit": metrics.unit_cost
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "utility_score": item.get('utility_score', 1000.0)
                }
            
            if item.get('constraint_decision') == "fallback":
                logger.info(f"🔍 [Sub-step] {sku}: Processing fallback decision...")
                # Create fallback decision
                return {
                    "sku": sku,
                    "product_name": item['product_name'],
                    "reorder_required": True,
                    "order_quantity": item['fallback_qty'],
                    "urgency_level": UrgencyLevel.HIGH,
                    "reason": "Low confidence fallback",
                    "details": {
                        "type": "fallback",
                        "unit_price": metrics.unit_cost
                    },
                    "cost_analysis": {
                        "purchasing_cost_per_unit": metrics.unit_cost
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "utility_score": item.get('utility_score', 500.0)
                }
            
            # Normal optimization
            logger.info(f"🔍 [Sub-step] {sku}: Analyzing demand trends and constraints...")

            logger.info(f"📐 [Sub-step] {sku}: Calculating EOQ & Reorder Point...")
            eoq = _engine.calculate_eoq(metrics)
            reorder_point = _engine.calculate_dynamic_reorder_point(metrics)
            
            # Effective stock
            effective_stock = metrics.current_stock + metrics.pending_orders
            
            # Use engine for decision logic to keep it DRY
            # Note: _engine.decide_reorder returns a DecisionResult, but we need to integrate it with the manual checks here
            # For now, keeping the manual logic consistent with previous implementation but adding the logging
            
            if metrics.forecast_confidence < _engine.min_confidence_to_order:
                 # Already handled by constraint check, but safe fallback
                 pass

            # Days until stockout
            days_until_stockout = None
            if metrics.daily_avg_demand > 0:
                days_until_stockout = effective_stock / metrics.daily_avg_demand
            
            reorder_required = effective_stock < reorder_point or effective_stock == 0
            
            order_qty = 0
            urgency = UrgencyLevel.LOW
            
            logger.info(f"⚖️ [Sub-step] {sku}: Scoring Urgency & Stockout Risk (Day to Stockout: {days_until_stockout:.1f} days)...")
            
            if reorder_required:
                target_stock = reorder_point + eoq
                order_qty = max(0, target_stock - effective_stock)
                
            urgency = _engine.calculate_urgency(metrics, reorder_point, eoq, days_until_stockout)
            cost_analysis = _engine.calculate_cost_analysis(metrics, eoq)
            cost_analysis["purchasing_cost_per_unit"] = metrics.unit_cost
            
            reason = ""
            if reorder_required:
                reason = f"Stock {effective_stock} < ROP {reorder_point}. EOQ {eoq}."
            else:
                reason = f"Stock {effective_stock} >= ROP {reorder_point}."
            
            return {
                "sku": sku,
                "product_name": item['product_name'],
                "reorder_required": reorder_required,
                "order_quantity": order_qty,
                "urgency_level": urgency,
                "reason": reason,
                "details": {
                    "reorder_point": reorder_point,
                    "eoq": eoq,
                    "safety_stock": metrics.safety_stock,
                    "lead_time_days": metrics.lead_time_days
                },
                "cost_analysis": cost_analysis,
                "timestamp": datetime.utcnow().isoformat(),
                "utility_score": item.get('utility_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Optimization failed for {sku}: {e}")
            return {"sku": sku, "error": str(e)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_optimization, item) for item in state.constrained_skus]
        for future in as_completed(futures):
            result = future.result()
            if "error" not in result:
                decisions.append(result)
                
    state.decisions = decisions
    return state
