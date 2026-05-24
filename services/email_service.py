"""邮件服务 - 发送时光信"""
import aiosmtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from config import settings
import logging

logger = logging.getLogger(__name__)


MOOD_EMOJI = {
    "happy": "😊 开心", "sad": "😢 难过", "love": "💗 心动",
    "angry": "😠 愤怒", "calm": "😌 平静", "excited": "🤩 兴奋",
    "tired": "😪 疲惫", "thinking": "🤔 思考", "neutral": "😐 平和",
}


EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; background: linear-gradient(135deg,#f5f0ff 0%,#fef3e2 100%); margin: 0; padding: 24px; }}
  .container {{ max-width: 640px; margin: 0 auto; background: #fffdf7; border-radius: 18px; overflow: hidden; box-shadow: 0 8px 36px rgba(120,80,200,0.18); }}
  .header {{ background: linear-gradient(135deg,#667eea 0%,#764ba2 50%,#f59e0b 100%); padding: 44px 30px; text-align: center; position: relative; }}
  .header h1 {{ color: white; margin: 0; font-size: 30px; letter-spacing: 3px; font-weight: 600; }}
  .header p {{ color: rgba(255,255,255,0.85); margin: 10px 0 0; font-size: 14px; letter-spacing: 1px; }}
  .meta {{ display: flex; gap: 18px; padding: 16px 30px; background: #faf7ee; border-bottom: 1px dashed #e8dfc8; font-size: 13px; color: #8a7a55; }}
  .meta span {{ display: inline-flex; align-items: center; gap: 4px; }}
  .body {{ padding: 36px 32px; background-image: linear-gradient(transparent 95%, rgba(180,150,80,0.08) 95%); background-size: 100% 32px; line-height: 32px; }}
  .letter-title {{ font-size: 24px; color: #4a3570; font-weight: bold; margin-bottom: 24px; text-align: center; font-family: 'KaiTi','楷体',serif; }}
  .letter-content {{ font-size: 16px; color: #3a2f4a; white-space: pre-wrap; font-family: 'KaiTi','楷体',serif; }}
  .images {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 10px; margin-top: 24px; }}
  .images img {{ width: 100%; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
  .footer {{ padding: 24px 30px; text-align: center; color: #b29a6a; font-size: 12px; border-top: 1px solid #f0eaff; background: #faf7ee; }}
  .capsule-icon {{ font-size: 52px; margin-bottom: 8px; display: block; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2)); }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="capsule-icon">⏳</span>
    <h1>时空胶囊</h1>
    <p>来自过去的你 · 一封穿越时光的信</p>
  </div>
  <div class="meta">
    <span>📅 写于 {created_at}</span>
    {mood_block}
    {weather_block}
  </div>
  <div class="body">
    <div class="letter-title">「 {title} 」</div>
    <div class="letter-content">{content}</div>
    {images_block}
  </div>
  <div class="footer">
    <p>💌 这是过去的你写给现在的你</p>
    <p>时空胶囊 · 珍藏每一个重要时刻</p>
  </div>
</div>
</body>
</html>
"""


def _render_images(images_json: str) -> str:
    """把图片 URL 列表（JSON）渲染为邮件中的图片块"""
    if not images_json:
        return ""
    try:
        urls = json.loads(images_json) if isinstance(images_json, str) else (images_json or [])
    except Exception:
        return ""
    if not urls:
        return ""
    # 注意：邮件里的图片需要绝对 URL 才能在客户端显示
    base = (settings.PUBLIC_BASE_URL or "").rstrip("/")
    if not base:
        # 没配置公网地址就不嵌图（避免邮件里坏图）
        return f'<div style="margin-top:24px;color:#b29a6a;font-size:13px">📎 附 {len(urls)} 张图片（请登录时空胶囊查看）</div>'
    items = "".join(
        f'<img src="{base + u if u.startswith("/") else u}" alt="附图">' for u in urls
    )
    return f'<div class="images">{items}</div>'


async def send_time_capsule_email(
    to_email: str,
    title: str,
    content: str,
    created_at: str,
    images: str = "",
    mood: str = "",
    weather: str = "",
) -> bool:
    """发送时光信邮件"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("邮件配置未设置，跳过发送")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⏳ 时空胶囊 · {title}"
        msg["From"] = formataddr((str(Header(settings.SMTP_FROM_NAME, "utf-8")), settings.SMTP_USER))
        msg["To"] = to_email

        mood_block = f"<span>{MOOD_EMOJI.get(mood, mood)}</span>" if mood else ""
        weather_block = f"<span>🌤️ {weather}</span>" if weather else ""

        html_content = EMAIL_TEMPLATE.format(
            title=title,
            content=content,
            created_at=created_at,
            images_block=_render_images(images),
            mood_block=mood_block,
            weather_block=weather_block,
        )
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        logger.info(f"时光信已发送至 {to_email}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False
