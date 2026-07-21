#!/usr/bin/env python3
"""EV validation piece 2 — empirical calibration (S231 commission spec).

Read-only against capture.db. Replicates evEngine.ts exactly:
geometric-midpoint true odds (lay rejected if <= back or > 2x back;
fallback back + 2 Betfair ticks), multiplicative field normalisation,
corrected-Harville place probs (gamma/delta/epsilon = 0.77/0.62/0.48).
"""
import math
import random
import sqlite3
import sys
from collections import defaultdict

DB = "file:/home/racing/racing-data-capture/data/capture.db?mode=ro"
GAMMA, DELTA, EPSILON = 0.77, 0.62, 0.48
random.seed(231)

# ---- Betfair tick ladder ---------------------------------------------------
LADDER = [(1.01, 2, 0.01), (2, 3, 0.02), (3, 4, 0.05), (4, 6, 0.1),
          (6, 10, 0.2), (10, 20, 0.5), (20, 30, 1), (30, 50, 2),
          (50, 100, 5), (100, 1000, 10)]

def add_ticks(price, n):
    p = price
    for _ in range(n):
        step = 10.0
        for lo, hi, s in LADDER:
            if lo <= p < hi:
                step = s
                break
        p = round(p + step, 2)
    return p

def true_odds(back, lay):
    if not back or back <= 1:
        return 1000.0
    if lay and lay > back and lay <= back * 2:
        return math.sqrt(back * lay)
    return add_ticks(back, 2)

def normalise(odds):
    implied = [1.0 / o if o > 1 else 0.0 for o in odds]
    t = sum(implied)
    return [p / t for p in implied] if t > 1e-12 else implied

def renorm_exp(probs, excluded, exponent):
    out = [0.0] * len(probs)
    t = 0.0
    for i, p in enumerate(probs):
        if i not in excluded and p > 1e-12:
            out[i] = p ** exponent
            t += out[i]
    if t == 0:
        return out
    return [v / t if i not in excluded else 0.0 for i, v in enumerate(out)]

def p_second(win, gamma=GAMMA):
    n = len(win)
    p2 = [0.0] * n
    for j in range(n):
        if win[j] < 1e-12:
            continue
        cond = renorm_exp(win, {j}, gamma)
        for i in range(n):
            p2[i] += win[j] * cond[i]
    return p2

def p_third(win, gamma=GAMMA, delta=DELTA):
    n = len(win)
    p3 = [0.0] * n
    for j in range(n):
        if win[j] < 1e-12:
            continue
        c2 = renorm_exp(win, {j}, gamma)
        for k in range(n):
            if k == j or c2[k] < 1e-12:
                continue
            c3 = renorm_exp(win, {j, k}, delta)
            for i in range(n):
                p3[i] += win[j] * c2[k] * c3[i]
    return p3

def p_fourth(win, gamma=GAMMA, delta=DELTA, eps=EPSILON):
    n = len(win)
    p4 = [0.0] * n
    for j in range(n):
        if win[j] < 1e-12:
            continue
        c2 = renorm_exp(win, {j}, gamma)
        for k in range(n):
            if k == j or c2[k] < 1e-12:
                continue
            c3 = renorm_exp(win, {j, k}, delta)
            for m in range(n):
                if m in (j, k) or c3[m] < 1e-12:
                    continue
                c4 = renorm_exp(win, {j, k, m}, eps)
                w = win[j] * c2[k] * c3[m]
                for i in range(n):
                    p4[i] += w * c4[i]
    return p4

# ---- Replica cross-check vs TS engine (S231 session values) -----------------
def crosscheck():
    field = [(3.5, 3.6), (4.9, 5.1), (6.4, 6.8), (8.8, 9.2), (12.0, 13.0),
             (16.0, 17.0), (21.0, 23.0), (27.0, 30.0), (38.0, 44.0), (60.0, 75.0)]
    win = normalise([true_odds(b, l) for b, l in field])
    p2, p3, p4 = p_second(win), p_third(win), p_fourth(win)
    got = (win[1] * 100, p2[1] * 100, p3[1] * 100, p4[1] * 100)
    want = (19.9, 17.0, 14.1, 11.4)
    ok = all(abs(g - w) <= 0.15 for g, w in zip(got, want))
    print("CROSSCHECK vs TS engine: got %.1f/%.1f/%.1f/%.1f want %s -> %s"
          % (*got, want, "PASS" if ok else "FAIL"))
    if not ok:
        sys.exit("replica does not match engine — aborting")

