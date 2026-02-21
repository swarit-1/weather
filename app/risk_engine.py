"""Deterministic risk scoring engine."""

from app.schemas import WeatherSnapshot, DerivedScenario, RiskScores

ALERT_WEIGHTS = {
    "Tornado Warning": 60,
    "Flash Flood Warning": 50,
    "Severe Thunderstorm Warning": 40,
    "Heat Advisory": 30,
}


def _clamp(value: float) -> int:
    return int(max(0, min(100, value)))


def _get_alert_weight(snapshot: WeatherSnapshot) -> float:
    weight = 0.0
    for alert in snapshot.alerts:
        weight = max(weight, ALERT_WEIGHTS.get(alert.event, 0))
    return weight


def calculate_risk_scores(snapshot: WeatherSnapshot, scenario: DerivedScenario) -> RiskScores:
    """Calculate deterministic risk scores from weather data and derived scenario."""

    alert_weight = _get_alert_weight(snapshot)

    load_stress = (snapshot.heat_index * 0.6) + (snapshot.precipitation_probability * 0.1)
    outage_likelihood = (snapshot.wind_gust * 1.7) + alert_weight
    restoration_difficulty = (snapshot.wind_gust * 1.3) + (snapshot.precipitation_probability * 0.4)
    crew_urgency = outage_likelihood * 0.85
    public_safety_risk = (alert_weight * 1.5) + (snapshot.wind_gust * 0.7)

    return RiskScores(
        load_stress=_clamp(load_stress),
        outage_likelihood=_clamp(outage_likelihood),
        restoration_difficulty=_clamp(restoration_difficulty),
        crew_urgency=_clamp(crew_urgency),
        public_safety_risk=_clamp(public_safety_risk),
    )
