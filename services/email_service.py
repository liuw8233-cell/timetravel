"""邮件服务 - 发送时光信"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from config import settings
import logging

logger = logging.getLogger(__name__)


EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f5f0ff; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(120,80,200,0.15); }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }}
  .header h1 {{ color: white; margin: 0; font-size: 28px; letter-spacing: 2px; }}
  .header p {{ color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px; }}
  .body {{ padding: 40px 30px; }}
  .letter-title {{ font-size: 22px; color: #4a3570; font-weight: bold; margin-bottom: 20px; }}
  .letter-content {{ font-size: 16px; color: #333; line-height: 1.8; white-space: pre-wrap; background: #faf8ff; border-left: 4px solid #764ba2; padding: 20px; border-radius: 8px; }}
  .footer {{ padding: 20px 30px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #f0eaff; }}
  .capsule-icon {{ font-size: 48px; margin-bottom: 10px; display: block; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="capsule-icon">⏳</span>
    <h1>时空胶囊</h1>
    <p>来自过去的你，一封穿越时光的信</p>
  </div>
  <div class="body">
    <div class="letter-title">📝 {title}</div>
    <div class="letter-content">{content}</div>
  </div>
  <div class="footer">
    <p>💌 这封信由你在 {created_at} 写给现在的自己</p>
    <p>时空胶囊 · 珍藏每一个重要时刻</p>
  </div>
</div>
</body>
</html>
"""


async def send_time_capsule_email(
    to_email: str,
    title: str,
    content: str,
    created_at: str
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

        html_content = EMAIL_TEMPLATE.format(
            title=title,
            content=content,
            created_at=created_at
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
