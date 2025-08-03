from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from app.routes import product, payment
from app.database import Base, engine
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use ["http://127.0.0.1:5500"] if you want to restrict it
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

# Database init
Base.metadata.create_all(bind=engine)

# Define the directory to store uploaded images
UPLOAD_FOLDER = "photos"

# Ensure the directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...)):
    # Ensure the file is valid
    if file.content_type not in ['image/jpeg', 'image/png']:
        raise HTTPException(status_code=400, detail="Invalid file format. Only PNG and JPEG are allowed.")

    # Save the image file to the "photos/" directory
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"
    
    with open(file_location, "wb") as buffer:
        # Read the file content and save to disk
        buffer.write(await file.read())

    return {"filename": file.filename, "file_location": file_location}
# Routers
app.include_router(product.router)
app.include_router(payment.router)
