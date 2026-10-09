def calculate_sensor_health(data):
    temperature = data["temperature"]
    dust = data["dust"]
    motion = data["motion"]
    ldr = data["ldr"]

    warnings = []

    if temperature < 0 or temperature > 70:
        warnings.append("Temperature reading may be abnormal")

    if dust < 0:
        warnings.append("Dust reading is invalid")

    if motion not in [0, 1]:
        warnings.append("Motion reading is invalid")

    if ldr < 0:
        warnings.append("LDR reading is invalid")

    if warnings:
        status = "WARNING"
    else:
        status = "NORMAL"

    return {
        "status": status,
        "warnings": warnings
    }