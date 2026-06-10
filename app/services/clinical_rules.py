from typing import Dict, Optional


def calculate_sirs_score(observation: Dict[str, Optional[float]]) -> dict:
    temp = observation.get("Temp")
    hr = observation.get("HR")
    resp = observation.get("Resp")
    wbc = observation.get("WBC")

    criteria = {
        "temperature": False,
        "heart_rate": False,
        "respiratory_rate": False,
        "wbc": False
    }

    if temp is not None:
        criteria["temperature"] = temp > 38.0 or temp < 36.0

    if hr is not None:
        criteria["heart_rate"] = hr > 90

    if resp is not None:
        criteria["respiratory_rate"] = resp > 20

    if wbc is not None:
        criteria["wbc"] = wbc > 12 or wbc < 4

    sirs_score = sum(criteria.values())

    return {
        "sirs_score": sirs_score,
        "sirs_positive": sirs_score >= 2,
        "criteria": criteria
    }