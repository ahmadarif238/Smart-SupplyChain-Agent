# app/persistence/recovery_manager.py
"""
Recovery and resumption management for agentic AI.
Enables agent to recover from interruptions and continue from last stable state.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.persistence.persistent_memory import PersistentMemoryManager
from app.persistence.memory_types import Checkpoint, MemoryType

logger = logging.getLogger("recovery_manager")


class RecoveryManager:
    """
    Manages agent recovery, resumption, and rollback capabilities.
    Ensures the agent can continue work even after interruptions.
    """
    
    def __init__(self, memory_manager: PersistentMemoryManager):
        self.memory_manager = memory_manager
    
    def initiate_recovery(self, db: Session, goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate recovery process after interruption.
        Returns recovery plan and checkpoint to resume from.
        """
        logger.info("Initiating recovery process...")
        
        # Get latest stable checkpoint
        checkpoint = self.memory_manager.get_latest_stable_checkpoint(db, goal)
        
        if not checkpoint:
            logger.warning("No stable checkpoint found. Starting fresh.")
            return {
                "status": "no_recovery",
                "message": "No stable checkpoint found. Agent will start fresh.",
                "checkpoint": None
            }
        
        # Analyze what happened before interruption
        recovery_plan = {
            "status": "ready_for_recovery",
            "checkpoint_id": checkpoint.checkpoint_id,
            "cycle_number": checkpoint.cycle_number,
            "goal": checkpoint.goal,
            "last_progress": checkpoint.progress,
            "decisions_to_retry": len([d for d in checkpoint.decisions_made if d.get("status") == "pending"]),
            "tasks_completed": checkpoint.progress.get("tasks_completed", 0),
            "tasks_total": checkpoint.progress.get("total_tasks", 0),
            "errors_to_fix": checkpoint.errors_encountered,
            "message_history_size": len(checkpoint.message_history)
        }
        
        logger.info(f"Recovery plan ready: {recovery_plan}")
        return recovery_plan
    
    def resume_from_checkpoint(
        self, 
        db: Session, 
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """
        Resume execution from a specific checkpoint.
        Restores agent state and continues work.
        """
        try:
            # Get checkpoint history to find the one we want
            checkpoints = self.memory_manager.get_checkpoint_history(db, limit=100)
            checkpoint = next((c for c in checkpoints if c.checkpoint_id == checkpoint_id), None)
            
            if not checkpoint:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return {"status": "error", "message": "Checkpoint not found"}
            
            logger.info(f"Resuming from checkpoint {checkpoint_id} (cycle {checkpoint.cycle_number})")
            
            return {
                "status": "resumed",
                "checkpoint_id": checkpoint.checkpoint_id,
                "agent_state": checkpoint.agent_state,
                "goal": checkpoint.goal,
                "progress": checkpoint.progress,
                "message_history": checkpoint.message_history,
                "next_cycle": checkpoint.cycle_number + 1,
                "message": f"Resumed from cycle {checkpoint.cycle_number}"
            }
        except Exception as e:
            logger.error(f"Error resuming from checkpoint: {e}")
            return {"status": "error", "message": str(e)}
    
    def rollback_to_checkpoint(
        self, 
        db: Session, 
        checkpoint_id: str,
        reason: str = "manual_rollback"
    ) -> Dict[str, Any]:
        """
        Rollback to previous checkpoint (undo failed actions).
        Useful when a decision path leads to problems.
        """
        try:
            checkpoints = self.memory_manager.get_checkpoint_history(db, limit=100)
            checkpoint = next((c for c in checkpoints if c.checkpoint_id == checkpoint_id), None)
            
            if not checkpoint:
                logger.error(f"Checkpoint {checkpoint_id} not found for rollback")
                return {"status": "error", "message": "Checkpoint not found"}
            
            logger.info(f"Rolling back to checkpoint {checkpoint_id}. Reason: {reason}")
            
            # Record the rollback event
            from uuid import uuid4
            episode_id = f"rollback_{uuid4().hex[:8]}"
            from app.persistence.memory_types import EpisodicMemory
            
            episode = EpisodicMemory(
                event_id=episode_id,
                timestamp=datetime.utcnow(),
                event_type="rollback",
                sku=None,
                description=f"Rolled back to checkpoint {checkpoint_id}",
                context={
                    "rollback_reason": reason,
                    "from_checkpoint": checkpoint_id,
                    "cycle_number": checkpoint.cycle_number
                },
                outcome="success",
                learning=f"Rolled back due to: {reason}. Trying alternative path."
            )
            self.memory_manager.store_episode(db, episode)
            
            return {
                "status": "rolled_back",
                "checkpoint_id": checkpoint.checkpoint_id,
                "agent_state": checkpoint.agent_state,
                "goal": checkpoint.goal,
                "message": f"Rolled back to cycle {checkpoint.cycle_number}"
            }
        except Exception as e:
            logger.error(f"Error rolling back to checkpoint: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_available_checkpoints(
        self, 
        db: Session,
        goal: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List available checkpoints for recovery/rollback"""
        try:
            checkpoints = self.memory_manager.get_checkpoint_history(db, goal, limit)
            
            checkpoint_list = []
            for cp in checkpoints:
                checkpoint_list.append({
                    "checkpoint_id": cp.checkpoint_id,
                    "timestamp": cp.timestamp.isoformat(),
                    "cycle_number": cp.cycle_number,
                    "goal": cp.goal,
                    "progress": cp.progress,
                    "is_stable": cp.is_stable,
                    "errors_count": len(cp.errors_encountered),
                    "decisions_made": len(cp.decisions_made)
                })
            
            return {
                "status": "success",
                "total_checkpoints": len(checkpoint_list),
                "checkpoints": checkpoint_list
            }
        except Exception as e:
            logger.error(f"Error listing checkpoints: {e}")
            return {"status": "error", "message": str(e)}
    
    def analyze_failure_pattern(
        self, 
        db: Session,
        goal: Optional[str] = None,
        lookback_cycles: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze patterns in failures to improve future recovery.
        Learn from errors to avoid repeating them.
        """
        try:
            checkpoints = self.memory_manager.get_checkpoint_history(db, goal, lookback_cycles)
            
            error_patterns = {}
            total_errors = 0
            failed_decisions = 0
            
            for cp in checkpoints:
                # Analyze errors in this checkpoint
                for error in cp.errors_encountered:
                    if error not in error_patterns:
                        error_patterns[error] = 0
                    error_patterns[error] += 1
                    total_errors += 1
                
                # Analyze failed decisions
                for decision in cp.decisions_made:
                    if decision.get("status") == "failed":
                        failed_decisions += 1
            
            # Sort by frequency
            common_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
            
            analysis = {
                "status": "success",
                "lookback_cycles": lookback_cycles,
                "total_checkpoints_analyzed": len(checkpoints),
                "total_errors": total_errors,
                "failed_decisions": failed_decisions,
                "common_errors": [{"error": err, "frequency": count} for err, count in common_errors[:10]],
                "error_rate": total_errors / len(checkpoints) if checkpoints else 0
            }
            
            logger.info(f"Failure analysis: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {e}")
            return {"status": "error", "message": str(e)}
