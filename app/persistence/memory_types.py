# app/persistence/memory_types.py
"""
Memory types for agentic AI persistence.
Implements Episodic, Semantic, and Procedural memory types.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class MemoryType(str, Enum):
    """Different types of memory in the agent"""
    EPISODIC = "episodic"      # Specific past events and experiences
    SEMANTIC = "semantic"      # General facts and learned knowledge
    PROCEDURAL = "procedural"  # How-to knowledge and strategies
    GOAL = "goal"              # Long-term objectives and goals


@dataclass
class EpisodicMemory:
    """Records of specific past interactions, actions, and experiences"""
    event_id: str
    timestamp: datetime
    event_type: str  # e.g., "decision_made", "error_encountered", "goal_achieved"
    sku: Optional[str]
    description: str
    context: Dict[str, Any]  # Full context of the event
    outcome: Optional[str]   # What happened (success/failure)
    learning: Optional[str]  # What we learned from this
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class SemanticMemory:
    """General facts, learned preferences, and extracted insights"""
    fact_id: str
    timestamp: datetime
    category: str  # e.g., "sku_profile", "market_trend", "system_insight"
    key: str       # e.g., "SKU001_demand_pattern"
    value: Any     # e.g., "high_volatility" or {"trend": "increasing", "confidence": 0.85}
    confidence: float  # 0-1, how sure we are about this
    source: str    # Where this fact came from (e.g., "forecast_accuracy", "user_feedback")
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class ProceduralMemory:
    """How-to knowledge and successful strategies"""
    procedure_id: str
    timestamp: datetime
    procedure_type: str  # e.g., "ordering_strategy", "forecasting_approach"
    name: str
    description: str
    steps: List[Dict[str, Any]]  # Sequence of steps
    conditions: Dict[str, Any]   # When to use this procedure
    success_rate: float  # 0-1, historical success rate
    last_used: Optional[datetime] = None
    usage_count: int = 0
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.last_used, str):
            self.last_used = datetime.fromisoformat(self.last_used)


@dataclass
class Checkpoint:
    """State checkpoint for resumption and rollback"""
    checkpoint_id: str
    timestamp: datetime
    cycle_number: int
    agent_state: Dict[str, Any]     # Internal state variables
    goal: str                        # Current goal
    progress: Dict[str, Any]        # Progress on goal (e.g., {"tasks_completed": 5, "total_tasks": 10})
    decisions_made: List[Dict]      # List of decisions in this session
    message_history: List[Dict]     # Conversation history
    resources_used: Dict[str, Any]  # Database queries, API calls, etc.
    errors_encountered: List[str]   # Any errors that occurred
    is_stable: bool = True          # Can we safely resume from this point?
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class Goal:
    """Long-term persistent goal"""
    goal_id: str
    created_at: datetime
    objective: str                  # What we're trying to achieve
    status: str                     # "active", "paused", "completed", "failed"
    priority: int                   # 1-10, higher = more important
    context: Dict[str, Any]         # Business context for the goal
    target_metrics: Dict[str, Any]  # How we measure success
    current_progress: Dict[str, Any]
    deadline: Optional[datetime] = None
    related_memories: List[str] = field(default_factory=list)  # IDs of related memories
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.deadline, str):
            self.deadline = datetime.fromisoformat(self.deadline)
