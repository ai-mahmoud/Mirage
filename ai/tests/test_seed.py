from mirage_ai.seed import PROFILES, seed_sessions


def test_seed_sessions_populates_all_profiles():
    sessions: dict = {}
    seed_sessions(sessions)
    assert set(sessions.keys()) == {p[0] for p in PROFILES}


def test_seed_sessions_is_idempotent():
    sessions: dict = {}
    seed_sessions(sessions)
    first = dict(sessions)
    seed_sessions(sessions)  # should be a no-op — never overwrite
    assert sessions is not None
    assert set(sessions.keys()) == set(first.keys())
    for key, engine in sessions.items():
        assert engine is first[key]  # same objects, not replaced


def test_seeded_ended_sessions_have_a_final_snapshot():
    sessions: dict = {}
    seed_sessions(sessions)
    for session_id, _, _, _, _, _, _, outcome in PROFILES:
        engine = sessions[session_id]
        if outcome == "live":
            assert engine.ended_at is None
        else:
            assert engine.ended_at is not None
            snapshot = engine.tick(engine.ended_at + 999_999.0)
            assert snapshot.status == "ended"
