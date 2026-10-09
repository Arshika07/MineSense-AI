"""
Loads the Stage 8 trained model and turns a live reading into a prediction.
Falls back gracefully (feature-flagged as unavailable) if the model file
hasn't been trained yet, so the API never crashes because of this layer.
"""

import json
import os

import joblib
import numpy as np

MODEL_PATH = os.path.join("models", "degradation_model.pkl")
METRICS_PATH = os.path.join("models", "metrics.json")


class MLPredictor:
    def __init__(self):
        self.available = False
        self.model = None
        self.encoder = None
        self.feature_columns = []
        self.model_name = None
        self.test_accuracy = None
        self.feature_importances = {}

        self._load()

    def _load(self):
        try:
            bundle = joblib.load(MODEL_PATH)
            self.model = bundle["model"]
            self.encoder = bundle["encoder"]
            self.feature_columns = bundle["feature_columns"]
            self.model_name = bundle["model_name"]

            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH) as f:
                    metrics = json.load(f)
                self.test_accuracy = metrics.get("test_accuracy")
                self.feature_importances = metrics.get("feature_importances", {})

            self.available = True
        except Exception as e:
            print(f"[ml_predictor] Model not loaded yet ({e}). "
                  f"Run generate_dataset.py then train_model.py.")
            self.available = False

    def build_feature_vector(self, model_reading, anomaly_scores, fusion, coupled, scenario_step_fraction):
        row = {
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
            "scenario_step_fraction": scenario_step_fraction,
        }
        return [row[c] for c in self.feature_columns]

    def predict(self, model_reading, anomaly_scores, fusion, coupled, scenario_step_fraction=0.5):
        if not self.available:
            return {
                "available": False,
                "predicted_class": None,
                "confidence": None,
                "model_name": None,
                "test_accuracy": None,
                "top_features": [],
                "explanation": "ML model not trained yet. Run generate_dataset.py then train_model.py."
            }

        vector = np.array([self.build_feature_vector(
            model_reading, anomaly_scores, fusion, coupled, scenario_step_fraction
        )])

        proba = self.model.predict_proba(vector)[0]
        class_index = int(np.argmax(proba))
        predicted_class = self.encoder.inverse_transform([class_index])[0]
        confidence = round(float(proba[class_index]) * 100, 1)

        top_features = list(self.feature_importances.items())[:5]

        return {
            "available": True,
            "predicted_class": predicted_class,
            "confidence": confidence,
            "model_name": self.model_name,
            "test_accuracy": round(self.test_accuracy * 100, 1) if self.test_accuracy else None,
            "top_features": [{"name": n, "importance": round(v, 3)} for n, v in top_features],
            "explanation": (
                f"Gradient-boosted model trained on {self.model_name and 'the synthetic degradation dataset'} "
                f"predicts '{predicted_class}' with {confidence}% confidence, independent of the rule-based engine."
            )
        }
