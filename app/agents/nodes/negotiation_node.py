# app/agents/nodes/negotiation_node.py
import logging
from typing import Dict, Any, List
from app.agents.state import CycleState
from app.config import LLMConfig
from app.utils.groq_utils import query_groq

logger = logging.getLogger("negotiation_node")

class NegotiationNode:
    """
    Negotiation Agent: Proposes QUANTITY REDUCTIONS for rejected orders.
    Uses realistic supply chain approach: reduce quantities to fit budget.
    """
    
    def calculate_reduction_factor(self, days_until_stockout: float, current_stock: int) -> float:
        """
        Calculate how much to reduce order quantity based on urgency.
        More urgent items get higher reduction factors (buy more of what we need).
        """
        if days_until_stockout < 3:
            return 0.6  # Buy 60% of requested (critical urgency)
        elif days_until_stockout < 7:
            return 0.5  # Buy 50% (moderate urgency)
        elif days_until_stockout < 14:
            return 0.4  # Buy 40% (low urgency)
        else:
            return 0.3  # Buy 30% (very low urgency)
    
    def generate_counter_arguments(
        self, 
        state: CycleState,
        rejected_items: List[Dict],
        approved_items: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate QUANTITY REDUCTION PROPOSALS for rejected items.
        This is how real supply chains handle budget constraints - reduce quantities.
        
        Returns proposals with reduced quantities that can be re-optimized by Finance.
        """
        proposals = []
        
        for rejected in rejected_items:
            sku = rejected.get('sku')
            product_name = rejected.get('product_name')
            original_qty = rejected.get('order_quantity', 0)
            
            # Get cost and inventory details
            fin_metrics = rejected.get('finance_metrics', {})
            unit_cost = fin_metrics.get('total_cost', 0) / max(original_qty, 1)
            
            inventory_item = rejected.get('inventory_item', {})
            current_stock = inventory_item.get('stock', 0)
            threshold = inventory_item.get('threshold', 10)
            
            # Calculate urgency
            details = rejected.get('details', {})
            daily_demand = float(details.get('daily_avg_demand', 1))
            days_until_stockout = current_stock / max(daily_demand, 0.1)
            
            # Only negotiate for critical items (stock below threshold)
            if current_stock >= threshold:
                logger.debug(f"Skipping {sku}: Not critical (stock {current_stock} >= threshold {threshold})")
                continue
            
            # Calculate proposed reduction
            reduction_factor = self.calculate_reduction_factor(days_until_stockout, current_stock)
            new_qty = int(original_qty * reduction_factor)
            new_cost = new_qty * unit_cost
            
            # Ensure minimum order quantity
            if new_qty < 10:
                new_qty = max(10, int(original_qty * 0.3))  # At least 30% or 10 units
                new_cost = new_qty * unit_cost
            
            # Generate LLM justification for the proposal
            prompt = f"""Supply Chain Negotiation: Propose quantity reduction to fit budget.

CONTEXT:
- Product: {product_name} (SKU: {sku})
- Original Request: {original_qty} units @ ${fin_metrics.get('total_cost', 0):.2f}
- Current Stock: {current_stock} units
- Days Until Stockout: {days_until_stockout:.1f} days
- Urgency: {'CRITICAL' if days_until_stockout < 7 else 'MODERATE'}

PROPOSAL:
- Reduced Quantity: {new_qty} units ({reduction_factor*100:.0f}% of original)
- Reduced Cost: ${new_cost:.2f}
- Justification: Reduce quantity to fit within budget while addressing critical stock shortage

Generate a concise 2-sentence justification explaining:
1. Why this product is critical (stockout risk)
2. Why the reduced quantity is acceptable (buys time until next cycle)

Format: "JUSTIFICATION: [your text]"
"""
            
            try:
                response_text = query_groq(
                    model=LLMConfig.NEGOTIATION_MODEL,
                    prompt=prompt,
                    timeout=LLMConfig.NEGOTIATION_TIMEOUT,
                    max_tokens=200
                )
                
                # Extract justification
                justification = response_text
                if "JUSTIFICATION:" in response_text:
                    justification = response_text.split("JUSTIFICATION:")[-1].strip()
                    
            except Exception as e:
                logger.error(f"LLM negotiation failed for {sku}: {e}")
                justification = f"Critical stock shortage. Reduced to {reduction_factor*100:.0f}% quantity to fit budget."
            
            # Create FIPA PROPOSE message
            fipa_message = {
                "performative": "PROPOSE",
                "sender": "Decision",
                "receiver": "Finance",
                "content": {
                    "proposal": "Quantity Reduction",
                    "sku": sku,
                    "original_quantity": original_qty,
                    "proposed_quantity": new_qty,
                    "cost_reduction": fin_metrics.get('total_cost', 0) - new_cost,
                    "justification": justification
                },
                "language": "JSON",
                "ontology": "SupplyChain-Ontology",
                "protocol": "ANEX-Negotiation"
            }
            
            proposals.append({
                "sku": sku,
                "product_name": product_name,
                "original_quantity": original_qty,
                "new_quantity": new_qty,
                "new_cost": new_cost,
                "reduction_factor": reduction_factor,
                "days_until_stockout": days_until_stockout,
                "counter_argument": justification,  # For backward compatibility with War Room
                "fipa": fipa_message,
                "timestamp": state.started_at.isoformat()
            })
            
            logger.info(f"💬 Negotiation: Propose {sku} qty reduction {original_qty} → {new_qty} (${new_cost:.2f})")
        
        return proposals

negotiation_node = NegotiationNode()
