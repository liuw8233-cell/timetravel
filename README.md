# ⏳ 时空胶囊 · 穿越时光的记录

一个集时光信、漂流瓶、AI情绪陪伴、AI算命于一体的全栈 Web 应用。

## ✨ 功能

- **✉️ 时光信** — 给未来的自己或他人写信，到期自动发送邮件
- **🫙 漂流瓶** — 匿名倾诉心事，陌生人可以捞取并温暖回复
- **🌊 情绪树洞** — AI 化身温柔陪伴师，随时倾听你的心声
- **🔮 AI算命** — 结合八字命理与星座，AI 娱乐解读命运

## 🛠️ 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JS（单页面应用）
- **AI**: OpenAI 兼容 API（支持通义千问/智谱GLM/DeepSeek 等）
- **邮件**: Python smtplib + SMTP
- **定时任务**: APScheduler

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key 和 SMTP 配置
```

### 3. 启动服务

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问 http://localhost:8000 即可使用。

## 📁 项目结构

```
shiguangjiaonang/
├── main.py              # FastAPI 入口
├── config.py            # 配置管理
├── database.py          # 数据库连接
├── models.py            # SQLAlchemy 模型
├── schemas.py           # Pydantic 数据结构
├── auth.py              # 认证工具
├── routers/
│   ├── auth.py          # 登录/注册
│   ├── letters.py       # 时光信
│   ├── bottles.py       # 漂流瓶
│   ├── ai.py            # AI 聊天/算命
│   └── settings.py      # 用户设置
├── services/
│   ├── ai_service.py    # AI 调用服务
│   ├── email_service.py # 邮件发送服务
│   └── scheduler.py     # 定时任务
├── static/
│   └── index.html       # 前端页面
└── templates/
```

## 📄 License

MIT
