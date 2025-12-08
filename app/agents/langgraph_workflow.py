# app/agents/langgraph_workflow.py
"""LangGraph workflow for the autonomous supply chain agent."""

import logging
import threading
from datetime import datetime
from uuid import uuid4
from typing import Generator, Dict, Any

from langgraph.graph import StateGraph, END

from app.agents.state import CycleState
from app.agents.nodes.fetch_data_node import fetch_data_node
from app.agents.nodes.forecast_node import forecast_node
from app.agents.nodes.decision_node import DecisionNode
from app.agents.nodes.action_node import ActionNode
from app.agents.nodes.memory_node import MemoryNode
from app.agents.memory_manager import MemoryManager
from app.models.database import SessionLocal
from app.utils.common import serialize_model
from app.agents.streaming import job_stream_manager

from app.agents.nodes.finance_node import FinanceNode
from app.agents.nodes.negotiation_node import negotiation_node
from app.config.settings import settings

logger = logging.getLogger("langgraph_workflow")

from app.agents.nodes.review_node import ReviewNode

# Initialize node implementations
_decision_node_impl = DecisionNode()
_finance_node_impl = FinanceNode()
_review_node_impl = ReviewNode(approval_threshold=1000.0)
_action_node_impl = ActionNode(session_factory=SessionLocal)
_memory_node_impl = MemoryNode()
_memory_manager = MemoryManager(session_factory=SessionLocal)

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


from app.agents.nodes.decision_subgraph import analyze_trends_node, check_constraints_node, optimize_cost_node

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
    
    # Emit granular events for reorders
    for decision in reorders:
         job_stream_manager.log_event(
            cycle_state.cycle_id, 
            "decision_item", 
            f"⚠️ @FinanceController, requesting budget for {decision['product_name']}. Stock is critical. Need {decision['order_quantity']} units.", 
            details={"sku": decision['sku'], "qty": decision['order_quantity'], "reason": decision.get('reason')},
            stage="DECISION"
        )
        
    return state_to_dict(result)


def finance_node_wrapper(state) -> dict:
    """Wrapper for finance_node with dialogue streaming."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "💰 Finance Agent reviewing budget...", stage="FINANCE")
    try:
        # Check if this is initial review (Round 0) or re-optimization (Round 1+)
        if cycle_state.negotiation_rounds == 0:
            # Round 0: Initial budget review
            result = _finance_node_impl.review_orders(cycle_state)
        else:
            # Round 1+: Re-optimize with negotiation proposals
            logger.info(f"🔄 Finance Round {cycle_state.negotiation_rounds}: Re-optimizing with proposals")
            result = _finance_node_impl.re_optimize_with_proposals(cycle_state)
        
        # Stream agent dialogues to frontend (only NEW ones to avoid duplicates)
        # Track how many dialogues have been streamed before this round
        streamed_count = cycle_state.streamed_dialogues_count
        new_dialogues = cycle_state.agent_dialogues[streamed_count:]
        
        for dialogue in new_dialogues:
            job_stream_manager.log_event(
                cycle_state.cycle_id,
                "agent_dialogue",
                dialogue['message'],
                details={
                    "agent": dialogue['agent'],
                    "target": dialogue.get('target'),
                    "type": dialogue.get('type'),
                    "sku": dialogue.get('sku')
                },
                stage="FINANCE"
            )
        
        # Update streamed count
        cycle_state.streamed_dialogues_count = len(cycle_state.agent_dialogues)
        
        # Emit summary
        overrides = result.get('overrides', 0)
        feedback_msg = f"💰 {result['finance_feedback']}"
        if overrides > 0:
            feedback_msg += f" ✨ {overrides} negotiation wins!"
            
        job_stream_manager.log_event(
            cycle_state.cycle_id,
            "finance_feedback",
            feedback_msg,
            details={"budget_remaining": result.get("budget_remaining")},
            stage="FINANCE"
        )
        
        return state_to_dict(cycle_state)
    except Exception as e:
        logger.error(f"[{cycle_state.cycle_id}] Finance error: {str(e)}")
        job_stream_manager.log_event(cycle_state.cycle_id, "error", f"Finance Agent failed: {e}", stage="FINANCE")
        return state_to_dict(cycle_state)


def negotiation_node_wrapper(state) -> dict:
    """Wrapper for negotiation_node - generates quantity reduction proposals."""
    cycle_state = ensure_state(state)
    logger.debug(f"[{cycle_state.cycle_id}] Entering negotiation_node_wrapper")
    
    try:
        # Get rejected items from finance
        rejected_items = getattr(cycle_state, 'finance_rejections', [])
        approved_items = cycle_state.decisions
        
        if len(rejected_items) > 0:
            logger.debug(f"[{cycle_state.cycle_id}] Rejected Items Count: {len(rejected_items)}")
        if not rejected_items:
            logger.info(f"[{cycle_state.cycle_id}] No rejections to negotiate")
            return state_to_dict(cycle_state)
        
        # Generate quantity reduction proposals (NEW APPROACH)
        logger.info(f"💬 Negotiation: Generating quantity reduction proposals for {len(rejected_items)} items")
        proposals = negotiation_node.generate_counter_arguments(
            cycle_state,
            rejected_items,
            approved_items
        )
        
        # Store proposals in state for Finance to re-optimize
        cycle_state.negotiation_proposals = proposals
        cycle_state.counter_arguments = proposals  # For backward compatibility
        logger.info(f"[{cycle_state.cycle_id}] Generated {len(proposals)} quantity reduction proposals")
        
        # Stream proposals to War Room
        for proposal in proposals:
            sku = proposal.get("sku")
            original_qty = proposal.get("original_quantity")
            new_qty = proposal.get("new_quantity")
            reduction = proposal.get("reduction_factor", 0.5)
            justification = proposal.get("counter_argument", "")
            
            job_stream_manager.log_event(
                cycle_state.cycle_id,
                "agent_dialogue",
                f"💬 PROPOSE: {proposal.get('product_name')} - Reduce quantity from {original_qty} to {new_qty} ({reduction*100:.0f}%). {justification}",
                stage="NEGOTIATION",
                details={
                    "agent": "Decision",
                    "target": "Finance",
                    "type": "PROPOSE",
                    "sku": sku,
                    "fipa": proposal.get("fipa", {})
                }
            )
        
        # Increment negotiation round
        cycle_state.negotiation_rounds += 1
        logger.info(f"📊 Negotiation Round {cycle_state.negotiation_rounds} complete. Proposals ready for Finance re-optimization.")
        
        return state_to_dict(cycle_state)
    except Exception as e:
        logger.error(f"[{cycle_state.cycle_id}] Negotiation error: {str(e)}")
        job_stream_manager.log_event(cycle_state.cycle_id, "error", f"Negotiation failed: {e}", stage="NEGOTIATION")
        return state_to_dict(cycle_state)


def should_negotiate(state) -> str:
    """Check if there are rejections that need negotiation."""
    cycle_state = ensure_state(state)
    
    has_rejections = len(cycle_state.finance_rejections) > 0
    can_negotiate = cycle_state.negotiation_rounds < cycle_state.max_negotiation_rounds
    
    # CRITICAL: Only negotiate ONCE (Round 0 → Round 1)
    # After Round 1 (re-optimization), go straight to Action
    already_negotiated = cycle_state.negotiation_rounds > 0
    
    logger.debug(f"Negotiation check. Rejections={len(cycle_state.finance_rejections)}, Rounds={cycle_state.negotiation_rounds}")
    
    logger.info(
        f"[{cycle_state.cycle_id}] Negotiation decision: "
        f"Rejections={len(cycle_state.finance_rejections)}, "
        f"Round={cycle_state.negotiation_rounds}/{cycle_state.max_negotiation_rounds}, "
        f"AlreadyNegotiated={already_negotiated}, "
        f"Decision={'action' if already_negotiated else ('negotiation' if (has_rejections and can_negotiate) else 'action')}"
    )
    
    # If we already negotiated (Round 1+), go to Action (no more negotiation)
    if already_negotiated:
        return "action"
    
    # Otherwise, negotiate if we have rejections and haven't hit max rounds
    if has_rejections and can_negotiate:
        return "negotiation"
    return "action"


def action_node_wrapper(state) -> dict:
    """Wrapper for action_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "🛒 Procurement Agent executing orders...", stage="ACTION")
    
    # Execute each decision
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
                    f"✅ Order placed for {action_result['sku']}: {action_result['quantity']} units at ${action_result['total_cost']:.2f}",
                    details=action_result,
                    stage="ACTION"
                )
    
    # Update state with executed actions
    cycle_state.actions = executed_actions
    
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", f"✅ Procurement complete. {len(executed_actions)} orders executed.", stage="ACTION")
    return state_to_dict(cycle_state)


