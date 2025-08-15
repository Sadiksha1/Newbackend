import qrcode
import os
from datetime import datetime

QR_FOLDER = "qrcodes"
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

def generate_fonepay_qr(amount: float, product_name: str) -> str:
    # Static merchant details for showcase
    merchant_code = "TESTMERCHANT123"
    invoice_number = datetime.now().strftime("%Y%m%d%H%M%S")

    # Simulated Fonepay QR content
    qr_data = f"FONEPAY://merchant={merchant_code}&amount={amount}&invoice={invoice_number}&product={product_name}"

    # File path
    qr_filename = f"fonepay_{invoice_number}.png"
    qr_path = os.path.join(QR_FOLDER, qr_filename)

    # Generate QR
    img = qrcode.make(qr_data)
    img.save(qr_path)

    return qr_path
