import os
import sys
import time
import serial
from PySide6.QtCore import QThread, Signal

class SerialWorker(QThread):
    board_detected = Signal()
    connection_status = Signal(bool, str) # Emits (connected, port_info)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.ser = None
        self.baudrate = 115200
        # Determine default port based on OS
        if sys.platform.startswith("win"):
            self.default_port = "COM8"
        else:
            self.default_port = "/dev/serial0"

    def run(self):
        self.running = True
        print(f"[SerialWorker] Starting serial connection thread...")
        
        # 1. Try default port
        try:
            self.ser = serial.Serial(self.default_port, self.baudrate, timeout=1)
            time.sleep(1) # Let the connection settle
            self.connection_status.emit(True, self.default_port)
            print(f"[SerialWorker] Connected to default port: {self.default_port}")
        except Exception:
            # 2. Try common fallback ports
            fallback_ports = []
            if sys.platform.startswith("win"):
                fallback_ports = [f"COM{i}" for i in range(1, 12) if f"COM{i}" != self.default_port]
            else:
                fallback_ports = ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyUSB1", "/dev/ttyUSB2"]
            
            connected = False
            for port in fallback_ports:
                try:
                    self.ser = serial.Serial(port, self.baudrate, timeout=1)
                    time.sleep(1)
                    self.connection_status.emit(True, port)
                    print(f"[SerialWorker] Connected to fallback port: {port}")
                    connected = True
                    break
                except Exception:
                    continue
            
            if not connected:
                print("[SerialWorker] Failed to connect to any serial port.")
                self.connection_status.emit(False, "Disconnected")
                self.running = False
                return

        # 3. Listen to incoming data loop
        while self.running:
            try:
                if self.ser and self.ser.is_open:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        print(f"[SerialWorker] Received from ESP32: {line}")
                    if line == "BOARD_DETECTED":
                        self.board_detected.emit()
            except Exception as e:
                print(f"[SerialWorker] Error during reading: {e}")
                self.connection_status.emit(False, "Error")
                break
            time.sleep(0.05) # Prevent high CPU usage

        # 4. Clean up connection
        self.close_connection()

    def send_cmd(self, cmd: str):
        """Writes command to the serial port safely."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(cmd.encode("utf-8"))
                self.ser.flush()
                print(f"[SerialWorker] Sent to ESP32: {cmd.strip()}")
            except Exception as e:
                print(f"[SerialWorker] Error writing command: {e}")

    def close_connection(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("[SerialWorker] Serial connection closed.")
            except Exception as e:
                print(f"[SerialWorker] Error closing connection: {e}")
        self.connection_status.emit(False, "Disconnected")

    def stop(self):
        self.running = False
        self.close_connection()
        self.wait() # Wait for thread to exit
