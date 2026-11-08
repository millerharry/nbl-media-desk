from typing import Any

import pytest

from nbl_media_desk.facts import FactCategory, FactSheet, build_fact_sheet
from nbl_media_desk.facts.generators import count, flow_facts, pct, possessive
from nbl_media_desk.models import Game, PlayerLine, PlayEvent, TeamGame
from nbl_media_desk.sources.livestats import map_game


def values(sheet: FactSheet, **filters: Any) -> list[Any]:
    return [f.value for f in sheet.find(**filters)]


# --- engine ------------------------------------------------------------------------------------


def test_ids_are_sequential_and_unique(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    assert [f.id for f in sheet.facts] == [f"F-{i:03d}" for i in range(1, len(sheet.facts) + 1)]


def test_fact_sheet_is_deterministic(golden_game: Game) -> None:
    assert build_fact_sheet(golden_game) == build_fact_sheet(golden_game)


def test_by_id_and_prompt_lines(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    first = sheet.facts[0]
    assert sheet.by_id(first.id) == first
    assert sheet.by_id("F-999") is None
    assert sheet.to_prompt_lines().splitlines()[0] == f"{first.id} | {first.text}"


# --- result and periods (golden game) ----------------------------------------------------------


def test_result_facts(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    assert values(sheet, metric="winner") == ["Harbour City Hawks"]
    assert values(sheet, metric="margin") == [6]
    assert values(sheet, metric="overtime_periods") == [0]
    winner = sheet.find(metric="winner")[0]
    assert winner.text == "Harbour City Hawks beat Inland Rivers Rams 94-88 at home."


def test_leaders_at_breaks(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    assert values(sheet, metric="leader_at_break") == [
        "Inland Rivers Rams",
        "Harbour City Hawks",
        "Inland Rivers Rams",
    ]
    assert values(sheet, metric="led_at_every_break") == [False, False]


def test_comeback_fact_text(golden_game: Game) -> None:
    fact = build_fact_sheet(golden_game).find(metric="trailed_at_break_and_won")[0]
    assert fact.text == ("Harbour City Hawks trailed 71-67 after the third quarter and won 94-88.")


def test_no_flow_facts_without_events(golden_game: Game) -> None:
    assert build_fact_sheet(golden_game).find(category=FactCategory.FLOW) == []


# --- players, leaders, milestones, team totals --------------------------------------------------


def test_player_line_facts(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    okafor = {f.metric: f.value for f in sheet.find(subject="Jalen Okafor")}
    assert okafor["points"] == 28
    assert okafor["field_goals_pct"] == 52.6
    assert okafor["threes_made"] == 3
    assert okafor["team_high_points"] == 28
    assert okafor["game_high_points"] == 28


def test_double_doubles(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    assert {f.subject for f in sheet.find(metric="double_double")} == {
        "Sam Petrovic",
        "Theo Nakamura",
    }


def test_team_totals_add_up(golden_game: Game) -> None:
    sheet = build_fact_sheet(golden_game)
    hawks = "Harbour City Hawks"
    assert values(sheet, subject=hawks, metric="team_field_goals_made") == [36]
    assert values(sheet, subject=hawks, metric="bench_points") == [12]
    assert values(sheet, subject=hawks, metric="players_in_double_figures") == [4]
    bench = sheet.find(subject=hawks, metric="bench_points")[0]
    assert bench.text == "Harbour City Hawks' bench scored 12 points."


def _team(name: str, players: tuple[PlayerLine, ...], periods: tuple[int, ...]) -> TeamGame:
    return TeamGame(
        name=name,
        code=name[:3].upper(),
        period_scores=periods,
        final_score=sum(periods),
        players=players,
    )


def _line(name: str, **stats: int) -> PlayerLine:
    fgm = stats.get("field_goals_made", 0)
    return PlayerLine(
        name=name,
        shirt_number="0",
        starter=True,
        minutes=30.0,
        points=2 * fgm,
        field_goals_made=fgm,
        field_goals_attempted=max(fgm, 1),
        threes_made=0,
        threes_attempted=0,
        free_throws_made=0,
        free_throws_attempted=0,
        rebounds=stats.get("rebounds", 0),
        assists=stats.get("assists", 0),
        steals=stats.get("steals", 0),
        blocks=0,
        turnovers=0,
    )


def _simple_game(home: tuple[PlayerLine, ...], away: tuple[PlayerLine, ...]) -> Game:
    hp = sum(p.points for p in home)
    ap = sum(p.points for p in away)
    return Game(
        game_id="t",
        source="test",
        synthetic=True,
        competition="c",
        season="s",
        home=_team("Home Hornets", home, (hp, 0, 0, 0)),
        away=_team("Away Owls", away, (ap, 0, 0, 0)),
    )


def test_triple_double_and_shared_leaders() -> None:
    game = _simple_game(
        (_line("Tri Ple", field_goals_made=6, rebounds=10, assists=10),),
        (_line("Other One", field_goals_made=6, rebounds=2),),
    )
    sheet = build_fact_sheet(game)
    assert values(sheet, metric="triple_double") == [True]
    assert values(sheet, metric="double_double") == []
    shared = sheet.find(metric="game_high_points")
    assert {f.subject for f in shared} == {"Tri Ple", "Other One"}
    assert all("(shared)" in f.text for f in shared)
    assert values(sheet, metric="winner") == []  # tied game: no winner fact


def test_led_every_break_and_tied_period() -> None:
    home = (_line("H One", field_goals_made=5),)
    away = (_line("A One", field_goals_made=2),)
    game = Game(
        game_id="t",
        source="test",
        synthetic=True,
        competition="c",
        season="s",
        home=_team("Home Hornets", home, (4, 2, 2, 2)),
        away=_team("Away Owls", away, (2, 2, 0, 0)),
    )
    sheet = build_fact_sheet(game)
    assert values(sheet, subject="Home Hornets", metric="led_at_every_break") == [True]
    q2 = sheet.find(metric="period_winner", scope="q2")[0]
    assert (q2.value, q2.text) == ("tied", "The second quarter was tied 2-2.")
    assert sheet.find(metric="trailed_at_break_and_won") == []


# --- flow and overtime (synthetic LiveStats fixture) --------------------------------------------


def test_flow_and_overtime(livestats_raw: dict[str, Any]) -> None:
    sheet = build_fact_sheet(map_game(livestats_raw, game_id="900001"))
    comets, vipers = "Coastline Comets", "Valley Vipers"
    assert values(sheet, metric="lead_changes") == [4]
    assert values(sheet, metric="times_tied") == [4]
    assert values(sheet, subject=comets, metric="largest_lead") == [3]
    assert values(sheet, subject=vipers, metric="largest_lead") == [1]
    assert values(sheet, subject=comets, metric="longest_unanswered_run") == [4]
    assert values(sheet, subject=vipers, metric="longest_unanswered_run") == [3]
    assert values(sheet, metric="largest_deficit_overcome") == [1]
    assert values(sheet, metric="overtime_periods") == [1]
    assert values(sheet, metric="leader_at_break", scope="after_q4") == ["tied"]
    assert values(sheet, subject=comets, metric="period_points", scope="ot1") == [3]
    assert values(sheet, subject="Zoe Hart", metric="did_not_play") == [True]
    texts = sheet.to_prompt_lines()
    assert "The game went to 1 overtime period." in texts
    assert "Valley Vipers' largest lead was 1 point." in texts
    assert "The score was tied 10-10 at the end of regulation." in texts


def test_flow_rejects_score_going_backwards(golden_game: Game) -> None:
    bad = golden_game.model_copy(
        update={
            "events": (
                PlayEvent(
                    sequence=1, period=1, clock="09:00", home_score=4, away_score=0, action="2pt"
                ),
                PlayEvent(
                    sequence=2, period=1, clock="08:00", home_score=2, away_score=0, action="2pt"
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="score decreased"):
        flow_facts(bad)


# --- helpers -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("n", "noun", "expected"),
    [
        (1, "points", "1 point"),
        (2, "points", "2 points"),
        (0, "rebounds", "0 rebounds"),
        (1, "free throws", "1 free throw"),
        (1, "unknown", "1 unknown"),
    ],
)
def test_count(n: int, noun: str, expected: str) -> None:
    assert count(n, noun) == expected


def test_possessive_and_pct() -> None:
    assert possessive("Sydney Kings") == "Sydney Kings'"
    assert possessive("Melbourne United") == "Melbourne United's"
    assert pct(1, 3) == 33.3
    assert pct(0, 0) is None
