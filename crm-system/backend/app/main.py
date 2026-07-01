from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse, Response
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .models import *  # 导入所有模型

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 前端产物目录
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# 创建 FastAPI 应用
app = FastAPI(
    title="CRM System API",
    description="Telegram CRM 系统后端 API",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入并注册路由
from .api import auth, users, regions, products, messages, orders, dashboard, rules

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(regions.router, prefix="/api/regions", tags=["区域管理"])
app.include_router(products.router, prefix="/api/products", tags=["产品管理"])
app.include_router(messages.router, prefix="/api/messages", tags=["原始消息"])
app.include_router(orders.router, prefix="/api/orders", tags=["订单管理"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(rules.router, prefix="/api/rules", tags=["规则管理"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# SPA 中间件：对非 API 请求返回前端静态文件或 index.html
class SPAMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # 只处理 404 的 GET 请求，且不是 /api 路径
        if response.status_code == 404 and request.method == "GET":
            path = request.url.path.lstrip("/")
            if not path.startswith("api/"):
                # 尝试返回静态文件
                file_path = FRONTEND_DIST / path
                if file_path.is_file():
                    return FileResponse(str(file_path))
                # SPA fallback：返回 index.html
                index = FRONTEND_DIST / "index.html"
                if index.is_file():
                    return FileResponse(str(index))
        return response


if FRONTEND_DIST.exists():
    # 静态资源（CSS/JS/图片等）直接由 StaticFiles 处理
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
    app.add_middleware(SPAMiddleware)