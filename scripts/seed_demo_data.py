"""
Demo Data Seeding Script for Agent Video Showcase
Creates 15 affordable items with varied stock levels to demonstrate:
- Budget optimization
- Negotiation with quantity reduction
- Multiple approvals within budget
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.database import SessionLocal

def clear_existing_data(session):
    """Clear all existing data from relevant tables"""
    print("🗑️  Clearing existing data...")
    session.execute(text("DELETE FROM orders"))
    session.execute(text("DELETE FROM sales"))
    session.execute(text("DELETE FROM inventory"))
    session.commit()
    print("✅ Existing data cleared")

def seed_demo_inventory(session):
    """Seed 15 affordable demo items with varied stock levels"""
    print("📦 Seeding demo inventory...")
    
    # 15 affordable items for demo
    items = [
        # CRITICAL STOCK (0-10 units) - Will trigger immediate reordering
        {"sku": "OFF-001", "name": "Ballpoint Pens (Pack of 12)", "stock": 2, "threshold": 50, "price": 15.99, "lead_time": 3},
        {"sku": "OFF-002", "name": "Sticky Notes (100 sheets)", "stock": 5, "threshold": 40, "price": 8.99, "lead_time": 2},
        {"sku": "OFF-003", "name": "Paper Clips (Box of 100)", "stock": 3, "threshold": 45, "price": 4.99, "lead_time": 2},
        {"sku": "FOOD-001", "name": "Coffee Beans (1kg)", "stock": 8, "threshold": 50, "price": 24.99, "lead_time": 5},
        {"sku": "FOOD-002", "name": "Green Tea (50 bags)", "stock": 4, "threshold": 35, "price": 12.99, "lead_time": 4},
        {"sku": "TECH-001", "name": "USB Flash Drive 16GB", "stock": 6, "threshold": 40, "price": 18.99, "lead_time": 7},
        {"sku": "TECH-002", "name": "HDMI Cable (2m)", "stock": 9, "threshold": 30, "price": 14.99, "lead_time": 5},
        {"sku": "CLEAN-001", "name": "Hand Sanitizer (500ml)", "stock": 7, "threshold": 60, "price": 9.99, "lead_time": 3},
        
        # MODERATE STOCK (20-50 units) - May trigger reordering based on forecast
        {"sku": "OFF-004", "name": "Markers (Set of 8)", "stock": 35, "threshold": 40, "price": 11.99, "lead_time": 3},
        {"sku": "FOOD-003", "name": "Bottled Water (24-pack)", "stock": 25, "threshold": 50, "price": 6.99, "lead_time": 2},
        {"sku": "TECH-003", "name": "Mouse Pad", "stock": 42, "threshold": 35, "price": 7.99, "lead_time": 4},
        {"sku": "CLEAN-002", "name": "Paper Towels (6-pack)", "stock": 28, "threshold": 40, "price": 16.99, "lead_time": 3},
        
        # ACCEPTABLE STOCK (60-100 units) - Should not trigger reordering
        {"sku": "OFF-005", "name": "Notebooks (A5, 100 pages)", "stock": 75, "threshold": 50, "price": 5.99, "lead_time": 4},
        {"sku": "FOOD-004", "name": "Instant Noodles (5-pack)", "stock": 90, "threshold": 60, "price": 8.99, "lead_time": 5},
        {"sku": "TECH-004", "name": "AA Batteries (4-pack)", "stock": 85, "threshold": 55, "price": 9.99, "lead_time": 6},
    ]
    
    for item in items:
        session.execute(text("""
            INSERT INTO inventory (sku, product_name, quantity, threshold, unit_price, lead_time_days, supplier, min_order_qty, safety_stock, category, is_active)
            VALUES (:sku, :name, :quantity, :threshold, :price, :lead_time, 'Demo Supplier Co.', 10, 20, 'Demo', true)
        """), {
            "sku": item["sku"],
            "name": item["name"],
            "quantity": item["stock"],
            "threshold": item["threshold"],
            "price": item["price"],
            "lead_time": item["lead_time"]
        })
    
    session.commit()
    print(f"✅ Seeded {len(items)} demo items")
    return items

def seed_demo_sales(session, items):
    """Seed realistic sales data for demo items"""
    print("💰 Seeding demo sales data...")
    
    # Generate sales for the past 30 days
    sales_count = 0
    base_date = datetime.now() - timedelta(days=30)
    
    for item in items:
        # Critical items: high sales velocity
        # Moderate items: medium sales velocity  
        # Acceptable items: low sales velocity
        
        if item["stock"] < 15:  # Critical stock items
            daily_sales = 15  # High demand
        elif item["stock"] < 40:  # Moderate stock items
            daily_sales = 8   # Medium demand
        else:  # Acceptable stock items
            daily_sales = 3   # Low demand
        
        # Generate sales for past 30 days
        for day in range(30):
            sale_date = base_date + timedelta(days=day)
            
            # Vary quantity slightly (±3 units)
            import random
            quantity = max(1, daily_sales + random.randint(-3, 3))
            total = quantity * item["price"]
            
            session.execute(text("""
                INSERT INTO sales (sku, sold_quantity, date)
                VALUES (:sku, :qty, :date)
            """), {
                "sku": item["sku"],
                "qty": quantity,
                "date": sale_date
            })
            sales_count += 1
    
    session.commit()
    print(f"✅ Seeded {sales_count} sales records")

def main():
    """Main seeding function"""
    print("="*60)
    print("🎬 DEMO DATA SEEDING FOR AGENT VIDEO SHOWCASE")
    print("="*60)
    
    session = SessionLocal()
    
    try:
        # Step 1: Clear existing data
        clear_existing_data(session)
        
        # Step 2: Seed demo inventory
        items = seed_demo_inventory(session)
        
        # Step 3: Seed demo sales
        seed_demo_sales(session, items)
        
        print("\n" + "="*60)
        print("✅ DEMO DATA SEEDING COMPLETE!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   - 15 demo items with affordable prices ($5-$25)")
        print(f"   - 8 critical stock items (stock < 15)")
        print(f"   - 4 moderate stock items (stock 20-50)")
        print(f"   - 3 acceptable stock items (stock > 60)")
        print(f"   - 30 days of realistic sales data")
        print("\n🎥 Ready for agent demo video!")
        print("\n⚙️  Next Step: Update budget to $600 in settings.py")
        print("   This will trigger negotiation when 8-10 items need reordering")
        print("\nExpected Agent Behavior:")
        print("   1. Forecast will predict high demand for critical items")
        print("   2. Decision will propose reorders for 8-10 items (~$1,000 total)")
        print("   3. Finance will reject items (budget $600 < cost $1,000)")
        print("   4. Negotiation will propose quantity reductions")
        print("   5. Finance re-optimizes and approves 6-7 items within $600 budget")
        print("\n💡 Total estimated cost: ~$1,000 (exceeds $600 budget → triggers negotiation)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
