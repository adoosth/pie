# Archive

Working notes that produced today's rules but are not rules themselves. Read
them when you need to know *why* a decision went the way it did; never quote
them as current policy — `AGENTS.md` and `docs/DECISIONS.md` are.

| file | what it holds |
|---|---|
| `DECISIONS-2026-11.md.gz` | the full append-only decision log, 134 entries, 2026-11-05 … 2026-11-13 — the reasoning behind every rule in `docs/DECISIONS.md` |
| `CRITIC-2026-11.md.gz` | the critic's batch log: the Old Persian rounds, the Persian rounds, and each diagnosis that became a rule (`docs/CRITIC.md` keeps the protocol) |
| `UI_PLAN-2026-11.md.gz` | the interface plan the current page grew out of, including designs that were rejected |
| `LOANS_FA_AR.md.gz` | the Arabic-loan analysis of Persian that shaped the `ie_loan` / `non_pie` split |

Open one with `gunzip -c docs/archive/<file> | less`.
