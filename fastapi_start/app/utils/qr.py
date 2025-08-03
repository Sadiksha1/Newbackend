import qrcode

def generate_qr(payment_url: str, filename: str = "qr.png") -> str:
    img = qrcode.make(payment_url)
    path = f"photos/{filename}"
    img.save(path)
    return path
