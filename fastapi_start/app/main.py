from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes import product, payment
import os

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables
Base.metadata.create_all(bind=engine)

# Static folders
app.mount("/photos", StaticFiles(directory="photos"), name="photos")
app.mount("/qrcodes", StaticFiles(directory="qrcodes"), name="qrcodes")

# Ensure directories exist
for folder in ["photos", "qrcodes"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Image upload endpoint
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(status_code=400, detail="Invalid file format.")
    file_location = f"photos/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename, "file_location": file_location}

# Routers
app.include_router(product.router)
app.include_router(payment.router)
