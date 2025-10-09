"""
Pydantic 資料驗證模型
用於 API 請求和響應的資料驗證與序列化
"""

import json
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _quantize_amount(value: Decimal) -> Decimal:
    quantized = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if quantized <= Decimal('0.00'):
        raise ValueError('金額必須大於 0')
    return quantized


def _parse_iso_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError('recorded_at 不能為空字串')
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        try:
            return datetime.fromisoformat(text)
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise ValueError('recorded_at 不是有效的 ISO 8601 時間格式') from exc
    raise ValueError('recorded_at 需要是 ISO8601 字串或 datetime 物件')


def _parse_metadata(value: Any) -> Optional[Dict[str, Any]]:
    if value in (None, ''):
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    raise ValueError('metadata 僅接受 JSON 字串或物件')


# === 認證相關模型 ===
class LoginModel(BaseModel):
    username: str = Field(..., min_length=1, max_length=80, description="用戶名")
    password: str = Field(..., min_length=1, description="密碼")


class RegisterModel(BaseModel):
    username: str = Field(..., min_length=1, max_length=80, description="用戶名")
    password: str = Field(..., min_length=6, description="密碼，至少6個字符")


# === 羊隻相關模型 ===
class SheepCreateModel(BaseModel):
    """新增羊隻的資料模型"""
    EarNum: str = Field(..., min_length=1, max_length=100, description="耳號")
    BirthDate: Optional[str] = Field(None, max_length=50, description="出生日期")
    Sex: Optional[str] = Field(None, max_length=20, description="性別")
    Breed: Optional[str] = Field(None, max_length=100, description="品種")
    Sire: Optional[str] = Field(None, max_length=100, description="父號")
    Dam: Optional[str] = Field(None, max_length=100, description="母號")
    BirWei: Optional[float] = Field(None, ge=0, description="出生體重(kg)")
    Body_Weight_kg: Optional[float] = Field(None, ge=0, description="體重(kg)")
    Age_Months: Optional[int] = Field(None, ge=0, le=300, description="月齡")
    breed_category: Optional[str] = Field(None, max_length=50, description="品種類別")
    status: Optional[str] = Field(None, max_length=100, description="生理狀態")
    FarmNum: Optional[str] = Field(None, max_length=100, description="牧場編號")

    @field_validator('EarNum')
    @classmethod
    def validate_ear_num(cls, v):
        if not v or not v.strip():
            raise ValueError('耳號不能為空')
        return v.strip()


class SheepUpdateModel(BaseModel):
    """更新羊隻的資料模型"""
    BirthDate: Optional[str] = Field(None, max_length=50, description="出生日期")
    Sex: Optional[str] = Field(None, max_length=20, description="性別")
    Breed: Optional[str] = Field(None, max_length=100, description="品種")
    Sire: Optional[str] = Field(None, max_length=100, description="父號")
    Dam: Optional[str] = Field(None, max_length=100, description="母號")
    BirWei: Optional[float] = Field(None, ge=0, description="出生體重(kg)")
    Body_Weight_kg: Optional[float] = Field(None, ge=0, description="體重(kg)")
    Age_Months: Optional[int] = Field(None, ge=0, le=300, description="月齡")
    breed_category: Optional[str] = Field(None, max_length=50, description="品種類別")
    status: Optional[str] = Field(None, max_length=100, description="生理狀態")
    status_description: Optional[str] = Field(None, description="生理狀態描述")
    target_average_daily_gain_g: Optional[float] = Field(None, ge=0, description="目標日增重(g)")
    milk_yield_kg_day: Optional[float] = Field(None, ge=0, description="日產奶量(kg)")
    milk_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="乳脂率(%)")
    number_of_fetuses: Optional[int] = Field(None, ge=0, le=10, description="懷胎數")
    activity_level: Optional[str] = Field(None, max_length=100, description="活動量")
    other_remarks: Optional[str] = Field(None, description="其他備註")
    agent_notes: Optional[str] = Field(None, description="AI代理人備註")
    next_vaccination_due_date: Optional[str] = Field(None, max_length=50, description="下次疫苗日期")
    next_deworming_due_date: Optional[str] = Field(None, max_length=50, description="下次驅蟲日期")
    expected_lambing_date: Optional[str] = Field(None, max_length=50, description="預計產仔日期")
    manure_management: Optional[str] = Field(None, max_length=100, description="糞肥管理方式")
    primary_forage_type: Optional[str] = Field(None, max_length=100, description="主要草料類型")
    welfare_score: Optional[int] = Field(None, ge=1, le=5, description="動物福利評分(1-5)")
    FarmNum: Optional[str] = Field(None, max_length=100, description="牧場編號")


