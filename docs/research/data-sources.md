# Research: game data sources

_Last checked: 2026-11-08_

NBL Media Desk needs, for every game: the final score, team and player box scores, play-by-play, and enough history to say things like "season high". This note records what is available, how reliable it is, and the licensing risk.

## 1. NBL: FIBA LiveStats via Genius Sports

**What it is.** The NBL's official statistics are captured with FIBA LiveStats and distributed by Genius Sports, the league's long-term data partner ([Genius Sports newsroom](https://www.geniussports.com/newsroom/australian-national-basketball-league-extends-data-technology-partnership-with-genius-sports-group/)). The same data drives nbl.com.au, broadcast graphics and NBL fantasy.

**Public endpoints (undocumented).** Each game has a numeric ID and public pages on `fibalivestats.dcd.shared.geniussports.com`:

| URL pattern | Content |
|---|---|
| `/u/NBL/{gameId}/bs.html` | HTML box score ([example](https://fibalivestats.dcd.shared.geniussports.com/u/NBL/2120057/bs.html)) |
| `/data/{gameId}/data.json` | Full game JSON (≈460 KB per game) |

Verified on 2026-11-08 with game `2120057` (Sydney Kings 91, South East Melbourne Phoenix 79). The JSON returned HTTP 200 without authentication and has these top-level keys:

```
attendance, clock, disableMatch, inOT, leaddata, officials, othermatches,
pbp, period, periodLength, periodLengthOVERTIME, periodLengthREGULAR,
periodType, periodsMax, scorers, timeline, tm, totalTimeAdded, totallds
```

- `tm["1"|"2"]`: team name/code, coach, quarter scores (`p1_score` to `p4_score`), `full_score`, ~60 team totals (`tot_sPoints`, `tot_sBiggestLead`, `tot_sLeadChanges`, `tot_sPointsFromTurnovers`, `tot_sBenchPoints` and more), and `pl` (players).
- `pl[*]`: name, shirt number, starter flag, minutes, full shooting splits, rebounds, assists, steals, blocks, turnovers, fouls, plus-minus, efficiency.
- `pbp[]`: 615 events for this game. Each has the game clock, period, running score (`s1`, `s2`), lead, team, player, `actionType`/`subType`, `success` and `qualifier`. The last event is `actionType: "game", subType: "end"`, which is a clean "final whistle" signal.

**Strengths.** Official, rich, near real time during games, and has everything v1 needs in one document.

**Risks.**
- **No documented contract.** There is no published schema or SLA, so the format can change without notice. Genius's documented products are commercial: an in-venue TCP TV feed on port 7677 ([developer docs](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html)) and a Data Warehouse REST API that needs a key.
- **No published licence for reuse.** We found no NBL or Genius terms that allow automated access or redistribution. nbl.com.au's `robots.txt` doesn't block these paths, but that isn't a licence. Treat the data as **all rights reserved**.
- **Trademarks.** "NBL", club names and logos are trademarks. The feed includes logo URLs; we must not ship or rehost them.

**Conclusion.** It's fine for personal, low-volume, non-commercial development use if we cache aggressively and identify ourselves politely. It is **not** safe to redistribute the raw data in the repo, and any commercial use needs a data agreement with the NBL or Genius Sports.

## 2. NBA: `nba_api` (fallback)

- [`nba_api`](https://github.com/swar/nba_api) 1.12.0, MIT-licensed, wraps the undocumented stats.nba.com endpoints (box scores, play-by-play, player game logs, season history).
- The MIT licence covers the code, not the data: data is subject to the NBA.com Terms of Use ([PyPI](https://pypi.org/project/nba-api/1.12.0/)).
- Operationally fragile: it rate-limits and often blocks cloud IPs (AWS, GCP, Azure, Colab), and endpoints change without notice.
- Richer history and a far bigger audience, but further from the NBL story that makes this project relevant to LK Group.

## 3. Synthetic fixtures (always)

Hand-built or generated games in the canonical schema. No licensing risk, fully deterministic, and safe to commit. They're the only game data the repo ships, and the backbone of unit tests and the public eval set.

## Recommendation

1. Define a **canonical game model** and a `GameSource` adapter interface (ADR-0001).
2. Ship three adapters: `FixtureSource` (committed data), `LiveStatsSource` (NBL, fetched on demand into a git-ignored local cache), and optionally `NbaApiSource`.
3. **Never commit raw third-party feed data** (ADR-0006). Real-game evals run locally from the cache, and the public golden set uses synthetic games.
4. Before any commercial use, get written permission or a data licence. Track this as an open question in `docs/design.md`.

Sources: [Genius Sports / NBL partnership](https://www.geniussports.com/newsroom/australian-national-basketball-league-extends-data-technology-partnership-with-genius-sports-group/), [FIBA LiveStats box score example](https://fibalivestats.dcd.shared.geniussports.com/u/NBL/2120057/bs.html), [LiveStats TV feed docs](https://developer.geniussports.com/livestats/tvfeed/index_basketball.html), [nba_api on GitHub](https://github.com/swar/nba_api), [nba_api on PyPI](https://pypi.org/project/nba-api/1.12.0/).
