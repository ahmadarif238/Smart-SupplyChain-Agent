# app/agents/langgraph_workflow.py
"""LangGraph workflow for the autonomous supply chain agent."""

import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.state import CycleState
from app.agents.nodes.fetch_data_node import fetch_data_node
from app.agents.nodes.forecast_node import forecast_node
from app.agents.nodes.decision_node import DecisionNode
from app.agents.nodes.action_node import ActionNode
from app.agents.nodes.memory_node import MemoryNode
from app.agents.memory_manager import MemoryManager
from app.models.database import SessionLocal
from app.agents.streaming import job_stream_manager
from app.agents.nodes.finance_node import FinanceNode
from app.config.settings import settings

# Import Decision Subgraph Nodes
from app.agents.nodes.decision_subgraph import analyze_trends_node, check_constraints_node, optimize_cost_node

logger = logging.getLogger("langgraph_workflow")

import os
import json

def _load_dynamic_budget():
    try:
        config_path = os.path.join("app", "config", "dynamic_settings.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                return data.get("budget", settings.DEFAULT_BUDGET)
    except Exception as e:
        logger.error(f"Failed to load dynamic settings: {e}")
    return settings.DEFAULT_BUDGET

# Initialize node implementations
_finance_node_impl = FinanceNode()
_action_node_impl = ActionNode(session_factory=SessionLocal)
_memory_node_impl = MemoryNode()

# Helper to convert dict states to CycleState for node processing
def ensure_state(state) -> CycleState:
    """Convert dict to CycleState if needed."""
    if isinstance(state, dict):
        return CycleState(**state)
    return state

def state_to_dict(state: CycleState) -> dict:
    """Convert CycleState to dict for LangGraph."""
    return state.__dict__

def fetch_node_wrapper(state) -> dict:
    """Wrapper for fetch_data_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "🔄 Syncing with ERP system...", stage="FETCH")
    result = fetch_data_node(cycle_state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", f"✅ Data synced. {len(result.inventory_data)} SKUs loaded.", stage="FETCH")
    return state_to_dict(result)


def forecast_node_wrapper(state) -> dict:
    """Wrapper for forecast_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "🧠 Analyzing market trends...", stage="FORECAST")
    result = forecast_node(cycle_state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", f"✅ Forecasts updated for {len(result.forecast_results)} items.", stage="FORECAST")
    return state_to_dict(result)

def analyze_trends_wrapper(state) -> dict:
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "📊 Subgraph: Analyzing trends...", stage="DECISION")
    result = analyze_trends_node(cycle_state)
    return state_to_dict(result)

def check_constraints_wrapper(state) -> dict:
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "🚧 Subgraph: Checking constraints...", stage="DECISION")
    result = check_constraints_node(cycle_state)
    return state_to_dict(result)

def optimize_cost_wrapper(state) -> dict:
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "💎 Subgraph: Optimizing cost...", stage="DECISION")
    result = optimize_cost_node(cycle_state)
    
    # Emit summary of decisions
    reorders = [d for d in result.decisions if d.get('reorder_required')]
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", f"Decisions complete. {len(reorders)} reorders identified.", stage="DECISION")
    
    return state_to_dict(result)


def finance_node_wrapper(state) -> dict:
    """Wrapper for finance_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "💰 Finance Agent reviewing budget...", stage="FINANCE")
    
    # Simple strict budget check
    result = _finance_node_impl.review_orders(cycle_state)
    
    # Log feedback
    job_stream_manager.log_event(
        cycle_state.cycle_id,
        "finance_feedback",
        f"💰 {result['finance_feedback']}",
        details={"budget_remaining": result.get("budget_remaining")},
        stage="FINANCE"
    )
    
    return state_to_dict(cycle_state)


def action_node_wrapper(state) -> dict:
    """Wrapper for action_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "🛒 Preparing Purchase Orders...", stage="ACTION")
    
    # Execute each decision (Simulate placing order)
    executed_actions = []
    for decision in cycle_state.decisions:
        if decision.get("reorder_required"):
            action_result = _action_node_impl.execute(decision)
            if action_result.get("executed"):
                executed_actions.append(action_result)
                # Emit granular event for each action
                job_stream_manager.log_event(
                    cycle_state.cycle_id,
                    "action_item",
                    f"✅ Order Placed: {action_result['sku']} - {action_result['quantity']} units",
                    details=action_result,
                    stage="ACTION"
                )
    
    # Update state with executed actions
    cycle_state.actions = executed_actions
    
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", f"✅ Cycle Complete. {len(executed_actions)} orders processed.", stage="ACTION")
    return state_to_dict(cycle_state)


