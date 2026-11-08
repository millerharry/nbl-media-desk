"""Deterministic fact generators (ADR-0003).

Each generator is a pure function `Game -> list[FactDraft]`. They never call a model, never read
the clock, and always emit facts in the same order, so fact IDs are stable across runs.

Adding a storyline type means adding a generator here, with unit tests.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from nbl_media_desk.facts.models import FactCategory, FactDraft
from nbl_media_desk.models import Game, PlayerLine, Side, TeamGame

Generator = Callable[[Game], list[FactDraft]]

REGULATION_PERIODS = 4
DOUBLE_FIGURES = 10
_ORDINALS = {1: "first", 2: "second", 3: "third", 4: "fourth"}
_COUNTING_STATS = ("points", "rebounds", "assists", "steals", "blocks")
_STAT_WORDS = {
    "points": "points",
    "rebounds": "rebounds",
    "assists": "assists",
    "steals": "steals",
    "blocks": "blocks",
    "turnovers": "turnovers",
}


# --- helpers -----------------------------------------------------------------------------------


def period_scope(period: int) -> str:
    return f"q{period}" if period <= REGULATION_PERIODS else f"ot{period - REGULATION_PERIODS}"


def period_name(period: int) -> str:
    if period <= REGULATION_PERIODS:
        return f"the {_ORDINALS[period]} quarter"
    n = period - REGULATION_PERIODS
    return "overtime" if n == 1 else f"overtime period {n}"


def break_name(period: int) -> str:
    if period < REGULATION_PERIODS:
        return f"after the {_ORDINALS[period]} quarter"
    if period == REGULATION_PERIODS:
        return "at the end of regulation"
    return f"after overtime period {period - REGULATION_PERIODS}"


_SINGULAR = {
    "points": "point",
    "rebounds": "rebound",
    "assists": "assist",
    "steals": "steal",
    "blocks": "block",
    "turnovers": "turnover",
    "minutes": "minute",
    "field goals": "field goal",
    "threes": "three",
    "free throws": "free throw",
    "lead changes": "lead change",
    "times": "time",
    "players": "player",
    "overtime periods": "overtime period",
}


def count(n: int | float, plural_noun: str) -> str:
    """'1 point', '28 points'. Grammar matters: these sentences reach the writer verbatim."""
    noun = _SINGULAR.get(plural_noun, plural_noun) if n == 1 else plural_noun
    return f"{n} {noun}"


def possessive(name: str) -> str:
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def pct(made: int, attempted: int) -> float | None:
    return round(100 * made / attempted, 1) if attempted else None


def _sides(game: Game) -> Iterator[tuple[Side, TeamGame]]:
    yield Side.HOME, game.home
    yield Side.AWAY, game.away


def _cumulative(team: TeamGame, through_period: int) -> int:
    return sum(team.period_scores[:through_period])


def _player(
    team: TeamGame,
    p: PlayerLine,
    metric: str,
    value: bool | int | float | str,
    text: str,
    *,
    category: FactCategory = FactCategory.PLAYER,
) -> FactDraft:
    return FactDraft(
        category=category,
        subject_type="player",
        subject=p.name,
        team=team.name,
        metric=metric,
        value=value,
        text=text,
    )


# --- generators --------------------------------------------------------------------------------


def result_facts(game: Game) -> list[FactDraft]:
    facts = [
        FactDraft(
            category=FactCategory.RESULT,
            subject_type="team",
            subject=team.name,
            team=team.name,
            metric="final_score",
            value=team.final_score,
            text=f"{team.name} scored {team.final_score} points.",
        )
        for _, team in _sides(game)
    ]
    winner_side = game.winner
    if winner_side is not None:
        winner, loser = game.team(winner_side), game.team(winner_side.other)
        margin = winner.final_score - loser.final_score
        venue = "at home" if winner_side is Side.HOME else "on the road"
        facts += [
            FactDraft(
                category=FactCategory.RESULT,
                subject_type="game",
                subject="game",
                metric="winner",
                value=winner.name,
                text=(
                    f"{winner.name} beat {loser.name} "
                    f"{winner.final_score}-{loser.final_score} {venue}."
                ),
            ),
            FactDraft(
                category=FactCategory.RESULT,
                subject_type="game",
                subject="game",
                metric="margin",
                value=margin,
                text=f"The winning margin was {count(margin, 'points')}.",
            ),
        ]
    overtime = game.periods - REGULATION_PERIODS
    facts.append(
        FactDraft(
            category=FactCategory.RESULT,
            subject_type="game",
            subject="game",
            metric="overtime_periods",
            value=overtime,
            text=(
                "The game was decided in regulation."
                if overtime == 0
                else f"The game went to {count(overtime, 'overtime periods')}."
            ),
        )
    )
    return facts


def period_facts(game: Game) -> list[FactDraft]:
    facts: list[FactDraft] = []
    leaders_at_breaks: list[Side | None] = []
    for period in range(1, game.periods + 1):
        scope = period_scope(period)
        home_pts = game.home.period_scores[period - 1]
        away_pts = game.away.period_scores[period - 1]
        for side, team in _sides(game):
            pts = home_pts if side is Side.HOME else away_pts
            facts.append(
                FactDraft(
                    category=FactCategory.PERIOD,
                    subject_type="team",
                    subject=team.name,
                    team=team.name,
                    metric="period_points",
                    value=pts,
                    scope=scope,
                    text=f"{team.name} scored {count(pts, 'points')} in {period_name(period)}.",
                )
            )
        if home_pts == away_pts:
            text = f"{period_name(period).capitalize()} was tied {home_pts}-{away_pts}."
            period_winner = "tied"
        else:
            side = Side.HOME if home_pts > away_pts else Side.AWAY
            hi, lo = max(home_pts, away_pts), min(home_pts, away_pts)
            period_winner = game.team(side).name
            text = (
                f"{period_winner} outscored {game.team(side.other).name} "
                f"{hi}-{lo} in {period_name(period)}."
            )
        facts.append(
            FactDraft(
                category=FactCategory.PERIOD,
                subject_type="game",
                subject="game",
                metric="period_winner",
                value=period_winner,
                scope=scope,
                text=text,
            )
        )

        if period == game.periods:
            continue  # the last break is the final score
        home_cum, away_cum = _cumulative(game.home, period), _cumulative(game.away, period)
        if home_cum == away_cum:
            leader_side: Side | None = None
            leader_text = f"The score was tied {home_cum}-{away_cum} {break_name(period)}."
            leader_value = "tied"
        else:
            leader_side = Side.HOME if home_cum > away_cum else Side.AWAY
            leader_value = game.team(leader_side).name
            leader_text = (
                f"{leader_value} led {max(home_cum, away_cum)}-{min(home_cum, away_cum)} "
                f"{break_name(period)}."
            )
        leaders_at_breaks.append(leader_side)
        facts.append(
            FactDraft(
                category=FactCategory.PERIOD,
                subject_type="game",
                subject="game",
                metric="leader_at_break",
                value=leader_value,
                scope=f"after_{scope}",
                text=leader_text,
            )
        )

    for side, team in _sides(game):
        led_every = bool(leaders_at_breaks) and all(s is side for s in leaders_at_breaks)
        facts.append(
            FactDraft(
                category=FactCategory.PERIOD,
                subject_type="team",
                subject=team.name,
                team=team.name,
                metric="led_at_every_break",
                value=led_every,
                text=(
                    f"{team.name} led at every break."
                    if led_every
                    else f"{team.name} did not lead at every break."
                ),
            )
        )

    winner_side = game.winner
    if winner_side is not None:
        facts.extend(_comeback_facts(game, winner_side))
    return facts


def _comeback_facts(game: Game, winner_side: Side) -> list[FactDraft]:
    """The winner's largest deficit at a break, preferring the latest break on ties."""
    winner, loser = game.team(winner_side), game.team(winner_side.other)
    worst: tuple[int, int] | None = None  # (deficit, period)
    for period in range(1, game.periods):
        deficit = _cumulative(loser, period) - _cumulative(winner, period)
        if deficit > 0 and (worst is None or deficit >= worst[0]):
            worst = (deficit, period)
    if worst is None:
        return []
    deficit, period = worst
    return [
        FactDraft(
            category=FactCategory.PERIOD,
            subject_type="team",
            subject=winner.name,
            team=winner.name,
            metric="trailed_at_break_and_won",
            value=deficit,
            scope=f"after_{period_scope(period)}",
            text=(
                f"{winner.name} trailed {_cumulative(loser, period)}-{_cumulative(winner, period)} "
                f"{break_name(period)} and won {winner.final_score}-{loser.final_score}."
            ),
        )
    ]


