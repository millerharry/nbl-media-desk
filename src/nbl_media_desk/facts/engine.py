"""Build a numbered `FactSheet` from a `Game` (ADR-0003)."""

from collections.abc import Sequence

from nbl_media_desk.facts.generators import ALL_GENERATORS, Generator
from nbl_media_desk.facts.models import Fact, FactSheet
from nbl_media_desk.models import Game


def build_fact_sheet(game: Game, generators: Sequence[Generator] = ALL_GENERATORS) -> FactSheet:
    """Run every generator in order and number the facts F-001, F-002, ...

    Ordering is deterministic, so the same game always produces the same IDs.
    """
    drafts = [draft for generate in generators for draft in generate(game)]
    facts = tuple(
        Fact(id=f"F-{i:03d}", **draft.model_dump()) for i, draft in enumerate(drafts, start=1)
    )
    return FactSheet(game_id=game.game_id, facts=facts)
