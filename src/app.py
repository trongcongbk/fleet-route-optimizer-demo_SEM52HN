"""Main application entry point."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .config import setup_logging, get_settings, get_logger

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Fleet Route Optimizer - API for solving Capacitated Vehicle Routing Problem with Time Windows (CVRPTW) using real-world distances and traffic patterns",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, tags=["solver"])


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"{settings.app_name} starting up...")
    logger.info(f"Debug mode: {settings.debug}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"{settings.app_name} shutting down...")


# --- PHẦN THÊM MỚI ĐỂ CHẠY WEBUI ---

# 1. Xác định đường dẫn tới thư mục build (nằm trong src)
current_dir = os.path.dirname(os.path.abspath(__file__))
build_path = os.path.join(current_dir, "build")

# 2. Phục vụ các file tĩnh của React (CSS, JS)
# Lưu ý: Phải đặt sau app.include_router để không đè lên các đường dẫn API
if os.path.exists(os.path.join(build_path, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")


# 3. Trình duyệt truy cập đường dẫn bất kỳ (không phải /api) thì trả về index.html
@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    # Kiểm tra nếu file cụ thể tồn tại trong build (ví dụ: favicon.ico, logo.png)
    local_file = os.path.join(build_path, full_path)
    if full_path != "" and os.path.exists(local_file):
        return FileResponse(local_file)

    # Mặc định trả về index.html để React Router xử lý giao diện
    index_path = os.path.join(build_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"error": "WebUI build folder not found inside src/"}


# --- KẾT THÚC PHẦN THÊM MỚI ---

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
