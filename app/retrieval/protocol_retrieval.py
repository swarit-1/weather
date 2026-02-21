"""
Production retrieval: RiskAnalysisOutput → metadata filter → cosine ranking → ContextBundle.
Uses existing embed() and vector DB; no severity/risk computation in this module.
"""

from typing import Dict, List, Optional, Tuple, Callable

from app.retrieval.rag_schema import (
    RiskAnalysisOutput,
    ContextBundle,
    RAGSnippet,
    VectorRecord,
    SeverityLevel,
    RoleTag,
    SEVERITY_RANK,
    vector_record_to_snippet,
)

# Alert keywords for optional score bonus (not a hard filter)
ALERT_BONUS_KEYWORDS = frozenset(
    {"warning", "watch", "advisory", "evacuation", "emergency"}
)
ALERT_BONUS_DELTA = 0.02


# --- 1) Severity order helper ---

def severity_to_int(level: SeverityLevel) -> int:
    """Map severity to comparable int: low=0, medium=1, high=2, critical=3."""
    return SEVERITY_RANK.get(level, 0)


def severity_ge(a: SeverityLevel, b: SeverityLevel) -> bool:
    """True iff a >= b in severity order (low < medium < high < critical)."""
    return severity_to_int(a) >= severity_to_int(b)


# --- 2) Build query text for embedding ---

def build_query_text(ra: RiskAnalysisOutput) -> str:
    """
    Compact, information-dense query string for embedding.
    Uses only: derived_scenario, forecast_summary, top_risk_driver, and 1–2 key numerics by event_type.
    """
    ds = ra.derived_scenario
    ws = ra.weather_snapshot
    parts = [
        f"event_type={ds.event_type} severity={ds.severity_level}",
        ds.trigger_reason,
        ws.forecast_summary,
        f"top_risk_driver={ra.top_risk_driver}",
    ]
    if ds.event_type == "heat":
        parts.append(f"heat_index={ws.heat_index} temperature={ws.temperature}")
    elif ds.event_type == "wind":
        parts.append(f"wind_gust={ws.wind_gust} wind_speed={ws.wind_speed}")
    elif ds.event_type == "storm":
        parts.append(f"precipitation_probability={ws.precipitation_probability}")
        if ws.alerts:
            parts.append(" ".join(a.headline for a in ws.alerts[:2]))
    elif ds.event_type == "critical" and ws.alerts:
        for a in ws.alerts[:2]:
            parts.append(f"alert: {a.event} {a.severity} {a.headline}")
    return " ".join(str(p) for p in parts if p)


# --- 3) Select roles from RiskAnalysisOutput ---

def select_roles(ra: RiskAnalysisOutput) -> List[RoleTag]:
    """
    Deterministic role selection from risk_scores and top_risk_driver.
    Returns at least one role; default to grid_ops if none selected.
    """
    rs = ra.risk_scores
    driver = (ra.top_risk_driver or "").strip().lower()
    max_any = max(
        rs.load_stress,
        rs.outage_likelihood,
        rs.restoration_difficulty,
        rs.crew_urgency,
        rs.public_safety_risk,
    )
    roles: List[RoleTag] = []
    if driver == "load_stress" or rs.load_stress == max_any:
        roles.append("grid_ops")
    if driver in ("crew_urgency", "restoration_difficulty") or rs.crew_urgency == max_any or rs.restoration_difficulty == max_any:
        roles.append("field_ops")
    if driver == "public_safety_risk" or rs.public_safety_risk == max_any:
        roles.append("comms")
    if not roles:
        roles.append("grid_ops")
    return roles


# --- 4) Metadata filter with fallbacks ---

def _record_has_alert_keywords(record: VectorRecord) -> bool:
    text = " ".join(
        (record.tags.keywords or []) + [record.title, record.text[:300]]
    ).lower()
    return any(kw in text for kw in ALERT_BONUS_KEYWORDS)


