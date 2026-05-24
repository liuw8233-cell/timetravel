"""时光信路由"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import uuid
import json
from datetime import datetime, timezone

from database import get_db
from models import TimeCapsuleLetter, User
from schemas import LetterCreate, LetterOut
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/letters", tags=["时光信"])

# 图片上传目录
UPLOAD_DIR = os.path.join("static", "uploads", "letters")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/email-status")
async def email_status():
    """检查邮件服务是否已配置"""
    configured = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
    return {"configured": configured, "smtp_user": settings.SMTP_USER if configured else ""}


def _letter_to_out(letter: TimeCapsuleLetter) -> dict:
    """ORM 对象 -> Pydantic 可识别的字典（解析 images JSON）"""
    try:
        images = json.loads(letter.images) if letter.images else []
    except Exception:
        images = []
    return {
        "id": letter.id,
        "title": letter.title,
        "content": letter.content,
        "recipient_email": letter.recipient_email,
        "send_at": letter.send_at,
        "is_sent": letter.is_sent,
        "sent_at": letter.sent_at,
        "created_at": letter.created_at,
        "mood": letter.mood,
        "weather": letter.weather or "",
        "images": images,
    }


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传时光信附图，返回可用的相对 URL"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp")

    # 读取并校验大小
    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")

    filename = f"{current_user.id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)

    # 注意：StaticFiles 挂在根路径，所以可直接访问 /uploads/letters/...
    url = f"/uploads/letters/{filename}"
    return {"url": url}


@router.post("", response_model=LetterOut)
async def create_letter(
    data: LetterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 统一用带时区的 UTC 时间比较，避免本地/UTC 混用
    now = datetime.now(timezone.utc)
    send_time = data.send_at
    if send_time.tzinfo is None:
        # 客户端传来 naive datetime，默认按 UTC 解读
        send_time = send_time.replace(tzinfo=timezone.utc)
    if send_time <= now:
        raise HTTPException(status_code=400, detail="发送时间必须在当前时间之后")

    # 图片字段为 JSON 字符串
    images_json = json.dumps(data.images or [], ensure_ascii=False)

    letter = TimeCapsuleLetter(
        user_id=current_user.id,
        title=data.title,
        content=data.content,
        recipient_email=data.recipient_email,
        send_at=send_time,
        mood=data.mood,
        weather=data.weather or "",
        images=images_json,
    )
    db.add(letter)
    await db.commit()
    await db.refresh(letter)
    return _letter_to_out(letter)


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
    return [_letter_to_out(l) for l in result.scalars().all()]


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
