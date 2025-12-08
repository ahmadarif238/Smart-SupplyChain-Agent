# app/agents/nodes/memory_node.py
from app.models import schemas
from app.models.database import SessionLocal
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger("memory_node")

def append_run_summary(session_factory, summary: dict):
    db: Session = session_factory()
    try:
        msg = f"Agent run at {summary.get('run_at')}: processed {len(summary.get('summary', []))} items."
        alert = schemas.Alerts(message=msg, type="AgentRun")
        db.add(alert)
        
        # Extract decision summaries from each item
        decision_summary_list = []
        for item in summary.get("summary", []):
            decision = item.get("decision", {})
            if decision:
                decision_summary_list.append({
                    "sku": item.get("sku"),
                    "product_name": item.get("product_name"),
                    "reorder_required": decision.get("reorder_required"),
                    "order_quantity": decision.get("order_quantity"),
                    "urgency_level": decision.get("urgency_level"),
                    "reason": decision.get("reason"),
                    "explanation": decision.get("explanation")
                })
        
        # Store full context and create a summary for the decision field
        decision_summary = json.dumps(decision_summary_list)
        reasoning_summary = f"Processed {len(summary.get('summary', []))} SKUs. Reorders triggered: {sum(1 for item in summary.get('summary', []) if item.get('decision', {}).get('reorder_required', False))}"
        
        mem = schemas.AgentMemory(
            context=json.dumps(summary.get("summary", [])),  # Full data (will be stored in TEXT column in DB)
            decision=decision_summary,  # Decision summaries
            reasoning=reasoning_summary  # Summary text
        )
        db.add(mem)
        db.commit()
        logger.info(f"Memory saved: {len(summary.get('summary', []))} items processed")
        return {"alert_id": alert.id, "memory_id": mem.id}
    except Exception as e:
        logger.error(f"Error saving memory: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()

class MemoryNode:
    def append_run_summary(self, session_factory, summary: dict):
        return append_run_summary(session_factory, summary)
