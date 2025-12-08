# app/agents/dialogue_generator.py
"""
LLM-powered dialogue generator for multi-agent communication using ANEX protocol.
Uses Groq API to create natural, context-aware agent conversations with FIPA ACL compliance.
"""

import logging
from typing import Dict, Any, Optional
from app.utils.groq_utils import query_groq
from app.config.llm_config import LLMConfig

logger = logging.getLogger("dialogue_generator")

class DialogueGenerator:
    """Generate natural dialogue for agent-to-agent communication following ANEX protocol."""
    
    AGENT_PERSONAS = {
        "Finance": {
            "role": "Chief Financial Officer (CFO)",
            "personality": "Conservative, budget-conscious, data-driven. Focuses on ROI and fiscal responsibility.",
            "emoji": "💰"
        },
        "Decision": {
            "role": "Supply Chain Manager",
            "personality": "Analytical, urgency-aware, customer-focused. Prioritizes avoiding stockouts.",
            "emoji": "📊"
        },
        "Action": {
            "role": "Procurement Manager",
            "personality": "Execution-focused, detail-oriented, relationship-driven.",
            "emoji": "🛒"
        },
        "Learning": {
            "role": "Analytics Lead",
            "personality": "Data scientist mindset, feedback-oriented, continuous improvement focused.",
            "emoji": "🧠"
        }
    }
    
    def __init__(self, model: str = None):
        self.model = model or LLMConfig.DIALOGUE_MODEL  # llama-3.1-8b-instant
    
    def generate_rejection(
        self, 
        agent: str, 
        sku: str, 
        product_name: str,
        cost: float, 
        budget_remaining: float,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a FIPA ACL 'REFUSE' message using LLM."""
        
        persona = self.AGENT_PERSONAS.get(agent, {})
        
        prompt = f"""You are the {persona.get('role', agent)} in a supply chain management system.
Personality: {persona.get('personality', 'Professional')}

You need to reject a purchase order with the following details:
- Product: {product_name} (SKU: {sku})
- Order Cost: ${cost:,.2f}
- Budget Remaining: ${budget_remaining:,.2f}
- Reason: {reason}

Generate a BRIEF, professional rejection explanation (1 sentence max). Be concise but empathetic.
"""
        
        # Use Groq LLM for dialogue
        try:
            response = query_groq(
                model=self.model,
                prompt=prompt,
                max_tokens=100,
                timeout=LLMConfig.DIALOGUE_TIMEOUT
            )
            message = response.strip().strip('"') if response else f"Rejecting {product_name} order (${cost:,.2f}). {reason}"
        except Exception as e:
            logger.error(f"Dialogue generation failed: {e}")
            message = f"Rejecting {product_name} order (${cost:,.2f}). {reason}"
            
        # Construct FIPA ACL Message
        return {
            "performative": "REFUSE",
            "sender": agent,
            "receiver": "Decision",
            "content": {
                "reason": reason,
                "message": message,
                "sku": sku,
                "cost": cost
            },
            "language": "JSON",
            "ontology": "SupplyChain-Ontology",
            "protocol": "ANEX-Negotiation"
        }
    
    def generate_counter_argument(
        self,
        agent: str,
        sku: str,
        product_name: str,
        stockout_days: float,
        current_stock: int,
        daily_demand: float,
        roi: float,
        lost_revenue: float,
        target_agent: str = "Finance"
    ) -> Dict[str, Any]:
        """Generate a FIPA ACL 'PROPOSE' message with counter-argument using LLM."""
        
        persona = self.AGENT_PERSONAS.get(agent, {})
        
        prompt = f"""You are the {persona.get('role', agent)}.
The {target_agent} Agent rejected an order. You need to persuade them to reconsider.

Order Details:
- Product: {product_name} (SKU: {sku})
- Stockout in: {stockout_days:.1f} days
- Current Stock: {current_stock} units
- Daily Demand: {daily_demand:.1f} units
- ROI: {roi:.1f}x
- Potential Lost Revenue: ${lost_revenue:,.2f}

Generate a compelling 1-2 sentence counter-argument that emphasizes business impact.
"""
        
        # Use Groq LLM for negotiation
        try:
            response = query_groq(
                model=LLMConfig.NEGOTIATION_MODEL,  # qwen-qwen-3-32b for reasoning
                prompt=prompt,
                max_tokens=150,
                timeout=LLMConfig.NEGOTIATION_TIMEOUT
            )
            message = response.strip().strip('"') if response else f"Proposing reconsideration for {product_name}. ROI: {roi:.1f}x"
        except Exception as e:
            logger.error(f"Counter-argument generation failed: {e}")
            message = f"Proposing reconsideration for {product_name}. ROI: {roi:.1f}x"
            
        return {
            "performative": "PROPOSE",
            "sender": agent,
            "receiver": target_agent,
            "content": {
                "proposal": "Reconsider Rejection",
                "argument": message,
                "sku": sku,
                "roi": roi
            },
            "language": "JSON",
            "ontology": "SupplyChain-Ontology",
            "protocol": "ANEX-Negotiation"
        }
    
    def generate_override_approval(
        self,
        agent: str,
        sku: str,
        product_name: str,
        roi: float,
        cost: float,
        justification: str
    ) -> Dict[str, Any]:
        """Generate a FIPA ACL 'AGREE' message using LLM."""
        
        persona = self.AGENT_PERSONAS.get(agent, {})
        prompt = f"""You are the {persona.get('role', agent)}.
You initially rejected {product_name} (${cost:,.2f}) but after reviewing the counter-argument (ROI {roi:.1f}x), you agree to proceed.

Generate a 1-sentence approval confirmation that acknowledges the business case.
"""
        
        # Use Groq LLM
        try:
            response = query_groq(
                model=self.model,
                prompt=prompt,
                max_tokens=80,
                timeout=LLMConfig.DIALOGUE_TIMEOUT
            )
            message = response.strip().strip('"') if response else f"Approving {product_name} order (${cost:,.2f}). {justification}"
        except Exception as e:
            logger.error(f"Override approval generation failed: {e}")
            message = f"Approving {product_name} order (${cost:,.2f}). {justification}"
            
        return {
            "performative": "AGREE",
            "sender": agent,
            "receiver": "Decision",
            "content": {
                "response": "Override Approved",
                "message": message,
                "sku": sku,
                "cost": cost
            },
            "language": "JSON",
            "ontology": "SupplyChain-Ontology",
            "protocol": "ANEX-Negotiation"
        }

# Global instance
dialogue_generator = DialogueGenerator()
