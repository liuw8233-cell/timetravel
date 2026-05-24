"""时光信路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from database import get_db
from models import TimeCapsuleLetter, User
from schemas import LetterCreate, LetterOut
from auth import get_current_user
from config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/api/letters", tags=["时光信"])


@router.get("/email-status")
async def email_status():
    """检查邮件服务是否已配置"""
    configured = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
    return {"configured": configured, "smtp_user": settings.SMTP_USER if configured else ""}


@router.post("", response_model=LetterOut)
async def create_letter(
    data: LetterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 发送时间必须在未来
    now = datetime.now()
    send_time = data.send_at.replace(tzinfo=None) if data.send_at.tzinfo else data.send_at
    if send_time <= now:
        raise HTTPException(status_code=400, detail="发送时间必须在当前时间之后")

    letter = TimeCapsuleLetter(
        user_id=current_user.id,
        title=data.title,
        content=data.content,
        recipient_email=data.recipient_email,
        send_at=send_time,
        mood=data.mood,
    )
    db.add(letter)
    await db.commit()
    await db.refresh(letter)
    return letter


@router.get("", response_model=List[LetterOut])
async def list_my_letters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(TimeCapsuleLetter)
        .where(TimeCapsuleLetter.user_id == current_user.id)
        .order_by(TimeCapsuleLetter.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{letter_id}")
async def delete_letter(
    letter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(TimeCapsuleLetter).where(
            TimeCapsuleLetter.id == letter_id,
            TimeCapsuleLetter.user_id == current_user.id
        )
    )
    letter = result.scalar_one_or_none()
    if not letter:
        raise HTTPException(status_code=404, detail="信件不存在")
    if letter.is_sent:
        raise HTTPException(status_code=400, detail="已发送的信件无法删除")
    await db.delete(letter)
    await db.commit()
    return {"message": "删除成功"}
