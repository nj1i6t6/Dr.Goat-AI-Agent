from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

import markdown
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from sqlalchemy import and_, case, func, literal, select, union_all
from sqlalchemy.sql import ColumnElement

from app import db
from app.cache import check_bi_rate_limit, get_bi_cache, set_bi_cache
from app.models import CostEntry, RevenueEntry
from app.schemas import BiAiReportRequestModel, CohortAnalysisQueryModel, CostBenefitQueryModel
from app.utils import call_gemini_api

bp = Blueprint('bi', __name__)

_DIMENSION_EXPRESSIONS: Dict[str, tuple[ColumnElement, ColumnElement]] = {
    'category': (CostEntry.category, RevenueEntry.category),
    'subcategory': (CostEntry.subcategory, RevenueEntry.subcategory),
    'breed': (CostEntry.breed, RevenueEntry.breed),
    'age_group': (CostEntry.age_group, RevenueEntry.age_group),
    'parity': (CostEntry.parity, RevenueEntry.parity),
    'herd_tag': (CostEntry.herd_tag, RevenueEntry.herd_tag),
    'recorded_date': (func.date(CostEntry.recorded_at), func.date(RevenueEntry.recorded_at)),
}


def _normalize_filter_values(key: str, values: Iterable[Any]) -> List[Any]:
    normalized: List[Any] = []
    for raw in values:
        if raw in (None, ''):
            continue
        if key == 'parity':
            try:
                normalized.append(int(raw))
            except (TypeError, ValueError):
                continue
        elif key == 'recorded_date':
            text = str(raw).strip()
            if text.endswith('Z'):
                text = text[:-1]
            try:
                normalized.append(datetime.fromisoformat(text).date())
            except ValueError:
                try:
                    normalized.append(datetime.strptime(text, '%Y-%m-%d').date())
                except ValueError:
                    continue
        else:
            normalized.append(str(raw))
    return normalized


def _build_conditions(model, filters: Optional[Dict[str, List[Any]]], time_range) -> List[ColumnElement]:
    conditions: List[ColumnElement] = [model.user_id == current_user.id]
    if filters:
        for key, values in filters.items():
            norm = _normalize_filter_values(key, values)
            if not norm:
                continue
            if key == 'recorded_date':
                conditions.append(func.date(model.recorded_at).in_(norm))
            else:
                column = getattr(model, key)
                conditions.append(column.in_(norm))
    if time_range:
        if time_range.start:
            conditions.append(model.recorded_at >= time_range.start)
        if time_range.end:
            conditions.append(model.recorded_at <= time_range.end)
    return conditions


def _build_dimension_specs(dimensions: List[str], overrides: Optional[Dict[str, tuple[ColumnElement, ColumnElement]]] = None):
    specs = []
    for dim in dimensions:
        if overrides and dim in overrides:
            specs.append({'key': dim, 'cost': overrides[dim][0], 'revenue': overrides[dim][1]})
        else:
            specs.append({'key': dim, 'cost': _DIMENSION_EXPRESSIONS[dim][0], 'revenue': _DIMENSION_EXPRESSIONS[dim][1]})
    return specs


def _build_side_select(model, specs, filters, time_range, kind: str):
    if specs:
        select_columns = [entry['cost' if kind == 'cost' else 'revenue'].label(entry['key']) for entry in specs]
        group_columns = [entry['cost' if kind == 'cost' else 'revenue'] for entry in specs]
    else:
        select_columns = []
        group_columns = []
    stmt = select(
        *select_columns,
        func.sum(model.amount).label('amount'),
        func.count(model.id).label('entry_count'),
        literal(kind).label('kind'),
    )
    conditions = _build_conditions(model, filters, time_range)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    if group_columns:
        stmt = stmt.group_by(*group_columns)
    return stmt


