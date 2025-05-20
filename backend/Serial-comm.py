import serial
import time
import os
import math

# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(script_dir, "../Temp")
GCODE_FILE = os.path.join(temp_dir, "output.gcode")
SERIAL_PORT = '/dev/ttyACM0'  
BAUD_RATE = 9600  
VERBOSE = True  




class GCodeSender:
    def __init__(self, port, baud_rate):
        self.port_name = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.gcodes = []
        self.current_line = 0
        self.streaming = False

    def open_serial_port(self):
        try:
            self.serial_connection = serial.Serial(self.port_name, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            if VERBOSE:
                print(f"Connected to {self.port_name} at {self.baud_rate} baud.")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            self.serial_connection = None

    def load_gcode_file(self, filepath):
        try:
            with open(filepath, 'r') as file:
                self.gcodes = [line.strip() for line in file if line.strip()]
            if VERBOSE:
                print(f"Loaded {len(self.gcodes)} G-code lines from {filepath}.")
        except FileNotFoundError:
            print(f"Error: G-code file '{filepath}' not found.")
            self.gcodes = []

    def stream_gcode(self):
        if not self.serial_connection or not self.gcodes:
            print("Error: No serial connection or G-code loaded.")
            return

        self.streaming = True
        while self.streaming and self.current_line < len(self.gcodes):
            line = self.gcodes[self.current_line]
            if VERBOSE:
                print(f"Sending: {line} ({self.current_line + 1})")
            self.serial_connection.write((line + '\n').encode())
            while True:
                response = self.serial_connection.readline().decode().strip()
                # trying not to overwhelm the arduino with too many requests
                if response:
                    if VERBOSE:
                        print(f"Arduino response: {response}")
                    if response.startswith("ok") or response.startswith("error"):
                        self.current_line += 1
                        break  
                else:
                    time.sleep(0.05)  # Give Arduino more time to reply if needed

            time.sleep(0.1)  # Small delay for serial communication

        if self.current_line >= len(self.gcodes):
            print("Finished streaming G-code.")
            self.streaming = False

    def close_serial_port(self):
        if self.serial_connection:
            self.serial_connection.close()
            if VERBOSE:
                print(f"Closed serial connection to {self.port_name}.")


if __name__ == "__main__":
    sender = GCodeSender(SERIAL_PORT, BAUD_RATE)
    try:
        # Open the serial connection
        sender.open_serial_port()

        # Load the G-code file
        sender.load_gcode_file(GCODE_FILE)

        # Start streaming G-code to Arduino
        sender.stream_gcode()

    except KeyboardInterrupt:
        print("\nProgram interrupted. Closing serial port...")

    finally:
        sender.close_serial_port()
        print("Shutdown complete.")
