"""Persistence layer: SQLAlchemy models and session-factory construction.

Data definitions
----------------
An `InterviewSessionRow` represents one interview session record: its
identity (candidate/observer/position/department/interview type), its
lifecycle (status "active" | "ended", created_at, ended_at), and a cached
mirror of the ai/ service's latest SessionSnapshot — trust_overall,
trust_dimensions (the 6-dimension breakdown, as the raw list of camelCase
dicts ai/ returns), evidence_confidence, recommendation_confidence,
recommendation_status, recommendation_label, current_risk,
executive_summary — so the Live Session, Dashboard, and Report screens can
all be served without re-calling the AI service on every read.

An `EvidenceRow` represents one EvidenceCard mirrored from the ai/
service, keyed by the ai/ service's own evidence id (`ai_evidence_id`) so
mirroring the same card twice never creates a duplicate row.

An `Organization` is one customer account and a `User` belongs to exactly
one Organization (multi-tenancy groundwork — schema only for now, see
migrations/versions/0002_orgs_and_users.py; nothing enforces `org_id`
scoping yet, that's real auth's job).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


def new_id() -> str:
    """new_id: -> String
    Purpose: produce a fresh random identifier for a new row.
    """
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """now_utc: -> DateTime
    Purpose: the current time, timezone-aware in UTC (used as a Column default).
    """
    return datetime.now(timezone.utc)


class Organization(Base):
    """An Organization is one customer account (multi-tenancy root —
    Phase 1 of the production-readiness roadmap). `plan_tier` gates
    session-creation limits (see billing_service.PLAN_LIMITS);
    `stripe_customer_id`/`subscription_status` are set once the org's
    first checkout completes (see billing_service.py) — both are None
    for an org that's never started a paid plan."""

    __tablename__ = "organizations"

    org_id = Column(String, primary_key=True, default=new_id)
    name = Column(String, nullable=False)
    plan_tier = Column(String, nullable=False, default="free")
    stripe_customer_id = Column(String, nullable=True, unique=True)
    # None (never subscribed) | "active" | "trialing" | "past_due" | "canceled"
    # — Stripe's own subscription.status values, mirrored verbatim so
    # webhook handling never needs a translation table.
    subscription_status = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)

    users = relationship("User", back_populates="organization")
    sessions = relationship("InterviewSessionRow", back_populates="organization")


class User(Base):
    """A User belongs to exactly one Organization. Schema only for now —
    no route reads or enforces this yet; Phase 2 (real auth) is what
    issues credentials, checks `hashed_password`, and scopes every
    `/sessions*` query by `org_id`."""

    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=new_id)
    org_id = Column(String, ForeignKey("organizations.org_id"), nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="member")
    created_at = Column(DateTime, nullable=False, default=now_utc)

    organization = relationship("Organization", back_populates="users")


class InterviewSessionRow(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, default=new_id)
    ai_session_id = Column(String, nullable=True)
    # Nullable until Phase 2 (real auth) makes every session creation
    # request carry an authenticated org — see migrations/versions/0002.
    org_id = Column(String, ForeignKey("organizations.org_id"), nullable=True)

    candidate_name = Column(String, nullable=False)
    interview_type = Column(String, nullable=False)
    position = Column(String, nullable=True)
    department = Column(String, nullable=True)
    observer_name = Column(String, nullable=True)

    status = Column(String, nullable=False, default="active")  # "active" | "ended"
    created_at = Column(DateTime, nullable=False, default=now_utc)
    ended_at = Column(DateTime, nullable=True)

    trust_overall = Column(Float, nullable=False, default=75.0)
    trust_dimensions = Column(JSON, nullable=False, default=list)
    evidence_confidence = Column(Float, nullable=False, default=0.0)
    recommendation_confidence = Column(Float, nullable=False, default=0.0)
    recommendation_status = Column(String, nullable=False, default="evidence_insufficient")
    recommendation_label = Column(String, nullable=False, default="Insufficient Evidence")
    current_risk = Column(String, nullable=False, default="insufficient")
    executive_summary = Column(String, nullable=True)

    evidence = relationship("EvidenceRow", back_populates="session", order_by="EvidenceRow.timestamp")
    organization = relationship("Organization", back_populates="sessions")

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)


class UserConsent(Base):
    """A UserConsent is one record of a User accepting one versioned
    legal document (see legal.py for the current version strings) —
    Phase 7 of the production-readiness roadmap. Never updated in
    place: accepting a newer version of the same document inserts a new
    row rather than overwriting the old one, so there's always a full
    acceptance history to point to if it's ever disputed."""

    __tablename__ = "user_consents"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    # "terms_of_service" | "privacy_policy" | "session_tracking_notice"
    document = Column(String, nullable=False)
    version = Column(String, nullable=False)
    accepted_at = Column(DateTime, nullable=False, default=now_utc)


class EvidenceRow(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=new_id)
    ai_evidence_id = Column(String, nullable=False, unique=True)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False)

    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # "info" | "low" | "medium" | "high"
    polarity = Column(String, nullable=False)  # "supports_trust" | "reduces_trust" | "informational"
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    supporting_signals = Column(JSON, nullable=False, default=list)

    session = relationship("InterviewSessionRow", back_populates="evidence")


def make_engine(database_url: str):
    """make_engine: String -> Engine
    Purpose: build a SQLAlchemy engine for `database_url` and ensure all
    tables exist.
    Examples:
      make_engine("sqlite:///:memory:") -- a fresh in-memory schema, for tests
      make_engine("sqlite:///./backend.db") -- the real on-disk database

    An in-memory sqlite URL is pinned to a single shared connection
    (StaticPool) — plain per-connection ":memory:" sqlite gives each new
    connection its own empty database, which would silently "forget"
    every row as soon as a second Session opened a second connection.
    """
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    kwargs = {"poolclass": StaticPool} if database_url == "sqlite:///:memory:" else {}
    engine = create_engine(database_url, connect_args=connect_args, **kwargs)
    Base.metadata.create_all(bind=engine)
    return engine


def make_session_factory(engine) -> sessionmaker:
    """make_session_factory: Engine -> sessionmaker
    Purpose: build a DBSession factory bound to `engine`.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
