"""Test decision subgraph nodes"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.state import CycleState
from app.agents.nodes.fetch_data_node import fetch_data_node
from app.agents.nodes.forecast_node import forecast_node
from app.agents.nodes.decision_subgraph import analyze_trends_node, check_constraints_node, optimize_cost_node
from uuid import uuid4
from datetime import datetime

def test_decision_pipeline():
    # Setup
    state = CycleState(
        cycle_id=str(uuid4())[:8],
        cycle_number=1,
        started_at=datetime.utcnow()
    )
    
    # Step 1: Fetch + Forecast
    state = fetch_data_node(state)
    state = forecast_node(state)
    
    print("="*60)
    print("AFTER FORECAST")
    print("="*60)
    print(f"Forecast Results: {len(state.forecast_results)} items")
    print(f"SKUs: {[f['sku'] for f in state.forecast_results]}")
    
    #  Step 2: Analyze Trends
    print("\n" + "="*60)
    print("STEP: Analyze Trends")
    print("="*60)
    state = analyze_trends_node(state)
    print(f"Analyzed SKUs: {len(state.analyzed_skus)} items")
    print(f"SKUs: {[a['sku'] for a in state.analyzed_skus]}")
    
    # Step 3: Check Constraints
    print("\n" + "="*60)
    print("STEP: Check Constraints")
    print("="*60)
    state = check_constraints_node(state)
    print(f"Constrained SKUs: {len(state.constrained_skus)} items")
    print(f"SKUs: {[c['sku'] for c in state.constrained_skus]}")
    
    # Step 4: Optimize Cost
    print("\n" + "="*60)
    print("STEP: Optimize Cost")
    print("="*60)
    state = optimize_cost_node(state)
    print(f"Decisions: {len(state.decisions)} items")
    print(f"SKUs: {[d['sku'] for d in state.decisions]}")
    
    # Show final reorders
    reorders = [d for d in state.decisions if d.get('reorder_required')]
    print(f"\n✅ Reorders: {len(reorders)} items")
    for d in reorders:
        print(f"  - {d['sku']} ({d['product_name']}): {d['order_quantity']} units")

if __name__ == "__main__":
    test_decision_pipeline()
