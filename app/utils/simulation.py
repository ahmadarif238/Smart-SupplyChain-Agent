import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import schemas
import logging

logger = logging.getLogger("simulation")

def simulate_market_activity(db: Session):
    """
    Simulate market activity to create dynamic changes between agent runs.
    1. Generate random sales for active products
    2. Deplete inventory based on sales
    3. Update 'recent sales revenue' for dynamic budgeting
    """
    logger.info("🎲 Simulating market activity...")
    
    inventory_items = db.query(schemas.Inventory).all()
    total_revenue = 0.0
    sales_count = 0
    
    for item in inventory_items:
        # 10% chance of sales per item per cycle, or higher if stock is high
        if random.random() < 0.3:  # 30% chance of activity
            # Sell 1-5 units or 10% of stock
            max_sales = max(1, int(item.quantity * 0.1))
            qty_sold = random.randint(1, max(1, max_sales))
            
            if item.quantity >= qty_sold:
                # Update Inventory
                item.quantity -= qty_sold
                
                # Record Sale
                sale = schemas.Sales(
                    sku=item.sku,
                    sold_quantity=qty_sold,
                    date=datetime.utcnow()
                )
                db.add(sale)
                
                # Calculate Revenue
                unit_price = item.unit_price or 10.0
                revenue = qty_sold * unit_price
                total_revenue += revenue
                sales_count += 1
                
                logger.info(f"📉 Sold {qty_sold} of {item.sku}. New Stock: {item.quantity}")
            else:
                logger.warning(f"⚠️ Stockout! Could not sell {qty_sold} of {item.sku}")
    
    db.commit()
    logger.info(f"✅ Simulation complete. {sales_count} sales generated. Revenue: ${total_revenue:.2f}")
    return total_revenue
