# app/agents/state.py
"""LangGraph state definition for the supply chain agent cycle."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CycleState:
    """State shared across all nodes in the agent cycle."""
    
    # Cycle metadata
    cycle_id: str
    cycle_number: int
    started_at: datetime
    
    # Data flow - Input
    inventory_data: Dict[str, Any] = field(default_factory=dict)
    sales_data: List[Dict[str, Any]] = field(default_factory=list)
    sales_by_sku: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    orders_data: List[Dict[str, Any]] = field(default_factory=list)
    pending_orders_by_sku: Dict[str, int] = field(default_factory=dict)
    overdue_orders: List[Dict[str, Any]] = field(default_factory=list)  # New: For supplier scoring
    alerts_data: List[Dict[str, Any]] = field(default_factory=list)
    
    # Data flow - Processing
    forecast_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Decision Subgraph Intermediate States
    analyzed_skus: List[Dict[str, Any]] = field(default_factory=list)
    constrained_skus: List[Dict[str, Any]] = field(default_factory=list)
    
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    agent_dialogues: List[Dict[str, Any]] = field(default_factory=list)  # New: Agent conversations
    
    # Negotiation tracking (NEW)
    finance_rejections: List[Dict[str, Any]] = field(default_factory=list)  # Items rejected by Finance
    counter_arguments: List[Dict[str, Any]] = field(default_factory=list)   # Arguments from Decision
    negotiation_rounds: int = 0
    max_negotiation_rounds: int = 3
    negotiation_proposals: List[Dict[str, Any]] = field(default_factory=list)  # New: Proposals for Finance to review
    budget_remaining: float = 0.0  # Track remaining budget for negotiation calculations
    streamed_dialogues_count: int = 0  # Track streamed dialogues to avoid duplicates
    
    # Learning & adaptation (REMOVED)
    # learning_results: Dict[str, Any] = field(default_factory=dict)
    # reinforcement_results: Dict[str, Any] = field(default_factory=dict)
    
    # Execution control
    skip_forecast: bool = False  # Skip if forecasting disabled
    urgent_mode: bool = False    # Fast cycle if urgent actions pending
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    failed_skus: List[str] = field(default_factory=list)
    
    # Results & summary
    summary: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False
    
    # Finance & Strategy
    budget: float = 5000.0
    recent_sales_revenue: float = 0.0  # New: For dynamic budgeting
    finance_feedback: str = ""

    def add_error(self, sku: str, error: str):
        """Track errors per SKU"""
        error_msg = f"{sku}: {error}"
        self.errors.append(error_msg)
        if sku not in self.failed_skus:
            self.failed_skus.append(sku)
    
    def is_success(self) -> bool:
        """Check if cycle succeeded (no critical errors)"""
        return len(self.failed_skus) == 0 or len(self.failed_skus) < len(self.inventory_data) * 0.1
    
    def get_urgent_actions(self) -> List[Dict[str, Any]]:
        """Get high-priority actions from this cycle"""
        return [a for a in self.actions if a.get("urgency") == "urgent"]
