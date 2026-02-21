"""Deterministic risk scoring 0–100 from WeatherSnapshot and DerivedScenario."""

from app.core.models import DerivedScenario, RiskScores, WeatherSnapshot


def compute_risk_scores(snapshot: WeatherSnapshot, scenario: DerivedScenario) -> RiskScores:
    """
    Purely deterministic RiskScores (0–100).
    No LLM.
    """
    load_stress = _score_load_stress(snapshot)
    outage_likelihood = _score_outage_likelihood(snapshot, scenario)
    restoration_difficulty = _score_restoration_difficulty(snapshot, scenario)
    public_safety_risk = _score_public_safety(snapshot, scenario)
    crew_urgency = max(outage_likelihood, public_safety_risk)

    return RiskScores(
        load_stress=round(load_stress, 1),
        outage_likelihood=round(outage_likelihood, 1),
        restoration_difficulty=round(restoration_difficulty, 1),
        crew_urgency=round(crew_urgency, 1),
        public_safety_risk=round(public_safety_risk, 1),
    )


def _is_nighttime(snapshot: WeatherSnapshot) -> bool:
    ts = snapshot.timestamp
    if ts is None:
        return False
    hour = ts.hour
    return hour < 6 or hour >= 19


def _score_load_stress(snapshot: WeatherSnapshot) -> float:
    base = 20.0
    hi = snapshot.heat_index
    if hi is not None:
        if hi >= 110:
            base = 85
        elif hi >= 105:
            base = 70
        elif hi >= 100:
            base = 55
        elif hi >= 95:
            base = 45
        elif hi >= 90:
            base = 35
    if _is_nighttime(snapshot):
        base = max(0, base - 25)
    return min(100.0, base)


def _score_outage_likelihood(snapshot: WeatherSnapshot, scenario: DerivedScenario) -> float:
    score = 15.0
    gust = snapshot.wind_gust
    if gust is not None:
        if gust >= 60:
            score += 55
        elif gust >= 45:
            score += 40
        elif gust >= 35:
            score += 25
        elif gust >= 25:
            score += 15
    if scenario.event_type == "storm":
        score += 25
    if scenario.event_type == "critical":
        score = max(score, 80)
    return min(100.0, score)


def _score_restoration_difficulty(snapshot: WeatherSnapshot, scenario: DerivedScenario) -> float:
    score = 10.0
    gust = snapshot.wind_gust
    if gust is not None:
        if gust >= 45:
            score += 40
        elif gust >= 35:
            score += 25
    if scenario.event_type == "storm":
        score += 30
    if scenario.event_type == "critical":
        score = max(score, 75)
    return min(100.0, score)


def _score_public_safety(snapshot: WeatherSnapshot, scenario: DerivedScenario) -> float:
    if scenario.severity_level == "critical":
        return 85.0
    if scenario.severity_level == "high":
        return 65.0
    if scenario.severity_level == "medium":
        return 45.0
    for a in snapshot.alerts or []:
        sev = (a.get("severity") or "").lower()
        if sev == "extreme":
            return 90.0
        if sev == "severe":
            return 70.0
    return 20.0
