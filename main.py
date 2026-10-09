import json
import time

from simulator import SensorSimulator
from anomaly_detector import AnomalyDetector
from degradation_predictor import DegradationPredictor
from coupled_degradation import detect_coupled_degradation
from readiness_model import calculate_readiness


def main():
    simulator = SensorSimulator()
    detector = AnomalyDetector()
    predictor = DegradationPredictor()

    # Change this to test different situations:
    # normal, dust_buildup, vibration, coupled, recovery
    simulator.set_scenario("normal")

    print("\nMINING SENSOR PREDICTIVE DEGRADATION SYSTEM")
    print("=" * 55)

    try:
        while True:
            reading = simulator.generate_reading()

            anomaly_scores = detector.analyze(reading)

            predictions = {}

            for sensor in [
                "temperature",
                "dust",
                "motion",
                "ldr"
            ]:
                predictions[sensor] = predictor.predict(
                    sensor,
                    reading[sensor],
                    anomaly_scores[sensor]
                )

            coupled_result = detect_coupled_degradation(
                anomaly_scores,
                predictions
            )

            readiness = calculate_readiness(
                anomaly_scores,
                coupled_result
            )

            output = {
                "reading": reading,
                "anomaly_scores": anomaly_scores,
                "predictions": predictions,
                "coupled_degradation": coupled_result,
                "system_readiness": readiness
            }

            print(json.dumps(output, indent=2))
            print("-" * 55)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSystem stopped.")


if __name__ == "__main__":
    main()