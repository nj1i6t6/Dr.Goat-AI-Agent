"""Helpers for managing the verifiable append-only log."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set

from app import db
from app.models import ProductBatch, ProcessingStep, SheepEvent, VerifiableLog
from app.schemas import VerifiableLogEventModel
from app.utils import normalise_json_payload

from .hash_service import HashService


LEDGER_VERIFICATION_BATCH_SIZE = 200
RECENT_LOOKUP_PAGE_SIZE = 200


def append_event(
    *,
    entity_type: str,
    entity_id: int,
    event: VerifiableLogEventModel | Dict[str, Any],
) -> VerifiableLog:
    """Append a new log entry for the given entity."""

    event_model = event if isinstance(event, VerifiableLogEventModel) else VerifiableLogEventModel(**event)
    payload = event_model.model_dump()
    payload["metadata"] = normalise_json_payload(payload.get("metadata") or {})
    timestamp = datetime.utcnow()

    previous_entry = (
        VerifiableLog.query.order_by(VerifiableLog.id.desc()).with_for_update().first()
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

    for entry in query.yield_per(LEDGER_VERIFICATION_BATCH_SIZE):
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


def list_entity_entries(
    entity_type: str,
    entity_id: int,
    *,
    user_id: int,
) -> Optional[List[Dict[str, Any]]]:
    """Return serialised log entries for a specific entity, scoped to a user."""

    allowed_ids = _owned_ids_for_type(entity_type, {entity_id}, user_id)
    if entity_id not in allowed_ids:
        return None

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


def recent_entries(limit: int = 100, *, user_id: int) -> List[Dict[str, Any]]:
    """Return the most recent log entries visible to the user in chronological order."""

    limit = max(limit, 1)
    collected: List[VerifiableLog] = []
    last_seen_id: Optional[int] = None

    while len(collected) < limit:
        query = VerifiableLog.query.order_by(VerifiableLog.id.desc())
        if last_seen_id is not None:
            query = query.filter(VerifiableLog.id < last_seen_id)
        chunk = query.limit(RECENT_LOOKUP_PAGE_SIZE).all()
        if not chunk:
            break

        accessible = _filter_entries_for_user(chunk, user_id)
        collected.extend(accessible)
        last_seen_id = chunk[-1].id

    trimmed = collected[:limit]
    return [serialize_entry(entry) for entry in reversed(trimmed)]


def _filter_entries_for_user(entries: Iterable[VerifiableLog], user_id: int) -> List[VerifiableLog]:
    ids_by_type: Dict[str, Set[int]] = {}
    for entry in entries:
        ids_by_type.setdefault(entry.entity_type, set()).add(entry.entity_id)

    allowed: Dict[str, Set[int]] = {}
    for entity_type, ids in ids_by_type.items():
        owned_ids = _owned_ids_for_type(entity_type, ids, user_id)
        if owned_ids:
            allowed[entity_type] = owned_ids

    return [
        entry
        for entry in entries
        if entry.entity_type in allowed and entry.entity_id in allowed[entry.entity_type]
    ]


def _owned_ids_for_type(entity_type: str, entity_ids: Iterable[int], user_id: int) -> Set[int]:
    ids = {int(entity_id) for entity_id in entity_ids if entity_id is not None}
    if not ids:
        return set()

    if entity_type == "product_batch":
        rows = (
            ProductBatch.query.with_entities(ProductBatch.id)
            .filter(ProductBatch.id.in_(ids), ProductBatch.user_id == user_id)
            .all()
        )
        return {row[0] for row in rows}

    if entity_type == "processing_step":
        rows = (
            ProcessingStep.query.with_entities(ProcessingStep.id)
            .join(ProductBatch, ProcessingStep.batch_id == ProductBatch.id)
            .filter(ProcessingStep.id.in_(ids), ProductBatch.user_id == user_id)
            .all()
        )
        return {row[0] for row in rows}

    if entity_type == "sheep_event":
        rows = (
            SheepEvent.query.with_entities(SheepEvent.id)
            .filter(SheepEvent.id.in_(ids), SheepEvent.user_id == user_id)
            .all()
        )
        return {row[0] for row in rows}

    return set()
