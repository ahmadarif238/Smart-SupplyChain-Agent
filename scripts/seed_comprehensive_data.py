"""
Comprehensive Data Seeder for Smart Supply Chain Agent
Creates 100 diverse products with realistic scenarios for testing
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models import schemas

# Product categories with different characteristics
PRODUCT_CATEGORIES = {
    "Electronics": {
        "prefix": "ELEC",
        "unit_price_range": (50, 500),
        "demand_pattern": "volatile",  # High variance
        "lead_time_range": (14, 30),
        "margin": 0.3
    },
    "Apparel": {
        "prefix": "APRL",
        "unit_price_range": (20, 150),
        "demand_pattern": "seasonal",  # Varies by season
        "lead_time_range": (21, 45),
        "margin": 0.5
    },
    "Food": {
        "prefix": "FOOD",
        "unit_price_range": (5, 50),
        "demand_pattern": "stable",  # Low variance
        "lead_time_range": (3, 7),
        "margin": 0.2
    },
    "Furniture": {
        "prefix": "FURN",
        "unit_price_range": (100, 1000),
        "demand_pattern": "low_volume",  # Occasional sales
        "lead_time_range": (30, 60),
        "margin": 0.4
    },
    "Toys": {
        "prefix": "TOY",
        "unit_price_range": (10, 80),
        "demand_pattern": "seasonal",  # Christmas spike
        "lead_time_range": (14, 21),
        "margin": 0.45
    }
}

# Supplier names
SUPPLIERS = ["Acme Corp", "Global Supply Ltd", "FastShip Inc", "QualityFirst Co", "BudgetSupplies"]

# Product name generators
PRODUCT_NAMES = {
    "Electronics": ["Smartphone", "Laptop", "Tablet", "Headphones", "Smartwatch", "Camera", "Speaker", "Monitor"],
    "Apparel": ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes", "Hat", "Scarf", "Socks"],
    "Food": ["Coffee", "Tea", "Pasta", "Rice", "Oil", "Flour", "Sugar", "Salt"],
    "Furniture": ["Chair", "Table", "Desk", "Sofa", "Bed", "Shelf", "Cabinet", "Lamp"],
    "Toys": ["Action Figure", "Doll", "Board Game", "Puzzle", "Building Blocks", "RC Car", "Stuffed Animal", "Ball"]
}


def generate_sales_history(sku: str, category_info: dict, days_back: int = 90) -> list:
    """Generate realistic sales history based on demand pattern"""
    sales = []
    pattern = category_info["demand_pattern"]
    
    for i in range(days_back):
        date = datetime.utcnow() - timedelta(days=days_back - i)
        
        if pattern == "stable":
            # Low variance, predictable
            base_demand = random.randint(5, 15)
            variance = random.randint(-2, 2)
            quantity = max(0, base_demand + variance)
            
        elif pattern == "volatile":
            # High variance, unpredictable
            base_demand = random.randint(10, 30)
            variance = random.randint(-15, 20)
            quantity = max(0, base_demand + variance)
            
        elif pattern == "seasonal":
            # Varies by day of week and seasonality
            base_demand = random.randint(5, 20)
            # Weekend boost
            if date.weekday() >= 5:
                base_demand *= 1.5
            # Month-based seasonality
            month_factor = 1 + (abs(date.month - 6) / 10)  # Higher in Dec/Jan
            quantity = int(base_demand * month_factor)
            
        elif pattern == "low_volume":
            # Occasional large orders
            if random.random() < 0.2:  # 20% chance of sale
                quantity = random.randint(1, 5)
            else:
                quantity = 0
        else:
            quantity = random.randint(1, 10)
        
        if quantity > 0:
            sales.append({
                "date": date,
                "quantity": quantity
            })
    
    return sales


def create_comprehensive_dataset(db: Session):
    """Create 100 diverse products with realistic data"""
    
    print("🗑️  Clearing existing data...")
    db.query(schemas.Sales).delete()
    db.query(schemas.Orders).delete()
    db.query(schemas.Feedback).delete()
    db.query(schemas.SKUParameters).delete()
    db.query(schemas.Inventory).delete()
    db.commit()
    
    print("📦 Creating 100 products...")
    
    products_created = 0
    
    for category, category_info in PRODUCT_CATEGORIES.items():
        # Create 20 products per category
        for i in range(20):
            sku = f"{category_info['prefix']}-{i+1:03d}"
            
            # Generate product attributes
            unit_price = random.uniform(*category_info['unit_price_range'])
            lead_time = random.randint(*category_info['lead_time_range'])
            
            # Calculate current stock (some critical, some overstocked)
            stock_scenario = random.choice(['critical', 'low', 'medium', 'high', 'overstocked'])
            if stock_scenario == 'critical':
                quantity = random.randint(0, 5)
                threshold = random.randint(20, 30)
            elif stock_scenario == 'low':
                quantity = random.randint(10, 20)
                threshold = random.randint(25, 40)
            elif stock_scenario == 'medium':
                quantity = random.randint(40, 80)
                threshold = random.randint(30, 50)
            elif stock_scenario == 'high':
                quantity = random.randint(100, 200)
                threshold = random.randint(40, 60)
            else:  # overstocked
                quantity = random.randint(300, 500)
                threshold = random.randint(50, 70)
            
            # Create product
            product_name = f"{random.choice(PRODUCT_NAMES[category])} {category} {i+1}"
            supplier = random.choice(SUPPLIERS)
            
            product = schemas.Inventory(
                sku=sku,
                product_name=product_name,
                quantity=quantity,
                threshold=threshold,
                unit_price=round(unit_price, 2),
                holding_cost_percent=random.uniform(0.10, 0.20),
                reorder_cost=random.uniform(20, 100),
                lead_time_days=lead_time,
                supplier=supplier,
                min_order_qty=random.randint(10, 50),
                max_order_qty=random.randint(500, 2000),
                safety_stock=random.randint(15, 40),
                reorder_point=threshold + random.randint(10, 30),
                category=category,
                is_active=True
            )
            db.add(product)
            
            # Generate sales history
            sales_history = generate_sales_history(sku, category_info, days_back=90)
            for sale_data in sales_history:
                sale = schemas.Sales(
                    sku=sku,
                    sold_quantity=sale_data['quantity'],
                    date=sale_data['date']
                )
                db.add(sale)
            
            products_created += 1
            
            if products_created % 20 == 0:
                print(f"   ✓ Created {products_created} products...")
    
    db.commit()
    print(f"✅ Created {products_created} products with sales history!")
    
    # Create synthetic feedback to kickstart learning
    print("\n🎓 Creating synthetic feedback for learning system...")
    create_synthetic_feedback(db)
    
    print("\n📊 Database Statistics:")
    print(f"   - Inventory items: {db.query(schemas.Inventory).count()}")
    print(f"   - Sales records: {db.query(schemas.Sales).count()}")
    print(f"   - Feedback records: {db.query(schemas.Feedback).count()}")
    print(f"   - Categories: {len(PRODUCT_CATEGORIES)}")


def create_synthetic_feedback(db: Session):
    """Create synthetic user feedback to kickstart the learning system"""
    
    # Get all SKUs
    all_skus = db.query(schemas.Inventory.sku).all()
    
    # Create feedback for 30% of products (to simulate partial user engagement)
    sample_size = int(len(all_skus) * 0.3)
    sampled_skus = random.sample(all_skus, sample_size)
    
    feedback_count = 0
    
    for (sku,) in sampled_skus:
        # Create 5-15 feedback entries per SKU (simulating a month of usage)
        num_feedbacks = random.randint(5, 15)
        
        # Simulate different accuracy levels for different products
        accuracy_level = random.choice(['high', 'medium', 'low'])
        
        if accuracy_level == 'high':
            approval_rate = 0.95  # 95% good decisions
        elif accuracy_level == 'medium':
            approval_rate = 0.75  # 75% good decisions
        else:
            approval_rate = 0.50  # 50% good decisions
        
        for i in range(num_feedbacks):
            # Create feedback with timestamps spread over 30 days
            days_ago = random.randint(1, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago)
            
            approved = random.random() < approval_rate
            
            feedback = schemas.Feedback(
                memory_id=None,  # Not linked to specific memory for synthetic data
                sku=sku,
                approved=approved,
                note="Synthetic feedback for testing" if not approved else "Good decision",
                created_at=created_at
            )
            db.add(feedback)
            feedback_count += 1
    
    db.commit()
    print(f"   ✓ Created {feedback_count} feedback entries for {sample_size} SKUs")
    print(f"   ✓ Learning system will now have data to work with!")


def print_sample_products(db: Session):
    """Print sample of created products for verification"""
    print("\n📋 Sample Products Created:")
    print("-" * 100)
    
    samples = db.query(schemas.Inventory).limit(10).all()
    
    for p in samples:
        # Get sales count
        sales_count = db.query(schemas.Sales).filter(schemas.Sales.sku == p.sku).count()
        
        print(f"SKU: {p.sku:15} | {p.product_name:30} | Stock: {p.quantity:4} | Threshold: {p.threshold:3} | "
              f"Price: ${p.unit_price:6.2f} | Sales: {sales_count:3} | Supplier: {p.supplier}")
    
    print("-" * 100)
    
    # Print stock level distribution
    print("\n📊 Stock Level Distribution:")
    critical = db.query(schemas.Inventory).filter(schemas.Inventory.quantity < schemas.Inventory.threshold).count()
    low = db.query(schemas.Inventory).filter(
        schemas.Inventory.quantity >= schemas.Inventory.threshold,
        schemas.Inventory.quantity < schemas.Inventory.threshold * 2
    ).count()
    medium = db.query(schemas.Inventory).filter(
        schemas.Inventory.quantity >= schemas.Inventory.threshold * 2,
        schemas.Inventory.quantity < schemas.Inventory.threshold * 4
    ).count()
    high = db.query(schemas.Inventory).filter(schemas.Inventory.quantity >= schemas.Inventory.threshold * 4).count()
    
    print(f"   🔴 Critical (below threshold): {critical}")
    print(f"   🟡 Low (1-2x threshold): {low}")
    print(f"   🟢 Medium (2-4x threshold): {medium}")
    print(f"   🔵 High (4x+ threshold): {high}")


if __name__ == "__main__":
    print("=" * 100)
    print("🚀 Smart Supply Chain Agent - Comprehensive Data Seeder")
    print("=" * 100)
    print()
    
    db = SessionLocal()
    try:
        create_comprehensive_dataset(db)
        print_sample_products(db)
        
        print("\n" + "=" * 100)
        print("✅ Data seeding complete! You can now run the agent.")
        print("=" * 100)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
