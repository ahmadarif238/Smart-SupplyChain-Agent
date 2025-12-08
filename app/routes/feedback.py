from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import database, schemas
from datetime import datetime
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/agent", tags=["AgentFeedback"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FeedbackIn(BaseModel):
    memory_id: int
    sku: str
    approved: bool
    note: str | None = None

@router.post("/feedback")
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Submit feedback on a decision.
    
    The feedback is used by the learning node to:
    1. Calculate accuracy per SKU
    2. Adapt safety_multiplier (more conservative if low accuracy)
    3. Adjust confidence_threshold based on forecast reliability
    
    approved=True means the decision was good
    approved=False means the decision should have been different
    """
    # Verify memory record exists
    mem = db.query(schemas.AgentMemory).filter(schemas.AgentMemory.id == payload.memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory record not found")

    # ✅ NEW: Create feedback record in Feedback table
    # This is picked up by learning_node.learn() for parameter adaptation
    feedback = schemas.Feedback(
        memory_id=payload.memory_id,
        sku=payload.sku,
        approved=payload.approved,
        note=payload.note,
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    
    # Also create an audit alert
    status = "✅ Approved" if payload.approved else "❌ Rejected"
    alert_msg = f"[FEEDBACK] {payload.sku} decision {status}. Note: {payload.note or 'No comment'}"
    alert = schemas.Alerts(message=alert_msg, type="Feedback")
    db.add(alert)
    
    db.commit()
    db.refresh(feedback)
    
    return {
        "message": "Feedback recorded",
        "feedback_id": feedback.id,
        "approved": payload.approved,
        "note": "This feedback will be used by the learning node to adapt parameters on the next cycle"
    }

@router.get("/feedback/history/{sku}")
def get_feedback_history(sku: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get feedback history for a specific SKU.
    Shows decision accuracy trend.
    """
    try:
        feedback_records = db.query(schemas.Feedback).filter(
            schemas.Feedback.sku == sku
        ).order_by(schemas.Feedback.created_at.desc()).limit(50).all()
        
        if not feedback_records:
            return {"sku": sku, "records": [], "accuracy": 0.5, "samples": 0, "note": "No feedback yet for this SKU"}
        
        approved = sum(1 for fb in feedback_records if fb.approved)
        total = len(feedback_records)
        accuracy = approved / total if total > 0 else 0.5
        
        return {
            "sku": sku,
            "accuracy": accuracy,
            "samples": total,
            "approved_count": approved,
            "rejected_count": total - approved,
            "records": [
                {
                    "feedback_id": fb.id,
                    "approved": fb.approved,
                    "note": fb.note,
                    "created_at": fb.created_at.isoformat() if fb.created_at else None
                }
                for fb in feedback_records
            ]
        }
    except Exception as e:
        # Handle case where Feedback table doesn't exist yet
        return {
            "sku": sku,
            "records": [],
            "accuracy": 0.5,
            "samples": 0,
            "error": "Feedback table not initialized yet. Run database initialization.",
            "details": str(e)[:100]
        }

@router.get("/learned-parameters")
def get_learned_parameters(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get all learned parameters for all SKUs.
    Shows how agent has adapted based on feedback.
    """
    try:
        params_list = db.query(schemas.SKUParameters).all()
        
        return {
            "parameters": [
                {
                    "sku": p.sku,
                    "safety_multiplier": p.safety_multiplier,
                    "confidence_threshold": p.confidence_threshold,
                    "accuracy_score": p.accuracy_score,
                    "samples_count": p.samples_count,
                    "last_updated": p.last_updated.isoformat() if p.last_updated else None
                }
                for p in params_list
            ],
            "count": len(params_list)
        }
    except Exception as e:
        # Handle case where SKUParameters table doesn't exist yet
        return {
            "parameters": [],
            "count": 0,
            "error": "SKU Parameters table not initialized yet. Run database initialization or wait for first agent cycle.",
            "details": str(e)[:100]
        }
