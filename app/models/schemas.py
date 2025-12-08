from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func, Text
from app.models.database import Base

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    quantity = Column(Integer)
    threshold = Column(Integer)
    
    # ✅ NEW: Pricing & Cost Factors
    unit_price = Column(Float, nullable=True)  # Cost per unit
    holding_cost_percent = Column(Float, default=0.15)  # Annual holding cost as % of unit price (e.g., 15%)
    reorder_cost = Column(Float, nullable=True)  # Fixed cost per order
    
    # ✅ NEW: Supply Chain Factors
    lead_time_days = Column(Integer, default=7)  # Days from order to delivery
    supplier = Column(String, nullable=True)  # Supplier name
    min_order_qty = Column(Integer, default=1)  # Minimum order quantity
    max_order_qty = Column(Integer, nullable=True)  # Maximum order quantity (if any limit)
    
    # ✅ NEW: Inventory Policy
    safety_stock = Column(Integer, default=10)  # Base safety stock level
    reorder_point = Column(Integer, nullable=True)  # Automatic reorder point (can be calculated)
    
    # ✅ NEW: Product Metadata
    category = Column(String, nullable=True)  # Product category (e.g., "Shoes", "Accessories")
    is_active = Column(Boolean, default=True)  # Track obsolete products
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now())

class Sales(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String)
    sold_quantity = Column(Integer)
    date = Column(DateTime(timezone=True), server_default=func.now())

class Orders(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String)
    quantity = Column(Integer)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="Pending")
    notes = Column(String, nullable=True)  # Store decision details as JSON string

class Alerts(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    type = Column(String)
    sku = Column(String, nullable=True)  # SKU related to alert
    priority = Column(String, nullable=True)  # Priority level (low, medium, high, critical)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentMemory(Base):
    __tablename__ = "agent_memory"
    id = Column(Integer, primary_key=True, index=True)
    context = Column(Text)  # Full detailed context (can be very long)
    decision = Column(Text)  # Decision summaries (can be large JSON)
    reasoning = Column(Text)  # Detailed reasoning
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("agent_memory.id"))
    sku = Column(String, index=True)
    approved = Column(Boolean)  # True = good decision, False = bad decision
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SKUParameters(Base):
    __tablename__ = "sku_parameters"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    safety_multiplier = Column(Float, default=3.0)  # How much buffer to order
    confidence_threshold = Column(Float, default=0.5)  # Min forecast confidence to act
    accuracy_score = Column(Float, default=0.5)  # % of decisions user approved
    samples_count = Column(Integer, default=0)  # Number of decisions evaluated
    last_updated = Column(DateTime(timezone=True), server_default=func.now())


# ============ PERSISTENCE TABLES ============

class PersistentMemory(Base):
    """
    Unified table for all memory types (episodic, semantic, procedural).
    Stores agent's accumulated knowledge and experiences.
    """
    __tablename__ = "persistent_memory"
    id = Column(Integer, primary_key=True, index=True)
    
    # Memory classification
    memory_type = Column(String, index=True)  # "episodic", "semantic", "procedural"
    
    # Identifiers and timestamps
    event_id = Column(String, nullable=True, index=True)      # For episodic
    fact_id = Column(String, nullable=True, index=True)       # For semantic
    procedure_id = Column(String, nullable=True, index=True)  # For procedural
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Content fields
    event_type = Column(String, nullable=True)    # Type of event (e.g., "decision_made")
    category = Column(String, nullable=True, index=True)  # Category (e.g., "sku_profile")
    key = Column(String, nullable=True, index=True)       # Key for semantic/procedural
    description = Column(Text, nullable=True)
    content = Column(Text)  # Full JSON content
    source = Column(String, nullable=True)  # Where this memory came from
    
    # Metadata
    sku = Column(String, nullable=True, index=True)
    confidence = Column(Float, default=0.5)  # 0-1, how confident are we
    is_active = Column(Boolean, default=True, index=True)
    
    # For querying and retrieval
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentCheckpoint(Base):
    """
    State checkpoints for resumption and recovery.
    Allows agent to save progress and resume from exact point.
    """
    __tablename__ = "agent_checkpoints"
    id = Column(Integer, primary_key=True, index=True)
    
    # Checkpoint metadata
    checkpoint_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    cycle_number = Column(Integer, index=True)  # Which cycle/iteration
    goal = Column(String, nullable=True, index=True)  # Goal being pursued
    
    # State information
    state = Column(Text)  # Full state JSON (agent_state, progress, decisions, history, errors)
    
    # Stability and recoverability
    is_stable = Column(Boolean, default=True, index=True)  # Safe to resume from here
    is_active = Column(Boolean, default=True, index=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PersistentGoal(Base):
    """
    Long-term goals that persist across sessions.
    Enables the agent to maintain objectives and track progress.
    """
    __tablename__ = "persistent_goals"
    id = Column(Integer, primary_key=True, index=True)
    
    # Goal definition
    goal_id = Column(String, unique=True, index=True)
    objective = Column(Text)  # What we're trying to achieve
    status = Column(String, default="active", index=True)  # active, paused, completed, failed
    priority = Column(Integer, default=5)  # 1-10, higher = more important
    
    # Context and metrics
    context = Column(Text)  # Business context
    target_metrics = Column(Text)  # How we measure success
    current_progress = Column(Text)  # Current progress JSON
    
    # Timeline
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Management
    is_active = Column(Boolean, default=True, index=True)


class Job(Base):
    """
    Track agent execution jobs.
    Replaces in-memory _agent_jobs dictionary.
    """
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="queued", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(Text, nullable=True)  # JSON result
    summary = Column(Text, nullable=True)  # Natural language summary
    error = Column(Text, nullable=True)


class User(Base):
    """
    Application users for authentication.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())




