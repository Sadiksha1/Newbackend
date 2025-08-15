from fastapi import APIRouter, HTTPException
from app.utils.qr import generate_fonepay_qr
import os

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.get("/fonepay_qr/{amount}/{product_name}")
async def get_fonepay_qr(amount: float, product_name: str):
    try:
        qr_path = generate_fonepay_qr(amount, product_name)
        return {"qr_code_url": f"/qrcodes/{os.path.basename(qr_path)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
