import csv
import os

from serial_reader import ESP32SerialReader
from data_processor import process_sensor_data
from sensor_health import calculate_sensor_health


PORT = "COM7"
BAUD_RATE = 115200

CSV_FILE = "../data/sensor_readings.csv"


def save_to_csv(data, health):
    file_exists = os.path.exists(CSV_FILE)

    os.makedirs("../data", exist_ok=True)

    with open(CSV_FILE, "a", newline="") as file:
        fieldnames = [
            "timestamp",
            "temperature",
            "dust",
            "motion",
            "ldr",
            "status",
            "warnings"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": data["timestamp"],
            "temperature": data["temperature"],
            "dust": data["dust"],
            "motion": data["motion"],
            "ldr": data["ldr"],
            "status": health["status"],
            "warnings": "; ".join(health["warnings"])
        })


def main():
    reader = ESP32SerialReader(PORT, BAUD_RATE)
    reader.connect()

    if reader.connection is None:
        return

    print("Waiting for sensor data...")

    try:
        while True:
            raw_data = reader.read_data()

            if raw_data is not None:
                processed_data = process_sensor_data(raw_data)

                if processed_data is not None:
                    health = calculate_sensor_health(processed_data)

                    print("\nSensor data:")
                    print(processed_data)

                    print("Health status:", health["status"])

                    if health["warnings"]:
                        print("Warnings:", health["warnings"])

                    save_to_csv(processed_data, health)

    except KeyboardInterrupt:
        print("\nStopping program...")

    finally:
        reader.close()


if __name__ == "__main__":
    main()