def _execute_union_query(
    dimensions: List[str],
    filters: Optional[Dict[str, List[Any]]],
    time_range,
    limit: Optional[int] = None,
    overrides: Optional[Dict[str, tuple[ColumnElement, ColumnElement]]] = None,
    order_by_dimensions: bool = False,
):
    specs = _build_dimension_specs(dimensions, overrides)
    cost_stmt = _build_side_select(CostEntry, specs, filters, time_range, 'cost')
    revenue_stmt = _build_side_select(RevenueEntry, specs, filters, time_range, 'revenue')

    combined = union_all(cost_stmt, revenue_stmt).subquery()

    dimension_columns = [combined.c[entry['key']] for entry in specs]
    total_cost_expr = func.sum(case((combined.c.kind == 'cost', combined.c.amount), else_=0)).label('total_cost')
    total_revenue_expr = func.sum(case((combined.c.kind == 'revenue', combined.c.amount), else_=0)).label('total_revenue')
    cost_count_expr = func.sum(case((combined.c.kind == 'cost', combined.c.entry_count), else_=0)).label('cost_entries')
    revenue_count_expr = func.sum(case((combined.c.kind == 'revenue', combined.c.entry_count), else_=0)).label('revenue_entries')

    stmt = select(*dimension_columns, total_cost_expr, total_revenue_expr, cost_count_expr, revenue_count_expr)
    if dimension_columns:
        stmt = stmt.group_by(*dimension_columns)
    if order_by_dimensions and dimension_columns:
        stmt = stmt.order_by(*dimension_columns)
    else:
        stmt = stmt.order_by(total_revenue_expr.desc(), total_cost_expr.desc())
    if limit is not None:
        stmt = stmt.limit(limit)

    return db.session.execute(stmt).mappings().all()


def _decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _decimal_to_float(value: Decimal) -> float:
    return float(value.quantize(Decimal('0.01')))


def _format_rows(dimensions: List[str], metrics: List[str], rows: List[Dict[str, Any]]):
    formatted = []
    for row in rows:
        dimension_values: Dict[str, Any] = {}
        for key in dimensions:
            value = row.get(key)
            if isinstance(value, datetime):
                dimension_values[key] = value.isoformat()
            elif isinstance(value, date):
                dimension_values[key] = value.isoformat()
            else:
                dimension_values[key] = value
        total_cost = _decimal(row.get('total_cost'))
        total_revenue = _decimal(row.get('total_revenue'))
        cost_entries = int(row.get('cost_entries') or 0)
        revenue_entries = int(row.get('revenue_entries') or 0)
        metrics_payload: Dict[str, Any] = {}
        for metric in metrics:
            if metric == 'total_cost':
                metrics_payload[metric] = _decimal_to_float(total_cost)
            elif metric == 'total_revenue':
                metrics_payload[metric] = _decimal_to_float(total_revenue)
            elif metric == 'net_income':
                metrics_payload[metric] = _decimal_to_float(total_revenue - total_cost)
            elif metric == 'cost_entries':
                metrics_payload[metric] = cost_entries
            elif metric == 'revenue_entries':
                metrics_payload[metric] = revenue_entries
            elif metric == 'avg_cost':
                metrics_payload[metric] = _decimal_to_float(total_cost / cost_entries) if cost_entries else None
            elif metric == 'avg_revenue':
                metrics_payload[metric] = _decimal_to_float(total_revenue / revenue_entries) if revenue_entries else None
            elif metric == 'cost_revenue_ratio':
                metrics_payload[metric] = _decimal_to_float(total_cost / total_revenue) if total_revenue != 0 else None
        formatted.append({'dimensions': dimension_values, 'metrics': metrics_payload})
    return formatted


