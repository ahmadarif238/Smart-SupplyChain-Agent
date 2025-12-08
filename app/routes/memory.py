from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import database, schemas
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/agent", tags=["AgentMemory"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/memory")
def get_memory(limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rows = db.query(schemas.AgentMemory).order_by(schemas.AgentMemory.created_at.desc()).limit(limit).all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "context": r.context,
            "decision": r.decision,
            "reasoning": r.reasoning,
            "created_at": str(r.created_at)
        })
    return out

@router.get("/reinforcement-stats")
def get_reinforcement_stats(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Get reinforcement learning statistics:
    - Total auto-generated feedback
    - Accuracy distribution
    - SKUs with most auto-feedback
    """
    from datetime import datetime, timedelta
    
    # Count auto-generated feedback (marked with [AUTO] prefix)
    auto_feedback = db.query(schemas.Feedback).filter(
        schemas.Feedback.note.like('[AUTO]%')
    ).all()
    
    total_auto_feedback = len(auto_feedback)
    
    # Count approved vs rejected auto-feedback
    approved_count = sum(1 for f in auto_feedback if f.approved)
    rejected_count = total_auto_feedback - approved_count
    
    # Get accuracy by SKU
    sku_stats = {}
    for feedback in auto_feedback:
        sku = feedback.sku
        if sku not in sku_stats:
            sku_stats[sku] = {"total": 0, "approved": 0, "accuracy": 0}
        
        sku_stats[sku]["total"] += 1
        if feedback.approved:
            sku_stats[sku]["approved"] += 1
    
    # Calculate accuracy percentage per SKU
    for sku in sku_stats:
        sku_stats[sku]["accuracy"] = round(
            (sku_stats[sku]["approved"] / sku_stats[sku]["total"] * 100) if sku_stats[sku]["total"] > 0 else 0,
            2
        )
    
    # Recent feedback (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_auto_feedback = db.query(schemas.Feedback).filter(
        schemas.Feedback.note.like('[AUTO]%'),
        schemas.Feedback.created_at >= week_ago
    ).count()
    
    return {
        "status": "success",
        "total_auto_feedback": total_auto_feedback,
        "approved": approved_count,
        "rejected": rejected_count,
        "approval_rate": round(approved_count / total_auto_feedback * 100, 2) if total_auto_feedback > 0 else 0,
        "recent_feedback_7days": recent_auto_feedback,
        "sku_statistics": sku_stats,
        "timestamp": datetime.utcnow().isoformat()
    }
