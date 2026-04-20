# services/realtime_sync.py - Real-time Sync Service
# Optimized polling endpoint for 3D Knowledge Galaxy
# The 3D graph iframe polls this endpoint every 1s instead of 3s

import os
import json
import time
from knowledge_tracing import get_student_state


def get_node_state_json(user_id: str, subject_id: str) -> dict:
    """
    Get current student state for real-time sync.
    Returns mastery data with Ebbinghaus decay applied.
    This is called by the 3D iframe via fetch() every 1 second.
    """
    state = get_student_state(user_id, subject_id)
    return state


def get_state_with_diff(user_id: str, subject_id: str, last_timestamp: float = 0) -> dict:
    """
    Get state changes since last_timestamp.
    Returns only changed nodes to minimize payload.
    Useful for debounced sync.
    """
    state = get_student_state(user_id, subject_id)
    
    if last_timestamp <= 0:
        return {
            "full": True,
            "mastery": state.get("mastery", {}),
            "timestamp": time.time()
        }
    
    # Filter only nodes updated after last_timestamp
    changed = {}
    for node_id, data in state.get("mastery", {}).items():
        last_updated = data.get("last_updated", 0)
        if last_updated > last_timestamp:
            changed[node_id] = data
    
    return {
        "full": False,
        "mastery": changed,
        "timestamp": time.time(),
        "changed_count": len(changed)
    }


def notify_mastery_change(user_id: str, subject_id: str, node_id: str, new_level: float):
    """
    Called after quiz/assessment completion to signal that a node's mastery changed.
    In the current architecture (file-based state), this is handled automatically
    by the polling mechanism. This function exists as a hook for future WebSocket upgrade.
    
    Future: Could push via WebSocket to instantly update 3D graph without polling.
    """
    print(f"[RealtimeSync] Mastery changed: {user_id}/{subject_id}/{node_id} → {new_level:.2f}")
    # Currently no-op: the 3D iframe polls the state file every 1s
    # When we add WebSocket support, this will push to connected clients
    pass