def metadata_filter(
    records: List[VectorRecord],
    ra: RiskAnalysisOutput,
    desired_role: RoleTag,
) -> List[VectorRecord]:
    """
    Deterministic filter:
    - ra.derived_scenario.event_type in record.tags.event_types
    - ra.derived_scenario.severity_level >= record.tags.severity_min
    - Role: if desired_role == "general" then record.tags.role_tag == "general";
      else record.tags.role_tag in {desired_role, "general"}

    Fallback order if eligible is empty:
    1) Allow records whose event_types include "critical"
    2) Allow records whose event_types include "normal"
    Severity filtering is kept intact in fallbacks.
    """
    ds = ra.derived_scenario
    event_type = ds.event_type
    severity_level = ds.severity_level

    def passes_role(r: VectorRecord) -> bool:
        if desired_role == "general":
            return r.tags.role_tag == "general"
        return r.tags.role_tag == desired_role or r.tags.role_tag == "general"

    def passes_severity(r: VectorRecord) -> bool:
        return severity_ge(severity_level, r.tags.severity_min)

    # Primary: exact event_type match
    eligible = [
        r for r in records
        if event_type in r.tags.event_types and passes_severity(r) and passes_role(r)
    ]
    if eligible:
        return eligible

    # Fallback 1: accept records tagged for critical events (broader relevance)
    eligible = [
        r for r in records
        if "critical" in r.tags.event_types and passes_severity(r) and passes_role(r)
    ]
    if eligible:
        return eligible

    # Fallback 2: accept records tagged with normal (keep severity intact)
    eligible = [
        r for r in records
        if "normal" in r.tags.event_types and passes_severity(r) and passes_role(r)
    ]
    return eligible


# --- 5) Retrieve top-k by cosine + optional alert bonus ---

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    import numpy as np
    va = np.asarray(a, dtype=float)
    vb = np.asarray(b, dtype=float)
    dot = float(np.dot(va, vb))
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    return dot / (na * nb) if na > 0 and nb > 0 else 0.0


