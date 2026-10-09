from flask import Flask, jsonify
from flask_cors import CORS

from simulator import SensorSimulator
from anomaly_detector import AnomalyDetector
from degradation_predictor import DegradationPredictor
from coupled_degradation import detect_coupled_degradation
from readiness_model import calculate_readiness
from perception_simulator import PerceptionSimulator
from sensor_fusion import calculate_perception_fusion
from recovery_engine import RecoveryEngine
from esp32_serial import ESP32SerialReader
from ml_predictor import MLPredictor

app = Flask(__name__)
CORS(app)

simulator = SensorSimulator()
detector = AnomalyDetector()
predictor = DegradationPredictor()
perception_simulator = PerceptionSimulator()
recovery_engine = RecoveryEngine()
ml_predictor = MLPredictor()
scenario_step_counter = 0

# The ESP32 environmental stream is real hardware data.
# Camera/LiDAR/Radar remain synthetic perception data for the prototype.
esp32_reader = ESP32SerialReader(port="COM7", baud_rate=115200)

current_scenario = "coupled"

VALID_SCENARIOS = [
    "normal", "dust_buildup", "vibration", "coupled", "fog",
    "camera_failure", "lidar_failure", "radar_interference", "recovery"
]


def build_environmental_reading():
    """
    Convert the ESP32 JSON schema into the four environmental signals
    expected by the existing MineSense AI models.

    motion is derived from acceleration magnitude:
    ~1 g at rest -> ~0 vibration, while deviation from 1 g increases
    the normalized vibration signal.

    The LM393 module is digital-only in this build, so it is used as a
    light/dark proxy for the existing LDR feature.
    """
    raw = esp32_reader.read_latest()

    if raw is not None:
        acceleration = float(raw.get("acceleration", 1.0))
        lm393_state = int(raw.get("lm393_state", 1))

        return {
            "timestamp": raw.get("timestamp"),
            "temperature": round(float(raw.get("temperature", 0)), 2),
            "dust": round(float(raw.get("dust_density", 0)), 2),
            "motion": round(min(1.0, abs(acceleration - 1.0)), 3),
            "ldr": 200 if lm393_state == 0 else 850,
            "_source": "REAL ESP32"
        }, raw

    # If the ESP32 is temporarily unavailable, keep the dashboard usable
    # and make the fallback explicit instead of pretending it is hardware.
    fallback = simulator.generate_reading()
    fallback["_source"] = "SIMULATED - ESP32 DISCONNECTED"
    return fallback, None


def analyze_current_reading():
    reading, esp32_raw = build_environmental_reading()

    # _source is metadata, not an AI sensor feature.
    model_reading = {
        key: value for key, value in reading.items()
        if not key.startswith("_")
    }

    perception = perception_simulator.generate_reading()
    anomaly_scores = detector.analyze(model_reading)

    predictions = {
        sensor: predictor.predict(
            sensor,
            model_reading[sensor],
            anomaly_scores[sensor]
        )
        for sensor in ["temperature", "dust", "motion", "ldr"]
    }

    coupled_result = detect_coupled_degradation(
        anomaly_scores,
        predictions
    )

    fusion = calculate_perception_fusion(perception)
    perception_scores = fusion["degradation_scores"]
    degraded_perception = [
        sensor for sensor, value in perception_scores.items()
        if value >= 0.55
    ]

    if len(degraded_perception) >= 2:
        coupled_result["detected"] = True
        coupled_result["level"] = (
            "HIGH" if len(degraded_perception) == 3 else "MEDIUM"
        )
        coupled_result["affected_sensors"] = list(dict.fromkeys(
            coupled_result["affected_sensors"] + degraded_perception
        ))
        coupled_result["score"] = round(
            sum(
                perception_scores[sensor]
                for sensor in degraded_perception
            ) / len(degraded_perception),
            3
        )
        coupled_result["explanation"] = (
            "Multiple perception channels are degrading together. "
            "Environmental and vehicle-condition signals should be "
            "checked for the underlying cause."
        )

    readiness = calculate_readiness(anomaly_scores, coupled_result)
    readiness["readiness_score"] = round(max(
        0,
        readiness["readiness_score"]
        - max(0, 100 - fusion["fused_perception_confidence"]) * 0.35
    ), 1)

    score = readiness["readiness_score"]
    readiness["status"] = (
        "READY" if score >= 80 else
        "LIMITED" if score >= 60 else
        "DEGRADED" if score >= 40 else
        "CRITICAL"
    )

    recovery = recovery_engine.analyze(
        readiness["readiness_score"],
        current_scenario
    )

    # STAGE 8 / 11: independent ML prediction, computed from the same live
    # feature set as the rule engine, so the two can be compared side by
    # side for the judges.
    global scenario_step_counter
    scenario_step_counter += 1
    step_fraction = min(1.0, (scenario_step_counter % 30) / 30)
    ml_insight = ml_predictor.predict(
        model_reading, anomaly_scores, fusion, coupled_result, step_fraction
    )

    # Keep the AI models' expected reading clean, but expose the complete
    # real ESP32 packet so the dashboard/API can show the hardware values.
    return {
        "scenario": current_scenario,
        "ml_insight": ml_insight,
        "data_sources": {
            "environmental": reading["_source"],
            "camera": "SIMULATED",
            "lidar": "SIMULATED",
            "radar": "SIMULATED"
        },
        "reading": model_reading,
        "esp32_raw": esp32_raw,
        "perception": perception,
        "perception_fusion": fusion,
        "anomaly_scores": anomaly_scores,
        "predictions": predictions,
        "coupled_degradation": coupled_result,
        "system_readiness": readiness,
        "recovery": recovery
    }


@app.route("/")
def home():
    return jsonify({
        "message": "MineSense AI Predictive Perception Health API",
        "status": "running",
        "esp32_port": "COM7"
    })


@app.route("/api/data")
def get_data():
    return jsonify(analyze_current_reading())


@app.route("/api/scenario/<scenario>")
def change_scenario(scenario):
    global current_scenario

    if scenario not in VALID_SCENARIOS:
        return jsonify({
            "error": "Invalid scenario",
            "valid_scenarios": VALID_SCENARIOS
        }), 400

    global scenario_step_counter
    current_scenario = scenario
    scenario_step_counter = 0
    # Scenarios continue to control the synthetic perception channels.
    # Real ESP32 environmental values are never silently overwritten.
    perception_simulator.set_scenario(scenario)
    recovery_engine.history.clear()

    # Reset the simulated environmental fallback only.
    simulator.set_scenario(scenario)

    return jsonify({
        "message": "Scenario changed",
        "scenario": scenario
    })


if __name__ == "__main__":
    simulator.set_scenario(current_scenario)
    perception_simulator.set_scenario(current_scenario)

    # Important: Flask debug/reloader can open the COM port twice.
    # Keep it off so the ESP32 has one serial owner.
    esp32_reader.connect()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
