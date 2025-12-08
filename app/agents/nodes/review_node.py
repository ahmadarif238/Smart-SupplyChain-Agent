# app/agents/nodes/review_node.py
import logging
from typing import Dict, Any, List
from app.agents.state import CycleState

logger = logging.getLogger("review_node")

class ReviewNode:
    """
    Review Node: Human-in-the-Loop Guardrail.
    
    Role:
    - Intercepts decisions before execution.
    - Identifies high-risk/high-value actions (e.g., Orders > $1000).
    - Flags them for manual approval instead of auto-execution.
    """
    
    def __init__(self, approval_threshold: float = 1000.0):
        self.approval_threshold = approval_threshold
    
    def review(self, state: CycleState) -> CycleState:
        """
        Review decisions and flag those needing approval.
        """
        logger.info(f"🛡️ Review Node: Checking {len(state.decisions)} decisions for risk...")
        
        reviewed_decisions = []
        approval_queue = []
        
        for decision in state.decisions:
            # Calculate estimated cost
            qty = decision.get("order_quantity", 0)
            # Try to get cost from details, or estimate
            details = decision.get("details", {})
            unit_cost = details.get("unit_cost", 0)
            if not unit_cost:
                 # Fallback to cost analysis if available
                 cost_analysis = decision.get("cost_analysis", {})
                 unit_cost = cost_analysis.get("cost_per_unit", 0)
            
            total_cost = qty * unit_cost
            
            # Check threshold
            if total_cost > self.approval_threshold:
                # Flag for approval
                decision["requires_approval"] = True
                decision["approval_reason"] = f"High value order (${total_cost:.2f} > ${self.approval_threshold})"
                approval_queue.append(decision)
                logger.warning(f"✋ Review Node: Flagged {decision['sku']} for approval (Cost: ${total_cost:.2f})")
            else:
                decision["requires_approval"] = False
                reviewed_decisions.append(decision)
        
        # Update state
        # We keep ALL decisions in the list, but ActionNode will check the flag
        state.decisions = reviewed_decisions + approval_queue
        
        if approval_queue:
            from app.agents.streaming import stream_manager
            stream_manager.emit(
                state.cycle_id, 
                "review_required", 
                f"🛡️ Paused {len(approval_queue)} high-value orders for human review.",
                {"count": len(approval_queue), "threshold": self.approval_threshold}
            )
            
        return state
