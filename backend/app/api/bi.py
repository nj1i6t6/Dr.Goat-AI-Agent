"""BI 分析 API"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import and_, func, literal, select

from app import db
from app.cache import check_bi_rate_limit, get_bi_cache, set_bi_cache
from app.models import CostEntry, RevenueEntry, Sheep
from app.schemas import CohortAnalysisRequest, CostBenefitRequest, create_error_response

bp = Blueprint('bi', __name__)

_DIMENSION_CONFIG = {
    'breed': {
        'sheep_attr': 'Breed',
        'finance_attr': 'breed',
        'fallback': '未填寫',
    },
    'lactation_number': {
        'sheep_attr': 'Lactation',
        'finance_attr': 'lactation_number',
        'fallback': -1,
    },
    'production_stage': {
        'sheep_attr': 'status',
        'finance_attr': 'production_stage',
        'fallback': '未填寫',
    },
}


def _dimension_expression(model, dimension: str):
    config = _DIMENSION_CONFIG[dimension]
    column = getattr(model, config['sheep_attr'] if model is Sheep else config['finance_attr'])
    fallback = config['fallback']
    return func.coalesce(column, literal(fallback))


def _apply_sheep_filters(query, filters) -> Iterable:
    if not filters:
        return query
    if filters.breed:
        query = query.where(Sheep.Breed.in_(filters.breed))
    if filters.lactation_number:
        query = query.where(Sheep.Lactation.in_(filters.lactation_number))
    if filters.production_stage:
        query = query.where(Sheep.status.in_(filters.production_stage))
    if filters.min_age_months is not None:
        query = query.where(Sheep.Age_Months >= filters.min_age_months)
    if filters.max_age_months is not None:
        query = query.where(Sheep.Age_Months <= filters.max_age_months)
    return query


def _apply_finance_filters(query, model, filters, time_range):
    conditions = [model.user_id == current_user.id]

    if filters:
        if filters.category:
            conditions.append(model.category.in_(filters.category))
        if filters.breed:
            conditions.append(model.breed.in_(filters.breed))
        if filters.lactation_number:
            conditions.append(model.lactation_number.in_(filters.lactation_number))
        if filters.production_stage:
            conditions.append(model.production_stage.in_(filters.production_stage))
        if filters.min_age_months is not None:
            conditions.append(model.age_months >= filters.min_age_months)
        if filters.max_age_months is not None:
            conditions.append(model.age_months <= filters.max_age_months)

    if time_range:
        if time_range.start:
            conditions.append(model.recorded_at >= time_range.start)
        if time_range.end:
            conditions.append(model.recorded_at <= time_range.end)

    return query.where(and_(*conditions))


def _serialize_decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _cohort_analysis(payload: dict) -> dict:
    try:
        request_model = CohortAnalysisRequest(**payload)
    except ValidationError as exc:
        return {'error': create_error_response('請求資料驗證失敗', exc.errors()), 'status': 400}

    wrapped_payload = {'endpoint': 'cohort', 'payload': request_model.model_dump()}
    cached = get_bi_cache(current_user.id, wrapped_payload)
    if cached:
        return {'data': cached, 'status': 200}

    if not check_bi_rate_limit(current_user.id, 'cohort-analysis'):
        return {'error': create_error_response('查詢次數過多，請稍後再試'), 'status': 429}

    dimension_exprs = []
    dimension_labels = []
    group_by_columns = []
    for dimension in request_model.cohort_by:
        expr = _dimension_expression(Sheep, dimension)
        dimension_exprs.append(expr.label(dimension))
        dimension_labels.append(dimension)
        group_by_columns.append(expr)

    sheep_query = select(
        *dimension_exprs,
        func.count(Sheep.id).label('sheep_count'),
        func.avg(Sheep.Body_Weight_kg).label('avg_weight'),
        func.avg(Sheep.milk_yield_kg_day).label('avg_milk'),
    ).where(Sheep.user_id == current_user.id)
    sheep_query = _apply_sheep_filters(sheep_query, request_model.filters)
    if group_by_columns:
        sheep_query = sheep_query.group_by(*group_by_columns)

    sheep_rows = db.session.execute(sheep_query).all()
    if not sheep_rows:
        result = {'items': [], 'metrics': request_model.metrics}
        set_bi_cache(current_user.id, wrapped_payload, result)
        return {'data': result, 'status': 200}

    cost_group_exprs = [
        _dimension_expression(CostEntry, dimension).label(dimension) for dimension in request_model.cohort_by
    ]
    cost_query = select(
        *cost_group_exprs,
        func.sum(CostEntry.amount).label('total_cost'),
    )
    cost_query = _apply_finance_filters(cost_query, CostEntry, request_model.filters, request_model.time_range)
    if request_model.cohort_by:
        cost_query = cost_query.group_by(*[_dimension_expression(CostEntry, d) for d in request_model.cohort_by])
    cost_rows = {tuple(row[:len(request_model.cohort_by)]): row[-1] for row in db.session.execute(cost_query).all()}

    revenue_group_exprs = [
        _dimension_expression(RevenueEntry, dimension).label(dimension) for dimension in request_model.cohort_by
    ]
    revenue_query = select(
        *revenue_group_exprs,
        func.sum(RevenueEntry.amount).label('total_revenue'),
    )
    revenue_query = _apply_finance_filters(revenue_query, RevenueEntry, request_model.filters, request_model.time_range)
    if request_model.cohort_by:
        revenue_query = revenue_query.group_by(*[_dimension_expression(RevenueEntry, d) for d in request_model.cohort_by])
    revenue_rows = {tuple(row[:len(request_model.cohort_by)]): row[-1] for row in db.session.execute(revenue_query).all()}

    response_items = []
    for row in sheep_rows:
        mapping = getattr(row, '_mapping', row)
        group_key_raw = [mapping[label] for label in dimension_labels]
        normalized_key = []
        for dimension, value in zip(dimension_labels, group_key_raw):
            if dimension == 'lactation_number' and (value is None or value == -1):
                normalized_key.append(None)
            elif dimension != 'lactation_number' and value == '未填寫':
                normalized_key.append(None)
            else:
                normalized_key.append(value)
        group_key = tuple(group_key_raw)
        sheep_count = mapping['sheep_count'] or 0
        avg_weight = mapping['avg_weight']
        avg_milk = mapping['avg_milk']
        total_cost = cost_rows.get(group_key, Decimal('0'))
        total_revenue = revenue_rows.get(group_key, Decimal('0'))
        net_profit = total_revenue - total_cost
        cost_per_head = (total_cost / sheep_count) if sheep_count else None
        revenue_per_head = (total_revenue / sheep_count) if sheep_count else None

        item = {label: value for label, value in zip(dimension_labels, normalized_key)}
        metrics_payload = {
            'sheep_count': sheep_count,
            'avg_weight': float(avg_weight) if avg_weight is not None else None,
            'avg_milk_yield': float(avg_milk) if avg_milk is not None else None,
            'total_cost': _serialize_decimal(total_cost),
            'total_revenue': _serialize_decimal(total_revenue),
            'net_profit': _serialize_decimal(net_profit),
            'cost_per_head': _serialize_decimal(cost_per_head),
            'revenue_per_head': _serialize_decimal(revenue_per_head),
        }
        item['metrics'] = {metric: metrics_payload.get(metric) for metric in request_model.metrics}
        response_items.append(item)

    result = {
        'items': response_items,
        'metrics': request_model.metrics,
    }
    set_bi_cache(current_user.id, wrapped_payload, result)
    return {'data': result, 'status': 200}


def _time_group_expression(model, group_by: str):
    if group_by == 'none':
        return []
    if group_by == 'month':
        bind = db.session.get_bind()
        dialect_name = getattr(bind.dialect, 'name', 'sqlite') if bind is not None else 'sqlite'
        if dialect_name == 'sqlite':
            return [func.strftime('%Y-%m', model.recorded_at).label('period')]
        return [func.date_trunc('month', model.recorded_at).label('period')]
    if group_by in _DIMENSION_CONFIG:
        expr = _dimension_expression(model, group_by).label(group_by)
        return [expr]
    if group_by == 'category':
        return [model.category.label('category')]
    raise ValueError('不支援的分組方式')


def _cost_benefit(payload: dict) -> dict:
    try:
        request_model = CostBenefitRequest(**payload)
    except ValidationError as exc:
        return {'error': create_error_response('請求資料驗證失敗', exc.errors()), 'status': 400}

    wrapped_payload = {'endpoint': 'cost-benefit', 'payload': request_model.model_dump()}
    cached = get_bi_cache(current_user.id, wrapped_payload)
    if cached:
        return {'data': cached, 'status': 200}

    if not check_bi_rate_limit(current_user.id, 'cost-benefit'):
        return {'error': create_error_response('查詢次數過多，請稍後再試'), 'status': 429}

    group_expr_cost = _time_group_expression(CostEntry, request_model.group_by)
    cost_query = select(
        *group_expr_cost,
        func.sum(CostEntry.amount).label('total_cost'),
        func.count(func.distinct(CostEntry.sheep_id)).label('sheep_incurred'),
    )
    cost_query = _apply_finance_filters(cost_query, CostEntry, request_model.filters, request_model.time_range)
    if group_expr_cost:
        cost_query = cost_query.group_by(*group_expr_cost)
    cost_rows = db.session.execute(cost_query).all()

    group_expr_revenue = _time_group_expression(RevenueEntry, request_model.group_by)
    revenue_query = select(
        *group_expr_revenue,
        func.sum(RevenueEntry.amount).label('total_revenue'),
        func.count(func.distinct(RevenueEntry.sheep_id)).label('sheep_served'),
    )
    revenue_query = _apply_finance_filters(revenue_query, RevenueEntry, request_model.filters, request_model.time_range)
    if group_expr_revenue:
        revenue_query = revenue_query.group_by(*group_expr_revenue)
    revenue_rows = db.session.execute(revenue_query).all()

    # 統整資料
    grouped = {}
    for row in cost_rows:
        mapping = getattr(row, '_mapping', row)
        key = tuple(row[:-2]) if request_model.group_by != 'none' else ('總計',)
        grouped.setdefault(key, {'total_cost': Decimal('0'), 'total_revenue': Decimal('0'), 'sheep': 0})
        grouped[key]['total_cost'] = mapping['total_cost'] or Decimal('0')
        grouped[key]['sheep'] = max(grouped[key]['sheep'], mapping['sheep_incurred'] or 0)
    for row in revenue_rows:
        mapping = getattr(row, '_mapping', row)
        key = tuple(row[:-2]) if request_model.group_by != 'none' else ('總計',)
        grouped.setdefault(key, {'total_cost': Decimal('0'), 'total_revenue': Decimal('0'), 'sheep': 0})
        grouped[key]['total_revenue'] = mapping['total_revenue'] or Decimal('0')
        grouped[key]['sheep'] = max(grouped[key]['sheep'], mapping['sheep_served'] or 0)

    summary = {'total_cost': 0.0, 'total_revenue': 0.0, 'net_profit': 0.0}
    items = []
    for key, aggregate in grouped.items():
        total_cost = aggregate['total_cost']
        total_revenue = aggregate['total_revenue']
        sheep_count = aggregate['sheep']
        net_profit = total_revenue - total_cost
        summary['total_cost'] += float(total_cost)
        summary['total_revenue'] += float(total_revenue)
        summary['net_profit'] += float(net_profit)

        item = {
            'group': key[0] if request_model.group_by != 'none' else '總計',
            'metrics': {
                'total_cost': _serialize_decimal(total_cost),
                'total_revenue': _serialize_decimal(total_revenue),
                'net_profit': _serialize_decimal(net_profit),
            }
        }
        if 'avg_cost_per_head' in request_model.metrics:
            item['metrics']['avg_cost_per_head'] = _serialize_decimal((total_cost / sheep_count) if sheep_count else None)
        if 'avg_revenue_per_head' in request_model.metrics:
            item['metrics']['avg_revenue_per_head'] = _serialize_decimal((total_revenue / sheep_count) if sheep_count else None)
        items.append(item)

    result = {
        'summary': summary,
        'items': items,
        'metrics': request_model.metrics,
    }
    set_bi_cache(current_user.id, wrapped_payload, result)
    return {'data': result, 'status': 200}


@bp.route('/cohort-analysis', methods=['POST'])
@login_required
def cohort_analysis():
    payload = request.get_json(silent=True) or {}
    result = _cohort_analysis(payload)
    if 'error' in result:
        return jsonify(result['error']), result['status']
    return jsonify(result['data']), result['status']


@bp.route('/cost-benefit', methods=['POST'])
@login_required
def cost_benefit():
    payload = request.get_json(silent=True) or {}
    result = _cost_benefit(payload)
    if 'error' in result:
        return jsonify(result['error']), result['status']
    return jsonify(result['data']), result['status']
