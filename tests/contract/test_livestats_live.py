"""Contract test against the real NBL feed. Run locally with `pytest --run-live`.

It fetches one finished NBL game (into the git-ignored cache) and checks that our independently
computed flow stats agree with the feed's own official totals.
"""

from pathlib import Path

import pytest

from nbl_media_desk.cache import GameCache
from nbl_media_desk.facts import build_fact_sheet
from nbl_media_desk.sources import LiveStatsSource

GAME_ID = "2120057"  # NBL: Sydney Kings v South East Melbourne Phoenix


@pytest.mark.live
def test_flow_stats_match_official_feed_totals(tmp_path: Path) -> None:
    cache = GameCache(tmp_path)
    game = LiveStatsSource(cache, user_agent="nbl-media-desk contract test").get_game(GAME_ID)
    raw = cache.get("livestats", GAME_ID)
    assert raw is not None, "finished games must be cached"
    sheet = build_fact_sheet(game)

    def one(subject: str, metric: str) -> object:
        (fact,) = sheet.find(subject=subject, metric=metric)
        return fact.value

    for key, side in (("1", game.home), ("2", game.away)):
        feed = raw["tm"][key]
        assert one(side.name, "largest_lead") == feed["tot_sBiggestLead"]
        assert one(side.name, "longest_unanswered_run") == feed["tot_sBiggestScoringRun"]
        assert one("game", "lead_changes") == feed["tot_sLeadChanges"]
        # FIBA also counts 0-0 at tip-off as "level"; we count ties after the first score.
        assert one("game", "times_tied") == feed["tot_sTimesScoresLevel"] - 1
