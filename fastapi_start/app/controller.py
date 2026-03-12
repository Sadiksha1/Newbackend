import serial
import time

class VendingMachine:
    def __init__(self, port, baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None

    def connect(self):
        """
        Connects to the Arduino and waits for the reboot.
        """
        try:
            print(f"Connecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            # IMPORTANT: Arduino resets when Serial opens. 
            # We must wait 2 seconds for it to wake up.
            time.sleep(2) 
            print("Connected and Ready!")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False

    def dispense_item(self, product_number):
        """
        Sends command to blink LED (later to move motor).
        Returns True if successful, False if timed out.
        """
        if not self.connection or not self.connection.is_open:
            print("Error: Not Connected")
            return False

        # 1. Send the Command (e.g., "DISPENSE:1\n")
        command = f"DISPENSE:{product_number}\n"
        self.connection.write(command.encode('utf-8'))
        print(f"Sent command: {command.strip()}")

        # 2. Wait for Confirmation (Handshake)
        # We loop and listen for "STATUS:DONE"
        start_time = time.time()
        while (time.time() - start_time) < 5:  # 5 Second Timeout
            if self.connection.in_waiting > 0:
                try:
                    response = self.connection.readline().decode('utf-8').strip()
                    print(f"Arduino says: {response}")
                    
                    if "STATUS:DONE" in response:
                        return True
                except:
                    pass # Ignore decoding errors usually caused by noise
            
            time.sleep(0.1) # Small delay to prevent CPU hogging

        print("Error: Operation Timed Out (No confirmation from Arduino)")
        return False

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()