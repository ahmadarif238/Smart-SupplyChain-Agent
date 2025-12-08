# app/persistence/persistent_memory.py
"""
Persistent memory system for agentic AI.
Stores and retrieves episodic, semantic, and procedural memories.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import schemas
from app.persistence.memory_types import (
    EpisodicMemory, SemanticMemory, ProceduralMemory, 
    Checkpoint, Goal, MemoryType
)

logger = logging.getLogger("persistent_memory")


class PersistentMemoryManager:
    """
    Manages all aspects of agent persistence:
    - Episodic memory (past events)
    - Semantic memory (learned facts)
    - Procedural memory (strategies)
    - Checkpoints (state snapshots)
    - Goals (long-term objectives)
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    # ============ EPISODIC MEMORY ============
    
    def store_episode(self, db: Session, episode: EpisodicMemory) -> str:
        """Store a specific event/experience"""
        try:
            memory = schemas.PersistentMemory(
                memory_type=MemoryType.EPISODIC,
                event_id=episode.event_id,
                timestamp=episode.timestamp,
                event_type=episode.event_type,
                sku=episode.sku,
                description=episode.description,
                content=json.dumps({
                    "context": episode.context,
                    "outcome": episode.outcome,
                    "learning": episode.learning
                }),
                confidence=1.0,
                is_active=True
            )
            db.add(memory)
            db.commit()
            logger.info(f"Stored episodic memory: {episode.event_type} for {episode.sku}")
            return episode.event_id
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            db.rollback()
            raise
    
    def retrieve_episodes(
        self, 
        db: Session, 
        sku: Optional[str] = None,
        event_type: Optional[str] = None,
        days_back: int = 30,
        limit: int = 100
    ) -> List[EpisodicMemory]:
        """Retrieve past events (episodic memory)"""
        try:
            query = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == MemoryType.EPISODIC,
                schemas.PersistentMemory.timestamp >= datetime.utcnow() - timedelta(days=days_back),
                schemas.PersistentMemory.is_active == True
            )
            
            if sku:
                query = query.filter(schemas.PersistentMemory.sku == sku)
            if event_type:
                query = query.filter(schemas.PersistentMemory.event_type == event_type)
            
            results = query.order_by(schemas.PersistentMemory.timestamp.desc()).limit(limit).all()
            
            episodes = []
            for r in results:
                content = json.loads(r.content) if isinstance(r.content, str) else r.content
                episodes.append(EpisodicMemory(
                    event_id=r.event_id,
                    timestamp=r.timestamp,
                    event_type=r.event_type,
                    sku=r.sku,
                    description=r.description,
                    context=content.get("context", {}),
                    outcome=content.get("outcome"),
                    learning=content.get("learning")
                ))
            
            return episodes
        except Exception as e:
            logger.error(f"Error retrieving episodic memories: {e}")
            return []
    
    # ============ SEMANTIC MEMORY ============
    
    def store_fact(self, db: Session, fact: SemanticMemory) -> str:
        """Store a learned fact or insight"""
        try:
            memory = schemas.PersistentMemory(
                memory_type=MemoryType.SEMANTIC,
                fact_id=fact.fact_id,
                timestamp=fact.timestamp,
                category=fact.category,
                key=fact.key,
                content=json.dumps({"value": fact.value}),
                confidence=fact.confidence,
                source=fact.source,
                is_active=True
            )
            db.add(memory)
            db.commit()
            logger.info(f"Stored semantic memory: {fact.category}/{fact.key}")
            return fact.fact_id
        except Exception as e:
            logger.error(f"Error storing semantic memory: {e}")
            db.rollback()
            raise
    
    def retrieve_fact(
        self, 
        db: Session, 
        category: str, 
        key: str
    ) -> Optional[SemanticMemory]:
        """Retrieve a specific learned fact"""
        try:
            result = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == MemoryType.SEMANTIC,
                schemas.PersistentMemory.category == category,
                schemas.PersistentMemory.key == key,
                schemas.PersistentMemory.is_active == True
            ).order_by(schemas.PersistentMemory.timestamp.desc()).first()
            
            if not result:
                return None
            
            content = json.loads(result.content) if isinstance(result.content, str) else result.content
            return SemanticMemory(
                fact_id=result.fact_id,
                timestamp=result.timestamp,
                category=result.category,
                key=result.key,
                value=content.get("value"),
                confidence=result.confidence,
                source=result.source
            )
        except Exception as e:
            logger.error(f"Error retrieving semantic memory: {e}")
            return None
    
    def retrieve_facts_by_category(
        self, 
        db: Session, 
        category: str,
        min_confidence: float = 0.0
    ) -> List[SemanticMemory]:
        """Retrieve all facts in a category"""
        try:
            results = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == MemoryType.SEMANTIC,
                schemas.PersistentMemory.category == category,
                schemas.PersistentMemory.confidence >= min_confidence,
                schemas.PersistentMemory.is_active == True
            ).all()
            
            facts = []
            for r in results:
                content = json.loads(r.content) if isinstance(r.content, str) else r.content
                facts.append(SemanticMemory(
                    fact_id=r.fact_id,
                    timestamp=r.timestamp,
                    category=r.category,
                    key=r.key,
                    value=content.get("value"),
                    confidence=r.confidence,
                    source=r.source
                ))
            
            return sorted(facts, key=lambda x: x.confidence, reverse=True)
        except Exception as e:
            logger.error(f"Error retrieving semantic facts: {e}")
            return []
    
    # ============ PROCEDURAL MEMORY ============
    
    def store_procedure(self, db: Session, procedure: ProceduralMemory) -> str:
        """Store a successful procedure/strategy"""
        try:
            memory = schemas.PersistentMemory(
                memory_type=MemoryType.PROCEDURAL,
                procedure_id=procedure.procedure_id,
                timestamp=procedure.timestamp,
                category=procedure.procedure_type,
                key=procedure.name,
                content=json.dumps({
                    "description": procedure.description,
                    "steps": procedure.steps,
                    "conditions": procedure.conditions,
                    "success_rate": procedure.success_rate,
                    "usage_count": procedure.usage_count
                }),
                confidence=procedure.success_rate,
                is_active=True
            )
            db.add(memory)
            db.commit()
            logger.info(f"Stored procedural memory: {procedure.name}")
            return procedure.procedure_id
        except Exception as e:
            logger.error(f"Error storing procedural memory: {e}")
            db.rollback()
            raise
    
    def retrieve_procedure(
        self, 
        db: Session, 
        procedure_type: str,
        name: str
    ) -> Optional[ProceduralMemory]:
        """Retrieve a specific procedure"""
        try:
            result = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == MemoryType.PROCEDURAL,
                schemas.PersistentMemory.category == procedure_type,
                schemas.PersistentMemory.key == name,
                schemas.PersistentMemory.is_active == True
            ).first()
            
            if not result:
                return None
            
            content = json.loads(result.content) if isinstance(result.content, str) else result.content
            return ProceduralMemory(
                procedure_id=result.procedure_id,
                timestamp=result.timestamp,
                procedure_type=result.category,
                name=result.key,
                description=content.get("description", ""),
                steps=content.get("steps", []),
                conditions=content.get("conditions", {}),
                success_rate=result.confidence,
                usage_count=content.get("usage_count", 0)
            )
        except Exception as e:
            logger.error(f"Error retrieving procedural memory: {e}")
            return None
    
    def retrieve_best_procedures(
        self, 
        db: Session, 
        procedure_type: str,
        min_success_rate: float = 0.7,
        limit: int = 5
    ) -> List[ProceduralMemory]:
        """Get most successful procedures of a type"""
        try:
            results = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == MemoryType.PROCEDURAL,
                schemas.PersistentMemory.category == procedure_type,
                schemas.PersistentMemory.confidence >= min_success_rate,
                schemas.PersistentMemory.is_active == True
            ).order_by(
                schemas.PersistentMemory.confidence.desc()
            ).limit(limit).all()
            
            procedures = []
            for r in results:
                content = json.loads(r.content) if isinstance(r.content, str) else r.content
                procedures.append(ProceduralMemory(
                    procedure_id=r.procedure_id,
                    timestamp=r.timestamp,
                    procedure_type=r.category,
                    name=r.key,
                    description=content.get("description", ""),
                    steps=content.get("steps", []),
                    conditions=content.get("conditions", {}),
                    success_rate=r.confidence,
                    usage_count=content.get("usage_count", 0)
                ))
            
            return procedures
        except Exception as e:
            logger.error(f"Error retrieving best procedures: {e}")
            return []
    
    # ============ CHECKPOINTS (State Management) ============
    
    def save_checkpoint(self, db: Session, checkpoint: Checkpoint) -> str:
        """Save agent state snapshot"""
        try:
            memory = schemas.AgentCheckpoint(
                checkpoint_id=checkpoint.checkpoint_id,
                timestamp=checkpoint.timestamp,
                cycle_number=checkpoint.cycle_number,
                goal=checkpoint.goal,
                state=json.dumps({
                    "agent_state": checkpoint.agent_state,
                    "progress": checkpoint.progress,
                    "decisions_made": checkpoint.decisions_made,
                    "message_history": checkpoint.message_history,
                    "resources_used": checkpoint.resources_used,
                    "errors_encountered": checkpoint.errors_encountered
                }),
                is_stable=checkpoint.is_stable,
                is_active=True
            )
            db.add(memory)
            db.commit()
            logger.info(f"Saved checkpoint: {checkpoint.checkpoint_id} for cycle {checkpoint.cycle_number}")
            return checkpoint.checkpoint_id
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            db.rollback()
            raise
    
    def get_latest_stable_checkpoint(
        self, 
        db: Session,
        goal: Optional[str] = None
    ) -> Optional[Checkpoint]:
        """Get latest stable checkpoint for resumption"""
        try:
            query = db.query(schemas.AgentCheckpoint).filter(
                schemas.AgentCheckpoint.is_stable == True,
                schemas.AgentCheckpoint.is_active == True
            )
            
            if goal:
                query = query.filter(schemas.AgentCheckpoint.goal == goal)
            
            result = query.order_by(schemas.AgentCheckpoint.timestamp.desc()).first()
            
            if not result:
                return None
            
            state = json.loads(result.state) if isinstance(result.state, str) else result.state
            return Checkpoint(
                checkpoint_id=result.checkpoint_id,
                timestamp=result.timestamp,
                cycle_number=result.cycle_number,
                goal=result.goal,
                agent_state=state.get("agent_state", {}),
                progress=state.get("progress", {}),
                decisions_made=state.get("decisions_made", []),
                message_history=state.get("message_history", []),
                resources_used=state.get("resources_used", {}),
                errors_encountered=state.get("errors_encountered", []),
                is_stable=result.is_stable
            )
        except Exception as e:
            logger.error(f"Error retrieving latest checkpoint: {e}")
            return None
    
    def get_checkpoint_history(
        self, 
        db: Session,
        goal: Optional[str] = None,
        limit: int = 10
    ) -> List[Checkpoint]:
        """Get checkpoint history for recovery"""
        try:
            query = db.query(schemas.AgentCheckpoint).filter(
                schemas.AgentCheckpoint.is_active == True
            )
            
            if goal:
                query = query.filter(schemas.AgentCheckpoint.goal == goal)
            
            results = query.order_by(
                schemas.AgentCheckpoint.timestamp.desc()
            ).limit(limit).all()
            
            checkpoints = []
            for r in results:
                state = json.loads(r.state) if isinstance(r.state, str) else r.state
                checkpoints.append(Checkpoint(
                    checkpoint_id=r.checkpoint_id,
                    timestamp=r.timestamp,
                    cycle_number=r.cycle_number,
                    goal=r.goal,
                    agent_state=state.get("agent_state", {}),
                    progress=state.get("progress", {}),
                    decisions_made=state.get("decisions_made", []),
                    message_history=state.get("message_history", []),
                    resources_used=state.get("resources_used", {}),
                    errors_encountered=state.get("errors_encountered", []),
                    is_stable=r.is_stable
                ))
            
            return checkpoints
        except Exception as e:
            logger.error(f"Error retrieving checkpoint history: {e}")
            return []
    
    # ============ GOALS (Persistent Objectives) ============
    
    def create_goal(self, db: Session, goal: Goal) -> str:
        """Create a long-term goal"""
        try:
            goal_record = schemas.PersistentGoal(
                goal_id=goal.goal_id,
                created_at=goal.created_at,
                objective=goal.objective,
                status=goal.status,
                priority=goal.priority,
                context=json.dumps(goal.context),
                target_metrics=json.dumps(goal.target_metrics),
                current_progress=json.dumps(goal.current_progress),
                deadline=goal.deadline,
                is_active=True
            )
            db.add(goal_record)
            db.commit()
            logger.info(f"Created goal: {goal.objective}")
            return goal.goal_id
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            db.rollback()
            raise
    
    def get_active_goals(self, db: Session) -> List[Goal]:
        """Get all active goals"""
        try:
            results = db.query(schemas.PersistentGoal).filter(
                schemas.PersistentGoal.status == "active",
                schemas.PersistentGoal.is_active == True
            ).order_by(
                schemas.PersistentGoal.priority.desc()
            ).all()
            
            goals = []
            for r in results:
                goals.append(Goal(
                    goal_id=r.goal_id,
                    created_at=r.created_at,
                    objective=r.objective,
                    status=r.status,
                    priority=r.priority,
                    context=json.loads(r.context) if isinstance(r.context, str) else r.context,
                    target_metrics=json.loads(r.target_metrics) if isinstance(r.target_metrics, str) else r.target_metrics,
                    current_progress=json.loads(r.current_progress) if isinstance(r.current_progress, str) else r.current_progress,
                    deadline=r.deadline
                ))
            
            return goals
        except Exception as e:
            logger.error(f"Error retrieving active goals: {e}")
            return []
    
    def update_goal_progress(
        self, 
        db: Session, 
        goal_id: str, 
        progress_update: Dict[str, Any]
    ) -> bool:
        """Update progress on a goal"""
        try:
            goal = db.query(schemas.PersistentGoal).filter(
                schemas.PersistentGoal.goal_id == goal_id
            ).first()
            
            if not goal:
                return False
            
            current = json.loads(goal.current_progress) if isinstance(goal.current_progress, str) else goal.current_progress
            current.update(progress_update)
            goal.current_progress = json.dumps(current)
            
            db.commit()
            logger.info(f"Updated progress for goal {goal_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating goal progress: {e}")
            db.rollback()
            return False