def _build_cache_key(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _resolve_bucket_override(granularity: str):
    bind = db.session.get_bind()
    dialect = bind.dialect.name if bind else 'sqlite'
    if granularity == 'month':
        if dialect == 'postgresql':
            expr = func.date_trunc('month', CostEntry.recorded_at)
            expr_rev = func.date_trunc('month', RevenueEntry.recorded_at)
        else:
            expr = func.strftime('%Y-%m-01', CostEntry.recorded_at)
            expr_rev = func.strftime('%Y-%m-01', RevenueEntry.recorded_at)
        return {'recorded_date': (expr, expr_rev)}
    return None


@bp.route('/cohort-analysis', methods=['POST'])
@login_required
def cohort_analysis():
    data = request.get_json(silent=True) or {}
    try:
        payload = CohortAnalysisQueryModel(**data)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    if not check_bi_rate_limit(current_user.id, 'cohort'):
        return jsonify(error='查詢過於頻繁，請稍後再試'), 429

    cache_key = _build_cache_key(payload.model_dump(mode='json'))
    cached = get_bi_cache(current_user.id, 'cohort', cache_key)
    if cached:
        return jsonify(cached)

    rows = _execute_union_query(payload.dimensions, payload.filters, payload.time_range, limit=payload.limit)
    formatted = _format_rows(payload.dimensions, payload.metrics, rows)
    response = {
        'dimensions': payload.dimensions,
        'metrics': payload.metrics,
        'rows': formatted,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }
    set_bi_cache(current_user.id, 'cohort', cache_key, response)
    return jsonify(response)


@bp.route('/cost-benefit', methods=['POST'])
@login_required
def cost_benefit():
    data = request.get_json(silent=True) or {}
    try:
        payload = CostBenefitQueryModel(**data)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    if not check_bi_rate_limit(current_user.id, 'cost-benefit'):
        return jsonify(error='查詢過於頻繁，請稍後再試'), 429

    cache_key = _build_cache_key(payload.model_dump(mode='json'))
    cached = get_bi_cache(current_user.id, 'cost-benefit', cache_key)
    if cached:
        return jsonify(cached)

    overall_rows = _execute_union_query([], payload.filters, payload.time_range, limit=1)
    overall_metrics = _format_rows([], payload.metrics, overall_rows)
    overall = overall_metrics[0]['metrics'] if overall_metrics else {metric: None for metric in payload.metrics}

    overrides = _resolve_bucket_override(payload.granularity)
    trend_rows = _execute_union_query(
        ['recorded_date'],
        payload.filters,
        payload.time_range,
        overrides=overrides,
        order_by_dimensions=True,
    )
    trend_formatted = _format_rows(['recorded_date'], payload.metrics, trend_rows)
    trend = [
        {
            'period': row['dimensions'].get('recorded_date'),
            'metrics': row['metrics'],
        }
        for row in trend_formatted
    ]

    response = {
        'metrics': payload.metrics,
        'granularity': payload.granularity,
        'kpis': overall,
        'trend': trend,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }
    set_bi_cache(current_user.id, 'cost-benefit', cache_key, response)
    return jsonify(response)


@bp.route('/ai-report', methods=['POST'])
@login_required
def generate_ai_report():
    data = request.get_json(silent=True) or {}
    try:
        payload = BiAiReportRequestModel(**data)
    except ValidationError as exc:
        return jsonify(error='資料驗證失敗', details=exc.errors()), 400

    header_api_key = request.headers.get('X-Api-Key')
    if header_api_key and header_api_key != payload.api_key:
        return jsonify(error='X-Api-Key 與請求主體不一致'), 401

    api_key = header_api_key or payload.api_key
    if not api_key:
        return jsonify(error='缺少 API 金鑰'), 401

    metrics_text = ', '.join(payload.metrics)
    filters_text = json.dumps(payload.filters or {}, ensure_ascii=False, indent=2)
    time_range_text = ''
    if payload.time_range:
        time_range_text = f"從 {payload.time_range.start.isoformat() if payload.time_range.start else '未指定'} 到 {payload.time_range.end.isoformat() if payload.time_range.end else '未指定'}"
    aggregates_text = json.dumps(payload.aggregates, ensure_ascii=False, indent=2)
    highlights_text = '\n'.join(f"- {item}" for item in (payload.highlights or [])) or '（無額外備註）'

    prompt = (
        "你是一位熟悉乳羊與肉羊營運的資料分析師，請依據以下資訊撰寫一份 200-300 字的營運洞察報告，"
        "需包含關鍵 KPI 解讀、可能的操作建議與後續追蹤指標。\n\n"
        f"分析指標: {metrics_text}\n"
        f"篩選條件: {filters_text}\n"
        f"時間範圍: {time_range_text or '未指定'}\n"
        f"整體指標摘要:\n{aggregates_text}\n\n"
        f"人工重點:\n{highlights_text}\n\n"
        "請先用條列整理 2-3 項營運洞察，再補充一段整體分析摘要，語氣專業且精準。"
    )

    result = call_gemini_api(prompt, api_key)
    if 'error' in result:
        current_app.logger.error('AI report generation failed: %s', result['error'])
        return jsonify(error='AI 報告生成失敗'), 502

    markdown_text = result.get('text', '').strip()
    report_html = markdown.markdown(markdown_text, extensions=['nl2br', 'fenced_code', 'tables'])
    return jsonify({
        'report_markdown': markdown_text,
        'report_html': report_html,
    })