def player_facts(game: Game) -> list[FactDraft]:
    facts: list[FactDraft] = []
    for _, team in _sides(game):
        for p in team.players:
            if not p.played:
                facts.append(_player(team, p, "did_not_play", True, f"{p.name} did not play."))
                continue
            facts.append(
                _player(
                    team,
                    p,
                    "minutes",
                    round(p.minutes),
                    f"{p.name} played {count(round(p.minutes), 'minutes')}.",
                )
            )
            for stat in ("points", "rebounds", "assists", "steals", "blocks", "turnovers"):
                value = getattr(p, stat)
                facts.append(
                    _player(
                        team, p, stat, value, f"{p.name} had {count(value, _STAT_WORDS[stat])}."
                    )
                )
            for label, made, att, words in (
                ("field_goals", p.field_goals_made, p.field_goals_attempted, "from the field"),
                ("threes", p.threes_made, p.threes_attempted, "from three-point range"),
                (
                    "free_throws",
                    p.free_throws_made,
                    p.free_throws_attempted,
                    "from the free-throw line",
                ),
            ):
                facts.append(
                    _player(
                        team,
                        p,
                        f"{label}_made",
                        made,
                        f"{p.name} made {count(made, label.replace('_', ' '))}.",
                    )
                )
                facts.append(
                    _player(
                        team,
                        p,
                        f"{label}_attempted",
                        att,
                        f"{p.name} attempted {count(att, label.replace('_', ' '))}.",
                    )
                )
                share = pct(made, att)
                if share is not None:
                    facts.append(
                        _player(
                            team,
                            p,
                            f"{label}_pct",
                            share,
                            f"{p.name} shot {made}-of-{att} ({share}%) {words}.",
                        )
                    )
    return facts


