# app/utils/common.py
from typing import Any, Dict, List

def serialize_model(obj: Any):
    """
    Serialize SQLAlchemy model instance(s) to plain dict(s).
    Works with single model, list of models, or plain data.
    """
    if obj is None:
        return None
    if isinstance(obj, list):
        return [serialize_model(x) for x in obj]
    if hasattr(obj, "__dict__"):
        data = obj.__dict__.copy()
        data.pop("_sa_instance_state", None)
        return data
    # fallback for already-serializable objects
    return obj
