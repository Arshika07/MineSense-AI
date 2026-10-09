SENSOR_CONFIG = {
    "temperature": {
        "normal_min": 15,
        "normal_max": 45,
        "critical_max": 70,
        "direction": "high"
    },
    "dust": {
        "normal_min": 0,
        "normal_max": 300,
        "critical_max": 1000,
        "direction": "high"
    },
    "motion": {
        "normal_min": 0,
        "normal_max": 1,
        "critical_max": 1,
        "direction": "unstable"
    },
    "ldr": {
        "normal_min": 400,
        "normal_max": 1000,
        "critical_max": 1023,
        "direction": "low"
    }
}

DEGRADATION_THRESHOLD = 0.55
COUPLED_DEGRADATION_THRESHOLD = 0.60