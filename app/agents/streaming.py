# app/agents/streaming.py
import queue
import logging
from typing import Dict, Any, Generator
from datetime import datetime

logger = logging.getLogger("stream_manager")

class StreamManager:
    """
    Singleton manager for handling real-time agent event streaming.
    Allows deep nodes to emit events that are captured by the API stream.
    """
    _instance = None
    _streams: Dict[str, queue.Queue] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StreamManager, cls).__new__(cls)
        return cls._instance

    def create_stream(self, cycle_id: str) -> queue.Queue:
        """Create a new event queue for a cycle."""
        q = queue.Queue()
        self._streams[cycle_id] = q
        return q

    def emit(self, cycle_id: str, event_type: str, message: str, details: Any = None):
        """
        Emit an event to the stream.
        Safe to call from any thread.
        """
        if cycle_id in self._streams:
            event = {
                "type": event_type,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            self._streams[cycle_id].put(event)

    def get_events(self, cycle_id: str) -> Generator[Dict[str, Any], None, None]:
        """
        Yield events from the queue until a 'complete' or 'error' event is seen.
        """
        if cycle_id not in self._streams:
            return

        q = self._streams[cycle_id]
        
        while True:
            try:
                # Block for a short time to allow yielding control
                event = q.get(timeout=1.0)
                yield event
                
                if event["type"] in ["complete", "error", "cycle_complete"]:
                    break
            except queue.Empty:
                # Keep yielding to keep connection alive if needed, or just loop
                continue
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break
        
        # Cleanup
        if cycle_id in self._streams:
            del self._streams[cycle_id]

stream_manager = StreamManager()

class JobStreamManager:
    """
    Centralized event store for agent jobs.
    Replaces the local _job_progress in agent.py to allow cross-module logging.
    """
    _instance = None
    _job_events: Dict[str, Any] = {}  # job_id -> deque
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobStreamManager, cls).__new__(cls)
        return cls._instance
    
    def get_queue(self, job_id: str):
        from collections import deque
        if job_id not in self._job_events:
            self._job_events[job_id] = deque(maxlen=1000)
        return self._job_events[job_id]
    
    def log_event(self, job_id: str, event_type: str, message: str, details: Any = None, stage: str = None):
        """Log an event to the job's queue."""
        queue = self.get_queue(job_id)
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "stage": stage or event_type.upper(),
            "message": message,
            "details": details or {}
        }
        queue.append(event)
        logger.info(f"Job {job_id} [{event['stage']}]: {message}")

job_stream_manager = JobStreamManager()
