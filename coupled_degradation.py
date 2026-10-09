from config import COUPLED_DEGRADATION_THRESHOLD


def detect_coupled_degradation(anomaly_scores, predictions):
    degrading_sensors = []

    for sensor, score in anomaly_scores.items():
        if score >= COUPLED_DEGRADATION_THRESHOLD:
            degrading_sensors.append(sensor)

    if len(degrading_sensors) >= 2:
        severity = sum(
            anomaly_scores[sensor]
            for sensor in degrading_sensors
        ) / len(degrading_sensors)

        if severity >= 0.80:
            level = "HIGH"
        elif severity >= 0.65:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "detected": True,
            "level": level,
            "affected_sensors": degrading_sensors,
            "score": round(severity, 3),
            "explanation": (
                "Multiple sensors are degrading during the same "
                "observation period."
            )
        }

    return {
        "detected": False,
        "level": "NORMAL",
        "affected_sensors": [],
        "score": 0.0,
        "explanation": "No coupled degradation detected."
    }