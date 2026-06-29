# Session 19 log

**Date:** 2026-04-28 (Adelaide local, ACST)
**Open:** 21:19 ACST
**Close:** ~22:15 ACST
**Duration:** ~55 minutes

---

## Scope going in

(1) `data_layer_current.md` — companion document for the multi-agent governance review. New file. Descriptive document covering capture.db's current state, fields, cadence, gaps. Operator-Claude session pattern for empirical bits.

(2) Multi-agent governance review orchestration if capacity permitted (realistically Session 20).

Carry-out triggers: context tightening, operator fatigue, scope larger than current-state-doc shape. Bias toward closing early.

## Scope completed

**(1) data_layer_current.md created and operator-confirmed.** 184 lines, ~3–4 pages, in compression band alongside architecture_current.md (158 lines). Nine sections: framing, what capture.db is, current operational reality (with analytical-vs-operational distinction), race-data fields (schema-defined with empirical state deferred to DR-029 verification), bookmaker-data fields (schema-defined, including new §5.4 on operational soft-book live pricing with four architectural responses), known gaps (with population-state visibility named as a gap itself), data API contract surface vs DR-029 requirements, two v3-stakes questions for assessors, document scope notes.

**(2) NOT started.** Carries to Session 20 as planned. Operator chose close-out at ~22:15 ACST per established bias-toward-closing-early pattern (now seventeen consecutive early-close sessions).

## Substantive operator-discoveries during session

Three structurally-significant findings emerged from operator review of the draft, each materially strengthening the document for the multi-agent review.

**Discovery 1 — Operator familiarity with capture.db has decayed.** Operator's blanket response when asked for empirical population-state details across §§4.1–4.5, 5.1, 5.2, 6 was "I'm not sure, I'm not familiar with the VPS data capture fields anymore." Reframed sections 4–6 to schema-defined-with-empirical-verification-deferred-to-DR-029 rather than asserting state operator could not confirm. Added paragraph to §3 naming operator-familiarity-decay as same-root-cause as the reachability gap (data layer with no real active consumer accumulates uncertainty about its own state). Strengthens the Session 18 reachability finding into a two-surface framing in §8 Question 1.

**Discovery 2 — Decodo rotating residential proxy and cadence-on-reflection.** Operator added that VPS scrapers route through Decodo rotating residential proxy (factual addition to §5.1 explaining why current scrapers aren't blocked despite scraping protected books). Operator also reacted strongly to the documented 60-second pre-jump and in-running cadence: "feels woefully slow for what we need (close to jump and race duration should really be every second)."

**Discovery 3 — Analytical-versus-operational structural distinction.** Operator reflection on cadence surfaced that the existing documents have quietly conflated two structurally different data needs: analytical (post-hoc, retained, latency-tolerant) vs operational (sub-second, ephemeral, in-the-moment). For Betfair the operational pattern is uncontroversial (Streaming API). For soft-book the operational pattern is structurally harder (frequency-blocking risk, proxy economics, asymmetric detection arms race). Four plausible architectural responses identified: A in-scope build, B out-of-scope with staleness indicator, C on-demand per-burst-review, D third-party odds-feed vendor. Operator flagged vendor-scan as separate pre-decision homework. Edits made: extension to §3 (analytical-vs-operational paragraph), redirect of §4.4 (correctly proportioning bracketing-vs-operational), new §5.4 (operational soft-book with four architectural responses), restructured §8 into two questions (Q1 reachability+fitness, Q2 operational live pricing with 6a Betfair / 6b soft-book A/B/C/D).

## Tools used

- Desktop Commander: list_directory, read_file, write_file, edit_block, start_process — primary tools throughout, bash sandbox not reaching rebuild folder per filesystem note.

## Files touched

**Created:**
- `data_layer_current.md` (184 lines)
- `sessions/SESSION_19.md` (this file, archived from session_log.md at close)

**Edited:**
- `work_in_progress.md` (Session 19 close update — see close-out)

**Backups cleaned at close:**
- `.close_out_backups/SESSION_17_20260428T1920/` (carried from Session 18, was not cleaned despite Session 18 close-out summary stating it had been — small discipline drift, no operational consequence)
- `.close_out_backups/SESSION_18_20260428T210642/` (per Session 19 opening prompt directive)

**Backups created at close:**
- `.close_out_backups/SESSION_19_<timestamp>/`

**Pre-existed and not edited:**
- decision_under_review.md
- decisions.md
- architecture_current.md
- v3_data_requirements.md
- governance.md
- vision.md
- README.md
- architecture.md

## Lessons applied / discipline maintained

- **Session 15 lesson:** verified pre-condition polarities against this session's actual file movements before scripting close-out (see close-out script).
- **Session 16 lesson:** "FILES MOVED? VERIFIED." print before success-logged manifest in close-out script.
- **Session 18 standing instruction:** for empirical questions about v2/capture.db state, verify via codebase + log inspection rather than trusting operator memory. Applied differently this session — operator candidly stated unfamiliarity, so the document was reframed honestly rather than asserting state from any source. Same discipline, different surface.
- **DR-021:** Adelaide local time anchored at session open via TZ command.
- **DR-028 orientation discipline:** named DR-027 and DR-028 explicitly in orientation summary.
- **Standing instruction (Session 18+):** session-close opening prompt for Session 20 generated as part of close-out.

## Discipline drift noted

Session 18 close-out summary stated SESSION_17 backup had been cleaned, but it persisted into Session 19 open. No operational consequence; backup contents verified recoverable from canonical files before cleanup at this close. Worth noting for future close-out script reliability — verification of cleanup actually happening should be part of the script's closing manifest rather than asserted post-hoc in the human-readable summary.

## Open items going into Session 20

**Session 20 first priority:** Multi-agent governance review orchestration. Three independent assessment agents — software dev (fresh Claude), PM (GPT-5 or Gemini), skeptic (whichever non-Claude wasn't used for PM). Each given the full doc suite: DUR + v3_data_requirements + architecture_current + data_layer_current. Plus open_questions.md authored by an independent agent reading the factual + decision documents and surfacing what hasn't been asked. Then judge synthesis (fresh Claude session, given all three assessments). Synthesise rather than choose.

**Session 20+ carry-forward:**
- Build strategy decision (strangler-fig vs clean break + slice strategy) — post multi-agent review.
- DR-029 data review scoping after multi-agent review approves direction.

**Operator pre-decision-homework, separate from Session 20:**
- Vendor scan for third-party odds-feed vendors (§5.4 Option D). Whether suitable vendors exist for v3's specific day-one book list at acceptable cost. Informs whether 6b in the multi-agent review has four real options or three.
- VPS tunnel restart (~/Library/LaunchAgents/com.bethub.vps-tunnel.plist exists but isn't running, tunnel down 6+ days). Doesn't block Session 20 documentation work; worth restoring before any v3 build session that would actually exercise the integration.

**Parked separately:**
- Operator-Claude context-retention concern from Session 17 (folded into DUR Section 6 as secondary assessor ask; meta-governance fix is separate).
