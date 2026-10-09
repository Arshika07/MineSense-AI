"""
STAGE 7 - Synthetic historical dataset generator.

Runs the existing simulator + perception simulator through every scenario,
many times with different random seeds, and records the full feature set
(environmental + perception + fusion + coupled-degradation) together with
the readiness label the current rule engine assigns.

Why bootstrap labels from the rule engine instead of hand-labeling?
The rule engine already encodes the domain thresholds validated in Stages
5-6. Using it to label a large synthetic dataset gives Stage 8 a genuine,
evaluable ML model quickly, while real ESP32 telemetry accumulates for a
future retraining pass. This is a standard technique when live labeled
history isn't available yet.

Output: backend/data/degradation_dataset.csv
"""

import csv
import os
import random

from simulator import SensorSimulator
from perception_simulator import PerceptionSimulator
from anomaly_detector import AnomalyDetector
from coupled_degradation import detect_coupled_degradation
from degradation_predictor import DegradationPredictor
from sensor_fusion import calculate_perception_fusion
from readiness_model import calculate_readiness

SCENARIOS = [
    "normal", "dust_buildup", "vibration", "coupled", "fog",
    "camera_failure", "lidar_failure", "radar_interference", "recovery"
]

EPISODES_PER_SCENARIO = 40   # independent runs per scenario
STEPS_PER_EPISODE = 30       # timesteps per run

FEATURE_COLUMNS = [
    "temperature", "dust", "motion", "ldr",
    "anomaly_temperature", "anomaly_dust", "anomaly_motion", "anomaly_ldr",
    "camera_health", "lidar_health", "radar_health",
    "fused_perception_confidence",
    "coupled_detected", "coupled_score",
    "scenario_step_fraction",
]

LABEL_COLUMN = "readiness_status"


def run_episode(scenario, seed):
    random.seed(seed)

    sim = SensorSimulator()
    sim.set_scenario(scenario)

    perc = PerceptionSimulator()
    perc.set_scenario(scenario)

    detector = AnomalyDetector()
    predictor = DegradationPredictor()

    rows = []

    for step in range(1, STEPS_PER_EPISODE + 1):
        reading = sim.generate_reading()
        perception = perc.generate_reading()

        model_reading = {k: v for k, v in reading.items() if k != "timestamp"}
        anomaly_scores = detector.analyze(model_reading)

        predictions = {
            s: predictor.predict(s, model_reading[s], anomaly_scores[s])
            for s in ["temperature", "dust", "motion", "ldr"]
        }

        coupled = detect_coupled_degradation(anomaly_scores, predictions)
        fusion = calculate_perception_fusion(perception)

        perception_scores = fusion["degradation_scores"]
        degraded_perception = [s for s, v in perception_scores.items() if v >= 0.55]
        if len(degraded_perception) >= 2:
            coupled["detected"] = True
            coupled["score"] = round(
                sum(perception_scores[s] for s in degraded_perception) / len(degraded_perception), 3
            )

        readiness = calculate_readiness(anomaly_scores, coupled)
        readiness_score = max(
            0,
            readiness["readiness_score"]
            - max(0, 100 - fusion["fused_perception_confidence"]) * 0.35
        )
        status = (
            "READY" if readiness_score >= 80 else
            "LIMITED" if readiness_score >= 60 else
            "DEGRADED" if readiness_score >= 40 else
            "CRITICAL"
        )

        rows.append({
            "temperature": model_reading["temperature"],
            "dust": model_reading["dust"],
            "motion": model_reading["motion"],
            "ldr": model_reading["ldr"],
            "anomaly_temperature": anomaly_scores["temperature"],
            "anomaly_dust": anomaly_scores["dust"],
            "anomaly_motion": anomaly_scores["motion"],
            "anomaly_ldr": anomaly_scores["ldr"],
            "camera_health": fusion["camera_health"],
            "lidar_health": fusion["lidar_health"],
            "radar_health": fusion["radar_health"],
            "fused_perception_confidence": fusion["fused_perception_confidence"],
            "coupled_detected": int(coupled["detected"]),
            "coupled_score": coupled["score"],
            "scenario_step_fraction": round(step / STEPS_PER_EPISODE, 3),
            "scenario": scenario,
            "readiness_status": status,
        })

    return rows


def main():
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "degradation_dataset.csv")

    all_rows = []
    for scenario in SCENARIOS:
        for episode in range(EPISODES_PER_SCENARIO):
            all_rows.extend(run_episode(scenario, seed=hash((scenario, episode)) % (2**32)))

    fieldnames = FEATURE_COLUMNS + ["scenario", LABEL_COLUMN]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {out_path}")

    from collections import Counter
    label_counts = Counter(r[LABEL_COLUMN] for r in all_rows)
    print("Label distribution:", dict(label_counts))


if __name__ == "__main__":
    main()
