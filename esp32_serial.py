import json
import time
import serial


class ESP32SerialReader:
    """Reads the JSON stream produced by the MineSense ESP32 sketch."""

    def __init__(self, port="COM7", baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None
        self.last_data = None

    def connect(self):
        if self.connection and self.connection.is_open:
            return True

        try:
            self.connection = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=0.15
            )
            # Give the ESP32 time to reset after opening the port.
            time.sleep(2)
            self.connection.reset_input_buffer()
            print(f"[ESP32] Connected on {self.port}")
            return True
        except serial.SerialException as error:
            print(f"[ESP32] Not connected on {self.port}: {error}")
            self.connection = None
            return False

    def read_latest(self):
        """Drain all currently available lines and keep the newest valid JSON."""
        if not self.connection or not self.connection.is_open:
            return self.last_data

        latest = None

        try:
            while self.connection.in_waiting:
                raw = self.connection.readline().decode(
                    "utf-8", errors="ignore"
                ).strip()

                if not raw:
                    continue

                try:
                    candidate = json.loads(raw)
                    if isinstance(candidate, dict):
                        latest = candidate
                except json.JSONDecodeError:
                    # Ignore human-readable/non-JSON serial lines.
                    continue

        except serial.SerialException as error:
            print(f"[ESP32] Serial communication error: {error}")
            self.close()

        if latest is not None:
            self.last_data = latest

        return self.last_data

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.connection = None
        print("[ESP32] Serial connection closed")