def leader_facts(game: Game) -> list[FactDraft]:
    facts: list[FactDraft] = []
    everyone = [(team, p) for _, team in _sides(game) for p in team.players if p.played]
    for stat in ("points", "rebounds", "assists"):
        best = max((getattr(p, stat) for _, p in everyone), default=0)
        if best == 0:
            continue
        leaders = [(t, p) for t, p in everyone if getattr(p, stat) == best]
        shared = " (shared)" if len(leaders) > 1 else ""
        facts.extend(
            _player(
                t,
                p,
                f"game_high_{stat}",
                best,
                f"{p.name} led all players with {count(best, stat)}{shared}.",
                category=FactCategory.LEADER,
            )
            for t, p in leaders
        )
    for _, team in _sides(game):
        played = [p for p in team.players if p.played]
        for stat in ("points", "rebounds", "assists"):
            best = max((getattr(p, stat) for p in played), default=0)
            if best == 0:
                continue
            facts.extend(
                _player(
                    team,
                    p,
                    f"team_high_{stat}",
                    best,
                    f"{p.name} led {team.name} with {count(best, stat)}.",
                    category=FactCategory.LEADER,
                )
                for p in played
                if getattr(p, stat) == best
            )
    return facts


def milestone_facts(game: Game) -> list[FactDraft]:
    facts: list[FactDraft] = []
    for _, team in _sides(game):
        for p in team.players:
            doubles = [s for s in _COUNTING_STATS if getattr(p, s) >= DOUBLE_FIGURES]
            if len(doubles) < 2:
                continue
            kind = "triple_double" if len(doubles) >= 3 else "double_double"
            detail = " and ".join(f"{getattr(p, s)} {s}" for s in doubles)
            label = kind.replace("_", "-")
            facts.append(
                _player(
                    team,
                    p,
                    kind,
                    True,
                    f"{p.name} recorded a {label} with {detail}.",
                    category=FactCategory.MILESTONE,
                )
            )
    return facts


def team_total_facts(game: Game) -> list[FactDraft]:
    facts: list[FactDraft] = []

    def add(team: TeamGame, metric: str, value: bool | int | float | str, text: str) -> None:
        facts.append(
            FactDraft(
                category=FactCategory.TEAM,
                subject_type="team",
                subject=team.name,
                team=team.name,
                metric=metric,
                value=value,
                text=text,
            )
        )

    for _, t in _sides(game):
        ps = t.players
        total = {
            stat: sum(getattr(p, stat) for p in ps)
            for stat in (
                "field_goals_made",
                "field_goals_attempted",
                "threes_made",
                "threes_attempted",
                "free_throws_made",
                "free_throws_attempted",
                "rebounds",
                "assists",
                "steals",
                "blocks",
                "turnovers",
            )
        }
        for label, words in (
            ("field_goals", "from the field"),
            ("threes", "from three-point range"),
            ("free_throws", "from the free-throw line"),
        ):
            made, att = total[f"{label}_made"], total[f"{label}_attempted"]
            add(
                t,
                f"team_{label}_made",
                made,
                f"{t.name} made {count(made, label.replace('_', ' '))}.",
            )
            add(
                t,
                f"team_{label}_attempted",
                att,
                f"{t.name} attempted {count(att, label.replace('_', ' '))}.",
            )
            share = pct(made, att)
            if share is not None:
                add(
                    t,
                    f"team_{label}_pct",
                    share,
                    f"{t.name} shot {made}-of-{att} ({share}%) {words}.",
                )
        for stat in ("rebounds", "assists", "steals", "blocks", "turnovers"):
            add(t, f"team_{stat}", total[stat], f"{t.name} had {count(total[stat], stat)}.")
        bench = sum(p.points for p in ps if not p.starter)
        add(
            t, "bench_points", bench, f"{possessive(t.name)} bench scored {count(bench, 'points')}."
        )
        in_double_figures = sum(1 for p in ps if p.points >= DOUBLE_FIGURES)
        add(
            t,
            "players_in_double_figures",
            in_double_figures,
            f"{count(in_double_figures, 'players')} from {t.name} scored in double figures.",
        )
    return facts


