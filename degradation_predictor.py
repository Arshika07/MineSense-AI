from collections import deque
import numpy as np

class DegradationPredictor:
    def __init__(self, window_size=15):
        self.history = {
            "temperature": deque(maxlen=window_size),
            "dust": deque(maxlen=window_size),
            "motion": deque(maxlen=window_size),
            "ldr": deque(maxlen=window_size)
        }

    def update(self, sensor, value):
        self.history[sensor].append(float(value))

    def calculate_trend(self, sensor):
        values = list(self.history[sensor])
        if len(values) < 5:
            return 0.0
        x = np.arange(len(values))
        return float(np.polyfit(x, values, 1)[0])

    def is_degrading(self, sensor, trend):
        if sensor == "ldr":
            return trend < -0.01
        if sensor in ("temperature", "dust", "motion"):
            return trend > 0.01
        return False

    def predict(self, sensor, current_value, anomaly_score):
        self.update(sensor, current_value)
        trend = self.calculate_trend(sensor)
        degrading = self.is_degrading(sensor, trend)

        if anomaly_score >= 0.70:
            condition = "CRITICAL"
        elif anomaly_score >= 0.55:
            condition = "DEGRADING"
        elif anomaly_score >= 0.30:
            condition = "WATCH"
        else:
            condition = "NORMAL"

        if abs(trend) < 0.01:
            trend_status = "STABLE"
        elif degrading:
            trend_status = "DEGRADING"
        else:
            trend_status = "RECOVERING"

        predicted_score = anomaly_score
        if degrading:
            predicted_score = min(1.0, anomaly_score + abs(trend) * 0.08)

        time_to_critical = None
        if degrading and abs(trend) > 0.01 and anomaly_score < 1.0:
            rate = abs(trend) * 0.08
            time_to_critical = (1.0 - anomaly_score) / rate

        return {
            "condition": condition,
            "trend": trend_status,
            "trend_value": round(trend, 4),
            "current_degradation": round(anomaly_score, 3),
            "predicted_degradation": round(predicted_score, 3),
            "time_to_critical_steps": round(time_to_critical, 1)
                if time_to_critical is not None else None
        }
