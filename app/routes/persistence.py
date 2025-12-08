# app/routes/persistence.py
"""
API endpoints for agent persistence management.
Handles memory, checkpoints, goals, and recovery.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from app.models.database import SessionLocal
from app.auth.dependencies import get_current_user
from app.persistence import (
    PersistentMemoryManager, RecoveryManager,
    EpisodicMemory, SemanticMemory, ProceduralMemory, Goal
)

router = APIRouter(prefix="/persistence", tags=["Persistence"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_memory_manager():
    return PersistentMemoryManager(SessionLocal)


def get_recovery_manager():
    memory_mgr = PersistentMemoryManager(SessionLocal)
    return RecoveryManager(memory_mgr)


# ============ EPISODIC MEMORY ENDPOINTS ============

@router.post("/episodes/store")
def store_episode(
    event_type: str,
    description: str,
    outcome: Optional[str] = None,
    sku: Optional[str] = None,
    learning: Optional[str] = None,
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Store a specific event/experience in episodic memory"""
    try:
        episode = EpisodicMemory(
            event_id=f"ep_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            sku=sku,
            description=description,
            context={},
            outcome=outcome,
            learning=learning
        )
        
        episode_id = memory_mgr.store_episode(db, episode)
        return {
            "status": "success",
            "episode_id": episode_id,
            "message": "Episode stored in episodic memory"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/episodes/retrieve")
def retrieve_episodes(
    sku: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    days_back: int = Query(30),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Retrieve past events (episodic memory)"""
    try:
        episodes = memory_mgr.retrieve_episodes(db, sku, event_type, days_back, limit)
        
        return {
            "status": "success",
            "count": len(episodes),
            "episodes": [
                {
                    "event_id": ep.event_id,
                    "timestamp": ep.timestamp.isoformat(),
                    "event_type": ep.event_type,
                    "sku": ep.sku,
                    "description": ep.description,
                    "outcome": ep.outcome,
                    "learning": ep.learning
                }
                for ep in episodes
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============ SEMANTIC MEMORY ENDPOINTS ============

@router.post("/facts/store")
def store_fact(
    category: str,
    key: str,
    value: Any,
    confidence: float = 0.5,
    source: str = "manual",
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Store a learned fact or insight"""
    try:
        fact = SemanticMemory(
            fact_id=f"fact_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            category=category,
            key=key,
            value=value,
            confidence=min(1.0, max(0.0, confidence)),
            source=source
        )
        
        fact_id = memory_mgr.store_fact(db, fact)
        return {
            "status": "success",
            "fact_id": fact_id,
            "message": "Fact stored in semantic memory"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/facts/retrieve")
def retrieve_fact(
    category: str,
    key: str,
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Retrieve a specific learned fact"""
    try:
        fact = memory_mgr.retrieve_fact(db, category, key)
        
        if not fact:
            return {
                "status": "not_found",
                "message": f"No fact found for {category}/{key}"
            }, 404
        
        return {
            "status": "success",
            "fact": {
                "fact_id": fact.fact_id,
                "timestamp": fact.timestamp.isoformat(),
                "category": fact.category,
                "key": fact.key,
                "value": fact.value,
                "confidence": fact.confidence,
                "source": fact.source
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/facts/by-category")
def retrieve_facts_by_category(
    category: str,
    min_confidence: float = Query(0.0),
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Retrieve all facts in a category"""
    try:
        facts = memory_mgr.retrieve_facts_by_category(db, category, min_confidence)
        
        return {
            "status": "success",
            "category": category,
            "count": len(facts),
            "facts": [
                {
                    "fact_id": f.fact_id,
                    "key": f.key,
                    "value": f.value,
                    "confidence": f.confidence,
                    "source": f.source
                }
                for f in facts
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============ CHECKPOINT ENDPOINTS ============

@router.get("/checkpoints/latest")
def get_latest_checkpoint(
    goal: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Get latest checkpoint for recovery"""
    try:
        checkpoint = memory_mgr.get_latest_stable_checkpoint(db, goal)
        
        if not checkpoint:
            return {
                "status": "not_found",
                "message": "No stable checkpoint found"
            }, 404
        
        return {
            "status": "success",
            "checkpoint": {
                "checkpoint_id": checkpoint.checkpoint_id,
                "timestamp": checkpoint.timestamp.isoformat(),
                "cycle_number": checkpoint.cycle_number,
                "goal": checkpoint.goal,
                "progress": checkpoint.progress,
                "is_stable": checkpoint.is_stable
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/checkpoints/history")
def get_checkpoint_history(
    goal: Optional[str] = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db),
    memory_mgr: PersistentMemoryManager = Depends(get_memory_manager),
    current_user=Depends(get_current_user)
):
    """Get checkpoint history"""
    try:
        checkpoints = memory_mgr.get_checkpoint_history(db, goal, limit)
        
        return {
            "status": "success",
            "count": len(checkpoints),
            "checkpoints": [
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "timestamp": cp.timestamp.isoformat(),
                    "cycle_number": cp.cycle_number,
                    "goal": cp.goal,
                    "progress": cp.progress,
                    "is_stable": cp.is_stable
                }
                for cp in checkpoints
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============ RECOVERY ENDPOINTS ============

@router.post("/recover/initiate")
def initiate_recovery(
    goal: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    recovery_mgr: RecoveryManager = Depends(get_recovery_manager),
    current_user=Depends(get_current_user)
):
    """Initiate recovery after interruption"""
    try:
        plan = recovery_mgr.initiate_recovery(db, goal)
        return plan
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.post("/recover/resume")
def resume_from_checkpoint(
    checkpoint_id: str,
    db: Session = Depends(get_db),
    recovery_mgr: RecoveryManager = Depends(get_recovery_manager),
    current_user=Depends(get_current_user)
):
    """Resume execution from checkpoint"""
    try:
        result = recovery_mgr.resume_from_checkpoint(db, checkpoint_id)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.post("/recover/rollback")
def rollback_to_checkpoint(
    checkpoint_id: str,
    reason: str = Query("manual_rollback"),
    db: Session = Depends(get_db),
    recovery_mgr: RecoveryManager = Depends(get_recovery_manager),
    current_user=Depends(get_current_user)
):
    """Rollback to previous checkpoint"""
    try:
        result = recovery_mgr.rollback_to_checkpoint(db, checkpoint_id, reason)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/recover/checkpoints-available")
def list_available_checkpoints(
    goal: Optional[str] = Query(None),
    limit: int = Query(20),
    db: Session = Depends(get_db),
    recovery_mgr: RecoveryManager = Depends(get_recovery_manager),
    current_user=Depends(get_current_user)
):
    """List available checkpoints for recovery"""
    try:
        result = recovery_mgr.list_available_checkpoints(db, goal, limit)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


@router.get("/recover/failure-analysis")
def analyze_failures(
    goal: Optional[str] = Query(None),
    lookback_cycles: int = Query(10),
    db: Session = Depends(get_db),
    recovery_mgr: RecoveryManager = Depends(get_recovery_manager),
    current_user=Depends(get_current_user)
):
    """Analyze failure patterns for learning"""
    try:
        result = recovery_mgr.analyze_failure_pattern(db, goal, lookback_cycles)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


# ============ ANALYTICS & INSIGHTS ENDPOINTS ============

@router.get("/analytics/decision-history")
def get_decision_history_analytics(
    sku: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get complete decision history with feedback.
    Shows what decisions were made, why, and whether they were correct.
    """
    from app.models import schemas
    from datetime import timedelta
    import json
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        schemas.AgentMemory,
        schemas.Feedback.approved,
        schemas.Feedback.note
    ).outerjoin(
        schemas.Feedback,
        schemas.Feedback.memory_id == schemas.AgentMemory.id
    ).filter(
        schemas.AgentMemory.created_at >= cutoff_date
    )
    
    if sku:
        query = query.filter(schemas.Feedback.sku == sku)
    
    results = query.order_by(schemas.AgentMemory.created_at.desc()).limit(limit).all()
    
    history = []
    for memory, approved, note in results:
        try:
            decision_data = json.loads(memory.decision) if isinstance(memory.decision, str) else memory.decision
            if isinstance(decision_data, list):
                for item in decision_data:
                    if not sku or item.get("sku") == sku:
                        history.append({
                            "date": memory.created_at.isoformat(),
                            "sku": item.get("sku"),
                            "order_quantity": item.get("order_quantity"),
                            "urgency": item.get("urgency_level"),
                            "reason": item.get("reason"),
                            "approved": approved,
                            "feedback_note": note or "Pending"
                        })
        except:
            pass
    
    return {
        "status": "success",
        "records": history,
        "total": len(history),
        "period_days": days,
        "sku_filter": sku or "all"
    }


@router.get("/analytics/learning-progress")
def get_learning_progress_analytics(
    sku: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Track how the agent's learned parameters have evolved.
    Shows parameter changes and accuracy improvements.
    """
    from app.models import schemas
    
    query = db.query(schemas.SKUParameters).order_by(schemas.SKUParameters.sku)
    
    if sku:
        query = query.filter(schemas.SKUParameters.sku == sku)
    
    params = query.all()
    
    learning_data = []
    for param in params:
        feedback = db.query(schemas.Feedback).filter(
            schemas.Feedback.sku == param.sku,
            schemas.Feedback.note.like('[AUTO]%')
        ).all()
        
        if not feedback:
            continue
        
        approved = sum(1 for f in feedback if f.approved)
        total = len(feedback)
        accuracy = approved / total if total > 0 else 0
        
        learning_data.append({
            "sku": param.sku,
            "safety_multiplier": round(param.safety_multiplier, 2),
            "confidence_threshold": round(param.confidence_threshold, 2),
            "accuracy_score": round(param.accuracy_score, 3) if param.accuracy_score else None,
            "feedback_samples": total,
            "approved_decisions": approved,
            "approval_rate": round(accuracy * 100, 1)
        })
    
    return {
        "status": "success",
        "learning_data": learning_data,
        "total_skus": len(learning_data),
        "average_approval_rate": round(
            sum(d["approval_rate"] for d in learning_data) / len(learning_data) if learning_data else 0, 1
        )
    }


@router.get("/analytics/accuracy-by-sku")
def get_accuracy_by_sku(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Analyze which SKUs have the most accurate decisions.
    Identifies best/worst performers for targeted improvement.
    """
    from app.models import schemas
    
    skus = db.query(schemas.Feedback.sku).distinct().filter(
        schemas.Feedback.note.like('[AUTO]%')
    ).all()
    
    accuracy_data = []
    for (sku,) in skus:
        feedback = db.query(schemas.Feedback).filter(
            schemas.Feedback.sku == sku,
            schemas.Feedback.note.like('[AUTO]%')
        ).all()
        
        if not feedback:
            continue
        
        approved = sum(1 for f in feedback if f.approved)
        total = len(feedback)
        accuracy = approved / total if total > 0 else 0
        
        accuracy_data.append({
            "sku": sku,
            "total_decisions": total,
            "approved": approved,
            "rejected": total - approved,
            "accuracy_rate": round(accuracy * 100, 1),
            "trend": "improving" if accuracy > 0.75 else "stable" if accuracy > 0.5 else "needs_improvement"
        })
    
    accuracy_data.sort(key=lambda x: x["accuracy_rate"], reverse=True)
    
    return {
        "status": "success",
        "by_sku": accuracy_data,
        "top_5_performers": accuracy_data[:5],
        "bottom_5_performers": accuracy_data[-5:] if len(accuracy_data) > 5 else [],
        "total_skus": len(accuracy_data)
    }


@router.get("/analytics/improvement-trends")
def get_improvement_trends_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Track approval rate trends over time.
    Shows if the agent is improving or degrading.
    """
    from app.models import schemas
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    feedback_records = db.query(schemas.Feedback).filter(
        schemas.Feedback.note.like('[AUTO]%'),
        schemas.Feedback.created_at >= cutoff_date
    ).all()
    
    # Group by date
    daily_stats = {}
    for feedback in feedback_records:
        date_key = feedback.created_at.date().isoformat()
        if date_key not in daily_stats:
            daily_stats[date_key] = {"total": 0, "approved": 0}
        daily_stats[date_key]["total"] += 1
        if feedback.approved:
            daily_stats[date_key]["approved"] += 1
    
    trends = []
    for date_str in sorted(daily_stats.keys()):
        stats = daily_stats[date_str]
        approval_rate = (stats["approved"] / stats["total"] * 100) if stats["total"] > 0 else 0
        trends.append({
            "date": date_str,
            "total_decisions": stats["total"],
            "approved": stats["approved"],
            "rejected": stats["total"] - stats["approved"],
            "approval_rate": round(approval_rate, 1)
        })
    
    # Calculate trend direction
    if len(trends) > 1:
        first_week_avg = sum(t["approval_rate"] for t in trends[:7]) / min(7, len(trends))
        last_week_avg = sum(t["approval_rate"] for t in trends[-7:]) / min(7, len(trends))
        trend_direction = "improving" if last_week_avg > first_week_avg else "stable" if abs(last_week_avg - first_week_avg) < 5 else "declining"
    else:
        trend_direction = "insufficient_data"
    
    return {
        "status": "success",
        "daily_trends": trends,
        "trend_direction": trend_direction,
        "period_days": days,
        "total_decisions": sum(t["total_decisions"] for t in trends),
        "average_approval_rate": round(sum(t["approval_rate"] for t in trends) / len(trends), 1) if trends else 0
    }


@router.get("/analytics/memory-summary")
def get_memory_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Overall statistics about the agent's persistent memory.
    Shows composition and span of stored history.
    """
    from app.models import schemas
    
    total_memories = db.query(schemas.AgentMemory).count()
    total_feedback = db.query(schemas.Feedback).count()
    auto_feedback = db.query(schemas.Feedback).filter(
        schemas.Feedback.note.like('[AUTO]%')
    ).count()
    manual_feedback = total_feedback - auto_feedback
    
    oldest_memory = db.query(schemas.AgentMemory).order_by(
        schemas.AgentMemory.created_at.asc()
    ).first()
    
    memory_span_days = (datetime.utcnow() - oldest_memory.created_at).days if oldest_memory else 0
    
    avg_memory_size = 500
    total_size_mb = (total_memories * avg_memory_size) / (1024 * 1024)
    
    return {
        "status": "success",
        "total_memories": total_memories,
        "total_feedback": total_feedback,
        "auto_feedback": auto_feedback,
        "manual_feedback": manual_feedback,
        "memory_span_days": memory_span_days,
        "estimated_storage_mb": round(total_size_mb, 2),
        "avg_decisions_per_day": round(total_memories / max(1, memory_span_days), 1) if memory_span_days > 0 else 0
    }
