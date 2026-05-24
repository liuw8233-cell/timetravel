"""AI路由 - 树洞聊天 + 算命算卦"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from database import get_db
from models import User, UserAIConfig
from schemas import ChatRequest, ChatResponse, FortuneRequest
from auth import get_current_user, get_optional_user
from services.ai_service import ai_chat, build_fortune_messages
import json

router = APIRouter(prefix="/api/ai", tags=["AI服务"])


async def get_user_ai_config(user: Optional[User], db: AsyncSession) -> Optional[dict]:
    """获取用户的AI配置"""
    if not user:
        return None
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return None
    return {
        "provider": config.provider,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "model_name": config.model_name,
        "chat_model": config.chat_model,
        "fortune_model": config.fortune_model,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """AI树洞聊天"""
    if len(req.messages) > 50:
        raise HTTPException(status_code=400, detail="对话轮数过多，请开启新对话")

    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    user_config = await get_user_ai_config(current_user, db)

    reply = await ai_chat(messages, mode=req.mode, user_config=user_config)
    return ChatResponse(reply=reply, mode=req.mode)


@router.post("/fortune", response_model=ChatResponse)
async def fortune(
    req: FortuneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """AI算命算卦"""
    mode_map = {"bazi": "fortune_bazi", "star": "fortune_star", "tarot": "fortune_star"}
    ai_mode = mode_map.get(req.mode, "fortune_bazi")

    messages = await build_fortune_messages(req)
    user_config = await get_user_ai_config(current_user, db)

    reply = await ai_chat(messages, mode=ai_mode, user_config=user_config)
    return ChatResponse(reply=reply, mode=req.mode)
