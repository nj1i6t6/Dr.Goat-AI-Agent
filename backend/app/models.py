from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    sheep = db.relationship('Sheep', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    events = db.relationship('SheepEvent', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    chat_history = db.relationship('ChatHistory', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    event_type_options = db.relationship('EventTypeOption', backref='owner', lazy='dynamic', cascade="all, delete-orphan")
    event_description_options = db.relationship('EventDescriptionOption', backref='owner', lazy='dynamic', cascade="all, delete-orphan")


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class EventTypeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    
    descriptions = db.relationship('EventDescriptionOption', backref='event_type', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_default': self.is_default,
            'descriptions': [d.to_dict() for d in self.descriptions]
        }

class EventDescriptionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_type_option_id = db.Column(db.Integer, db.ForeignKey('event_type_option.id'), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'event_type_option_id': self.event_type_option_id,
            'description': self.description,
            'is_default': self.is_default
        }

class Sheep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # --- 核心基础识别资料 (Core Identification) ---
    EarNum = db.Column(db.String(100), nullable=False) # 耳号
    BirthDate = db.Column(db.String(50)) # 出生日期
    Sex = db.Column(db.String(20)) # 性别
    Breed = db.Column(db.String(100)) # 品种
    
    # --- 血统资料 (Pedigree) ---
    Sire = db.Column(db.String(100)) # 父号
    Dam = db.Column(db.String(100)) # 母号
    
    # --- 根据 Excel _Basic 工作表扩充的栏位 ---
    BirWei = db.Column(db.Float) # 出生体重 (Birth Weight)
    SireBre = db.Column(db.String(100)) # 父系品种 (Sire's Breed)
    DamBre = db.Column(db.String(100)) # 母系品种 (Dam's Breed)
    MoveCau = db.Column(db.String(100)) # 异动原因 (Move Cause)
    MoveDate = db.Column(db.String(50)) # 异动日期 (Move Date)
    Class = db.Column(db.String(100)) # 等级/分类
    LittleSize = db.Column(db.Integer) # 产仔数/窝数 (Litter Size)
    Lactation = db.Column(db.Integer) # 泌乳胎次
    ManaClas = db.Column(db.String(100)) # 管理分类 (Management Class)
    FarmNum = db.Column(db.String(100)) # 牧场编号
    RUni = db.Column(db.String(100)) # 唯一记录编号

    # --- 饲养管理与生产性能资料 (Management & Performance) ---
    Body_Weight_kg = db.Column(db.Float) # 体重
    Age_Months = db.Column(db.Integer) # 月龄
    breed_category = db.Column(db.String(50)) # 品种类别 (乳、肉、毛)
    status = db.Column(db.String(100)) # 生理状态
    status_description = db.Column(db.Text) # 其他生理状态描述
    target_average_daily_gain_g = db.Column(db.Float) # 目标日增重
    milk_yield_kg_day = db.Column(db.Float) # 日产奶量
    milk_fat_percentage = db.Column(db.Float) # 乳脂率
    number_of_fetuses = db.Column(db.Integer) # 怀胎数
    expected_fiber_yield_g_day = db.Column(db.Float) # 预计产毛量
    activity_level = db.Column(db.String(100)) # 活动量
    
    # --- 备注与提醒 (Notes & Reminders) ---
    other_remarks = db.Column(db.Text) # 使用者备注
    agent_notes = db.Column(db.Text) # AI代理人备注
    next_vaccination_due_date = db.Column(db.String(50)) # 下次疫苗日期
    next_deworming_due_date = db.Column(db.String(50)) # 下次驱虫日期
    expected_lambing_date = db.Column(db.String(50)) # 预计产仔日期
    
    # --- ESG 相關欄位 ---
    manure_management = db.Column(db.String(100)) # 糞肥管理方式 (例如：堆肥、厭氧發酵)
    primary_forage_type = db.Column(db.String(100)) # 主要草料類型 (例如：在地狼尾草、進口苜蓿草)
    welfare_score = db.Column(db.Integer) # 動物福利評分 (1-5分)

    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'EarNum', name='_user_ear_num_uc'),)
    
    historical_data = db.relationship('SheepHistoricalData', backref='sheep', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<Sheep {self.EarNum} OwnerID:{self.user_id}>'

class SheepEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)

    event_date = db.Column(db.String(50), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # --- ESG - 食品安全相關欄位 ---
    medication = db.Column(db.String(150)) # 用藥名稱
    withdrawal_days = db.Column(db.Integer) # 停藥天數

    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sheep = db.relationship('Sheep', backref=db.backref('events', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<Event {self.event_type} for SheepID:{self.sheep_id}>'
        
class SheepHistoricalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    record_date = db.Column(db.String(50), nullable=False)
    record_type = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f'<HistoricalData {self.record_type}:{self.value} for SheepID:{self.sheep_id}>'

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ear_num_context = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Chat {self.session_id} - {self.role}>'


class HealthAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sheep_id = db.Column(db.Integer, db.ForeignKey('sheep.id', ondelete='CASCADE'), nullable=False)
    ear_num = db.Column(db.String(100), nullable=False)

    alert_type = db.Column(db.String(100), nullable=False, default='體重偏離')
    message = db.Column(db.Text)  # Gemini 產生的精簡摘要
    details = db.Column(db.Text)  # 需要時可存完整 Markdown

    actual_weight = db.Column(db.Float)
    predicted_weight = db.Column(db.Float)
    deviation_pct = db.Column(db.Float)
    record_date = db.Column(db.String(50))
    model_name = db.Column(db.String(100))

    status = db.Column(db.String(50), default='open')  # open/resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sheep_id': self.sheep_id,
            'ear_num': self.ear_num,
            'alert_type': self.alert_type,
            'message': self.message,
            'details': self.details,
            'actual_weight': self.actual_weight,
            'predicted_weight': self.predicted_weight,
            'deviation_pct': self.deviation_pct,
            'record_date': self.record_date,
            'model_name': self.model_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }