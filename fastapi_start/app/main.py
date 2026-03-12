from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routes import product, payment, admin
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
app.include_router(admin.router)

from app.controller import VendingMachine

# --- CONFIGURATION ---
ARDUINO_PORT = 'COM3'  # <--- CHANGE THIS TO YOUR PORT

def main():
    # 1. Initialize the Machine
    vm = VendingMachine(ARDUINO_PORT)
    
    if not vm.connect():
        return # Exit if connection fails

    print("\n--- VENDING MACHINE TEST CONSOLE ---")
    print("Type a product number (1-4) to dispense.")
    print("Type 'q' to quit.\n")

    while True:
        user_input = input("Select Product (1-4): ")

        if user_input.lower() == 'q':
            break

        if user_input in ['1', '2', '3', '4']:
            print(f"\nProcessing Payment for Product {user_input}...")
            
            # --- MOCK PAYMENT SUCCESS ---
            payment_success = True 
            
            if payment_success:
                print("Payment Verified. Dispensing...")
                success = vm.dispense_item(int(user_input))
                
                if success:
                    print(">> SUCCESS: Please take your item.\n")
                else:
                    print(">> ERROR: Machine Malfunction (Refund Initiated).\n")
        else:
            print("Invalid Selection. Try 1, 2, 3, or 4.")

    vm.close()
    print("System Shutdown.")

if __name__ == "__main__":
    main()