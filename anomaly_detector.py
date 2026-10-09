from collections import deque
import numpy as np

from config import SENSOR_CONFIG


class AnomalyDetector:
    def __init__(self, window_size=20):
        self.history = {
            sensor: deque(maxlen=window_size)
            for sensor in SENSOR_CONFIG
        }

    def calculate_anomaly_score(self, sensor, value):
        config = SENSOR_CONFIG[sensor]
        history = self.history[sensor]

        history.append(value)

        if len(history) < 5:
            return 0.0

        values = np.array(history, dtype=float)
        mean = np.mean(values)
        standard_deviation = np.std(values)

        if standard_deviation == 0:
            statistical_score = 0.0
        else:
            z_score = abs(value - mean) / standard_deviation
            statistical_score = min(z_score / 3, 1.0)

        if sensor == "temperature":
            range_score = max(
                0,
                (value - config["normal_max"]) /
                (config["critical_max"] - config["normal_max"])
            )

        elif sensor == "dust":
            range_score = max(
                0,
                (value - config["normal_max"]) /
                (config["critical_max"] - config["normal_max"])
            )

        elif sensor == "ldr":
            range_score = max(
                0,
                (config["normal_min"] - value) /
                config["normal_min"]
            )

        elif sensor == "motion":
            range_score = max(0, (value - 0.2) / 0.8)

        else:
            range_score = 0.0

        score = (0.5 * statistical_score) + (0.5 * min(range_score, 1.0))

        return round(min(score, 1.0), 3)

    def analyze(self, reading):
        scores = {}

        for sensor, value in reading.items():
            if sensor == "timestamp":
                continue

            scores[sensor] = self.calculate_anomaly_score(
                sensor,
                float(value)
            )

        return scores