# ---- Load data ---------------------------------------------------------------
def load():
    con = sqlite3.connect(DB, uri=True)
    con.row_factory = sqlite3.Row
    print("win_result values:", dict(con.execute(
        "SELECT win_result, COUNT(*) FROM betfair_historical GROUP BY win_result")))
    rows = con.execute("""
        SELECT h.bf_win_market_id AS mkt, h.best_back_at_off AS back,
               h.best_lay_at_off AS lay, h.win_bsp AS bsp,
               h.win_result AS res, r.finish_position AS fp
        FROM betfair_historical h
        LEFT JOIN runners r ON h.runner_id = r.id
        WHERE h.bf_win_market_id IS NOT NULL""").fetchall()
    con.close()
    races = defaultdict(list)
    for r in rows:
        races[r["mkt"]].append(r)
    kept, drop_price, drop_winner, drop_small = {}, 0, 0, 0
    for mkt, rs in races.items():
        if len(rs) < 5:
            drop_small += 1
            continue
        if any(not r["back"] or r["back"] <= 1 for r in rs):
            drop_price += 1
            continue
        winners = sum(1 for r in rs if r["res"] == "WINNER")
        if winners != 1:
            drop_winner += 1
            continue
        kept[mkt] = rs
    print("races total=%d kept=%d dropped: no/bad price=%d, winners!=1 (dead-heat/void)=%d, field<5=%d"
          % (len(races), len(kept), drop_price, drop_winner, drop_small))
    return kept

# ---- Binning helpers ---------------------------------------------------------
def calib_table(pairs, nbins, label):
    """pairs: (predicted_prob, outcome 0/1). Quantile bins."""
    pairs = sorted(pairs)
    n = len(pairs)
    print(f"\n{label}  (N={n}, {nbins} quantile bins)")
    print("  bin   pred%   actual%   N      err(pts)")
    for b in range(nbins):
        lo, hi = b * n // nbins, (b + 1) * n // nbins
        chunk = pairs[lo:hi]
        if not chunk:
            continue
        pred = sum(p for p, _ in chunk) / len(chunk)
        act = sum(o for _, o in chunk) / len(chunk)
        se = math.sqrt(max(act * (1 - act), 1e-9) / len(chunk))
        flag = " *" if abs(pred - act) > 1.96 * se and len(chunk) >= 200 else ""
        print("  %2d   %6.2f  %6.2f   %-6d %+5.2f%s"
              % (b + 1, pred * 100, act * 100, len(chunk), (pred - act) * 100, flag))

def band_table(items, label):
    """items: (odds, predicted, outcome). Odds-band calibration."""
    bands = [(1.0, 2), (2, 4), (4, 6), (6, 10), (10, 20), (20, 1000)]
    print(f"\n{label} by odds band")
    print("  band       pred%   actual%   N")
    for lo, hi in bands:
        ch = [(p, o) for od, p, o in items if lo <= od < hi]
        if len(ch) < 200:
            continue
        pred = sum(p for p, _ in ch) / len(ch)
        act = sum(o for _, o in ch) / len(ch)
        print("  $%-4g-%-4g %6.2f  %6.2f   %d" % (lo, hi, pred * 100, act * 100, len(ch)))

# ---- Main --------------------------------------------------------------------
crosscheck()
races = load()

# Precompute per-race win probs (midpoint) once.
race_data = {}   # mkt -> (winprobs, rows)
for mkt, rs in races.items():
    win = normalise([true_odds(r["back"], r["lay"]) for r in rs])
    race_data[mkt] = (win, rs)

# TEST 1 — win calibration, midpoint vs BSP
mid_pairs, mid_band, bsp_pairs = [], [], []
for mkt, (win, rs) in race_data.items():
    odds = [true_odds(r["back"], r["lay"]) for r in rs]
    for i, r in enumerate(rs):
        out = 1 if r["res"] == "WINNER" else 0
        mid_pairs.append((win[i], out))
        mid_band.append((odds[i], win[i], out))
    if all(r["bsp"] and r["bsp"] > 1 for r in rs):
        bw = normalise([r["bsp"] for r in rs])
        for i, r in enumerate(rs):
            bsp_pairs.append((bw[i], 1 if r["res"] == "WINNER" else 0))
print("\n================ TEST 1 — WIN CALIBRATION ================")
calib_table(mid_pairs, 20, "T1a midpoint-at-off (engine method)")
band_table(mid_band, "T1a midpoint")
calib_table(bsp_pairs, 20, "T1b BSP (Betfair converged truth)")

# Ordinal subset: races where every runner has fp (full order known)
ordinal = {m: v for m, v in race_data.items()
           if all(v[1][i]["fp"] is not None for i in range(len(v[1])))}
part_ordinal = {m: v for m, v in race_data.items()
                if any(r["fp"] is not None for r in v[1])}
print("\nordinal races (full order)=%d, partial=%d" % (len(ordinal), len(part_ordinal)))

# TEST 2 — Harville place calibration on ordinal subset
p2_pairs, p3_pairs, cum23, cum234 = [], [], [], []
p4_sample_mkts = set(random.sample(sorted(ordinal), min(4000, len(ordinal))))
for mkt, (win, rs) in ordinal.items():
    p2 = p_second(win)
    p3 = p_third(win)
    p4 = p_fourth(win) if mkt in p4_sample_mkts else None
    for i, r in enumerate(rs):
        fp = r["fp"]
        p2_pairs.append((p2[i], 1 if fp == 2 else 0))
        p3_pairs.append((p3[i], 1 if fp == 3 else 0))
        cum23.append((p2[i] + p3[i], 1 if fp in (2, 3) else 0))
        if p4 is not None:
            cum234.append((p2[i] + p3[i] + p4[i], 1 if fp in (2, 3, 4) else 0))
