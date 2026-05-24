from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def utcnow():
    """统一的 UTC 时间获取函数（替代已弃用的 datetime.utcnow）"""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    nickname = Column(String(50), default="")
    avatar = Column(String(200), default="")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    is_active = Column(Boolean, default=True)

    letters = relationship("TimeCapsuleLetter", back_populates="owner")
    bottles = relationship("DriftBottle", back_populates="owner")
    ai_config = relationship("UserAIConfig", back_populates="user", uselist=False)


class TimeCapsuleLetter(Base):
    """时光信 - 给未来自己写的信"""
    __tablename__ = "time_capsule_letters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    recipient_email = Column(String(100), nullable=False)  # 收件邮箱（可以是自己或他人）
    send_at = Column(DateTime(timezone=True), nullable=False)  # 计划发送时间
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    mood = Column(String(20), default="neutral")  # 写信时的心情
    images = Column(Text, default="")  # 图片URL列表（JSON字符串）
    weather = Column(String(20), default="")  # 写信时的天气
    failed_count = Column(Integer, default=0)  # 失败重试次数

    owner = relationship("User", back_populates="letters")

    # 调度器频繁按 (is_sent, send_at) 查询，加复合索引
    __table_args__ = (
        Index("ix_letters_pending", "is_sent", "send_at"),
        Index("ix_letters_user_created", "user_id", "created_at"),
    )


class DriftBottle(Base):
    """漂流瓶 - 埋藏心事"""
    __tablename__ = "drift_bottles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String(20), default="sad")
    is_public = Column(Boolean, default=True)   # 是否允许他人看见
    is_reviewed = Column(Boolean, default=False)  # 是否通过内容审核
    is_hidden = Column(Boolean, default=False)    # 管理员隐藏
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    # 标签（逗号分隔）
    tags = Column(String(200), default="")

    owner = relationship("User", back_populates="bottles")
    comments = relationship("BottleComment", back_populates="bottle", cascade="all, delete-orphan")


class BottleComment(Base):
    """漂流瓶评论 - 排忧解难"""
    __tablename__ = "bottle_comments"

    id = Column(Integer, primary_key=True, index=True)
    bottle_id = Column(Integer, ForeignKey("drift_bottles.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可匿名
    nickname = Column(String(50), default="匿名旅人")
    content = Column(Text, nullable=False)
    is_reviewed = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    bottle = relationship("DriftBottle", back_populates="comments")


class UserAIConfig(Base):
    """用户自定义AI配置"""
    __tablename__ = "user_ai_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    provider = Column(String(50), default="openai")       # openai / qwen / zhipu / custom
    base_url = Column(String(300), default="")
    api_key = Column(String(500), default="")             # 加密存储
    model_name = Column(String(100), default="")
    # 各功能独立模型（可选，不填则用主模型）
    chat_model = Column(String(100), default="")          # 树洞聊天
    fortune_model = Column(String(100), default="")       # 算命算卦
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="ai_config")

    class Config:
        protected_namespaces = ()
