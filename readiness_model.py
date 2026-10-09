def calculate_readiness(anomaly_scores, coupled_result):
    average_degradation = sum(
        anomaly_scores.values()
    ) / len(anomaly_scores)

    coupled_penalty = 0.0

    if coupled_result["detected"]:
        coupled_penalty = coupled_result["score"] * 0.25

    readiness = 1.0 - average_degradation - coupled_penalty
    readiness = max(0.0, min(1.0, readiness))

    if readiness >= 0.80:
        status = "READY"
    elif readiness >= 0.60:
        status = "LIMITED"
    elif readiness >= 0.40:
        status = "DEGRADED"
    else:
        status = "CRITICAL"

    return {
        "readiness_score": round(readiness * 100, 1),
        "status": status
    }