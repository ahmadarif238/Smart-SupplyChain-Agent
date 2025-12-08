# app/persistence/__init__.py
"""
Persistence module for agentic AI.
Enables true autonomy through memory, state management, and learning.
"""

from app.persistence.memory_types import (
    MemoryType,
    EpisodicMemory,
    SemanticMemory,
    ProceduralMemory,
    Checkpoint,
    Goal
)
from app.persistence.persistent_memory import PersistentMemoryManager
from app.persistence.recovery_manager import RecoveryManager

__all__ = [
    "MemoryType",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "Checkpoint",
    "Goal",
    "PersistentMemoryManager",
    "RecoveryManager"
]
