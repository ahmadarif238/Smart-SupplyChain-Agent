import os
import json
import logging
from app.utils.groq_utils import query_groq
from app.config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            self.client_available = False
        else:
            self.client_available = True
            logger.info("Groq client configured")

    def summarize_cycle(self, cycle_data: dict) -> str:
        if not self.client_available:
            return "Summarization unavailable: GROQ_API_KEY not configured."

        try:
            # Optimize input data to save tokens
            lean_data = {
                "cycle_id": cycle_data.get("cycle_id"),
                "skus_processed": len(cycle_data.get("inventory_data", {})),
                "forecasts": len(cycle_data.get("forecast_results", [])),
                "decisions": len(cycle_data.get("decisions", [])),
                "reorders": len([d for d in cycle_data.get("decisions", []) if d.get("decision") == "reorder"]),
                "actions": len(cycle_data.get("actions", [])),
                "errors": len(cycle_data.get("errors", []))
            }

            # Extract top 3 decisions (narrative focus)
            top_decisions = cycle_data.get("decisions", [])[:3]
            lean_data["top_decisions"] = [
                {
                    "sku": d.get("sku"),
                    "decision": d.get("decision"),
                    "reasoning": d.get("reasoning", "")[:100]  # Limit reasoning to 100 chars
                }
                for d in top_decisions
            ]

            # Extract actions summary
            actions_summary = []
            for a in cycle_data.get("actions", [])[:5]:  # Top 5 actions
                actions_summary.append({
                    "action_type": a.get("action_type"),
                    "sku": a.get("sku"),
                    "quantity": a.get("quantity")
                })
            lean_data["actions_summary"] = actions_summary

            prompt = f"""
            Summarize this supply chain agent cycle in 2-3 concise paragraphs.
            Focus on:
            1. Overall activity (SKUs processed, forecasts generated)
            2. Key decisions made (reorders triggered)
            3. Actions taken and financial impact

            Cycle Data:
            {json.dumps(lean_data, indent=2)}
            """
            # Use Groq for summarization
            response = query_groq(
                model=LLMConfig.SUMMARY_MODEL,  # llama-3.3-70b-versatile
                prompt=prompt,
                max_tokens=800,
                timeout=LLMConfig.SUMMARY_TIMEOUT
            )
            
            if response:
                return response.strip()
            else:
                return "Unable to generate summary (Groq API unavailable)"
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to template summary if LLM fails (e.g. Rate Limit)
            return self._generate_fallback_summary(cycle_data)

    def _generate_fallback_summary(self, cycle_data: dict) -> str:
        """Fallback summary using template (no LLM)."""
        skus = len(cycle_data.get("inventory_data", {}))
        forecasts = len(cycle_data.get("forecast_results", []))
        decisions = cycle_data.get("decisions", [])
        reorders = [d for d in decisions if d.get("decision") == "reorder"]
        actions = cycle_data.get("actions", [])
        
        summary = f"SUPPLY CHAIN CYCLE SUMMARY\n\n"
        summary += f"Processed {skus} SKUs and generated {forecasts} demand forecasts.\n\n"
        summary += f"DECISIONS\nTriggered {len(reorders)} reorder decisions out of {len(decisions)} total decisions.\n\n"
        
        if actions:
            summary += f"ACTIONS TAKEN\n"
            total_val = sum(a.get("total_cost", 0) for a in actions)
            for a in actions[:5]:
                sku = a.get("sku")
                qty = a.get("quantity")
                oid = a.get("order_id")
                summary += f"• Created Order #{oid} for {sku} ({qty} units)\n"
            
            summary += f"\nFINANCIAL IMPACT\nTotal spend for this cycle was ${total_val:,.2f}."
        
        return summary


def call_gemini_api(model: str, messages: list, temperature: float = 0.7, max_tokens: int = 150) -> str:
    """
    DEPRECATED: Replaced with Groq.
    This function now uses Groq instead of Gemini for backwards compatibility.
    
    Helper function to call Groq API for dialogue generation.
    
    Args:
        model: Model name (ignored, uses Groq model)
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature
        max_tokens: Maximum completion tokens
        
    Returns:
        Generated text response
    """
    from app.utils.groq_utils import query_groq
    from app.config.llm_config import LLMConfig
    
    # Combine messages into a single prompt
    prompt = "\n".join([msg["content"] for msg in messages])
    
    # Use Groq instead of Gemini
    response = query_groq(
        model=LLMConfig.DIALOGUE_MODEL,  # llama-3.1-8b-instant
        prompt=prompt,
        max_tokens=max_tokens,
        timeout=15
    )
    
    return response if response else ""


def query_gemini(model: str, prompt: str, timeout: int = 30, max_tokens: int = 400) -> str:
    """
    DEPRECATED: Replaced with Groq.
    Compatibility wrapper for legacy calls (like in NegotiationNode).
    Adapts 'prompt' string to 'messages' list and uses Groq.
    """
    return call_gemini_api(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )


llm_service = LLMService()