def memory_node_wrapper(state) -> dict:
    """Wrapper for memory_node."""
    cycle_state = ensure_state(state)
    
    # Build summary from state
    summary = {
        "run_at": cycle_state.started_at.isoformat(),
        "summary": []
    }
    
    # Add decisions to summary
    for decision in cycle_state.decisions:
        if decision.get("reorder_required"):
            summary["summary"].append({
                "sku": decision.get("sku"),
                "product_name": decision.get("product_name"),
                "decision": decision
            })
    
    # Save to memory
    _memory_node_impl.append_run_summary(SessionLocal, summary)
    
    return state_to_dict(cycle_state)


# Define the graph with Dict type
workflow = StateGraph(dict)

# Add nodes
workflow.add_node("fetch_data", fetch_node_wrapper)
workflow.add_node("forecast", forecast_node_wrapper)

# Decision Subgraph Nodes
workflow.add_node("analyze_trends", analyze_trends_wrapper)
workflow.add_node("check_constraints", check_constraints_wrapper)
workflow.add_node("optimize_cost", optimize_cost_wrapper)

workflow.add_node("finance", finance_node_wrapper)
workflow.add_node("action", action_node_wrapper)
workflow.add_node("memory", memory_node_wrapper)

# Define edges - Linear Flow
workflow.set_entry_point("fetch_data")
workflow.add_edge("fetch_data", "forecast")
workflow.add_edge("forecast", "analyze_trends")
workflow.add_edge("analyze_trends", "check_constraints")
workflow.add_edge("check_constraints", "optimize_cost")
workflow.add_edge("optimize_cost", "finance")
workflow.add_edge("finance", "action") # Straight to action (Drafting)
workflow.add_edge("action", "memory")
workflow.add_edge("memory", END)

# Compile
app = workflow.compile()

def run_cycle(cycle_id: str, recent_revenue: float = 0.0):
    """Run the LangGraph workflow."""
    initial_state = {
        "cycle_id": cycle_id,
        "cycle_number": 1,
        "started_at": datetime.utcnow(),
        "inventory_data": [],
        "sales_data": [],
        "sales_by_sku": {},
        "orders_data": [],
        "pending_orders_by_sku": {},
        "overdue_orders": [],
        "alerts_data": [],
        "forecast_results": [],
        "analyzed_skus": [],
        "constrained_skus": [],
        "decisions": [],
        "actions": [],
        "agent_dialogues": [],
        "skip_forecast": False,
        "urgent_mode": False,
        "errors": [],
        "failed_skus": [],
        "summary": {},
        "completed": False,
        "budget": _load_dynamic_budget(),
        "recent_sales_revenue": recent_revenue,
        "finance_feedback": "",
        "finance_rejections": [],
        "negotiation_rounds": 0,
        "budget_remaining": 0.0
    }
    
    try:
        result_state = app.invoke(initial_state)
        
        # Result is already a dict
        result_dict = {
            "cycle_id": cycle_id,
            "decisions": result_state.get("decisions", []),
            "actions": result_state.get("actions", []),
            "forecast_results": result_state.get("forecast_results", []),
            "status": "completed",
            "skus_processed": len(result_state.get("inventory_data", [])),
            "errors": result_state.get("errors", [])
        }
        
        return result_dict
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        job_stream_manager.log_event(cycle_id, "error", f"Workflow failed: {str(e)}", stage="ERROR")
        raise e
