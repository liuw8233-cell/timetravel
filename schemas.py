from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ===== 用户 =====
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    nickname: Optional[str] = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ===== 时光信 =====
class LetterCreate(BaseModel):
    title: str
    content: str
    recipient_email: EmailStr
    send_at: datetime
    mood: Optional[str] = "neutral"
    weather: Optional[str] = ""
    images: Optional[List[str]] = []


class LetterOut(BaseModel):
    id: int
    title: str
    content: str
    recipient_email: str
    send_at: datetime
    is_sent: bool
    sent_at: Optional[datetime]
    created_at: datetime
    mood: str
    weather: Optional[str] = ""
    images: List[str] = []

    class Config:
        from_attributes = True


# ===== 漂流瓶 =====
class BottleCreate(BaseModel):
    content: str
    mood: Optional[str] = "sad"
    is_public: Optional[bool] = True
    tags: Optional[str] = ""

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("内容至少5个字")
        if len(v) > 1000:
            raise ValueError("内容不超过1000字")
        return v.strip()


class CommentCreate(BaseModel):
    content: str
    nickname: Optional[str] = "匿名旅人"

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("评论至少2个字")
        if len(v) > 300:
            raise ValueError("评论不超过300字")
        return v.strip()


class CommentOut(BaseModel):
    id: int
    nickname: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class BottleOut(BaseModel):
    id: int
    content: str
    mood: str
    is_public: bool
    view_count: int
    tags: str
    created_at: datetime
    comments: List[CommentOut] = []
    is_mine: bool = False

    class Config:
        from_attributes = True


# ===== AI 聊天 =====
class ChatMessage(BaseModel):
    role: str  # user / assistant
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    mode: str = "chat"  # chat（树洞）| fortune（算卦）


class ChatResponse(BaseModel):
    reply: str
    mode: str


# ===== AI配置 =====
class AIConfigUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    provider: Optional[str] = "openai"
    base_url: Optional[str] = ""
    api_key: Optional[str] = ""
    model_name: Optional[str] = ""
    chat_model: Optional[str] = ""
    fortune_model: Optional[str] = ""


class AIConfigOut(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}
    provider: str
    base_url: str
    api_key_masked: str  # 脱敏展示
    model_name: str
    chat_model: str
    fortune_model: str


# ===== 算命 =====
class FortuneRequest(BaseModel):
    mode: str  # bazi（八字）| star（星座）| tarot（塔罗）
    birth_date: Optional[str] = ""  # 生日，格式 YYYY-MM-DD
    birth_time: Optional[str] = ""  # 出生时辰 HH:MM
    birth_gender: Optional[str] = ""  # 性别
    star_sign: Optional[str] = ""   # 星座
    question: Optional[str] = ""    # 附加问题
