# Race EV & variance panel — implementation / rollout approach (S253)

## §0 STATE OF THE WORLD — READ FIRST (corrected after adversarial review)

**This is already live. It deployed itself when I ran `npm run build`.**

The earlier claim in this plan and in `SESSION_253.md` §4d — "built and green on
disk, NOT deployed" — was **wrong**, and I verified the correction myself:

- `BetHub.command` (PID 78428) and its uvicorn have been up since 23 Jul;
- `ui/api/static_serving.py` serves `dist` **from disk on every request**
  (`FileResponse` / `StaticFiles`), so there is no separate deploy step;
- `curl localhost:8787/` returns `assets/index-qvbi27G1.js` — the exact bundle
  a fresh `npm run build` produces — and that bundle contains the new panel.

**On this architecture `npm run build` IS the deploy.** Every verification build
I ran today shipped the code. The Fri/Sat/Sun-Mon calendar below was never a
control: the launcher rebuilds from whatever is in `src/` on any restart, and
the standing schedule includes a Friday restart.

### Two things needed immediate action (both done)
1. **The app could not have restarted.** A review agent left scratch tests in
   `ui/web/src/__adv__/`, inside the `tsconfig` root, so `npm run build` exited
   2 — and `BetHub.command` does `npm run build || exit 1`. Closing and
   relaunching would have produced **no app**, the evening before a race day.
   Files moved to the scratchpad; build restored (same bundle hash); suite
   410/410.
2. **`.claude/` (828 MB of agent worktrees) was untracked and un-ignored** — a
   `git add -A` would have committed it. Added to `.gitignore`.

### The S232 condition is live: HARD REFRESH REQUIRED
`dist/assets` was rewritten under the running app today. Old asset URLs now
404 and `index.html` is served with **no `Cache-Control`**, which is exactly the
S232 "BetHub not opening" blank-page mechanism. **Press Cmd-Shift-R on the
BetHub window before using it.**

### Decision required — keep, or roll back
- **(1) Keep it live** and run the verification pass (§4) this evening, ~15h
  before Saturday racing. Defensible: change B is a *convergence fix* (§1B).
- **(2) Roll back tonight, app-down:** `git stash` → `npm run build` →
  relaunch → hard refresh, then deploy properly Sun/Mon.

Everything below is the plan for the remaining work (committing it, verifying
it, and being able to reverse it) — not for "getting it live", which has
happened.

## 1. What is actually changing, and where the risk sits

Two very different kinds of change are sitting in the working tree, and they
should NOT be treated as one thing.

**A. Additive — new surfaces, nothing existing behaves differently.**
- new files: `ev/racePortfolio.ts`, `ev/racePortfolioInputs.ts`,
  `components/RacePortfolioPanel.*` (+ their tests);
- `routes/Racing.tsx` gains the panel and passes `raceMarginal` to the card;
- `components/ConfirmCard.tsx` gains an optional marginal line that renders
  only when the prop is supplied.
- Risk: **low**. Read-only, no money-path writes. Worst case is a panel showing
  a wrong number — bad, but it cannot alter a bet, a balance or a settlement.

**B. A CONVERGENCE FIX to an existing surface — one line.**
*(Rewritten after review: I had this backwards. The risk is in NOT shipping it.)*
- `components/OddsTable.tsx` field filter: `!== 'REMOVED' && !== 'WITHDRAWN'`
  → `=== 'ACTIVE'`.
- **It changes no stamped value.** All three persisted stamps already used
  `=== 'ACTIVE'` at HEAD and are untouched by this diff: `promo_ev_at_log`
  (via `evAtLogForRunner`, Racing.tsx HEAD:132), `grade_at_log` (HEAD:442) and
  `field_size_at_placement` (HEAD:699 → `record_builder.py:430`).
- So before this change, on any race with a `REMOVED_VACANT`/`HIDDEN` runner,
  **the column the operator reads and the number the app records were computed
  over different fields.** B removes that divergence. Deferring B means every
  vacant-trap race until deploy is bet off a column that disagrees with the
  record.
- Risk: low, and *negative* if deferred.

**A and B still ship as SEPARATE COMMITS** — not because B is dangerous, but so
either can be attributed or reversed independently. **Commit B must include
`components/OddsTable.test.tsx`**: reverting the code alone leaves 2 failing
tests, and `npm run build` (`tsc -b && vite build`) never runs vitest, so a red
suite would not block a launch.

## 2. Calendar

Standing schedule: **Fri** = operator app restart + sanity pass; **Sat** = race
day, **NO deploys**; **Sun/Mon** = deploy block. Today is Fri 24 Jul.

- **Fri (today):** nothing goes live. Code stays uncommitted or committed but
  unbuilt. Operator's normal Friday sanity pass runs against the CURRENT app.
- **Sat:** untouched. Race day. This is also a free opportunity — see §5.
- **Sun/Mon:** commit, build, restart, verify (§4). This is the deploy window.

No exception is worth taking here: the one change that could mislead a bet
(§1B) would be landing the day before a race day if we rushed it.

## 3. Deploy mechanics

The app serves a **static `dist`** — there is no dev server, and the standing
lesson from S232 is **never rebuild the served frontend under a running app**.
The launcher rebuilds `dist` app-down automatically.

Sequence:
0. **`git status --porcelain` must show ONLY the 14 intended files.** Nothing
   unexpected under `ui/web/src/` — any stray file there is compiled by the
   launcher and a type error is a hard app-down. (This bit us today.)
0.5 **Run `npm run build` while the app is STILL UP** and require exit 0. Never
   discover a build failure with no running app.
