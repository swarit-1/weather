"""Deterministic trigger engine for scenario derivation."""

from app.schemas import WeatherSnapshot, DerivedScenario


def derive_scenario(snapshot: WeatherSnapshot) -> DerivedScenario:
    """Derive a single scenario from weather snapshot using deterministic rules."""

    alert_events = {a.event for a in snapshot.alerts}

    # --- Event type ---
    if "Tornado Warning" in alert_events:
        event_type = "CRITICAL"
    elif "Flash Flood Warning" in alert_events:
        event_type = "CRITICAL"
    elif "Severe Thunderstorm Warning" in alert_events:
        event_type = "STORM"
    elif snapshot.precipitation_probability > 70 and snapshot.wind_gust > 30:
        event_type = "STORM"
    elif snapshot.wind_gust > 35:
        event_type = "WIND"
    elif snapshot.heat_index > 105:
        event_type = "HEAT"
    else:
        event_type = "NORMAL"

    # --- Severity ---
    if "Tornado Warning" in alert_events or snapshot.wind_gust > 60:
        severity = "CRITICAL"
    elif (
        snapshot.wind_gust > 45
        or snapshot.heat_index > 110
        or "Severe Thunderstorm Warning" in alert_events
    ):
        severity = "HIGH"
    elif snapshot.wind_gust > 35 or snapshot.heat_index > 100:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # --- Confidence ---
    alert_based = event_type in ("CRITICAL",) and len(alert_events) > 0
    threshold_based = event_type in ("STORM", "WIND", "HEAT")

    if alert_based or (event_type == "STORM" and "Severe Thunderstorm Warning" in alert_events):
        confidence = 0.95
    elif threshold_based:
        confidence = 0.85
    else:
        confidence = 0.5

    # --- Trigger reason ---
    reasons = []
    if "Tornado Warning" in alert_events:
        reasons.append("Tornado Warning active")
    if "Flash Flood Warning" in alert_events:
        reasons.append("Flash Flood Warning active")
    if "Severe Thunderstorm Warning" in alert_events:
        reasons.append("Severe Thunderstorm Warning active")
    if snapshot.wind_gust > 35:
        reasons.append(f"Wind gust {snapshot.wind_gust} mph exceeds threshold")
    if snapshot.heat_index > 105:
        reasons.append(f"Heat index {snapshot.heat_index}°F exceeds threshold")
    if snapshot.precipitation_probability > 70:
        reasons.append(f"Precipitation probability {snapshot.precipitation_probability}% exceeds threshold")

    trigger_reason = "; ".join(reasons) if reasons else "No significant weather triggers detected"

    return DerivedScenario(
        event_type=event_type,
        severity=severity,
        confidence=confidence,
        trigger_reason=trigger_reason,
    )