def retrieve_top_k(
    records: List[VectorRecord],
    query_embedding: List[float],
    k: int,
    ra: RiskAnalysisOutput,
) -> List[Tuple[VectorRecord, float]]:
    """
    Rank by cosine similarity; add small alert bonus (+0.02) when alerts present
    and record has alert-like keywords. Return top k (record, score) pairs.
    """
    if not records:
        return []
    has_alerts = bool(ra.weather_snapshot.alerts)
    scored = []
    for r in records:
        score = _cosine_similarity(query_embedding, r.embedding)
        if has_alerts and _record_has_alert_keywords(r):
            score += ALERT_BONUS_DELTA
        scored.append((r, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# --- 6) Map record to RAGSnippet ---

def record_to_ragsnippet(record: VectorRecord, relevance_score: float) -> RAGSnippet:
    """Map VectorRecord to RAGSnippet (id, title, url, text, relevance_score, role_tag)."""
    return vector_record_to_snippet(record, relevance_score)


# --- Main: RiskAnalysisOutput → ContextBundle ---

def retrieve_protocol_snippets_from_risk(
    ra: RiskAnalysisOutput,
    get_records: Callable[[], List[VectorRecord]],
    embed: Callable[[str], List[float]],
    top_k_general: int = 4,
    top_k_per_role: int = 3,
) -> ContextBundle:
    """
    Deterministic metadata filter + cosine ranking; returns ContextBundle with
    general_snippets and role_specific_snippets (RAGSnippet lists).
    """
    query_text = build_query_text(ra)
    query_embedding = embed(query_text)
    records = get_records()

    # General snippets: desired_role="general", filter, rank, top_k_general
    eligible_general = metadata_filter(records, ra, "general")
    general_scored = retrieve_top_k(eligible_general, query_embedding, top_k_general, ra)
    general_snippets = [record_to_ragsnippet(r, s) for r, s in general_scored]

    # Role-specific: select_roles(ra), then per-role filter + top_k_per_role, merge and de-dupe by id
    roles = select_roles(ra)
    role_snippet_by_id: dict[str, RAGSnippet] = {}
    for role in roles:
        eligible = metadata_filter(records, ra, role)
        scored = retrieve_top_k(eligible, query_embedding, top_k_per_role, ra)
        for r, s in scored:
            existing = role_snippet_by_id.get(r.id)
            if existing is None or s > existing.relevance_score:
                role_snippet_by_id[r.id] = record_to_ragsnippet(r, s)
    role_specific_snippets = list(role_snippet_by_id.values())
    role_specific_snippets.sort(key=lambda x: x.relevance_score, reverse=True)

    return ContextBundle(
        weather_snapshot=ra.weather_snapshot,
        derived_scenario=ra.derived_scenario,
        risk_scores=ra.risk_scores,
        general_snippets=general_snippets,
        role_specific_snippets=role_specific_snippets,
    )


# --- Format RAG context for LLM (playbook_context) ---

def format_snippets_for_llm(snippets: List[RAGSnippet], max_chars: Optional[int] = None) -> str:
    """
    Turn a list of RAGSnippet into a single string for LLM prompts (e.g. playbook_context).
    Each snippet is rendered as title, url, and text; optional max_chars truncates the total.
    """
    parts = []
    for s in snippets:
        parts.append(f"[{s.role_tag}] {s.title}\n  URL: {s.url}\n  {s.text.strip()}")
    out = "\n\n---\n\n".join(parts)
    if max_chars and len(out) > max_chars:
        out = out[:max_chars].rsplit("\n", 1)[0] + "\n...[truncated]"
    return out


def context_bundle_to_playbook_context(bundle: ContextBundle, max_chars: Optional[int] = 8000) -> str:
    """
    Build a single playbook_context string (shared by all agents).
    Merges general_snippets and role_specific_snippets (by id, keep higher score), then formats.
    """
    merged = merge_rag_evidence(bundle.general_snippets, bundle.role_specific_snippets, k_total=20)
    return format_snippets_for_llm(merged, max_chars=max_chars)


def context_bundle_to_playbook_context_per_role(
    bundle: ContextBundle,
    max_chars_per_role: Optional[int] = 6000,
) -> Dict[str, str]:
    """
    Build a separate playbook_context for each agent role (grid_ops, field_ops, comms).
    Each agent receives only snippets where role_tag matches that role or "general".
    Returns dict with keys "grid_ops", "field_ops", "comms"; each value is a string for that agent's context window.
    """
    merged = merge_rag_evidence(bundle.general_snippets, bundle.role_specific_snippets, k_total=30)
    out: Dict[str, str] = {}
    for role in ("grid_ops", "field_ops", "comms"):
        role_snippets = [s for s in merged if s.role_tag == role or s.role_tag == "general"]
        out[role] = format_snippets_for_llm(role_snippets, max_chars=max_chars_per_role)
    return out


# --- Optional: merge and set rag_evidence ---

def merge_rag_evidence(
    general_snippets: List[RAGSnippet],
    role_specific_snippets: List[RAGSnippet],
    k_total: int = 8,
) -> List[RAGSnippet]:
    """
    Merge general and role_specific, de-duplicate by id (keep highest relevance_score),
    return top k_total by relevance_score.
    """
    by_id: dict[str, RAGSnippet] = {}
    for s in general_snippets + role_specific_snippets:
        existing = by_id.get(s.id)
        if existing is None or s.relevance_score > existing.relevance_score:
            by_id[s.id] = s
    merged = sorted(by_id.values(), key=lambda x: x.relevance_score, reverse=True)
    return merged[:k_total]


def set_rag_evidence_from_bundle(
    ra: RiskAnalysisOutput,
    bundle: ContextBundle,
    k_total: int = 8,
) -> RiskAnalysisOutput:
    """Set ra.rag_evidence from bundle's general + role_specific (merged, top k_total)."""
    ra.rag_evidence = merge_rag_evidence(
        bundle.general_snippets,
        bundle.role_specific_snippets,
        k_total=k_total,
    )
    return ra


# --- Demo (no external calls) ---

def _demo_mock_embed(dim: int = 1536):
    """Return a mock embed function that returns deterministic vectors (no API)."""
    def _embed(text: str) -> List[float]:
        # Deterministic from text hash so query vs record similarity is stable
        h = hash(text) % 10000
        return [0.01 * ((h + i) % 100) / 100.0 for i in range(dim)]
    return _embed


def _demo_records() -> List[VectorRecord]:
    """Example VectorRecords: heat/grid_ops, wind/field_ops, storm/comms, general."""
    from app.retrieval.rag_schema import VectorRecordTags
    dim = 1536
    def vec(seed: int) -> List[float]:
        return [0.01 * ((seed + i) % 100) / 100.0 for i in range(dim)]
    return [
        VectorRecord(
            id="heat-grid-1",
            title="Heat load management procedures",
            url="https://example.com/heat-grid",
            text="During extreme heat reduce non-essential load and monitor transformer temperatures.",
            embedding=vec(1),
            tags=VectorRecordTags(
                event_types=["heat", "critical"],
                severity_min="medium",
                role_tag="grid_ops",
                keywords=["heat", "load", "warning"],
            ),
        ),
        VectorRecord(
            id="wind-field-1",
            title="Field ops wind safety",
            url="https://example.com/wind-field",
            text="When wind gusts exceed 40 mph suspend elevated work and secure equipment.",
            embedding=vec(2),
            tags=VectorRecordTags(
                event_types=["wind", "storm"],
                severity_min="high",
                role_tag="field_ops",
                keywords=["wind", "advisory", "safety"],
            ),
        ),
        VectorRecord(
            id="storm-comms-1",
            title="Storm public communications",
            url="https://example.com/storm-comms",
            text="Issue public advisory for severe storms and evacuation if needed.",
            embedding=vec(3),
            tags=VectorRecordTags(
                event_types=["storm", "critical"],
                severity_min="high",
                role_tag="comms",
                keywords=["storm", "advisory", "evacuation", "emergency"],
            ),
        ),
        VectorRecord(
            id="general-heat-1",
            title="General heat advisory guidance",
            url="https://example.com/general",
            text="Stay hydrated and limit outdoor exposure during heat advisories.",
            embedding=vec(4),
            tags=VectorRecordTags(
                event_types=["normal", "heat"],
                severity_min="low",
                role_tag="general",
                keywords=["heat", "advisory"],
            ),
        ),
    ]


def _demo_risk_output(
    event_type: str,
    severity_level: str,
    heat_index: float = 0.0,
    temperature: float = 0.0,
    wind_gust: float = 0.0,
    wind_speed: float = 0.0,
    precipitation_probability: float = 0.0,
    load_stress: int = 0,
    crew_urgency: int = 0,
    outage_likelihood: int = 0,
    public_safety_risk: int = 0,
    restoration_difficulty: int = 0,
    top_risk_driver: str = "load_stress",
    alerts_headlines: Optional[List[str]] = None,
) -> RiskAnalysisOutput:
    """Build a RiskAnalysisOutput for demo (datetime from app.retrieval.rag_schema)."""
    from datetime import datetime
    from app.retrieval.rag_schema import Alert, WeatherSnapshot, DerivedScenario, RiskScores
    alerts = []
    if alerts_headlines:
        for h in alerts_headlines:
            alerts.append(Alert(
                event="Event",
                severity="High",
                headline=h,
                description="",
                effective=datetime(2025, 7, 1, 12, 0),
                expires=datetime(2025, 7, 1, 20, 0),
            ))
    return RiskAnalysisOutput(
        zip="90210",
        weather_snapshot=WeatherSnapshot(
            zip="90210",
            latitude=34.05,
            longitude=-118.25,
            temperature=temperature,
            wind_speed=wind_speed,
            wind_gust=wind_gust,
            precipitation_probability=precipitation_probability,
            heat_index=heat_index,
            alerts=alerts,
            forecast_summary="Hot and dry." if event_type == "heat" else "Windy and stormy.",
            timestamp=datetime(2025, 7, 1, 12, 0),
        ),
        derived_scenario=DerivedScenario(
            event_type=event_type,
            severity_level=severity_level,
            trigger_reason="Demo trigger",
            confidence_score=0.9,
        ),
        risk_scores=RiskScores(
            load_stress=load_stress,
            outage_likelihood=outage_likelihood,
            restoration_difficulty=restoration_difficulty,
            crew_urgency=crew_urgency,
            public_safety_risk=public_safety_risk,
        ),
        top_risk_driver=top_risk_driver,
        rag_evidence=[],
    )


def demo_protocol_retrieval() -> None:
    """
    Demo: two RiskAnalysisOutput examples (heat high / wind critical), mock records and embed.
    Prints snippet id, title, role_tag, relevance_score for general and role_specific.
    No external API calls.
    """
    records = _demo_records()
    embed = _demo_mock_embed()
    get_records = lambda: records

    # Example 1: heat high, heat_index ~ 108, load_stress high, top_risk_driver load_stress
    ra1 = _demo_risk_output(
        event_type="heat",
        severity_level="high",
        heat_index=108.0,
        temperature=102.0,
        load_stress=85,
        crew_urgency=40,
        outage_likelihood=50,
        public_safety_risk=45,
        restoration_difficulty=40,
        top_risk_driver="load_stress",
    )
    bundle1 = retrieve_protocol_snippets_from_risk(
        ra1, get_records, embed, top_k_general=4, top_k_per_role=3
    )
    print("--- Example 1: heat high, top_risk_driver=load_stress ---")
    print("general_snippets:")
    for s in bundle1.general_snippets:
        print(f"  id={s.id} title={s.title!r} role_tag={s.role_tag} relevance_score={s.relevance_score:.4f}")
    print("role_specific_snippets:")
    for s in bundle1.role_specific_snippets:
        print(f"  id={s.id} title={s.title!r} role_tag={s.role_tag} relevance_score={s.relevance_score:.4f}")

    # Example 2: wind critical, wind_gust ~ 75, crew_urgency high, top_risk_driver crew_urgency
    ra2 = _demo_risk_output(
        event_type="wind",
        severity_level="critical",
        wind_gust=75.0,
        wind_speed=55.0,
        load_stress=50,
        crew_urgency=90,
        outage_likelihood=70,
        public_safety_risk=60,
        restoration_difficulty=85,
        top_risk_driver="crew_urgency",
    )
    bundle2 = retrieve_protocol_snippets_from_risk(
        ra2, get_records, embed, top_k_general=4, top_k_per_role=3
    )
    print("\n--- Example 2: wind critical, top_risk_driver=crew_urgency ---")
    print("general_snippets:")
    for s in bundle2.general_snippets:
        print(f"  id={s.id} title={s.title!r} role_tag={s.role_tag} relevance_score={s.relevance_score:.4f}")
    print("role_specific_snippets:")
    for s in bundle2.role_specific_snippets:
        print(f"  id={s.id} title={s.title!r} role_tag={s.role_tag} relevance_score={s.relevance_score:.4f}")

    # Optional: set rag_evidence on ra and show merged top-4
    set_rag_evidence_from_bundle(ra1, bundle1, k_total=4)
    print("\n--- ra1.rag_evidence (merged top 4) ---")
    for s in ra1.rag_evidence:
        print(f"  id={s.id} title={s.title!r} role_tag={s.role_tag} relevance_score={s.relevance_score:.4f}")


if __name__ == "__main__":
    demo_protocol_retrieval()
