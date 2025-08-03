from fastapi import APIRouter, HTTPException
from ..utils.qr import generate_qr

router = APIRouter(prefix="/pay", tags=["Payments"])

@router.get("/{product_id}")
def generate_payment_qr(product_id: int):
    fake_payment_url = f"https://khalti.com/pay/{product_id}"  # Replace with actual gateway
    qr_path = generate_qr(fake_payment_url, f"qr_{product_id}.png")
    return {"qr_path": qr_path, "payment_url": fake_payment_url}
