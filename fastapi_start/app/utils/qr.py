import qrcode
import os
from datetime import datetime

QR_FOLDER = "qrcodes"
if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)

def generate_fonepay_qr(amount: float, product_name: str, merchant_code: str = "TEST_MERCHANT_001"):
    invoice_number = datetime.now().strftime("%Y%m%d%H%M%S%f")

    # Realistic Fonepay-style payload (simulation)
    qr_data = (
        f"FONEPAY://PAY?"
        f"MERCHANT={merchant_code}&"
        f"AMOUNT={amount}&"
        f"PRODUCT={product_name}&"
        f"INVOICE={invoice_number}"
    )

    filename = f"{invoice_number}.png"
    filepath = os.path.join(QR_FOLDER, filename)

    qr = qrcode.make(qr_data)
    qr.save(filepath)

    # return invoice_number and absolute path to file
    return invoice_number, filepath
