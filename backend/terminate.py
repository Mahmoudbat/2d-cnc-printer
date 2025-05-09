import serial
import time

# Configuration
SERIAL_PORT = "/dev/ttyACM0"  # Replace with the correct serial port for your device
BAUD_RATE = 9600  # Ensure this matches the baud rate of your CNC device


def terminate_serial():
    try:
        # Open the serial connection
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud.")

            # Step 1: Send M300 S50 (Pen Up)
            ser.write(b"M300 S50\n")
            print("Sent: M300 S50 (Pen Up)")
            time.sleep(0.5)  # Wait for the command to process

            # Step 2: Send G1 X0 Y0 (Move to origin)
            ser.write(b"G1 X0 Y0\n")
            print("Sent: G1 X0 Y0 (Move to origin)")
            time.sleep(0.5)  # Wait for the command to process

            # Step 3: Send M300 S30 (Pen Down)
            ser.write(b"M300 S30\n")
            print("Sent: M300 S30 (Pen Down)")
            time.sleep(0.5)  # Wait for the command to process

            print("Termination sequence completed successfully.")

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    terminate_serial()