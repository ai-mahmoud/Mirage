"""Rendering the final Session Report as a PDF (Report/Export screen).

Design: the `*_rows` functions are pure data transformations — a
SessionReport dict in, a plain list-of-lists-of-strings out — and are
tested directly with no reportlab involved. `render_report` is the only
function with a side effect (writing a file); it wires those rows into
reportlab flowables.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("TitleStyle", parent=_STYLES["Title"], fontSize=20, spaceAfter=20)
_HEADING_STYLE = ParagraphStyle("HeadingStyle", parent=_STYLES["Heading2"], spaceBefore=15, spaceAfter=10)


def fmt_ms(ms: float) -> str:
    """fmt_ms: Number -> String
    Purpose: render an epoch-ms timestamp as a human-readable date/time.
    Example: fmt_ms(0) == "1970-01-01 00:00"
    """
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def header_rows(report: dict) -> list[list[str]]:
    """header_rows: SessionReport -> (list-of (list-of String))
    Purpose: the candidate/session identity rows shown at the top of the report.
    Example:
      header_rows({"candidateName": "Ada", ...})[0] == ["Candidate", "Ada"]
    """
    return [
        ["Candidate", report["candidateName"]],
        ["Interview Type", report["interviewType"] or "-"],
        ["Position", report.get("position") or "-"],
        ["Observer", report["observerName"]],
        ["Session ID", report["sessionId"]],
        ["Date", fmt_ms(report["startedAt"])],
    ]


def trust_dna_rows(report: dict) -> list[list[str]]:
    """trust_dna_rows: SessionReport -> (list-of (list-of String))
    Purpose: a header row plus one row per Trust DNA dimension.
    """
    dna = report["trustDna"]
    return [["Dimension", "Score", "Trend"]] + [
        [d["label"], f"{d['score']:.1f}", d["trend"]] for d in dna["dimensions"]
    ]


def evidence_rows(report: dict) -> list[list[str]]:
    """evidence_rows: SessionReport -> (list-of (list-of String))
    Purpose: a header row plus one row per evidence card, oldest first.
    An empty evidence list still returns just the header row — the caller
    decides how to render "no evidence" (see build_evidence_table).
    """
    return [["Evidence", "Severity", "Confidence", "Time"]] + [
        [e["title"], e["severity"], f"{e['confidence'] * 100:.0f}%", fmt_ms(e["timestamp"])]
        for e in report["evidence"]
    ]


def _styled_table(rows: list[list[str]], col_widths: list[float], header_color) -> Table:
    table = Table(rows, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def build_header_table(report: dict) -> Table:
    """build_header_table: SessionReport -> Table
    Purpose: the session-identity block, shaded on its label column.
    """
    table = Table(header_rows(report), colWidths=[5 * cm, 10 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def build_trust_dna_section(report: dict) -> list:
    """build_trust_dna_section: SessionReport -> (list-of Flowable)
    Purpose: the Trust DNA overall score plus per-dimension breakdown.
    """
    overall = report["trustDna"]["overall"]
    return [
        Paragraph("Trust DNA", _HEADING_STYLE),
        Paragraph(f"<b>Overall:</b> {overall:.1f} / 100", _STYLES["Normal"]),
        Spacer(1, 0.2 * cm),
        _styled_table(trust_dna_rows(report), [7 * cm, 3 * cm, 3 * cm], colors.HexColor("#123C69")),
    ]


def build_recommendation_section(report: dict) -> list:
    """build_recommendation_section: SessionReport -> (list-of Flowable)
    Purpose: dual-track confidence plus the conservative human recommendation.
    """
    conf = report["confidence"]
    rec = report["recommendation"]
    return [
        Paragraph("Confidence", _HEADING_STYLE),
        Paragraph(f"<b>Evidence Confidence:</b> {conf['evidenceConfidence'] * 100:.0f}%", _STYLES["Normal"]),
        Paragraph(
            f"<b>Recommendation Confidence:</b> {conf['recommendationConfidence'] * 100:.0f}%", _STYLES["Normal"]
        ),
        Paragraph("Recommendation", _HEADING_STYLE),
        Paragraph(f"<b>{rec['label']}</b>: {rec['suggestedAction']}", _STYLES["Normal"]),
    ]


def build_evidence_table(report: dict):
    """build_evidence_table: SessionReport -> Flowable
    Purpose: the evidence table, or a placeholder paragraph when no
    evidence was ever generated.
    """
    if not report["evidence"]:
        return Paragraph("No significant evidence recorded.", _STYLES["Normal"])
    return _styled_table(evidence_rows(report), [7 * cm, 3 * cm, 2.5 * cm, 2.5 * cm], colors.HexColor("#2B2B2B"))


def build_privacy_footer(report: dict) -> list:
    """build_privacy_footer: SessionReport -> (list-of Flowable)
    Purpose: the fixed privacy summary every report must carry.
    """
    text = " ".join(report["privacyStatement"])
    return [Spacer(1, 0.3 * cm), Paragraph(f"<i>{text}</i>", _STYLES["Normal"])]


def render_report(report: dict, reports_dir: str) -> str:
    """render_report: SessionReport String -> String
    Purpose: write `report` to a PDF file under `reports_dir` and return
    its path.
    """
    os.makedirs(reports_dir, exist_ok=True)
    file_path = os.path.join(reports_dir, f"report_{report['sessionId']}.pdf")
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = [
        Paragraph("Mirage AI — Session Report", _TITLE_STYLE),
        Spacer(1, 0.3 * cm),
        build_header_table(report),
        Spacer(1, 0.3 * cm),
        *build_trust_dna_section(report),
        Spacer(1, 0.3 * cm),
        *build_recommendation_section(report),
        Spacer(1, 0.3 * cm),
        Paragraph("Evidence Summary", _HEADING_STYLE),
        build_evidence_table(report),
        *build_privacy_footer(report),
    ]
    doc.build(elements)
    return file_path
