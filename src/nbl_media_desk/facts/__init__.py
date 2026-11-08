"""Deterministic fact engine: every number the writer may use comes from here (ADR-0003)."""

from nbl_media_desk.facts.engine import build_fact_sheet
from nbl_media_desk.facts.models import Fact, FactCategory, FactDraft, FactSheet

__all__ = ["Fact", "FactCategory", "FactDraft", "FactSheet", "build_fact_sheet"]
