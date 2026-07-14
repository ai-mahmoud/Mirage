from mirage_ai.demo import JIGGLE_END_MS, generate_demo_events
from mirage_ai.engine import SessionEngine


def test_insufficient_evidence_before_min_events():
    engine = SessionEngine(session_id="s1", started_at=0.0)
    snapshot = engine.tick(1_000.0)
    assert snapshot.recommendation.status == "evidence_insufficient"
    assert snapshot.confidence.evidence_confidence < 0.05


def test_demo_session_reaches_manual_review():
    engine = SessionEngine(session_id="s2", started_at=0.0, demo_mode=True, seed=7)
    early = None
    snapshot = None
    for t in range(1_000, int(JIGGLE_END_MS), 1_000):
        snapshot = engine.tick(float(t))
        if t == 20_000:
            early = snapshot
    assert early is not None and snapshot is not None
    # baseline behavior should have generated no negative evidence early on
    assert not any(e.polarity == "reduces_trust" for e in early.evidence)
    # the scripted jiggler should have dropped Trust DNA and produced evidence
    assert any(e.polarity == "reduces_trust" for e in snapshot.evidence)
    assert snapshot.trust_dna.overall < 70
    assert snapshot.recommendation.status in (
        "additional_observation_recommended",
        "manual_review_recommended",
    )


def test_report_includes_privacy_statement_and_history():
    engine = SessionEngine(session_id="s3", started_at=0.0, demo_mode=True, seed=1)
    for t in range(1_000, 45_000, 1_000):
        engine.tick(float(t))
    report = engine.finalize(45_000.0)
    assert report.privacy_statement
    assert len(report.trust_dna_history) > 1
    assert report.duration_ms == 45_000.0


def test_raw_event_rejects_unknown_fields():
    import pytest
    from pydantic import ValidationError

    from mirage_ai.schemas import RawEvent

    with pytest.raises(ValidationError):
        RawEvent(type="mouse_move", t=0.0, key="a")


def test_demo_events_are_deterministic():
    a = generate_demo_events(0.0, seed=42)
    b = generate_demo_events(0.0, seed=42)
    assert [e.t for e in a] == [e.t for e in b]
