from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.mask import router as mask_router

app = FastAPI(
    title="PersonalMasker API",
    version="0.1.0"
)

# CORS (development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health", tags=["system"], summary="ヘルスチェック", description="死活監視。APIプロセスが起動していれば200を返します。")
async def health_check():
    return {"status": "healthy"}


# Routers
app.include_router(mask_router)
