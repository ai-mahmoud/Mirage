from mirage_ai.seed import PROFILES, TOTAL_SESSIONS, build_profiles, seed_sessions


def test_build_profiles_produces_exactly_one_live_session():
    profiles = build_profiles()
    live = [p for p in profiles if p["live"]]
    assert len(live) == 1
    assert live[0]["days_ago"] == 0


def test_build_profiles_is_deterministic():
    a = build_profiles()
    b = build_profiles()
    assert a == b


def test_build_profiles_ids_are_unique():
    profiles = build_profiles()
    ids = [p["session_id"] for p in profiles]
    assert len(ids) == len(set(ids)) == TOTAL_SESSIONS


def test_seed_sessions_populates_all_profiles():
    sessions: dict = {}
    seed_sessions(sessions)
    assert set(sessions.keys()) == {p["session_id"] for p in PROFILES}


def test_seed_sessions_is_idempotent():
    sessions: dict = {}
    seed_sessions(sessions)
    first = dict(sessions)
    seed_sessions(sessions)  # should be a no-op — never overwrite
    assert set(sessions.keys()) == set(first.keys())
    for key, engine in sessions.items():
        assert engine is first[key]  # same objects, not replaced


def test_seeded_sessions_have_a_final_snapshot_unless_live():
    sessions: dict = {}
    seed_sessions(sessions)
    for profile in PROFILES:
        engine = sessions[profile["session_id"]]
        if profile["live"]:
            assert engine.ended_at is None
        else:
            assert engine.ended_at is not None
            snapshot = engine.tick(engine.ended_at + 999_999.0)
            assert snapshot.status == "ended"


def test_seeded_trust_scores_span_multiple_bands():
    """Real-data honesty check: the natural-behavior generator caps out
    around ~65-73 (never "high"/"very-high"), but clean vs. jiggler
    archetypes should still land in genuinely different ranges."""
    sessions: dict = {}
    seed_sessions(sessions)
    overalls = [
        sessions[p["session_id"]].tick(sessions[p["session_id"]].started_at + p["duration_ms"]).trust_dna.overall
        for p in PROFILES
        if not p["live"]
    ]
    assert max(overalls) - min(overalls) > 30  # meaningfully varied, not clustered
    assert min(overalls) < 40  # severe_flag reaches "very-low"
    assert max(overalls) >= 60  # clean sessions reach "moderate"
