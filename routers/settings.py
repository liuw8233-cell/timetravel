"""AI配置路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, UserAIConfig
from schemas import AIConfigUpdate, AIConfigOut
from auth import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/api/settings", tags=["配置"])


def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


@router.get("/ai", response_model=AIConfigOut)
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return AIConfigOut(
            provider="openai",
            base_url="",
            api_key_masked="",
            model_name="",
            chat_model="",
            fortune_model="",
        )
    return AIConfigOut(
        provider=config.provider,
        base_url=config.base_url,
        api_key_masked=mask_key(config.api_key),
        model_name=config.model_name,
        chat_model=config.chat_model,
        fortune_model=config.fortune_model,
    )


@router.put("/ai")
async def update_ai_config(
    data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = UserAIConfig(user_id=current_user.id)
        db.add(config)

    config.provider = data.provider or config.provider
    config.base_url = data.base_url or config.base_url
    # 如果传入的api_key不是脱敏格式才更新
    if data.api_key and "****" not in data.api_key:
        config.api_key = data.api_key
    config.model_name = data.model_name or config.model_name
    config.chat_model = data.chat_model or config.chat_model
    config.fortune_model = data.fortune_model or config.fortune_model
    config.updated_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": "AI配置已保存"}


@router.delete("/ai")
async def reset_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置为系统默认AI配置"""
    result = await db.execute(
        select(UserAIConfig).where(UserAIConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    if config:
        await db.delete(config)
        await db.commit()
    return {"message": "已重置为默认配置"}
