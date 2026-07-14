import os

from mirage_backend.pdf_service import (
    build_evidence_table,
    build_header_table,
    evidence_rows,
    fmt_ms,
    header_rows,
    render_report,
    trust_dna_rows,
)

SAMPLE_REPORT = {
    "sessionId": "s1",
    "candidateName": "Ada",
    "observerName": "Bob",
    "position": None,
    "department": None,
    "interviewType": "Technical Interview",
    "startedAt": 0.0,
    "endedAt": 60_000.0,
    "durationMs": 60_000.0,
    "generatedAt": 60_000.0,
    "executiveSummary": "Summary text.",
    "trustDna": {
        "overall": 71.2,
        "dimensions": [
            {"id": "behavioral_consistency", "label": "Behavioral Consistency", "score": 70.0, "confidence": 1.0, "trend": "down"}
        ],
    },
    "trustDnaHistory": [],
    "confidence": {"evidenceConfidence": 0.8, "recommendationConfidence": 0.7, "drivers": []},
    "recommendation": {
        "status": "continue_monitoring",
        "label": "Continue Monitoring",
        "reasons": [],
        "suggestedAction": "No action needed.",
        "humanReviewRequired": False,
    },
    "evidence": [
        {
            "id": "EV-1",
            "category": "attention",
            "title": "Attention shift",
            "description": "desc",
            "severity": "medium",
            "polarity": "reduces_trust",
            "confidence": 0.6,
            "timestamp": 1_000.0,
        }
    ],
    "timeline": [],
    "privacyStatement": ["No keystroke content was collected."],
}


def test_fmt_ms_renders_epoch_zero():
    assert fmt_ms(0) == "1970-01-01 00:00"


def test_header_rows_includes_candidate_and_session_id():
    rows = header_rows(SAMPLE_REPORT)
    assert ["Candidate", "Ada"] in rows
    assert ["Session ID", "s1"] in rows


def test_trust_dna_rows_has_header_plus_one_dimension():
    rows = trust_dna_rows(SAMPLE_REPORT)
    assert rows[0] == ["Dimension", "Score", "Trend"]
    assert rows[1] == ["Behavioral Consistency", "70.0", "down"]


def test_evidence_rows_has_header_plus_one_card():
    rows = evidence_rows(SAMPLE_REPORT)
    assert len(rows) == 2
    assert rows[1][0] == "Attention shift"


def test_evidence_rows_empty_is_just_the_header():
    empty = dict(SAMPLE_REPORT, evidence=[])
    assert evidence_rows(empty) == [["Evidence", "Severity", "Confidence", "Time"]]


def test_build_header_table_is_a_table_with_expected_rows():
    table = build_header_table(SAMPLE_REPORT)
    assert table._cellvalues == header_rows(SAMPLE_REPORT)


def test_build_evidence_table_falls_back_to_paragraph_when_empty():
    empty = dict(SAMPLE_REPORT, evidence=[])
    result = build_evidence_table(empty)
    assert "No significant evidence" in result.text


def test_render_report_writes_a_pdf_file(tmp_path):
    path = render_report(SAMPLE_REPORT, reports_dir=str(tmp_path))
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read(4) == b"%PDF"
