"""BI 分析 API"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import and_, func, literal, select, true

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

    dimension_pairs = [
        (dimension, _dimension_expression(Sheep, dimension)) for dimension in request_model.cohort_by
    ]
    dimension_labels = [label for label, _ in dimension_pairs]

    sheep_select = select(
        *[expr.label(label) for label, expr in dimension_pairs],
        func.count(Sheep.id).label('sheep_count'),
        func.avg(Sheep.Body_Weight_kg).label('avg_weight'),
        func.avg(Sheep.milk_yield_kg_day).label('avg_milk'),
    ).where(Sheep.user_id == current_user.id)
    sheep_select = _apply_sheep_filters(sheep_select, request_model.filters)
    if dimension_pairs:
        sheep_select = sheep_select.group_by(*[expr for _, expr in dimension_pairs])
    sheep_subquery = sheep_select.subquery()

    cost_pairs = [
        (label, _dimension_expression(CostEntry, label)) for label in dimension_labels
    ]
    cost_select = select(
        *[expr.label(label) for label, expr in cost_pairs],
        func.sum(CostEntry.amount).label('total_cost'),
    )
    cost_select = _apply_finance_filters(cost_select, CostEntry, request_model.filters, request_model.time_range)
    if cost_pairs:
        cost_select = cost_select.group_by(*[expr for _, expr in cost_pairs])
    cost_subquery = cost_select.subquery()

    revenue_pairs = [
        (label, _dimension_expression(RevenueEntry, label)) for label in dimension_labels
    ]
    revenue_select = select(
        *[expr.label(label) for label, expr in revenue_pairs],
        func.sum(RevenueEntry.amount).label('total_revenue'),
    )
    revenue_select = _apply_finance_filters(
        revenue_select, RevenueEntry, request_model.filters, request_model.time_range
    )
    if revenue_pairs:
        revenue_select = revenue_select.group_by(*[expr for _, expr in revenue_pairs])
    revenue_subquery = revenue_select.subquery()

    if not db.session.execute(select(func.count()).select_from(sheep_subquery)).scalar():
        result = {'items': [], 'metrics': request_model.metrics}
        set_bi_cache(current_user.id, wrapped_payload, result)
        return {'data': result, 'status': 200}

    join_condition_cost = (
        and_(*[sheep_subquery.c[label] == cost_subquery.c[label] for label in dimension_labels])
        if dimension_labels
        else true()
    )
    join_condition_revenue = (
        and_(*[sheep_subquery.c[label] == revenue_subquery.c[label] for label in dimension_labels])
        if dimension_labels
        else true()
    )

    from_clause = sheep_subquery.outerjoin(cost_subquery, join_condition_cost)
    from_clause = from_clause.outerjoin(revenue_subquery, join_condition_revenue)

    result_query = select(
        *[sheep_subquery.c[label] for label in dimension_labels],
        sheep_subquery.c.sheep_count,
        sheep_subquery.c.avg_weight,
        sheep_subquery.c.avg_milk,
        func.coalesce(cost_subquery.c.total_cost, literal(0)).label('total_cost'),
        func.coalesce(revenue_subquery.c.total_revenue, literal(0)).label('total_revenue'),
    ).select_from(from_clause)

    rows = db.session.execute(result_query).all()

    response_items = []
    for row in rows:
        mapping = getattr(row, '_mapping', row)
        raw_values = [mapping[label] for label in dimension_labels]
        normalized_key = []
        for dimension, value in zip(dimension_labels, raw_values):
            if dimension == 'lactation_number' and (value is None or value == -1):
                normalized_key.append(None)
            elif dimension != 'lactation_number' and value == '未填寫':
                normalized_key.append(None)
            else:
                normalized_key.append(value)

        sheep_count = mapping['sheep_count'] or 0
        avg_weight = mapping['avg_weight']
        avg_milk = mapping['avg_milk']
        raw_cost = mapping['total_cost']
        raw_revenue = mapping['total_revenue']
        total_cost = Decimal(str(raw_cost)) if raw_cost is not None else Decimal('0')
        total_revenue = Decimal(str(raw_revenue)) if raw_revenue is not None else Decimal('0')
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
    group_expr_revenue = _time_group_expression(RevenueEntry, request_model.group_by)
    group_labels = [expr.name for expr in group_expr_cost] if group_expr_cost else []

    zero_amount = literal(0).cast(CostEntry.amount.type)
    zero_count = literal(0)

    cost_query = select(
        *group_expr_cost,
        func.sum(CostEntry.amount).label('total_cost'),
        zero_amount.label('total_revenue'),
        func.count(func.distinct(CostEntry.sheep_id)).label('sheep_incurred'),
        zero_count.label('sheep_served'),
    )
    cost_query = _apply_finance_filters(cost_query, CostEntry, request_model.filters, request_model.time_range)
    if group_expr_cost:
        cost_query = cost_query.group_by(*group_expr_cost)

    revenue_query = select(
        *[expr.label(label) for expr, label in zip(group_expr_revenue, group_labels)],
        zero_amount.label('total_cost'),
        func.sum(RevenueEntry.amount).label('total_revenue'),
        zero_count.label('sheep_incurred'),
        func.count(func.distinct(RevenueEntry.sheep_id)).label('sheep_served'),
    )
    revenue_query = _apply_finance_filters(
        revenue_query, RevenueEntry, request_model.filters, request_model.time_range
    )
    if group_expr_revenue:
        revenue_query = revenue_query.group_by(*group_expr_revenue)

    combined_union = cost_query.union_all(revenue_query).subquery()

    group_columns = [combined_union.c[label] for label in group_labels]

    aggregation_query = select(
        *group_columns,
        func.sum(combined_union.c.total_cost).label('total_cost'),
        func.sum(combined_union.c.total_revenue).label('total_revenue'),
        func.max(combined_union.c.sheep_incurred).label('sheep_incurred'),
        func.max(combined_union.c.sheep_served).label('sheep_served'),
    )
    if group_columns:
        aggregation_query = aggregation_query.group_by(*group_columns)

    rows = db.session.execute(aggregation_query).all()

    summary = {'total_cost': 0.0, 'total_revenue': 0.0, 'net_profit': 0.0}
    items = []
    for row in rows:
        mapping = getattr(row, '_mapping', row)
        total_cost = Decimal(str(mapping['total_cost'])) if mapping['total_cost'] is not None else Decimal('0')
        total_revenue = Decimal(str(mapping['total_revenue'])) if mapping['total_revenue'] is not None else Decimal('0')
        sheep_count = max(mapping.get('sheep_incurred') or 0, mapping.get('sheep_served') or 0)
        net_profit = total_revenue - total_cost

        summary['total_cost'] += float(total_cost)
        summary['total_revenue'] += float(total_revenue)
        summary['net_profit'] += float(net_profit)

        if group_labels:
            group_value = mapping[group_labels[0]]
        else:
            group_value = '總計'

        metrics = {
            'total_cost': _serialize_decimal(total_cost),
            'total_revenue': _serialize_decimal(total_revenue),
            'net_profit': _serialize_decimal(net_profit),
        }
        if 'avg_cost_per_head' in request_model.metrics:
            metrics['avg_cost_per_head'] = _serialize_decimal((total_cost / sheep_count) if sheep_count else None)
        if 'avg_revenue_per_head' in request_model.metrics:
            metrics['avg_revenue_per_head'] = _serialize_decimal((total_revenue / sheep_count) if sheep_count else None)

        items.append({'group': group_value, 'metrics': metrics})

    if not rows:
        result = {'summary': summary, 'items': [], 'metrics': request_model.metrics}
        set_bi_cache(current_user.id, wrapped_payload, result)
        return {'data': result, 'status': 200}

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
