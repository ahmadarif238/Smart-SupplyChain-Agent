# app/agents/nodes/decision_node.py
"""LangGraph node: Make reorder decisions based on forecasts."""

import logging
from typing import Dict, Any, List

from app.agents.nodes.intelligent_decision_node import IntelligentDecisionNode, UrgencyLevel
from app.agents.state import CycleState

logger = logging.getLogger(__name__)


class DecisionNode:
    """
    Decision node wrapper that bridges the agent cycle with intelligent decision engine.
    
    Supports both old simple API and new advanced API with sales history.
    """
    
    def __init__(self, service_level: float = 0.95, cost_multiplier: float = 1.0):
        """
        Args:
            service_level: Target service level (0-1). Higher = less stockout risk.
            cost_multiplier: Adjust cost optimization aggressiveness.
        """
        self.engine = IntelligentDecisionNode(
            service_level=service_level,
            cost_multiplier=cost_multiplier
        )

    def decide(
        self,
        sku_item: Dict[str, Any],
        forecast: Dict[str, Any],
        learned_params: Dict[str, Any] = None,
        recent_sales: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make reorder decision using intelligent decision engine.
        
        Args:
            sku_item: Inventory record (dict or object with attributes)
            forecast: 7-day forecast from LLM
            learned_params: Optional learned parameters from feedback
            recent_sales: Optional recent sales for volatility calculation
        
        Returns:
            Dict with decision results (backward compatible with old format)
        """
        
        # Handle both dict and object input
        if not isinstance(sku_item, dict):
            sku_item = sku_item.__dict__ if hasattr(sku_item, '__dict__') else {}
        
        
        # Default to empty sales list if not provided (fallback to baseline)
        if recent_sales is None:
            recent_sales = []
        
        try:
            # Call intelligent decision engine
            result = self.engine.decide(
                sku_item=sku_item,
                forecast=forecast,
                recent_sales=recent_sales,
                pending_orders=sku_item.get("pending_orders", 0),
                learned_params=learned_params
            )
            
            # Convert DecisionResult to dict for backward compatibility
            return {
                "reorder_required": result.reorder_required,
                "order_quantity": result.order_quantity,
                "urgency_level": result.urgency_level.value,
                "reason": result.reason,
                "details": result.details,
                "cost_analysis": result.cost_analysis,
                "explanation": result.reason  # For backward compatibility
            }
        
        except Exception as e:
            logger.error(f"Decision error: {str(e)}")
            # Fallback: conservative decision
            current = sku_item.get("quantity", 0)
            threshold = sku_item.get("threshold", 10)
            
            if current < threshold:
                order_qty = int(threshold * 1.5 - current)
            else:
                order_qty = 0
            
            return {
                "reorder_required": order_qty > 0,
                "order_quantity": order_qty,
                "urgency_level": "medium" if order_qty > 0 else "low",
                "reason": f"Decision failed; using fallback (stock: {current}, threshold: {threshold})",
                "details": {"error": str(e)},
                "cost_analysis": {},
                "explanation": "Fallback decision"
            }
