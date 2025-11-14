from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes import product, payment, checkout
import os

app = FastAPI()

# -------------------------------------------
# CORS CONFIG
# -------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------
# CREATE DATABASE TABLES
# -------------------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------------------
# STATIC FOLDERS (Photos + QR Codes)
# -------------------------------------------
STATIC_FOLDERS = ["photos", "qrcodes"]

for folder in STATIC_FOLDERS:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.mount("/photos", StaticFiles(directory="photos"), name="photos")
app.mount("/qrcodes", StaticFiles(directory="qrcodes"), name="qrcodes")

# -------------------------------------------
# IMAGE UPLOAD ENDPOINT
# -------------------------------------------
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file format. Only JPG/PNG allowed.")

    file_path = f"photos/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {
        "filename": file.filename,
        "url": f"/photos/{file.filename}"
    }


# -------------------------------------------
# ROUTERS
# -------------------------------------------
app.include_router(product.router)
app.include_router(payment.router)
app.include_router(checkout.router)


# -------------------------------------------
# ROOT
# -------------------------------------------
@app.get("/")
def root():
    return {"message": "Vending Machine Backend Running"}
