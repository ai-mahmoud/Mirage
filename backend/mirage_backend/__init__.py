"""Mirage backend — session persistence, PDF export, and the HTTP proxy to
the ai/ evidence-synthesis service (see ../ai/README.md for that contract).

This service owns no behavioral-intelligence logic itself: it forwards raw
interaction events to ai/, mirrors the resulting Trust DNA / evidence into
its own database for the Live Session and Report screens, and renders the
final PDF. One pipeline, one source of truth for Trust DNA.
"""

__version__ = "0.1.0"
