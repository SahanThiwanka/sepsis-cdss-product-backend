def build_decision_support(
    calibrated_probability: float,
    ai_alert: bool,
    risk_level: str,
    clinical_rules: dict
) -> dict:
    sirs_positive = clinical_rules.get("sirs_positive", False)
    sirs_score = clinical_rules.get("sirs_score", 0)

    rationale = []

    if ai_alert:
        rationale.append("AI calibrated probability is above the alert threshold.")

    if sirs_positive:
        rationale.append("SIRS criteria are positive.")

    if sirs_score >= 3:
        rationale.append("Three or more SIRS criteria are present.")

    if ai_alert and sirs_positive:
        return {
            "final_alert": True,
            "priority": "high",
            "recommendation": (
                "High sepsis risk detected. Immediate clinical review is recommended."
            ),
            "rationale": rationale
        }

    if ai_alert and not sirs_positive:
        return {
            "final_alert": True,
            "priority": "moderate_high",
            "recommendation": (
                "AI model indicates high sepsis risk. Clinical review is recommended, "
                "even though SIRS criteria are not positive."
            ),
            "rationale": rationale
        }

    if risk_level == "moderate" and sirs_positive:
        rationale.append("AI risk is moderate and clinical rule screening is positive.")

        return {
            "final_alert": True,
            "priority": "moderate",
            "recommendation": (
                "Moderate AI risk with positive SIRS criteria. Review patient condition "
                "and continue close monitoring."
            ),
            "rationale": rationale
        }

    if not ai_alert and sirs_score >= 3:
        return {
            "final_alert": True,
            "priority": "moderate",
            "recommendation": (
                "SIRS score is high despite AI score being below threshold. "
                "Clinical review is recommended."
            ),
            "rationale": rationale
        }

    return {
        "final_alert": False,
        "priority": "low",
        "recommendation": (
            "No sepsis alert generated. Continue routine monitoring and reassess if "
            "patient condition changes."
        ),
        "rationale": rationale if rationale else ["AI and clinical rule thresholds were not met."]
    }