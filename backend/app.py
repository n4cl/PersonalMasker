from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.mask import router as mask_router
from backend.services.masker import Masker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリ起動/終了のライフサイクルでリソースを管理する。
    - 起動時に Masker を準備
    - 終了時に必要ならクリーンアップ（現状なし）
    """
    app.state.masker = Masker(model_name="ja_ginza")
    try:
        yield
    finally:
        # クリーンアップが必要ならここで実施
        pass


app = FastAPI(title="PersonalMasker API", version="0.1.0", lifespan=lifespan)

# CORS (development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["system"],
    summary="ヘルスチェック",
    description="死活監視。APIプロセスが起動していれば200を返します。",
)
async def health_check():
    return {"status": "healthy"}


# Routers
app.include_router(mask_router)