# === 事件相關模型 ===
class SheepEventCreateModel(BaseModel):
    """新增羊隻事件的資料模型"""
    event_date: str = Field(..., description="事件日期")
    event_type: str = Field(..., min_length=1, max_length=100, description="事件類型")
    description: Optional[str] = Field(None, description="事件描述")
    notes: Optional[str] = Field(None, description="備註")
    medication: Optional[str] = Field(None, max_length=150, description="用藥名稱")
    withdrawal_days: Optional[int] = Field(None, ge=0, description="停藥天數")


# === 歷史數據相關模型 ===
class HistoricalDataCreateModel(BaseModel):
    """新增歷史數據的資料模型"""
    record_date: str = Field(..., description="記錄日期")
    record_type: str = Field(..., min_length=1, max_length=100, description="記錄類型")
    value: float = Field(..., description="數值")
    notes: Optional[str] = Field(None, description="備註")


# === 成本 / 收益資料模型 ===
class CostRevenueBaseModel(BaseModel):
    category: str = Field(..., min_length=1, max_length=120, description="分類")
    subcategory: Optional[str] = Field(None, max_length=120, description="子分類")
    description: Optional[str] = Field(None, description="敘述")
    amount: Decimal = Field(..., description="金額")
    currency: str = Field('TWD', min_length=1, max_length=16, description="幣別")
    recorded_at: datetime = Field(default_factory=datetime.utcnow, description="紀錄時間")
    breed: Optional[str] = Field(None, max_length=100, description="品種")
    age_group: Optional[str] = Field(None, max_length=50, description="月齡群組")
    parity: Optional[int] = Field(None, ge=0, le=20, description="胎次")
    herd_tag: Optional[str] = Field(None, max_length=100, description="群組標籤")
    notes: Optional[str] = Field(None, description="備註")
    metadata: Optional[Dict[str, Any]] = Field(None, description="自訂欄位")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        return _quantize_amount(value)

    @field_validator('recorded_at', mode='before')
    @classmethod
    def validate_recorded_at(cls, value: Any) -> datetime:
        return _parse_iso_datetime(value)

    @field_validator('metadata', mode='before')
    @classmethod
    def validate_metadata(cls, value: Any) -> Optional[Dict[str, Any]]:
        return _parse_metadata(value)


class CostEntryCreateModel(CostRevenueBaseModel):
    pass


