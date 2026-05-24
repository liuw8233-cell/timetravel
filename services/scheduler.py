"""定时任务调度器 - 检查并发送到期时光信"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def check_and_send_letters():
    """每分钟检查是否有到期的时光信需要发送"""
    from database import AsyncSessionLocal
    from models import TimeCapsuleLetter
    from services.email_service import send_time_capsule_email

    async with AsyncSessionLocal() as db:
        now = datetime.now()
        result = await db.execute(
            select(TimeCapsuleLetter).where(
                TimeCapsuleLetter.is_sent == False,
                TimeCapsuleLetter.send_at <= now
            )
        )
        letters = result.scalars().all()

        for letter in letters:
            created_str = letter.created_at.strftime("%Y年%m月%d日")
            success = await send_time_capsule_email(
                to_email=letter.recipient_email,
                title=letter.title,
                content=letter.content,
                created_at=created_str
            )
            if success:
                letter.is_sent = True
                letter.sent_at = datetime.now()
                logger.info(f"时光信 #{letter.id} 已成功发送")
            else:
                logger.warning(f"时光信 #{letter.id} 发送失败，将在下次重试")

        await db.commit()


def start_scheduler():
    scheduler.add_job(
        check_and_send_letters,
        trigger=IntervalTrigger(minutes=1),
        id="send_letters",
        replace_existing=True
    )
    scheduler.start()
    logger.info("定时任务调度器已启动")


def stop_scheduler():
    scheduler.shutdown()
