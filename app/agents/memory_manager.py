# app/agents/memory_manager.py
from app.models.database import SessionLocal
from app.models import schemas
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

logger = logging.getLogger("memory_manager")

class MemoryManager:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def save_memory(self, payload: dict):
        db: Session = self.session_factory()
        try:
            mem = schemas.AgentMemory(
                context=json.dumps(payload.get("forecast", {}))[:4000],
                decision=json.dumps(payload.get("decision", {}))[:4000],
                reasoning=json.dumps(payload.get("action_result", {}))[:4000],
                created_at=datetime.utcnow()
            )
            db.add(mem)
            db.commit()
            db.refresh(mem)
            return mem.id
        except Exception as e:
            logger.exception("Failed to save memory: %s", e)
            return None
        finally:
            db.close()

    def save_semantic_memory(self, fact: str, entity: str, category: str = "general"):
        """Save a semantic fact about an entity (SKU, Supplier, etc.)"""
        db: Session = self.session_factory()
        try:
            # Check if similar fact exists to avoid duplicates
            existing = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == "semantic",
                schemas.PersistentMemory.key == entity,
                schemas.PersistentMemory.description == fact
            ).first()
            
            if existing:
                return existing.id
                
            mem = schemas.PersistentMemory(
                memory_type="semantic",
                key=entity, # The entity this fact is about (e.g. SKU-123)
                category=category,
                description=fact,
                content=json.dumps({"fact": fact, "created_at": datetime.utcnow().isoformat()}),
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.add(mem)
            db.commit()
            logger.info(f"Saved semantic memory for {entity}: {fact}")
            return mem.id
        except Exception as e:
            logger.exception("Failed to save semantic memory: %s", e)
            return None
        finally:
            db.close()

    def retrieve_relevant_facts(self, entity: str) -> list:
        """Retrieve all active semantic facts for an entity"""
        db: Session = self.session_factory()
        try:
            memories = db.query(schemas.PersistentMemory).filter(
                schemas.PersistentMemory.memory_type == "semantic",
                schemas.PersistentMemory.key == entity,
                schemas.PersistentMemory.is_active == True
            ).all()
            
            return [m.description for m in memories]
        finally:
            db.close()
