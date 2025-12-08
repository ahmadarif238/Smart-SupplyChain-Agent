from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import database, schemas
from pydantic import BaseModel
from app.utils.common import serialize_model
from app.utils.groq_utils import query_groq
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Define request schema for POST
class InventoryCreate(BaseModel):
    product_name: str
    sku: str
    quantity: int
    threshold: int
    unit_price: float = 0.0
    category: str = "General"
    supplier: str = "Unknown"
    lead_time_days: int = 7
    safety_stock: int = 10

@router.get("/")
def get_inventory(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = db.query(schemas.Inventory).all()
    return serialize_model(items)  # ✅ FIXED: Serialize ORM objects

# ✅ FIXED ENDPOINT
@router.post("/")
def add_item(item: InventoryCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_item = schemas.Inventory(
        product_name=item.product_name,
        sku=item.sku,
        quantity=item.quantity,
        threshold=item.threshold,
        unit_price=item.unit_price,
        category=item.category,
        supplier=item.supplier,
        lead_time_days=item.lead_time_days,
        safety_stock=item.safety_stock
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"message": "Item added successfully", "data": serialize_model(new_item)}

@router.get("/forecast")
def inventory_forecast(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    items = db.query(schemas.Inventory).all()
    
    from app.agents.langgraph_flow import AgentController
    ctrl = AgentController(session_factory=database.SessionLocal)
    
    result = ctrl.run_cycle()  # ✅ FIXED: Run single cycle instead of calling non-existent function

    return {
        "forecast": result.get("results", []),
        "run_at": result.get("run_at"),
        "urgent": result.get("urgent")
    }