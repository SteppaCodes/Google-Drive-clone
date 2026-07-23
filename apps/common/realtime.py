"""
Real-Time Event Manager for Lore Artifact Plane.
Provides thread-safe pub/sub queues for Server-Sent Events (SSE) and MCP Resource Notifications.
"""

import json
import logging
from queue import Queue
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Global thread-safe event listeners pool
_subscribers: List[Queue] = []


def subscribe_events() -> Queue:
    """Subscribe to global real-time event bus. Returns an SSE Queue."""
    q: Queue = Queue(maxsize=100)
    _subscribers.append(q)
    return q


def unsubscribe_events(q: Queue) -> None:
    """Unsubscribe from global real-time event bus."""
    if q in _subscribers:
        _subscribers.remove(q)


def publish_artifact_event(
    event_type: str,
    artifact_id: str,
    payload: Dict[str, Any] = None,
    owner_id: str = None,
) -> None:
    """
    Publish an event to all active SSE streaming clients and MCP subscribers.

    ``owner_id`` is the string id of the artifact owner's Principal. It is
    used by SSE consumers to filter delivery so a subscriber only receives
    events for artifacts it is authorized to see. Events published without
    an ``owner_id`` are treated as unscoped and are NOT delivered to any
    principal-scoped subscriber (fail closed).

    Event Types:
    - `artifact.created`: New artifact created.
    - `artifact.updated`: Artifact content or title updated.
    - `artifact.state_changed`: Lifecycle state changed (approved, rejected, draft).
    - `artifact.relationship_created`: Relationship edge added in graph.
    """
    if payload is None:
        payload = {}

    event_data = {
        "event": event_type,
        "artifact_id": str(artifact_id),
        "owner_id": str(owner_id) if owner_id is not None else None,
        "payload": payload,
    }

    dead_queues = []
    for q in _subscribers:
        try:
            q.put_nowait(event_data)
        except Exception:
            dead_queues.append(q)

    for dq in dead_queues:
        unsubscribe_events(dq)

    logger.info(f"Published real-time event [{event_type}] for artifact {artifact_id}")
