from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import database, schemas
from app.utils.groq_utils import query_groq
from app.utils.common import serialize_model
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_alerts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    alerts = db.query(schemas.Alerts).order_by(schemas.Alerts.created_at.desc()).limit(500).all()
    return serialize_model(alerts)  # ✅ FIXED: Serialize ORM objects to JSON-friendly dicts

@router.post("/")
def create_alert(message: str, type: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    alert = schemas.Alerts(message=message, type=type)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return {"message": "Alert created successfully", "data": alert}

@router.get("/analyze")
def analyze_alerts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    alerts = db.query(schemas.Alerts).all()
    clean = serialize_model(alerts)

    from app.agents.langgraph_flow import AgentController
    ctrl = AgentController(session_factory=database.SessionLocal)
    
    # Call run_cycle which analyzes current alerts and inventory
    result = ctrl.run_cycle()  # ✅ FIXED: Use existing run_cycle instead of non-existent function

    return {
        "analysis": {
            "alerts_analyzed": len(alerts),
            "results": result.get("results", []),
            "run_at": result.get("run_at")
        }
    }
