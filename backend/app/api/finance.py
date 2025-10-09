from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import or_

from app import db
from app.models import CostEntry, RevenueEntry
from app.schemas import (
    CostEntryBulkImportModel,
    CostEntryCreateModel,
    CostEntryUpdateModel,
    RevenueEntryBulkImportModel,
    RevenueEntryCreateModel,
    RevenueEntryUpdateModel,
)

bp = Blueprint('finance', __name__)


def _parse_date_bound(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError('recorded_at 需要使用 ISO8601 格式 (YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS)') from exc


def _serialize_entry(entry: CostEntry | RevenueEntry) -> Dict[str, Any]:
    payload = entry.to_dict()
    payload['amount'] = float(payload['amount']) if payload.get('amount') is not None else None
    return payload


def _prepare_model_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(data)
    if 'metadata' in payload:
        payload['metadata_json'] = payload.pop('metadata')
    return payload


def _apply_common_filters(model, params: Dict[str, str]):
    query = model.query.filter(model.user_id == current_user.id)

    category = params.get('category')
    if category:
        query = query.filter(model.category == category)

    breed = params.get('breed')
    if breed:
        query = query.filter(model.breed == breed)

    age_group = params.get('age_group')
    if age_group:
        query = query.filter(model.age_group == age_group)

    parity = params.get('parity')
    if parity is not None:
        try:
            parity_int = int(parity)
        except ValueError:
            raise ValueError('parity 必須為整數')
        query = query.filter(model.parity == parity_int)

    herd_tag = params.get('herd_tag')
    if herd_tag:
        query = query.filter(model.herd_tag == herd_tag)

    start_at = _parse_date_bound(params.get('start_at'))
    end_at = _parse_date_bound(params.get('end_at'))
    if start_at:
        query = query.filter(model.recorded_at >= start_at)
    if end_at:
        query = query.filter(model.recorded_at <= end_at)

    search = params.get('search')
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                model.description.ilike(pattern),
                model.notes.ilike(pattern),
                model.category.ilike(pattern),
                model.subcategory.ilike(pattern),
            )
        )

    return query.order_by(model.recorded_at.desc(), model.id.desc())


def _create_entries_from_payload(payload: Iterable[Dict[str, Any]], model_class):
    instances = []
    for item in payload:
        instance = model_class(user_id=current_user.id, **_prepare_model_payload(item))
        instances.append(instance)
        db.session.add(instance)
    db.session.commit()
    return instances


@bp.route('/costs', methods=['GET'])
@login_required
def list_costs():
    try:
        query = _apply_common_filters(CostEntry, request.args)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    try:
        limit = int(request.args.get('limit', 100))
    except (TypeError, ValueError):
        return jsonify(error='limit 必須為整數'), 400
    limit = max(1, min(limit, 500))
    entries = query.limit(limit).all()
    return jsonify([_serialize_entry(entry) for entry in entries])


@bp.route('/costs', methods=['POST'])
@login_required
def create_cost():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = CostEntryCreateModel(**data).model_dump()
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    entry = CostEntry(user_id=current_user.id, **_prepare_model_payload(payload))
    db.session.add(entry)
    db.session.commit()
    return jsonify(_serialize_entry(entry)), 201


@bp.route('/costs/<int:entry_id>', methods=['PUT'])
@login_required
def update_cost(entry_id: int):
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    entry = CostEntry.query.filter_by(user_id=current_user.id, id=entry_id).first()
    if not entry:
        return jsonify(error='找不到成本紀錄或無權存取'), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = CostEntryUpdateModel(**data).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    for field, value in payload.items():
        target_field = 'metadata_json' if field == 'metadata' else field
        setattr(entry, target_field, value)

    db.session.commit()
    return jsonify(_serialize_entry(entry))


@bp.route('/costs/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_cost(entry_id: int):
    entry = CostEntry.query.filter_by(user_id=current_user.id, id=entry_id).first()
    if not entry:
        return jsonify(error='找不到成本紀錄或無權存取'), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify(success=True)


@bp.route('/costs/bulk', methods=['POST'])
@login_required
def bulk_create_costs():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = CostEntryBulkImportModel(**data)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    entries = _create_entries_from_payload((item.model_dump() for item in payload.entries), CostEntry)
    return jsonify([_serialize_entry(entry) for entry in entries]), 201


@bp.route('/revenues', methods=['GET'])
@login_required
def list_revenues():
    try:
        query = _apply_common_filters(RevenueEntry, request.args)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    try:
        limit = int(request.args.get('limit', 100))
    except (TypeError, ValueError):
        return jsonify(error='limit 必須為整數'), 400
    limit = max(1, min(limit, 500))
    entries = query.limit(limit).all()
    return jsonify([_serialize_entry(entry) for entry in entries])


@bp.route('/revenues', methods=['POST'])
@login_required
def create_revenue():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = RevenueEntryCreateModel(**data).model_dump()
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    entry = RevenueEntry(user_id=current_user.id, **_prepare_model_payload(payload))
    db.session.add(entry)
    db.session.commit()
    return jsonify(_serialize_entry(entry)), 201


@bp.route('/revenues/<int:entry_id>', methods=['PUT'])
@login_required
def update_revenue(entry_id: int):
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400

    entry = RevenueEntry.query.filter_by(user_id=current_user.id, id=entry_id).first()
    if not entry:
        return jsonify(error='找不到收益紀錄或無權存取'), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = RevenueEntryUpdateModel(**data).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    for field, value in payload.items():
        target_field = 'metadata_json' if field == 'metadata' else field
        setattr(entry, target_field, value)

    db.session.commit()
    return jsonify(_serialize_entry(entry))


@bp.route('/revenues/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_revenue(entry_id: int):
    entry = RevenueEntry.query.filter_by(user_id=current_user.id, id=entry_id).first()
    if not entry:
        return jsonify(error='找不到收益紀錄或無權存取'), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify(success=True)


@bp.route('/revenues/bulk', methods=['POST'])
@login_required
def bulk_create_revenues():
    if not request.is_json:
        return jsonify(error='請提供 JSON 格式資料'), 400
    data = request.get_json(silent=True)
    if data is None:
        return jsonify(error='請提供 JSON 格式資料'), 400
    try:
        payload = RevenueEntryBulkImportModel(**data)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    entries = _create_entries_from_payload((item.model_dump() for item in payload.entries), RevenueEntry)
    return jsonify([_serialize_entry(entry) for entry in entries]), 201
