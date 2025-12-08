from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import database, schemas
from app.utils.groq_utils import query_groq
from pydantic import BaseModel
from app.models.schemas import Sales, Inventory
from datetime import datetime
from app.utils.common import serialize_model
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/sales", tags=["Sales"])

class SaleInput(BaseModel):
    sku: str
    sold_quantity: int

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_sales(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(schemas.Sales).order_by(schemas.Sales.date.desc()).all()

@router.post("/")
async def add_sale(sale: SaleInput, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1️⃣ Check if SKU exists in inventory
    inventory_item = db.query(Inventory).filter(Inventory.sku == sale.sku).first()
    if not inventory_item:
        raise HTTPException(status_code=404, detail="SKU not found in inventory")

    # 2️⃣ Reduce stock quantity (use 'quantity' instead of 'stock')
    if inventory_item.quantity < sale.sold_quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock for this sale")

    inventory_item.quantity -= sale.sold_quantity

    # 3️⃣ Record sale in database
    new_sale = Sales(
        sku=sale.sku,
        sold_quantity=sale.sold_quantity,
        date=datetime.now()
    )
    db.add(new_sale)
    db.commit()

    # 4️⃣ Return updated stock and confirmation
    return {
        "message": "Sale recorded and stock updated successfully",
        "data": {
            "sku": sale.sku,
            "sold_quantity": sale.sold_quantity,
            "remaining_stock": inventory_item.quantity
        }
    }

@router.get("/summary")
def sales_summary(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    sales = db.query(schemas.Sales).all()
    clean = serialize_model(sales)

    from app.agents.langgraph_flow import run_tool_sales_summary

    result = run_tool_sales_summary(clean)

    return {
        "summary": {
            "TopProducts": result.get("TopProducts", []),
            "DecliningProducts": result.get("DecliningProducts", []),
            "RevenueTrend": result.get("RevenueTrend", ""),
            "ActionableInsights": result.get("ActionableInsights", [])
        }
    }

