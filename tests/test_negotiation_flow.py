
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agents.langgraph_workflow import app, ensure_state
from app.agents.state import CycleState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_negotiation_flow():
    """
    Simulate a cycle where orders exceed budget to trigger negotiation.
    """
    print("\n🧪 STARTING NEGOTIATION FLOW TEST\n" + "="*50)
    
    # 1. Setup Mock State
    # Budget is $5000 (default in FinanceNode)
    # We will create orders totaling $8000
    
    initial_state = {
        "cycle_id": "test-negotiation-001",
        "cycle_number": 1,
        "started_at": datetime.utcnow(),
        "inventory_data": {
            "SKU-HIGH-COST": {"quantity": 5, "threshold": 20, "sku": "SKU-HIGH-COST"},
            "SKU-LOW-PRIORITY": {"quantity": 10, "threshold": 15, "sku": "SKU-LOW-PRIORITY"}
        },
        "decisions": [
            {
                "sku": "SKU-HIGH-COST",
                "product_name": "High Cost Widget",
                "reorder_required": True,
                "order_quantity": 50,
                "cost_analysis": {
                    "cost_per_unit": 100.0,
                    "purchasing_cost_per_unit": 100.0
                }, 
                "details": {
                    "daily_avg_demand": 2.0,
                    "lead_time_days": 7,
                    "current_stock": 5,
                    "unit_price": 100.0
                },
                "reason": "Critical stockout risk"
            },
            {
                "sku": "SKU-LOW-PRIORITY",
                "product_name": "Low Priority Widget",
                "reorder_required": True,
                "order_quantity": 100,
                "cost_analysis": {
                    "cost_per_unit": 30.0,
                    "purchasing_cost_per_unit": 30.0
                }, 
                "details": {
                    "daily_avg_demand": 1.0,
                    "lead_time_days": 7,
                    "current_stock": 10,
                    "unit_price": 30.0
                },
                "reason": "Routine restocking"
            }
        ],
        "budget": 5000.0,
        "recent_sales_revenue": 0.0,
        "finance_rejections": [],
        "counter_arguments": [],
        "negotiation_rounds": 0,
        "max_negotiation_rounds": 3,
        "agent_dialogues": []
    }
    
    # 2. Run Workflow
    # We need to bypass fetch/forecast/decision nodes and start at finance?
    # LangGraph usually starts at entry point.
    # But we can invoke the app with this state, and if we mock the earlier nodes to pass through or 
    # if we just want to test the loop, we might need to be careful.
    # 
    # Actually, the workflow defines:
    # fetch -> forecast -> analyze -> check -> optimize -> finance
    # 
    # If we pass 'decisions' in the initial state, the earlier nodes might overwrite them if they run.
    # Let's see if we can just run the relevant nodes or if we need to let the whole thing run.
    # 
    # The 'fetch_data' node will overwrite inventory_data.
    # The 'decision_node' (subgraph) will overwrite decisions.
    # 
    # To test JUST the negotiation loop, we might want to unit test the nodes or 
    # temporarily modify the workflow for this test script, OR mock the node functions.
    # 
    # Let's try to mock the node wrappers in this script before importing/running? 
    # No, they are already imported in langgraph_workflow.
    
    # Alternative: We can manually invoke the nodes in sequence to simulate the graph
    # since we have access to the node functions (wrappers).
    
    from app.agents.langgraph_workflow import finance_node_wrapper, negotiation_node_wrapper, should_negotiate, action_node_wrapper
    
    state = CycleState(**initial_state)
    
    print(f"💰 Initial Budget: ${state.budget}")
    print(f"📦 Initial Orders: ${sum(d['cost_analysis']['cost_per_unit'] * d['order_quantity'] for d in state.decisions)}")
    
    # --- ROUND 1 ---
    print("\n🔄 --- ROUND 1: FINANCE REVIEW ---")
    state_dict = finance_node_wrapper(state)
    state = CycleState(**state_dict)
    
    print(f"   Approved: {len(state.decisions)}")
    print(f"   Rejected: {len(state.finance_rejections)}")
    
    if not state.finance_rejections:
        print("❌ Test Failed: Expected rejections but got none.")
        return
        
    # Check conditional
    next_step = should_negotiate(state)
    print(f"   Next Step: {next_step}")
    
    if next_step != "negotiation":
        print("❌ Test Failed: Expected negotiation step.")
        return

    # --- NEGOTIATION ---
    print("\n🗣️ --- NEGOTIATION PHASE ---")
    state_dict = negotiation_node_wrapper(state)
    state = CycleState(**state_dict)
    
    print(f"   Counter-Arguments: {len(state.counter_arguments)}")
    for arg in state.counter_arguments:
        print(f"   - {arg['product_name']}: {arg['strategy']}")
        print(f"     Proposal: {arg.get('proposal', 'N/A')}")

    # --- ROUND 2 ---
    print("\n🔄 --- ROUND 2: FINANCE RE-EVALUATION ---")
    state_dict = finance_node_wrapper(state)
    state = CycleState(**state_dict)
    
    print(f"   Approved: {len(state.decisions)}")
    print(f"   Rejected: {len(state.finance_rejections)}")
    print(f"   Overrides: {state_dict.get('overrides', 0)}")
    
    # Check if we are done or looping again
    next_step = should_negotiate(state)
    print(f"   Next Step: {next_step}")
    
    print("\n✅ TEST COMPLETE")

if __name__ == "__main__":
    test_negotiation_flow()
