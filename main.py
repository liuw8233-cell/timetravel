from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database import init_db
from services.scheduler import start_scheduler, stop_scheduler
from routers import auth, letters, bottles, ai, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    logger.info("🚀 时空胶囊服务启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")
    start_scheduler()
    logger.info("✅ 定时任务启动完成")
    yield
    # 关闭时清理
    stop_scheduler()
    logger.info("👋 时空胶囊服务已停止")


app = FastAPI(
    title="时空胶囊",
    description="给未来的自己写信，埋藏心事，AI情绪陪伴，娱乐算卦",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(letters.router)
app.include_router(bottles.router)
app.include_router(ai.router)
app.include_router(settings.router)

# 静态文件
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "时空胶囊"}
