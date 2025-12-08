# app/agents/nodes/decision_node_impl.py
from typing import Dict, Any
import re

class DecisionNode:
    """
    Deterministic decision logic for reorder quantities.
    Uses learned parameters from feedback when available.
    """

    def __init__(self, safety_max_multiplier: float = 3.0):
        self.default_safety_multiplier = safety_max_multiplier

    def _simple_qty_formula(self, current_qty: int, expected_weekly_demand: int, 
                           safety_multiplier: float = None) -> int:
        """
        Order enough for 2 weeks by default, clamp with safety multiplier.
        
        safety_multiplier can be:
        - 3.0 (default): balanced approach
        - > 3.0: conservative (stockout prevention)
        - < 3.0: aggressive (cost minimization)
        
        Learned from feedback:
        - High accuracy decisions → reduce multiplier
        - Low accuracy decisions → increase multiplier
        """
        if safety_multiplier is None:
            safety_multiplier = self.default_safety_multiplier
        
        # Order for 2 weeks at expected demand
        base = max(0, expected_weekly_demand * 2 - current_qty)
        
        # Cap with safety multiplier (learned from feedback)
        cap = int(max(1, expected_weekly_demand * safety_multiplier))
        
        return min(max(0, base), cap)

    def decide(self, sku_item, forecast: Dict[str, Any], learned_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make reorder decision.
        
        Args:
            sku_item: Inventory item
            forecast: LLM forecast result
            learned_params: Learned parameters from feedback (optional)
                - safety_multiplier: Adaptive value based on accuracy
                - confidence_threshold: Min forecast confidence to act
        """
        # Extract learned parameters if provided
        safety_multiplier = self.default_safety_multiplier
        confidence_threshold = 0.5
        
        if learned_params:
            safety_multiplier = learned_params.get("safety_multiplier", self.default_safety_multiplier)
            confidence_threshold = learned_params.get("confidence_threshold", 0.5)
        
        # forecast may be dict with 'forecast' list or nested strings
        forecast_list = None
        forecast_confidence = 0.8  # Default confidence if not specified
        
        if isinstance(forecast, dict):
            f = forecast.get("forecast")
            if isinstance(f, list):
                forecast_list = f
            
            # Extract confidence if available
            forecast_confidence = forecast.get("confidence", 0.8)
        
        if forecast_list and len(forecast_list) >= 7:
            weekly = int(sum(forecast_list[:7]))
        else:
            # try to parse numbers inside forecast_text or explanation
            weekly = 0
            if isinstance(forecast, dict):
                text = forecast.get("explanation", "") or forecast.get("forecast_text", "")
                if text:
                    cleaned = re.sub(r'[^0-9\s]', ' ', str(text))
                    nums = [int(x) for x in cleaned.split() if x.isdigit()]
                    if nums:
                        weekly = nums[0]

        current_qty = getattr(sku_item, "quantity", 0)
        threshold = getattr(sku_item, "threshold", 0)

        # Check if confidence is sufficient to make decision
        # Low confidence forecasts are treated conservatively
        confidence_ok = forecast_confidence >= confidence_threshold

        reorder_required = (current_qty < threshold) or (weekly > current_qty and confidence_ok)
        qty_to_order = 0
        reason = ""
        learned_note = ""

        if reorder_required:
            qty_to_order = self._simple_qty_formula(
                current_qty, 
                max(1, int(weekly or 1)),
                safety_multiplier=safety_multiplier
            )
            
            # Note learned adaptation
            if learned_params and "accuracy_score" in learned_params:
                accuracy = learned_params["accuracy_score"]
                if accuracy > 0.95:
                    learned_note = f" [High accuracy {accuracy:.0%}: conservative multiplier]"
                elif accuracy < 0.70:
                    learned_note = f" [Low accuracy {accuracy:.0%}: aggressive multiplier]"
            
            reason = f"Forecasted weekly demand {weekly}, current stock {current_qty}, threshold {threshold}.{learned_note}"
        else:
            reason = f"No reorder: forecasted week {weekly}, current stock {current_qty}."

        return {
            "reorder_required": bool(reorder_required),
            "qty_to_order": int(qty_to_order),
            "reason": reason,
            "explain": forecast.get("explanation") if isinstance(forecast, dict) else "",
            "applied_safety_multiplier": safety_multiplier,
            "forecast_confidence": forecast_confidence
        }
