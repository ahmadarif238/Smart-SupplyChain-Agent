# app/agents/langgraph_flow.py
"""LangGraph agent controller for autonomous supply chain management."""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.agents.langgraph_workflow import run_cycle
from app.models.database import SessionLocal, get_db_context
from app.persistence import PersistentMemoryManager, RecoveryManager, Checkpoint, EpisodicMemory

logger = logging.getLogger("langgraph_flow")
logger.setLevel(logging.INFO)

# Default interval (can be overridden by env vars or config)
DEFAULT_INTERVAL_MINUTES = 60

class AgentController:
    """Orchestrates the autonomous supply chain agent using LangGraph and APScheduler."""
    
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.cycle_count = 0
        self.persistent_memory = PersistentMemoryManager(session_factory=session_factory)
        self.recovery_manager = RecoveryManager(self.persistent_memory)
        self.scheduler = BackgroundScheduler()
        self._is_running = False
    
    def run_cycle(self) -> Dict[str, Any]:
        """
        Execute a single cycle using LangGraph.
        
        Returns:
            Dictionary with cycle results
        """
        self.cycle_count += 1
        
        logger.info(f"[START] Agent cycle #{self.cycle_count} started")
        
        # Run the LangGraph cycle
        
        # SIMULATION: Generate market activity before run to ensure dynamic data
        try:
            from app.utils.simulation import simulate_market_activity
            # Use new context manager for safe session handling
            db = self.session_factory()
            try:
                revenue = simulate_market_activity(db)
                logger.info(f"💰 Simulated Revenue: ${revenue:.2f}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            revenue = 0.0

        result = run_cycle(cycle_id=f"cycle_{self.cycle_count}", recent_revenue=revenue)
        
        # Save checkpoint for persistence
        try:
            # Use new context manager for safe session handling
            db = self.session_factory()
            try:
                checkpoint = Checkpoint(
                    checkpoint_id=f"cycle_{self.cycle_count}_{uuid4().hex[:8]}",
                    timestamp=datetime.utcnow(),
                    cycle_number=self.cycle_count,
                    goal="optimize_supply_chain_inventory",
                    agent_state={
                        "cycle_count": self.cycle_count,
                        "last_run": result.get('completed_at'),
                        "skus_processed": result.get('skus_processed', 0)
                    },
                    progress={
                        "tasks_completed": result.get('actions_executed', 0),
                        "total_tasks": result.get('skus_processed', 0),
                        "reorders_made": len([a for a in result.get('actions', []) if a.get('action_type') == 'reorder'])
                    },
                    decisions_made=result.get('decisions', []),
                    message_history=[
                        {
                            "stage": "graph_execution",
                            "message": f"LangGraph cycle completed: {result.get('status')}",
                            "timestamp": result.get('completed_at')
                        }
                    ],
                    resources_used={
                        "graph_invocations": 1,
                        "decisions_made": result.get('skus_processed', 0),
                        "errors": result.get('errors', 0)
                    },
                    errors_encountered=result.get('errors', []) if result.get('errors') else [],
                    is_stable=result.get('status') == 'success'
                )
                
                self.persistent_memory.save_checkpoint(db, checkpoint)
                
                # Store episode
                episode = EpisodicMemory(
                    event_id=f"cycle_complete_{self.cycle_count}",
                    timestamp=datetime.utcnow(),
                    event_type="cycle_completed",
                    sku=None,
                    description=f"Agent cycle #{self.cycle_count} completed via LangGraph",
                    context={
                        "skus_processed": result.get('skus_processed', 0),
                        "actions_executed": result.get('actions_executed', 0),
                        "errors_count": result.get('errors', 0)
                    },
                    outcome="success" if result.get('status') == 'success' else "partial",
                    learning="Cycle executed using LangGraph with state management and checkpointing"
                )
                self.persistent_memory.store_episode(db, episode)
                
                logger.info(f"✅ Checkpoint saved for cycle {self.cycle_count}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
        
        return result
    
    def start_scheduler(self, interval_minutes: int = DEFAULT_INTERVAL_MINUTES):
        """Start the agent scheduler."""
        if self._is_running:
            logger.warning("Agent scheduler already running")
            return

        logger.info(f"Starting agent scheduler with interval: {interval_minutes} minutes")
        
        # Add job to scheduler
        self.scheduler.add_job(
            self.run_cycle,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='agent_cycle',
            name='Autonomous Supply Chain Cycle',
            replace_existing=True
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info("Agent scheduler started successfully")

    def stop_scheduler(self):
        """Stop the agent scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Agent scheduler stopped")

# Global controller instance
agent_controller = AgentController()

def start_agent_background_job(interval_minutes: int = DEFAULT_INTERVAL_MINUTES):
    """Helper to start the global agent controller."""
    agent_controller.start_scheduler(interval_minutes)
