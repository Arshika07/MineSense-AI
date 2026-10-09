from collections import deque

class RecoveryEngine:
    def __init__(self, window_size=8):
        self.history = deque(maxlen=window_size)

    def update(self, health_percent):
        self.history.append(float(health_percent))

    def analyze(self, health_percent, scenario):
        self.update(health_percent)
        values = list(self.history)
        if len(values) < 3:
            rate = 0.0
        else:
            rate = (values[-1] - values[0]) / max(1, len(values) - 1)

        recovering = rate > 0.8 and scenario == "recovery"
        target = 80.0
        remaining = max(0.0, target - health_percent)
        eta = (remaining / rate) if recovering and rate > 0 else None
        confidence = min(95.0, 55.0 + len(values) * 5.0) if recovering else 0.0

        return {
            "status": "RECOVERING" if recovering else ("STABLE" if scenario != "recovery" else "WAITING"),
            "recovery_rate_percent_per_step": round(rate, 2),
            "estimated_recovery_steps": round(eta, 1) if eta is not None else None,
            "estimated_recovery_minutes": round(eta * 0.5, 1) if eta is not None else None,
            "confidence": round(confidence, 1),
            "target_health": target,
            "post_recovery_status": "MONITORING" if recovering else "NOT ACTIVE",
        }
