"""定时任务调度器 - 检查并发送到期时光信"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

MAX_RETRY = 5  # 单封信最多重试次数


async def _send_one(letter, db):
    """发送单封信件，返回 (letter, success)"""
    from services.email_service import send_time_capsule_email
    created_str = letter.created_at.strftime("%Y年%m月%d日")
    success = await send_time_capsule_email(
        to_email=letter.recipient_email,
        title=letter.title,
        content=letter.content,
        created_at=created_str,
        images=letter.images,
        mood=letter.mood,
        weather=letter.weather,
    )
    return letter, success


async def check_and_send_letters():
    """每分钟检查是否有到期的时光信需要发送"""
    from database import AsyncSessionLocal
    from models import TimeCapsuleLetter

    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(TimeCapsuleLetter).where(
                TimeCapsuleLetter.is_sent == False,
                TimeCapsuleLetter.send_at <= now,
                TimeCapsuleLetter.failed_count < MAX_RETRY,
            )
        )
        letters = result.scalars().all()
        if not letters:
            return

        # 并发发送，避免一封慢信卡住后面所有
        results = await asyncio.gather(
            *[_send_one(letter, db) for letter in letters],
            return_exceptions=True,
        )

        for item in results:
            if isinstance(item, Exception):
                logger.error(f"邮件发送异常: {item}")
                continue
            letter, success = item
            if success:
                letter.is_sent = True
                letter.sent_at = datetime.now(timezone.utc)
                logger.info(f"时光信 #{letter.id} 已成功发送")
            else:
                letter.failed_count = (letter.failed_count or 0) + 1
                logger.warning(
                    f"时光信 #{letter.id} 发送失败（{letter.failed_count}/{MAX_RETRY}）"
                )

        await db.commit()


def start_scheduler():
    scheduler.add_job(
        check_and_send_letters,
        trigger=IntervalTrigger(minutes=1),
        id="send_letters",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("定时任务调度器已启动")


def stop_scheduler():
    scheduler.shutdown()
