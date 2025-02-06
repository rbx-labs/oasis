from fastapi import FastAPI, HTTPException
from eth_account import Account
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_wallet()
    yield

app = FastAPI(lifespan=lifespan)

WALLET_PATH = Path("/data/wallet.json")

def init_wallet():
    if not WALLET_PATH.exists():
        # 새 지갑 생성
        account = Account.create()
        wallet_data = {
            "address": account.address,
            "private_key": account.key.hex()
        }
        
        # 데이터 디렉토리 생성
        WALLET_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 지갑 정보 저장
        with open(WALLET_PATH, "w") as f:
            json.dump(wallet_data, f)
        return wallet_data
    
    # 기존 지갑 로드
    with open(WALLET_PATH) as f:
        return json.load(f)

@app.get("/api/wallet")
async def get_wallet():
    try:
        wallet_data = init_wallet()
        return {"address": wallet_data["address"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 