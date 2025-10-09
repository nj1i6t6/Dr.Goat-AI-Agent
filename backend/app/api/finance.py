"""成本與收益資料管理 API"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Type

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import and_, select

from app import db
from app.models import CostEntry, RevenueEntry, Sheep
from app.schemas import (
    CostEntryCreateModel,
    CostEntryUpdateModel,
    FinanceBulkImportModel,
    RevenueEntryCreateModel,
    RevenueEntryUpdateModel,
    create_error_response,
)

bp = Blueprint('finance', __name__)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError('日期格式需為 ISO 8601 (例如 2024-01-31T12:00:00)')


def _serialize_entry(entry: CostEntry | RevenueEntry) -> dict:
    data = entry.to_dict()
    # SQLAlchemy 會回傳 Decimal 與 datetime，需要序列化
    data['amount'] = float(data['amount']) if data.get('amount') is not None else None
    for key in ('recorded_at', 'created_at', 'updated_at'):
        if data.get(key):
            data[key] = data[key].isoformat()
    return data


def _ensure_sheep_ownership(sheep_id: int | None) -> None:
    if sheep_id is None:
        return
    exists = db.session.scalar(
        select(Sheep.id).where(Sheep.id == sheep_id, Sheep.user_id == current_user.id)
    )
    if not exists:
        raise ValueError('指定的羊隻不存在或非當前使用者所有')


def _apply_filters(model: Type[CostEntry | RevenueEntry]):
    conditions = [model.user_id == current_user.id]

    start = _parse_iso_datetime(request.args.get('start'))
    end = _parse_iso_datetime(request.args.get('end'))
    if start:
        conditions.append(model.recorded_at >= start)
    if end:
        conditions.append(model.recorded_at <= end)

    for field in ('category', 'breed', 'production_stage'):
        value = request.args.get(field)
        if value:
            values = [v.strip() for v in value.split(',') if v.strip()]
            if values:
                conditions.append(model.__table__.c[field].in_(values))

    lactation = request.args.get('lactation_number')
    if lactation:
        try:
            values = [int(v.strip()) for v in lactation.split(',') if v.strip()]
        except ValueError:
            raise ValueError('胎次篩選需為整數')
        if values:
            conditions.append(model.lactation_number.in_(values))

    sheep_id = request.args.get('sheep_id')
    if sheep_id:
        try:
            sheep_id_int = int(sheep_id)
        except ValueError:
            raise ValueError('羊隻 ID 需為整數')
        conditions.append(model.sheep_id == sheep_id_int)

    return and_(*conditions)


def _create_entry(model_cls: Type[CostEntry | RevenueEntry], payload: dict) -> dict:
    _ensure_sheep_ownership(payload.get('sheep_id'))
    payload['user_id'] = current_user.id
    payload['amount'] = Decimal(str(payload['amount']))
    entry = model_cls(**payload)
    db.session.add(entry)
    db.session.commit()
    return _serialize_entry(entry)


def _update_entry(model_cls: Type[CostEntry | RevenueEntry], entry_id: int, payload: dict) -> dict:
    entry = db.session.get(model_cls, entry_id)
    if not entry or entry.user_id != current_user.id:
        raise LookupError('資料不存在')

    if 'sheep_id' in payload:
        _ensure_sheep_ownership(payload['sheep_id'])
    if 'amount' in payload and payload['amount'] is not None:
        payload['amount'] = Decimal(str(payload['amount']))

    for key, value in payload.items():
        if value is None and key not in {'sheep_id', 'subcategory', 'label', 'notes', 'extra_metadata'}:
            continue
        setattr(entry, key, value)
    db.session.commit()
    db.session.refresh(entry)
    return _serialize_entry(entry)


def _handle_bulk_import(model_cls: Type[CostEntry | RevenueEntry], entries: list[dict]) -> dict:
    created = []
    for item in entries:
        _ensure_sheep_ownership(item.get('sheep_id'))
        item['user_id'] = current_user.id
        item['amount'] = Decimal(str(item['amount']))
        entry = model_cls(**item)
        db.session.add(entry)
        created.append(entry)
    db.session.commit()
    return {'items': [_serialize_entry(e) for e in created]}


@bp.route('/costs', methods=['GET'])
@login_required
def list_costs():
    try:
        conditions = _apply_filters(CostEntry)
    except ValueError as exc:
        return jsonify(create_error_response(str(exc))), 400

    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))

    stmt = select(CostEntry).where(conditions).order_by(CostEntry.recorded_at.desc())
    total = db.session.scalar(select(db.func.count()).select_from(stmt.subquery()))
    items = db.session.scalars(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return jsonify({
        'total': total or 0,
        'items': [_serialize_entry(item) for item in items],
    })


@bp.route('/costs', methods=['POST'])
@login_required
def create_cost():
    try:
        payload = CostEntryCreateModel(**request.get_json()).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(create_error_response('輸入資料驗證失敗', exc.errors())), 400

    try:
        result = _create_entry(CostEntry, payload)
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result), 201


@bp.route('/costs/<int:entry_id>', methods=['PUT'])
@login_required
def update_cost(entry_id: int):
    try:
        payload = CostEntryUpdateModel(**request.get_json()).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(create_error_response('輸入資料驗證失敗', exc.errors())), 400

    try:
        result = _update_entry(CostEntry, entry_id, payload)
    except LookupError:
        return jsonify(create_error_response('資料不存在')), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result)


@bp.route('/costs/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_cost(entry_id: int):
    entry = db.session.get(CostEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        return jsonify(create_error_response('資料不存在')), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/costs/bulk-import', methods=['POST'])
@login_required
def bulk_import_costs():
    try:
        payload = FinanceBulkImportModel(**request.get_json()).model_dump()
    except ValidationError as exc:
        return jsonify(create_error_response('匯入資料驗證失敗', exc.errors())), 400

    try:
        result = _handle_bulk_import(CostEntry, payload['entries'])
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result), 201


@bp.route('/revenues', methods=['GET'])
@login_required
def list_revenues():
    try:
        conditions = _apply_filters(RevenueEntry)
    except ValueError as exc:
        return jsonify(create_error_response(str(exc))), 400

    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))

    stmt = select(RevenueEntry).where(conditions).order_by(RevenueEntry.recorded_at.desc())
    total = db.session.scalar(select(db.func.count()).select_from(stmt.subquery()))
    items = db.session.scalars(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()

    return jsonify({
        'total': total or 0,
        'items': [_serialize_entry(item) for item in items],
    })


@bp.route('/revenues', methods=['POST'])
@login_required
def create_revenue():
    try:
        payload = RevenueEntryCreateModel(**request.get_json()).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(create_error_response('輸入資料驗證失敗', exc.errors())), 400

    try:
        result = _create_entry(RevenueEntry, payload)
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result), 201


@bp.route('/revenues/<int:entry_id>', methods=['PUT'])
@login_required
def update_revenue(entry_id: int):
    try:
        payload = RevenueEntryUpdateModel(**request.get_json()).model_dump(exclude_unset=True)
    except ValidationError as exc:
        return jsonify(create_error_response('輸入資料驗證失敗', exc.errors())), 400

    try:
        result = _update_entry(RevenueEntry, entry_id, payload)
    except LookupError:
        return jsonify(create_error_response('資料不存在')), 404
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result)


@bp.route('/revenues/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_revenue(entry_id: int):
    entry = db.session.get(RevenueEntry, entry_id)
    if not entry or entry.user_id != current_user.id:
        return jsonify(create_error_response('資料不存在')), 404

    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/revenues/bulk-import', methods=['POST'])
@login_required
def bulk_import_revenues():
    try:
        payload = FinanceBulkImportModel(**request.get_json()).model_dump()
    except ValidationError as exc:
        return jsonify(create_error_response('匯入資料驗證失敗', exc.errors())), 400

    try:
        result = _handle_bulk_import(RevenueEntry, payload['entries'])
    except ValueError as exc:
        db.session.rollback()
        return jsonify(create_error_response(str(exc))), 400

    return jsonify(result), 201