1. `.claude/` into `.gitignore` (done), then `git checkout -b s253-race-panel`
   and explicit `git add <path>` lists — **never `git add -A`** (828 MB of
   agent worktrees sit untracked).
2. Commit A (feature), then commit B (`OddsTable.tsx` **and**
   `OddsTable.test.tsx`) separately.
3. Operator **closes the BetHub window** (app down).
4. Operator double-clicks `BetHub.command` — the launcher rebuilds and starts.
5. **Hard refresh (Cmd-Shift-R)** and confirm the page renders — the S232
   blank-page condition is real and is live today.
6. Verification pass (§4) before any real bet is placed off the new numbers.

Launcher caveat: its staleness check covers only `src`, `index.html`,
`package.json`, `vite.config.ts` — **not** `tsconfig*.json`, `package-lock.json`
or `public/`. Changes to those serve a stale bundle silently; rebuild by hand.

Backups: no DB backup is needed (nothing here writes to the money path), and
the launcher takes a `sqlite3 .backup` on every launch anyway (keep-30).

No database change, no migration, no backup required: nothing here writes to
the money path or alters a schema. (Stating that explicitly because the usual
pre-deploy DB backup ritual is genuinely not needed and doing it would imply a
risk that does not exist.)

## 4. Verification pass, in order — before betting off it

Run on a real race with a live market. Stop and revert at the first failure.

| # | Check | Pass condition |
|---|---|---|
| 1 | App starts, race page renders, browser console clean | no errors |
| 2 | Race with **no** bets on it | panel shows the invite, not a false zero |
| 3 | Race with a bet already on it | panel shows race EV in $ and %, and "$X at risk" matching the real stake |
| 4 | **Additivity check** (replaces a bad check — the panel's race-aggregate at locked prices and the column's live candidate EV at a typed price are different quantities and *should* differ) | arm a runner, note the confirm card's ΔEV, log it — the panel's race EV must rise by **exactly** that ΔEV |
| 11 | **The worst case: a wrongly EXCLUDED live runner** (silently corrupts every EV on the card) | on a normal thoroughbred race, "N active runners" equals the un-struck row count **and** the real field; every struck-through row is a genuine scratching |
| 12 | A **settled** race (all runners leave ACTIVE) | degrades to dashes, not a crash or a confident zero |
| 13 | **Proof the new code is actually live** | after relaunch, the asset hash in `view-source:localhost:8787` has changed |
| 5 | Arm a runner (click LOG) | the marginal line **is visible on the confirm card**, not hidden behind it |
| 6 | Arm a runner you already hold | reads "concentrates" |
| 7 | Arm an uncovered runner | reads "steadies" |
| 8 | **Greyhound race with a vacant trap** | field count excludes the trap; "N active runners" is the real number |
| 9 | Watch the last 60s before a jump | page stays responsive; numbers move with price, don't jitter when prices are static |
| 10 | A race holding a free bet | panel says "$X can't be valued here", NOT "no promo bets on this race" |

Check 4 is the important one — it is the single check that proves the three
surfaces agree, which is precisely what was broken before this round.

## 5. ~~Free dress rehearsal on Saturday~~ — WITHDRAWN

I claimed we could "re-run the offline benchmark" against Saturday's settled
results. **No such harness exists** — review grepped the whole repo and found
nothing; `racePortfolio.model.test.ts` is a unit test against
`harvillePlaceProbs`, not an outcome replay. Building one is new work, not a
free check. Offered honestly as a follow-on if wanted (~half a session), not as
part of this rollout.

## 6. Rollback

- **Feature (A) misbehaving:** revert commit A, rebuild app-down. The tool
  returns to exactly today's behaviour; nothing else depends on the new files.
- **Odds-table (B) suspected:** revert commit B alone. The column returns to
  its previous numbers instantly; the panel keeps working (it computes its own
  field) — the two will simply disagree again on vacant-trap races, which is
  the status quo we have lived with.
- Rollback is a git revert plus an app-down rebuild. No data to unwind.

## 7. What the operator should expect to LOOK different

Stated plainly so a correct change is not mistaken for a regression:
- a new "This race" panel under the odds table;
- a new line on the confirm card when a runner is armed;
- **the promo EV column will read differently on races containing a vacant trap
  or hidden runner** — change B working as intended, not a bug. On a measured
  8-box greyhound race with one vacant trap the same bet moved 42.59% → 45.02%.
- **Expect STEP changes, not nudges.** The corrected field size also feeds
  `droppedInsuredPositions`, so an 8→7 correction can *drop an insured
  position* entirely (BetRight excludes 3rd at ≤7 runners — your own standing
  lesson). The EV can move discretely, and the "3rd not covered" banner can
  appear where it previously didn't. That is the clause finally being applied
  to the true field size.

## 8. Post-deploy watch (first race day after go-live)

- the standing daily money check and bankroll==bank-app check must be unchanged
  (they should be — nothing here touches money);
- spot-check 2–3 races: does the panel's race EV equal the sum of the odds-table
  EVs for the bets actually on;
- note any race where the panel and the column disagree — that now indicates a
  real defect rather than a known one.

## 9. Deliberately NOT in this rollout

Carried as known and accepted, not blockers:
- the P&L range can hop on a sub-tick price move (outcome support is discrete);
- ~2% of single-bet races show a positive EV beside a wholly-negative likely
  range (arithmetically correct, reads oddly);
- multi-leg bets would attribute their whole stake to one race (latent — every
  live bet is single-leg);
- the bet-side filter relies on a server-side `side or "BACK"` coalesce.
