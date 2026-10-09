import json
import serial
import time


class ESP32SerialReader:
    def __init__(self, port, baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=1
            )

            time.sleep(2)
            print(f"Connected to ESP32 on {self.port}")

        except serial.SerialException as error:
            print(f"Could not connect to ESP32: {error}")
            self.connection = None

    def read_data(self):
        if self.connection is None:
            return None

        try:
            if self.connection.in_waiting > 0:
                raw_data = self.connection.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if raw_data:
                    try:
                        return json.loads(raw_data)

                    except json.JSONDecodeError:
                        print("Invalid data received:", raw_data)

        except serial.SerialException as error:
            print("Serial communication error:", error)

        return None

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Serial connection closed")