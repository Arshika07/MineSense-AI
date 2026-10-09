from datetime import datetime


def validate_sensor_data(data):
    required_fields = [
        "temperature",
        "dust",
        "motion",
        "ldr"
    ]

    if not isinstance(data, dict):
        return False

    for field in required_fields:
        if field not in data:
            return False

    return True


def process_sensor_data(data):
    if not validate_sensor_data(data):
        return None

    processed_data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "temperature": float(data["temperature"]),
        "dust": float(data["dust"]),
        "motion": int(data["motion"]),
        "ldr": float(data["ldr"])
    }

    return processed_data