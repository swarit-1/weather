"""Weather → DerivedScenario mapping (deterministic)."""

from app.core.models import DerivedScenario, WeatherSnapshot

CRITICAL_EVENTS = {
    "Tornado Warning",
    "Severe Thunderstorm Warning",
    "Flash Flood Warning",
}
THUNDERSTORM_KEYWORDS = ("thunderstorm", "thunder")


def derive_scenario(snapshot: WeatherSnapshot) -> DerivedScenario:
    """
    Map WeatherSnapshot to a single DerivedScenario.
    Deterministic and transparent trigger logic.
    """
    event_type = "normal"
    severity_level = "low"
    trigger_reason = "No significant weather triggers."
    confidence_score = 0.0

    alerts_events = {
        (a.get("event") or "").strip()
        for a in (snapshot.alerts or [])
    }
    has_tornado = any("Tornado" in e for e in alerts_events)
    has_severe_thunderstorm = any("Severe Thunderstorm" in e for e in alerts_events)
    has_flash_flood = any("Flash Flood" in e for e in alerts_events)
    has_thunderstorm_alert = any(
        any(kw in (a.get("event") or "").lower() for kw in THUNDERSTORM_KEYWORDS)
        for a in (snapshot.alerts or [])
    )

    # Critical: Tornado / Severe Thunderstorm / Flash Flood warnings
    if has_tornado:
        return DerivedScenario(
            event_type="critical",
            severity_level="critical",
            trigger_reason="Tornado Warning active.",
            confidence_score=1.0,
        )
    if has_severe_thunderstorm:
        return DerivedScenario(
            event_type="critical",
            severity_level="critical",
            trigger_reason="Severe Thunderstorm Warning active.",
            confidence_score=1.0,
        )
    if has_flash_flood:
        return DerivedScenario(
            event_type="critical",
            severity_level="critical",
            trigger_reason="Flash Flood Warning active.",
            confidence_score=1.0,
        )

    # Storm: precip > 60% and thunderstorm alert
    precip = snapshot.precipitation_probability
    if precip is not None and precip > 60 and has_thunderstorm_alert:
        return DerivedScenario(
            event_type="storm",
            severity_level="medium",
            trigger_reason=f"High precipitation ({precip:.0f}%) with thunderstorm activity.",
            confidence_score=0.85,
        )

    # High wind (wind_gust)
    gust = snapshot.wind_gust
    if gust is not None:
        if gust > 60:
            return DerivedScenario(
                event_type="wind",
                severity_level="critical",
                trigger_reason=f"Wind gust {gust:.0f} mph exceeds 60 mph.",
                confidence_score=1.0,
            )
        if gust > 45:
            return DerivedScenario(
                event_type="wind",
                severity_level="high",
                trigger_reason=f"Wind gust {gust:.0f} mph exceeds 45 mph.",
                confidence_score=0.95,
            )
        if gust > 35:
            return DerivedScenario(
                event_type="wind",
                severity_level="medium",
                trigger_reason=f"Wind gust {gust:.0f} mph exceeds 35 mph.",
                confidence_score=0.9,
            )

    # Extreme heat (heat_index)
    hi = snapshot.heat_index
    if hi is not None:
        if hi > 110:
            return DerivedScenario(
                event_type="heat",
                severity_level="critical",
                trigger_reason=f"Heat index {hi:.0f}°F exceeds 110°F.",
                confidence_score=1.0,
            )
        if hi > 105:
            return DerivedScenario(
                event_type="heat",
                severity_level="high",
                trigger_reason=f"Heat index {hi:.0f}°F exceeds 105°F.",
                confidence_score=0.95,
            )
        if hi > 100:
            return DerivedScenario(
                event_type="heat",
                severity_level="medium",
                trigger_reason=f"Heat index {hi:.0f}°F exceeds 100°F.",
                confidence_score=0.9,
            )

    return DerivedScenario(
        event_type="normal",
        severity_level="low",
        trigger_reason="No significant weather triggers.",
        confidence_score=0.7,
    )
