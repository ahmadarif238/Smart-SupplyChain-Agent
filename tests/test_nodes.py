"""
Check the state.errors and forecast_results by running the fetch and forecast nodes manually
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.state import CycleState
from app.agents.nodes.fetch_data_node import fetch_data_node
from app.agents.nodes.forecast_node import forecast_node
from uuid import uuid4
from datetime import datetime

def test_nodes():
    # Create initial state
    state = CycleState(
        cycle_id=str(uuid4())[:8],
        cycle_number=1,
        started_at=datetime.utcnow()
    )
    
    print("="*60)
    print("STEP 1: Fetch Data")
    print("="*60)
    state = fetch_data_node(state)
    print(f"Inventory loaded: {len(state.inventory_data)} items")
    print(f"SKUs: {list(state.inventory_data.keys())}")
    
    print("\n" + "="*60)
    print("STEP 2: Forecast")
    print("="*60)
    state = forecast_node(state)
    print(f"Forecasts generated: {len(state.forecast_results)} items")
    print(f"Forecast SKUs: {[f['sku'] for f in state.forecast_results]}")
    
    print("\n" + "="*60)
    print("ERRORS")
    print("="*60)
    if state.errors:
        for error in state.errors:
            print(f"ERROR: {error}")
    else:
        print("No errors")
    
    print("\n" + "="*60)
    print("MISSING ITEMS")
    print("="*60)
    inventory_skus = set(state.inventory_data.keys())
    forecast_skus = set(f['sku'] for f in state.forecast_results)
    missing = inventory_skus - forecast_skus
    
    if missing:
        print(f"❌ These items were NOT forecasted: {missing}")
    else:
        print("✅ All items were forecasted")

if __name__ == "__main__":
    test_nodes()
