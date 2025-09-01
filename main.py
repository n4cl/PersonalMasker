from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PersonalMasker API",
    version="0.1.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発時のみ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PersonalMasker API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/mask")
async def mask_text(text: str):
    """テキストの個人情報をマスクする"""
    # TODO: 実際のマスキング処理を実装
    return {
        "original": text,
        "masked": text.replace("XX", "***"),  # 仮実装
        "detected": ["氏名"]
    }
