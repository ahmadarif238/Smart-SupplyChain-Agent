# app/agents/agent_state.py
"""
AgentState - Centralized state management for the supply chain agent.

This makes the agent more robust by:
1. Explicitly tracking state through the entire cycle
2. Enabling LangGraph state persistence
3. Making node dependencies clear
4. Facilitating debugging and monitoring
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class SKUForecast(BaseModel):
    """Forecast result for a single SKU"""
    sku: str
    product_name: str
    current_quantity: int
    forecast_daily_demand: float
    forecast_7_day: float
    forecast_confidence: float
    explanation: str
    unit_price: Optional[float] = None
    lead_time_days: Optional[int] = None


class SKUDecision(BaseModel):
    """Decision result for a single SKU"""
    sku: str
    product_name: str
    reorder_required: bool
    order_quantity: int
    urgency_level: str  # "low", "medium", "high"
    reasoning: str
    safety_multiplier: Optional[float] = None
    confidence_threshold: Optional[float] = None


class SKUAction(BaseModel):
    """Action execution result for a single SKU"""
    sku: str
    product_name: str
    action_taken: bool
    order_id: Optional[int] = None
    alert_message: Optional[str] = None
    error: Optional[str] = None


class AgentState(BaseModel):
    """
    Complete state of the agent cycle.
    
    This replaces passing dicts between nodes and makes the agent:
    - Type-safe
    - Self-documenting
    - Easier to persist
    - Compatible with LangGraph
    """
    
    # Metadata
    cycle_id: str  # Unique ID for this cycle
    cycle_started_at: datetime
    cycle_stage: str  # "init" → "fetch" → "forecast" → "decision" → "action" → "learning" → "complete"
    
    # Fetch Stage
    inventory_data: List[Dict[str, Any]] = []  # Raw inventory from DB
    sales_data: List[Dict[str, Any]] = []  # Raw sales from DB
    fetch_error: Optional[str] = None
    
    # Forecast Stage
    forecasts: List[SKUForecast] = []  # Demand forecasts for each SKU
    forecast_error: Optional[str] = None
    
    # Decision Stage
    decisions: List[SKUDecision] = []  # Reorder decisions
    decision_error: Optional[str] = None
    
    # Action Stage
    actions: List[SKUAction] = []  # Executed actions
    action_error: Optional[str] = None
    
    # Learning Stage
    learning_updates: Dict[str, Any] = {}  # Parameters adjusted by learning
    learning_error: Optional[str] = None
    
    # Summary
    total_skus_processed: int = 0
    total_reorders_triggered: int = 0
    urgent_actions_pending: bool = False
    
    class Config:
        """Allow datetime serialization"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def has_errors(self) -> bool:
        """Check if any stage had errors"""
        return any([
            self.fetch_error,
            self.forecast_error,
            self.decision_error,
            self.action_error,
            self.learning_error
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging/storage"""
        return self.dict()
    
    def summary(self) -> Dict[str, Any]:
        """Get summary for user display"""
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.cycle_started_at.isoformat(),
            "stage": self.cycle_stage,
            "skus_processed": self.total_skus_processed,
            "reorders_triggered": self.total_reorders_triggered,
            "urgent": self.urgent_actions_pending,
            "errors": self.has_errors
        }