def flow_facts(game: Game) -> list[FactDraft]:
    """Lead changes, ties, largest leads and scoring runs. Needs play-by-play events.

    Definitions: a lead change is the lead passing from one team to the other (possibly via a
    tie). `times_tied` counts ties after the first score, so it is one less than FIBA's
    "times scores level", which also counts 0-0. Runs are consecutive points by one team.
    These match the LiveStats feed's own totals (see the live contract test).
    """
    if not game.events:
        return []
    lead_changes = times_tied = 0
    largest_lead = {Side.HOME: 0, Side.AWAY: 0}
    longest_run = {Side.HOME: 0, Side.AWAY: 0}
    run_side: Side | None = None
    run = 0
    prev_home = prev_away = 0
    prev_leader: Side | None = None

    for e in game.events:
        dh, da = e.home_score - prev_home, e.away_score - prev_away
        if dh < 0 or da < 0:
            msg = f"score decreased at event {e.sequence}"
            raise ValueError(msg)
        if dh == 0 and da == 0:
            continue
        for side, delta in ((Side.HOME, dh), (Side.AWAY, da)):
            if delta == 0:
                continue
            run = run + delta if run_side is side else delta
            run_side = side
            longest_run[side] = max(longest_run[side], run)
        margin = e.home_score - e.away_score
        if margin > 0:
            largest_lead[Side.HOME] = max(largest_lead[Side.HOME], margin)
        elif margin < 0:
            largest_lead[Side.AWAY] = max(largest_lead[Side.AWAY], -margin)
        leader = Side.HOME if margin > 0 else Side.AWAY if margin < 0 else None
        if leader is None:
            times_tied += 1
        elif prev_leader is not None and leader is not prev_leader:
            lead_changes += 1
        if leader is not None:
            prev_leader = leader
        prev_home, prev_away = e.home_score, e.away_score

    facts = [
        FactDraft(
            category=FactCategory.FLOW,
            subject_type="game",
            subject="game",
            metric="lead_changes",
            value=lead_changes,
            text=f"There were {count(lead_changes, 'lead changes')}.",
        ),
        FactDraft(
            category=FactCategory.FLOW,
            subject_type="game",
            subject="game",
            metric="times_tied",
            value=times_tied,
            text=f"The scores were level {count(times_tied, 'times')} after the opening tip.",
        ),
    ]
    for side, team in _sides(game):
        facts += [
            FactDraft(
                category=FactCategory.FLOW,
                subject_type="team",
                subject=team.name,
                team=team.name,
                metric="largest_lead",
                value=largest_lead[side],
                text=(
                    f"{possessive(team.name)} largest lead was "
                    f"{count(largest_lead[side], 'points')}."
                ),
            ),
            FactDraft(
                category=FactCategory.FLOW,
                subject_type="team",
                subject=team.name,
                team=team.name,
                metric="longest_unanswered_run",
                value=longest_run[side],
                text=f"{possessive(team.name)} longest unanswered run was {longest_run[side]}-0.",
            ),
        ]
    winner_side = game.winner
    if winner_side is not None and largest_lead[winner_side.other] > 0:
        winner = game.team(winner_side)
        deficit = largest_lead[winner_side.other]
        facts.append(
            FactDraft(
                category=FactCategory.FLOW,
                subject_type="team",
                subject=winner.name,
                team=winner.name,
                metric="largest_deficit_overcome",
                value=deficit,
                text=f"{winner.name} came back from {count(deficit, 'points')} down to win.",
            )
        )
    return facts


ALL_GENERATORS: tuple[Generator, ...] = (
    result_facts,
    period_facts,
    flow_facts,
    leader_facts,
    milestone_facts,
    player_facts,
    team_total_facts,
)
