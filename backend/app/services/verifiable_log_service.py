"""Helpers for managing the verifiable append-only log."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Optional

from app import db
from app.models import VerifiableLog
from app.schemas import VerifiableLogEventModel

from .hash_service import HashService


def _normalise_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(timespec="microseconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_normalise_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalise_value(val) for key, val in value.items()}
    return value


def append_event(
    *,
    entity_type: str,
    entity_id: int,
    event: VerifiableLogEventModel | Dict[str, Any],
) -> VerifiableLog:
    """Append a new log entry for the given entity."""

    event_model = event if isinstance(event, VerifiableLogEventModel) else VerifiableLogEventModel(**event)
    payload = event_model.model_dump()
    payload["metadata"] = _normalise_value(payload.get("metadata") or {})
    timestamp = datetime.utcnow()

    previous_entry = (
        VerifiableLog.query.order_by(VerifiableLog.id.desc()).first()
    )
    previous_hash = previous_entry.current_hash if previous_entry else None

    hash_payload = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "event_data": payload,
        "timestamp": timestamp.isoformat(timespec="microseconds"),
    }
    current_hash = HashService.generate_hash(previous_hash, hash_payload)

    entry = VerifiableLog(
        entity_type=entity_type,
        entity_id=entity_id,
        event_data=payload,
        timestamp=timestamp,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.session.add(entry)
    db.session.flush()
    return entry


def verify_chain(*, start_id: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """Verify the entire log chain."""

    query = VerifiableLog.query.order_by(VerifiableLog.id.asc())
    if start_id is not None:
        query = query.filter(VerifiableLog.id >= start_id)
    if limit is not None:
        query = query.limit(limit)

    previous_hash: Optional[str] = None
    checked = 0
    broken_at_id: Optional[int] = None
    last_hash: Optional[str] = None

    for entry in query.yield_per(200):
        if previous_hash is None and start_id is None and entry.previous_hash not in (None, ""):
            broken_at_id = entry.id
            break
        if previous_hash is not None and entry.previous_hash != previous_hash:
            broken_at_id = entry.id
            break

        timestamp_iso = entry.timestamp.isoformat(timespec="microseconds")
        hash_payload = {
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "event_data": entry.event_data,
            "timestamp": timestamp_iso,
        }
        computed_hash = HashService.generate_hash(entry.previous_hash, hash_payload)
        if computed_hash != entry.current_hash:
            broken_at_id = entry.id
            break

        previous_hash = entry.current_hash
        last_hash = entry.current_hash
        checked += 1

    integrity = "FAILED" if broken_at_id is not None else "OK"
    return {
        "integrity": integrity,
        "broken_at_id": broken_at_id,
        "checked": checked,
        "last_hash": last_hash,
    }


def list_entity_entries(entity_type: str, entity_id: int) -> List[Dict[str, Any]]:
    """Return serialised log entries for a specific entity."""

    entries: Iterable[VerifiableLog] = (
        VerifiableLog.query.filter_by(entity_type=entity_type, entity_id=entity_id)
        .order_by(VerifiableLog.id.asc())
        .all()
    )

    return [serialize_entry(entry) for entry in entries]


def serialize_entry(entry: VerifiableLog) -> Dict[str, Any]:
    """Serialise a log entry for API responses."""

    return {
        "id": entry.id,
        "entity_type": entry.entity_type,
        "entity_id": entry.entity_id,
        "timestamp": entry.timestamp.isoformat(timespec="microseconds"),
        "previous_hash": entry.previous_hash,
        "current_hash": entry.current_hash,
        "event_data": entry.event_data,
    }


def recent_entries(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent log entries in chronological order."""

    limit = max(limit, 1)
    entries = (
        VerifiableLog.query.order_by(VerifiableLog.id.desc())
        .limit(limit)
        .all()
    )
    return [serialize_entry(entry) for entry in reversed(entries)]
