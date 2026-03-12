import time
from controller import VendingMachine

# --- CONFIGURATION ---
ARDUINO_PORT = 'COM3'  # <--- UPDATE THIS (e.g., /dev/ttyUSB0)

# --- PRODUCT CATALOG MAPPING ---
# This acts as your database.
# 'slot': The number sent to Arduino (1=Pin4, 2=Pin5, 3=Pin6, 4=Pin7)
INVENTORY = {
    "101": {
        "name": "Lays Classic Chips",
        "price": 1.50,
        "slot": 1  # Maps to Arduino Pin 4
    },
    "102": {
        "name": "Coca Cola Can",
        "price": 2.00,
        "slot": 2  # Maps to Arduino Pin 5
    },
    "103": {
        "name": "Oreo Cookies",
        "price": 1.25,
        "slot": 3  # Maps to Arduino Pin 6
    },
    "104": {
        "name": "Protein Bar",
        "price": 2.50,
        "slot": 4  # Maps to Arduino Pin 7
    }
}

def display_menu():
    print("\n" + "="*40)
    print("      VENDING MACHINE MENU      ")
    print("="*40)
    print(f"{'ID':<6} {'PRODUCT':<20} {'PRICE':<8}")
    print("-" * 40)
    for pid, details in INVENTORY.items():
        print(f"{pid:<6} {details['name']:<20} ${details['price']:.2f}")
    print("="*40)

def process_transaction(vm):
    display_menu()
    
    # 1. User Selection
    product_id = input("\nEnter Product ID (or 'q' to quit): ").strip()
    
    if product_id.lower() == 'q':
        return False # Signal to exit

    # 2. Validate Product ID
    if product_id not in INVENTORY:
        print(">> ERROR: Invalid Product ID. Please try again.")
        return True # Continue loop

    item = INVENTORY[product_id]
    print(f"\nSelected: {item['name']} (${item['price']:.2f})")

    # 3. Mock Payment Gateway
    # In a real app, you would integrate Stripe/PayPal SDK here.
    user_money = float(input(f"Please insert payment (e.g., {item['price']}): "))

    if user_money >= item['price']:
        change = user_money - item['price']
        print(f">> Payment Accepted. Change: ${change:.2f}")
        print(">> Dispensing...")

        # 4. MAP TO HARDWARE LOGIC
        # We retrieve the 'slot' (1, 2, 3, 4) from our INVENTORY dictionary
        target_slot = item['slot']
        
        # 5. Send Command to Arduino
        # This sends "DISPENSE:1" (or 2, 3, 4) based on the mapping
        success = vm.dispense_item(target_slot)
        
        if success:
            print(">> STATUS: Product Dispensed Successfully! Enjoy.")
        else:
            print(">> CRITICAL ERROR: Hardware Timeout. Contact Support.")
    else:
        print(f">> ERROR: Insufficient Funds. Refunded ${user_money:.2f}")

    return True # Continue loop

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Initialize Hardware Connection
    vm = VendingMachine(ARDUINO_PORT)
    
    if vm.connect():
        running = True
        while running:
            running = process_transaction(vm)
            time.sleep(1) # Brief pause before next customer
        
        vm.close()
        print("System Shutdown.")
    else:
        print("System could not start. Check Arduino connection.")