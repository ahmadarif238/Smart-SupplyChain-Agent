from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import database, schemas
from app.utils.common import serialize_model
from datetime import datetime, timedelta
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_orders(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Sort by date descending and limit to recent 50
    orders = db.query(schemas.Orders).order_by(schemas.Orders.order_date.desc()).limit(50).all()
    
    # Enrich orders with product names and price from inventory
    result = []
    for order in orders:
        order_dict = serialize_model(order)
        
        # Look up product details from inventory by SKU
        inventory_item = db.query(schemas.Inventory).filter(
            schemas.Inventory.sku == order.sku
        ).first()
        
        if inventory_item:
            order_dict["product_name"] = inventory_item.product_name
            order_dict["supplier"] = inventory_item.supplier
            
            # Calculate total price
            unit_price = inventory_item.unit_price if inventory_item.unit_price is not None else 0.0
            order_dict["total_price"] = round(unit_price * order.quantity, 2)
        else:
            order_dict["product_name"] = order.sku  # Fallback to SKU
            order_dict["supplier"] = "Unknown"
            order_dict["total_price"] = 0.0
        
        result.append(order_dict)
    
    return result

@router.post("/")
def create_order(sku: str, quantity: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    order = schemas.Orders(sku=sku, quantity=quantity, status="Pending")
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"message": "Order created successfully", "data": serialize_model(order)}

@router.get("/recommend")
def recommend_orders(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Recommend orders by priority based on status and age.
    - Urgent: Pending orders older than 7 days
    - Upcoming: Recent pending orders (0-7 days)
    - Low Priority: Completed orders
    """
    orders = db.query(schemas.Orders).all()
    
    urgent = []
    upcoming = []
    low_priority = []
    
    # Use timezone-naive datetime for comparison (matches database timestamps)
    from datetime import datetime as dt
    cutoff_date = dt.utcnow() - timedelta(days=7)
    
    for order in orders:
        order_dict = serialize_model(order)
        
        try:
            order_date = order.order_date
            
            # Ensure both datetimes are comparable (strip timezone info if present)
            if order_date.tzinfo is not None:
                order_date = order_date.replace(tzinfo=None)
            if cutoff_date.tzinfo is not None:
                cutoff_date = cutoff_date.replace(tzinfo=None)
            
            if order.status.lower() == "completed":
                low_priority.append(order_dict)
            elif order.status.lower() == "pending":
                if order_date < cutoff_date:
                    urgent.append(order_dict)
                else:
                    upcoming.append(order_dict)
            else:
                upcoming.append(order_dict)
        except (AttributeError, TypeError):
            # If order_date is None or invalid, put in upcoming
            upcoming.append(order_dict)
    
    # Sort by date
    urgent.sort(key=lambda x: x.get("order_date", ""), reverse=True)
    upcoming.sort(key=lambda x: x.get("order_date", ""), reverse=True)
    
    return {
        "recommendation": {
            "UrgentOrders": urgent,
            "UpcomingOrders": upcoming,
            "LowPriority": low_priority,
            "summary": {
                "urgent_count": len(urgent),
                "upcoming_count": len(upcoming),
                "completed_count": len(low_priority)
            }
        }
    }