def memory_node_wrapper(state) -> dict:
    """Wrapper for memory_node."""
    cycle_state = ensure_state(state)
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "💾 Archiving cycle to long-term memory...", stage="MEMORY")
    
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
    
    job_stream_manager.log_event(cycle_state.cycle_id, "progress", "✅ Cycle archived successfully.", stage="MEMORY")
    return state_to_dict(cycle_state)


# Define the graph with Dict type
workflow = StateGraph(Dict)

# Add nodes
workflow.add_node("fetch_data", fetch_node_wrapper)
workflow.add_node("forecast", forecast_node_wrapper)

# Decision Subgraph Nodes
workflow.add_node("analyze_trends", analyze_trends_wrapper)
workflow.add_node("check_constraints", check_constraints_wrapper)
workflow.add_node("optimize_cost", optimize_cost_wrapper)

workflow.add_node("finance", finance_node_wrapper)
workflow.add_node("negotiation", negotiation_node_wrapper)
workflow.add_node("action", action_node_wrapper)
workflow.add_node("memory", memory_node_wrapper)

# Define edges
workflow.set_entry_point("fetch_data")
workflow.add_edge("fetch_data", "forecast")
workflow.add_edge("forecast", "analyze_trends")

# Connect subgraph
workflow.add_edge("analyze_trends", "check_constraints")
workflow.add_edge("check_constraints", "optimize_cost")
workflow.add_edge("optimize_cost", "finance")

# Conditional edge for negotiation
workflow.add_conditional_edges(
    "finance",
    should_negotiate,
    {
        "negotiation": "negotiation",
        "action": "action"
    }
)

# NEW PRODUCTION FLOW: Negotiation → Finance (for re-optimization) → Action
# Finance will check negotiation_rounds and call re_optimize_with_proposals
workflow.add_edge("negotiation", "finance")  # Re-optimize with proposals!
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
        "budget": settings.DEFAULT_BUDGET,
        "recent_sales_revenue": recent_revenue,
        "finance_feedback": "",
        "finance_rejections": [],
        "counter_arguments": [],
        "negotiation_rounds": 0,
        "max_negotiation_rounds": settings.MAX_NEGOTIATION_ROUNDS,
        "negotiation_proposals": [],
        "budget_remaining": 0.0
    }
    
    try:
        result_state = app.invoke(initial_state)
        
        # Result is already a dict
        result_dict = {
            "cycle_id": cycle_id,
            "decisions": result_state.get("decisions", []),
            "actions": result_state.get("actions", []),
            "agent_dialogues": result_state.get("agent_dialogues", []),
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