print("\n================ TEST 2 — PLACE CALIBRATION ================")
calib_table(p2_pairs, 10, "T2a P(exactly 2nd), gamma=0.77")
calib_table(p3_pairs, 10, "T2b P(exactly 3rd), delta=0.62")
calib_table(cum23, 10, "T2c P(2nd or 3rd) — the 2+3 insurance shape")
calib_table(cum234, 10, "T2d P(2nd-4th), 4000-race sample — epsilon=0.48")

# TEST 2e — exponent refit (log-loss minimisation)
def logloss_gamma(g, mkts):
    ll = n = 0
    for mkt in mkts:
        win, rs = ordinal[mkt]
        p2 = p_second(win, g)
        for i, r in enumerate(rs):
            p = min(max(p2[i], 1e-9), 1 - 1e-9)
            y = 1 if r["fp"] == 2 else 0
            ll += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            n += 1
    return ll / n

def logloss_delta(g, d, mkts):
    ll = n = 0
    for mkt in mkts:
        win, rs = ordinal[mkt]
        p3 = p_third(win, g, d)
        for i, r in enumerate(rs):
            p = min(max(p3[i], 1e-9), 1 - 1e-9)
            y = 1 if r["fp"] == 3 else 0
            ll += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            n += 1
    return ll / n

all_ord = sorted(ordinal)
gam_mkts = sorted(random.sample(all_ord, min(6000, len(all_ord))))
grid = [round(0.50 + 0.025 * i, 3) for i in range(21)]  # 0.50 .. 1.00
best_g = min(grid, key=lambda g: logloss_gamma(g, gam_mkts))
# refine +-0.025 at step 0.005
fine = [round(best_g - 0.025 + 0.005 * i, 3) for i in range(11)]
gscore = {g: logloss_gamma(g, gam_mkts) for g in fine}
best_g = min(gscore, key=gscore.get)
del_mkts = sorted(random.sample(all_ord, min(4000, len(all_ord))))
dgrid = [round(0.40 + 0.025 * i, 3) for i in range(21)]  # 0.40 .. 0.90
dscore = {d: logloss_delta(best_g, d, del_mkts) for d in dgrid}
best_d = min(dscore, key=dscore.get)
print("\nT2e exponent refit: gamma fitted=%.3f (current 0.77), delta fitted=%.3f (current 0.62)"
      % (best_g, best_d))
print("   gamma logloss at 0.77=%.5f fitted=%.5f | delta at 0.62=%.5f fitted=%.5f"
      % (logloss_gamma(0.77, gam_mkts), gscore[best_g],
         logloss_delta(best_g, 0.62, del_mkts), dscore[best_d]))

# TEST 3 — insurance EV backtest, $2-$10 midpoint band, ordinal subset
print("\n================ TEST 3 — INSURANCE EV BACKTEST ($2-$10) ================")
def backtest(fb_rate):
    acc = {"FB_2nd": [[], []], "FB_23": [[], []], "CASH_2nd": [[], []],
           "NOPROMO": [[], []]}
    for mkt, (win, rs) in ordinal.items():
        odds = [true_odds(r["back"], r["lay"]) for r in rs]
        p2 = p_second(win)
        p3 = p_third(win)
        for i, r in enumerate(rs):
            o, fp = odds[i], r["fp"]
            if not (2.0 <= o <= 10.0):
                continue
            wn = 1 if r["res"] == "WINNER" else 0
            base_pred = (win[i] * o - 1)
            base_real = (o - 1) if wn else -1.0
            acc["NOPROMO"][0].append(base_pred)
            acc["NOPROMO"][1].append(base_real)
            for name, hit_pred, hit_real, rate in (
                ("FB_2nd", p2[i], fp == 2, fb_rate),
                ("FB_23", p2[i] + p3[i], fp in (2, 3), fb_rate),
                ("CASH_2nd", p2[i], fp == 2, 1.0),
            ):
                acc[name][0].append(base_pred + hit_pred * rate)
                acc[name][1].append(base_real + (rate if (hit_real and not wn) else 0.0))
    return acc

for fb in (0.60, 0.65, 0.70, 0.748):
    acc = backtest(fb)
    print(f"\n  FB valued at {fb*100:.1f}%:")
    print("  promo      predEV%  realEV%   N       SE")
    for name, (pred, real) in acc.items():
        n = len(pred)
        mp = sum(pred) / n * 100
        mr = sum(real) / n * 100
        var = sum((x * 100 - mr) ** 2 for x in real) / (n - 1)
        se = math.sqrt(var / n)
        print("  %-9s %+7.2f  %+7.2f  %-7d %.2f" % (name, mp, mr, n, se))

print("\nDONE")