class CostEntryUpdateModel(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=120)
    subcategory: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None)
    amount: Optional[Decimal] = Field(None)
    currency: Optional[str] = Field(None, min_length=1, max_length=16)
    recorded_at: Optional[datetime] = Field(None)
    breed: Optional[str] = Field(None, max_length=100)
    age_group: Optional[str] = Field(None, max_length=50)
    parity: Optional[int] = Field(None, ge=0, le=20)
    herd_tag: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return value
        return _quantize_amount(value)

    @field_validator('recorded_at', mode='before')
    @classmethod
    def validate_recorded_at(cls, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        return _parse_iso_datetime(value)

    @field_validator('metadata', mode='before')
    @classmethod
    def validate_metadata(cls, value: Any) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        return _parse_metadata(value)


class CostEntryBulkImportModel(BaseModel):
    entries: List[CostEntryCreateModel] = Field(..., min_length=1, max_length=500, description="成本資料列")


class RevenueEntryCreateModel(CostRevenueBaseModel):
    pass


class RevenueEntryUpdateModel(CostEntryUpdateModel):
    pass


class RevenueEntryBulkImportModel(BaseModel):
    entries: List[RevenueEntryCreateModel] = Field(..., min_length=1, max_length=500, description="收益資料列")


class TimeRangeModel(BaseModel):
    start: Optional[datetime] = Field(None, description="起始時間")
    end: Optional[datetime] = Field(None, description="結束時間")

    @field_validator('start', 'end', mode='before')
    @classmethod
    def validate_bound(cls, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        return _parse_iso_datetime(value)

    @model_validator(mode='after')
    def validate_range(self) -> 'TimeRangeModel':
        if self.start and self.end and self.start > self.end:
            raise ValueError('時間區間的 start 不能晚於 end')
        return self


ALLOWED_BI_DIMENSIONS = {'category', 'subcategory', 'breed', 'age_group', 'parity', 'herd_tag', 'recorded_date'}
ALLOWED_BI_METRICS = {
    'total_cost',
    'total_revenue',
    'net_income',
    'cost_entries',
    'revenue_entries',
    'avg_cost',
    'avg_revenue',
    'cost_revenue_ratio',
}


class CohortAnalysisQueryModel(BaseModel):
    dimensions: List[str] = Field(..., min_length=1, max_length=4, description="分群欄位")
    metrics: List[str] = Field(..., min_length=1, max_length=7, description="指標列表")
    filters: Optional[Dict[str, List[Any]]] = Field(default=None, description="複合篩選條件")
    time_range: Optional[TimeRangeModel] = Field(default=None, description="時間範圍")
    limit: int = Field(50, ge=1, le=200, description="最大返回筆數")

    @model_validator(mode='after')
    def validate_payload(self) -> 'CohortAnalysisQueryModel':
        for dim in self.dimensions:
            if dim not in ALLOWED_BI_DIMENSIONS:
                raise ValueError(f'不支援的分群欄位: {dim}')
        for metric in self.metrics:
            if metric not in ALLOWED_BI_METRICS:
                raise ValueError(f'不支援的指標: {metric}')
        if self.filters:
            for key, values in self.filters.items():
                if key not in ALLOWED_BI_DIMENSIONS:
                    raise ValueError(f'不支援的篩選欄位: {key}')
                if not isinstance(values, list) or not values:
                    raise ValueError(f'篩選欄位 {key} 必須是非空列表')
        return self


class CostBenefitQueryModel(BaseModel):
    metrics: List[str] = Field(..., min_length=1, max_length=7, description="指標列表")
    filters: Optional[Dict[str, List[Any]]] = Field(default=None, description="篩選條件")
    time_range: Optional[TimeRangeModel] = Field(default=None, description="時間範圍")
    granularity: Literal['day', 'month'] = Field('month', description="時間粒度")

    @model_validator(mode='after')
    def validate_payload(self) -> 'CostBenefitQueryModel':
        for metric in self.metrics:
            if metric not in ALLOWED_BI_METRICS:
                raise ValueError(f'不支援的指標: {metric}')
        if self.filters:
            for key, values in self.filters.items():
                if key not in ALLOWED_BI_DIMENSIONS:
                    raise ValueError(f'不支援的篩選欄位: {key}')
                if not isinstance(values, list) or not values:
                    raise ValueError(f'篩選欄位 {key} 必須是非空列表')
        return self


class BiAiReportRequestModel(BaseModel):
    api_key: str = Field(..., min_length=16, description="AI 代理金鑰")
    metrics: List[str] = Field(..., min_length=1, max_length=7, description="指標列表")
    filters: Optional[Dict[str, List[Any]]] = Field(default=None, description="篩選條件")
    time_range: Optional[TimeRangeModel] = Field(default=None, description="查詢時間範圍")
    highlights: Optional[List[str]] = Field(default=None, description="人工整理亮點")
    aggregates: Dict[str, Any] = Field(..., description="前端整合的 KPI 摘要")

    @model_validator(mode='after')
    def validate_metrics(self) -> 'BiAiReportRequestModel':
        for metric in self.metrics:
            if metric not in ALLOWED_BI_METRICS:
                raise ValueError(f'不支援的指標: {metric}')
        if self.filters:
            for key, values in self.filters.items():
                if key not in ALLOWED_BI_DIMENSIONS:
                    raise ValueError(f'不支援的篩選欄位: {key}')
                if not isinstance(values, list) or not values:
                    raise ValueError(f'篩選欄位 {key} 必須是非空列表')
        return self


# === AI 代理人相關模型 ===
class AgentRecommendationModel(BaseModel):
    """AI 飼養建議請求模型"""
    api_key: str = Field(..., min_length=1, description="API 金鑰")
    EarNum: Optional[str] = Field(None, description="耳號")
    Breed: Optional[str] = Field(None, description="品種")
    Body_Weight_kg: Optional[float] = Field(None, ge=0, description="體重(kg)")
    Age_Months: Optional[int] = Field(None, ge=0, description="月齡")
    Sex: Optional[str] = Field(None, description="性別")
    status: Optional[str] = Field(None, description="生理狀態")
    target_average_daily_gain_g: Optional[float] = Field(None, ge=0, description="目標日增重(g)")
    milk_yield_kg_day: Optional[float] = Field(None, ge=0, description="日產奶量(kg)")
    milk_fat_percentage: Optional[float] = Field(None, ge=0, le=100, description="乳脂率(%)")
    number_of_fetuses: Optional[int] = Field(None, ge=0, description="懷胎數")
    other_remarks: Optional[str] = Field(None, description="其他備註")


class AgentChatModel(BaseModel):
    """AI 聊天請求模型"""
    api_key: str = Field(..., min_length=1, description="API 金鑰")
    message: str = Field(..., min_length=1, description="用戶訊息")
    session_id: str = Field(..., min_length=1, description="會話ID")
    ear_num_context: Optional[str] = Field(None, description="羊隻耳號上下文")


# === 數據管理相關模型 ===
class ImportMappingModel(BaseModel):
    """資料匯入映射配置模型"""
    file_type: str = Field(..., description="檔案類型")
    sheet_name: Optional[str] = Field(None, description="工作表名稱")
    mapping_config: Dict[str, Any] = Field(..., description="欄位映射配置")


# === 錯誤響應模型 ===
class ErrorResponse(BaseModel):
    """錯誤響應模型"""
    error: str = Field(..., description="錯誤訊息")
    details: Optional[List[Dict[str, Any]]] = Field(None, description="詳細錯誤資訊")
    field_errors: Optional[Dict[str, str]] = Field(None, description="欄位錯誤")


class SuccessResponse(BaseModel):
    """成功響應模型"""
    success: bool = Field(True, description="操作是否成功")
    message: Optional[str] = Field(None, description="成功訊息")
    data: Optional[Any] = Field(None, description="返回資料")


# === 產銷履歷相關模型 ===
class BatchSheepLinkModel(BaseModel):
    sheep_id: int = Field(..., description="羊隻 ID")
    contribution_type: Optional[str] = Field(None, max_length=100, description="貢獻類型")
    quantity: Optional[float] = Field(None, ge=0, description="數量")
    quantity_unit: Optional[str] = Field(None, max_length=50, description="數量單位")
    role: Optional[str] = Field(None, max_length=100, description="角色")
    notes: Optional[str] = Field(None, description="備註")


class ProcessingStepInputModel(BaseModel):
    title: str = Field(..., min_length=1, max_length=150, description="步驟標題")
    description: Optional[str] = Field(None, description="步驟描述")
    sequence_order: Optional[int] = Field(None, ge=1, description="排序")
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    evidence_url: Optional[str] = Field(None, max_length=255, description="佐證連結")


class ProductBatchBaseModel(BaseModel):
    batch_number: str = Field(..., min_length=1, max_length=100, description="批次號")
    product_name: str = Field(..., min_length=1, max_length=150, description="產品名稱")
    product_type: Optional[str] = Field(None, max_length=100, description="產品類型")
    description: Optional[str] = Field(None, description="產品描述")
    esg_highlights: Optional[str] = Field(None, description="ESG 亮點")
    production_date: Optional[date] = Field(None, description="生產日期")
    expiration_date: Optional[date] = Field(None, description="到期日")
    origin_story: Optional[str] = Field(None, description="品牌故事")
    is_public: bool = Field(False, description="是否公開")


class ProductBatchCreateModel(ProductBatchBaseModel):
    sheep_links: Optional[List[BatchSheepLinkModel]] = Field(default_factory=list, description="羊隻關聯列表")
    processing_steps: Optional[List[ProcessingStepInputModel]] = Field(default_factory=list, description="加工步驟列表")


class ProductBatchUpdateModel(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=150)
    product_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    esg_highlights: Optional[str] = Field(None)
    production_date: Optional[date] = Field(None)
    expiration_date: Optional[date] = Field(None)
    origin_story: Optional[str] = Field(None)
    is_public: Optional[bool] = Field(None)
    sheep_links: Optional[List[BatchSheepLinkModel]] = Field(default=None, description="重新設定羊隻關聯")


class ProcessingStepCreateModel(ProcessingStepInputModel):
    pass


class ProcessingStepUpdateModel(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = Field(None)
    sequence_order: Optional[int] = Field(None, ge=1)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    evidence_url: Optional[str] = Field(None, max_length=255)


# === IoT 模組模型 ===
class IotDeviceBaseModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="裝置名稱")
    device_type: str = Field(..., min_length=1, max_length=120, description="裝置類型")
    category: Literal['sensor', 'actuator']
    location: Optional[str] = Field(None, max_length=120, description="安裝地點")
    control_url: Optional[str] = Field(None, max_length=255, description="控制指令接收網址")
    status: Optional[str] = Field(None, max_length=32, description="裝置狀態")


class IotDeviceCreateModel(IotDeviceBaseModel):
    api_key: Optional[str] = Field(None, min_length=12, max_length=128, description="自定義 API 金鑰")


class IotDeviceUpdateModel(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    device_type: Optional[str] = Field(None, min_length=1, max_length=120)
    category: Optional[Literal['sensor', 'actuator']] = None
    location: Optional[str] = Field(None, max_length=120)
    control_url: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=32)


def _validate_trigger_condition_payload(value: Optional[Dict[str, Any]], *, allow_none: bool = False) -> Optional[Dict[str, Any]]:
    if value is None:
        if allow_none:
            return None
        raise ValueError('觸發條件不得為空')

    required_keys = {'variable', 'operator', 'value'}
    missing = required_keys - set(value.keys())
    if missing:
        missing_keys = ', '.join(sorted(missing))
        raise ValueError(f'觸發條件缺少必要欄位: {missing_keys}')
    return value


def _validate_action_command_payload(value: Optional[Dict[str, Any]], *, allow_none: bool = False) -> Optional[Dict[str, Any]]:
    if value is None:
        if allow_none:
            return None
        raise ValueError('action_command 不得為空')

    if 'command' not in value:
        raise ValueError('action_command 必須包含 command 欄位')
    return value


class AutomationRuleBaseModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    trigger_source_device_id: int = Field(..., ge=1)
    trigger_condition: Dict[str, Any] = Field(...)
    action_target_device_id: int = Field(..., ge=1)
    action_command: Dict[str, Any] = Field(...)
    is_enabled: Optional[bool] = True

    @field_validator('trigger_condition')
    @classmethod
    def validate_trigger_condition(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        return _validate_trigger_condition_payload(value)

    @field_validator('action_command')
    @classmethod
    def validate_action_command(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        return _validate_action_command_payload(value)


class AutomationRuleCreateModel(AutomationRuleBaseModel):
    pass


class AutomationRuleUpdateModel(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    trigger_source_device_id: Optional[int] = Field(None, ge=1)
    trigger_condition: Optional[Dict[str, Any]] = None
    action_target_device_id: Optional[int] = Field(None, ge=1)
    action_command: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

    @field_validator('trigger_condition')
    @classmethod
    def validate_trigger_condition(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return _validate_trigger_condition_payload(value, allow_none=True)

    @field_validator('action_command')
    @classmethod
    def validate_action_command(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return _validate_action_command_payload(value, allow_none=True)


class SensorIngestModel(BaseModel):
    data: Dict[str, Any] = Field(..., description="感測器回傳的數據")
    evidence_url: Optional[str] = Field(None, max_length=255)


# === 設定相關模型 ===
class EventTypeOptionModel(BaseModel):
    """事件類型選項模型"""
    name: str = Field(..., min_length=1, max_length=100, description="事件類型名稱")
    is_default: bool = Field(False, description="是否為預設選項")


class EventDescriptionOptionModel(BaseModel):
    """事件描述選項模型"""
    event_type_option_id: int = Field(..., description="事件類型選項ID")
    description: str = Field(..., min_length=1, max_length=200, description="事件描述")
    is_default: bool = Field(False, description="是否為預設選項")


def _metadata_json_encoder(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f'Unsupported metadata type: {type(value)!r}')


class VerifiableLogActorModel(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None


class VerifiableLogEventModel(BaseModel):
    action: Literal['create', 'update', 'delete', 'link', 'verify', 'sync'] = Field(..., description='事件動作')
    summary: str = Field(..., min_length=1, max_length=255, description='事件摘要')
    actor: Optional[VerifiableLogActorModel] = Field(None, description='操作人員資訊')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='補充資訊')

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        json.dumps(value, default=_metadata_json_encoder)
        return value


# === 工具函數 ===
def create_error_response(error_message: str, validation_errors: List[Dict] = None) -> Dict:
    """創建標準化錯誤響應"""
    error_response = {"error": error_message}
    
    if validation_errors:
        # 轉換 Pydantic 驗證錯誤為用戶友好的訊息
        field_errors = {}
        for error in validation_errors:
            field = error.get('loc', ['unknown'])[-1]  # 獲取欄位名
            msg = error.get('msg', '驗證失敗')
            
            # 轉換為中文錯誤訊息
            if 'Field required' in msg:
                field_errors[field] = f'{get_field_display_name(field)}為必填欄位'
            elif 'ensure this value is greater than or equal to' in msg:
                field_errors[field] = f'{get_field_display_name(field)}必須大於等於指定值'
            elif 'string too short' in msg:
                field_errors[field] = f'{get_field_display_name(field)}長度不足'
            elif 'string too long' in msg:
                field_errors[field] = f'{get_field_display_name(field)}長度超出限制'
            else:
                field_errors[field] = f'{get_field_display_name(field)}: {msg}'
        
        error_response['field_errors'] = field_errors
        error_response['details'] = validation_errors
    
    return error_response


def get_field_display_name(field_name: str) -> str:
    """獲取欄位的中文顯示名稱"""
    field_names = {
        'EarNum': '耳號',
        'BirthDate': '出生日期',
        'Sex': '性別',
        'Breed': '品種',
        'Body_Weight_kg': '體重',
        'Age_Months': '月齡',
        'username': '用戶名',
        'password': '密碼',
        'api_key': 'API金鑰',
        'message': '訊息',
        'session_id': '會話ID',
        'event_date': '事件日期',
        'event_type': '事件類型',
        'record_date': '記錄日期',
        'record_type': '記錄類型',
        'value': '數值',
    }
    return field_names.get(field_name, field_name)
