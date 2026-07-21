#!/usr/bin/env python3
"""EV validation piece 2 — calibration v2 (S231).

v2 after adversarial review: adds (R3) Test-3 odds-band slicing, (R4)
clean-lay subset to isolate the no-lay-fallback inflation mechanism,
(R5) epsilon refit, (R9) ordinal-vs-dropped bias check + small-field
note, (R10) place dead-heat counts, (R11) fp<->win_result sanity
check, (R12) binning tie-break fix, (R15) per-test CSVs, (R1) Test 4
live-feed check included in the archived script/output.
Read-only against capture.db. Replicates evEngine.ts (crosscheck at
tolerance +-0.15 vs recorded TS outputs; reviewer independently
diffed the replica against the TS source and confirmed faithful).
"""
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict

DB = "file:/home/racing/racing-data-capture/data/capture.db?mode=ro"
GAMMA, DELTA, EPSILON = 0.77, 0.62, 0.48
CSVDIR = "/tmp/ev_validation_csv"
os.makedirs(CSVDIR, exist_ok=True)
random.seed(231)

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

def lay_ok(back, lay):
    return bool(lay and back and lay > back and lay <= back * 2)

def true_odds(back, lay):
    if not back or back <= 1:
        return 1000.0
    if lay_ok(back, lay):
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

def crosscheck():
    field = [(3.5, 3.6), (4.9, 5.1), (6.4, 6.8), (8.8, 9.2), (12.0, 13.0),
             (16.0, 17.0), (21.0, 23.0), (27.0, 30.0), (38.0, 44.0), (60.0, 75.0)]
    win = normalise([true_odds(b, l) for b, l in field])
    p2, p3, p4 = p_second(win), p_third(win), p_fourth(win)
    got = (win[1] * 100, p2[1] * 100, p3[1] * 100, p4[1] * 100)
    want = (19.9, 17.0, 14.1, 11.4)
    ok = all(abs(g - w) <= 0.15 for g, w in zip(got, want))
    print("CROSSCHECK vs recorded TS outputs (tol 0.15): got %.2f/%.2f/%.2f/%.2f -> %s"
          % (*got, "PASS" if ok else "FAIL"))
    if not ok:
        sys.exit("replica mismatch — aborting")

def load():
    con = sqlite3.connect(DB, uri=True)
    con.row_factory = sqlite3.Row
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
        if sum(1 for r in rs if r["res"] == "WINNER") != 1:
            drop_winner += 1
            continue
        kept[mkt] = rs
    print("races total=%d kept=%d dropped: price=%d winners!=1=%d field<5=%d"
          % (len(races), len(kept), drop_price, drop_winner, drop_small))
    return kept

def calib_table(pairs, nbins, label, csv=None):
    # R12: random tie-break so ties straddling a boundary don't sort by outcome
    pairs = sorted(pairs, key=lambda t: (t[0], random.random()))
    n = len(pairs)
    print(f"\n{label}  (N={n}, {nbins} quantile bins)")
    print("  bin   pred%   actual%   N      err(pts)")
    f = open(f"{CSVDIR}/{csv}.csv", "w") if csv else None
    if f:
        f.write("bin,pred_pct,actual_pct,n,err_pts,significant\n")
    for b in range(nbins):
        lo, hi = b * n // nbins, (b + 1) * n // nbins
        chunk = pairs[lo:hi]
        if not chunk:
            continue
        pred = sum(p for p, _ in chunk) / len(chunk)
        act = sum(o for _, o in chunk) / len(chunk)
        se = math.sqrt(max(act * (1 - act), 1e-9) / len(chunk))
        sig = abs(pred - act) > 1.96 * se and len(chunk) >= 200
        print("  %2d   %6.2f  %6.2f   %-6d %+5.2f%s"
              % (b + 1, pred * 100, act * 100, len(chunk), (pred - act) * 100,
                 " *" if sig else ""))
        if f:
            f.write("%d,%.4f,%.4f,%d,%.4f,%d\n"
                    % (b + 1, pred * 100, act * 100, len(chunk),
                       (pred - act) * 100, 1 if sig else 0))
    if f:
        f.close()

def band_table(items, label, csv=None):
    bands = [(1.0, 2), (2, 4), (4, 6), (6, 10), (10, 20), (20, 1000)]
    print(f"\n{label} by odds band")
    print("  band       pred%   actual%   N")
    f = open(f"{CSVDIR}/{csv}.csv", "w") if csv else None
    if f:
        f.write("band_lo,band_hi,pred_pct,actual_pct,n\n")
    for lo, hi in bands:
        ch = [(p, o) for od, p, o in items if lo <= od < hi]
        if len(ch) < 200:
            continue
        pred = sum(p for p, _ in ch) / len(ch)
        act = sum(o for _, o in ch) / len(ch)
        print("  $%-4g-%-4g %6.2f  %6.2f   %d" % (lo, hi, pred * 100, act * 100, len(ch)))
        if f:
            f.write("%g,%g,%.4f,%.4f,%d\n" % (lo, hi, pred * 100, act * 100, len(ch)))
    if f:
        f.close()

crosscheck()
races = load()
race_data = {}
for mkt, rs in races.items():
    win = normalise([true_odds(r["back"], r["lay"]) for r in rs])
    clean = all(lay_ok(r["back"], r["lay"]) for r in rs)
    isum = sum(1.0 / true_odds(r["back"], r["lay"]) for r in rs)
    race_data[mkt] = (win, rs, clean, isum)

n_clean = sum(1 for v in race_data.values() if v[2])
print("clean-lay races (every runner has usable lay): %d of %d" % (n_clean, len(race_data)))
print("mean implied sum: all=%.4f clean-only=%.4f fallback-races=%.4f"
      % (sum(v[3] for v in race_data.values()) / len(race_data),
         sum(v[3] for v in race_data.values() if v[2]) / max(n_clean, 1),
         sum(v[3] for v in race_data.values() if not v[2]) / max(len(race_data) - n_clean, 1)))

# R11: fp semantics sanity — fp==1 must coincide with win_result=WINNER
agree = disagree = 0
for mkt, (win, rs, clean, isum) in race_data.items():
    for r in rs:
        if r["fp"] is None:
            continue
        w = r["res"] == "WINNER"
        if (r["fp"] == 1) == w:
            agree += 1
        else:
            disagree += 1
print("R11 fp sanity: fp==1 <-> WINNER agree=%d disagree=%d (%.3f%%)"
      % (agree, disagree, 100.0 * disagree / max(agree + disagree, 1)))

# ---- TEST 1 -----------------------------------------------------------------
mid_pairs, mid_band, bsp_pairs = [], [], []
mid_band_clean, mid_band_fb = [], []
ord_band, nonord_band = [], []
for mkt, (win, rs, clean, isum) in race_data.items():
    odds = [true_odds(r["back"], r["lay"]) for r in rs]
    full_ord = all(r["fp"] is not None for r in rs)
    for i, r in enumerate(rs):
        out = 1 if r["res"] == "WINNER" else 0
        mid_pairs.append((win[i], out))
        mid_band.append((odds[i], win[i], out))
        (mid_band_clean if clean else mid_band_fb).append((odds[i], win[i], out))
        (ord_band if full_ord else nonord_band).append((odds[i], win[i], out))
    if all(r["bsp"] and r["bsp"] > 1 for r in rs):
        bw = normalise([r["bsp"] for r in rs])
        for i, r in enumerate(rs):
            bsp_pairs.append((bw[i], 1 if r["res"] == "WINNER" else 0))
print("\n================ TEST 1 — WIN CALIBRATION ================")
calib_table(mid_pairs, 20, "T1a midpoint-at-off (engine method)", csv="t1a_midpoint")
band_table(mid_band, "T1a midpoint", csv="t1a_bands")
calib_table(bsp_pairs, 20, "T1b BSP", csv="t1b_bsp")
band_table(mid_band_clean, "T1c clean-lay races only (no fallback anywhere)", csv="t1c_clean")
band_table(mid_band_fb, "T1d races containing >=1 no-lay fallback runner", csv="t1d_fallback")
band_table(ord_band, "T1e races WITH full finishing order (T2/T3 population)", csv="t1e_ordinal")
band_table(nonord_band, "T1f races WITHOUT full order (dropped from T2/T3)", csv="t1f_nonordinal")

ordinal = {m: v for m, v in race_data.items()
           if all(r["fp"] is not None for r in v[1])}
print("\nordinal races=%d of %d kept" % (len(ordinal), len(race_data)))

# R10: place dead-heat counts within ordinal set
dh2 = sum(1 for m, v in ordinal.items() if sum(1 for r in v[1] if r["fp"] == 2) > 1)
dh3 = sum(1 for m, v in ordinal.items() if sum(1 for r in v[1] if r["fp"] == 3) > 1)
no2 = sum(1 for m, v in ordinal.items() if sum(1 for r in v[1] if r["fp"] == 2) == 0)
print("R10 place dead-heats in ordinal set: 2nd=%d 3rd=%d | races with no fp==2=%d" % (dh2, dh3, no2))

# ---- TEST 2 -----------------------------------------------------------------
p2_pairs, p3_pairs, cum23, cum234 = [], [], [], []
place_cache = {}
p4_sample = set(random.sample(sorted(ordinal), min(4000, len(ordinal))))
for mkt, (win, rs, clean, isum) in ordinal.items():
    p2 = p_second(win)
    p3 = p_third(win)
    place_cache[mkt] = (p2, p3)
    p4 = p_fourth(win) if mkt in p4_sample else None
    for i, r in enumerate(rs):
        fp = r["fp"]
        p2_pairs.append((p2[i], 1 if fp == 2 else 0))
        p3_pairs.append((p3[i], 1 if fp == 3 else 0))
        cum23.append((p2[i] + p3[i], 1 if fp in (2, 3) else 0))
        if p4 is not None:
            cum234.append((p2[i] + p3[i] + p4[i], 1 if fp in (2, 3, 4) else 0))
print("\n================ TEST 2 — PLACE CALIBRATION ================")
calib_table(p2_pairs, 10, "T2a P(exactly 2nd), gamma=0.77", csv="t2a_second")
calib_table(p3_pairs, 10, "T2b P(exactly 3rd), delta=0.62", csv="t2b_third")
calib_table(cum23, 10, "T2c P(2nd or 3rd)", csv="t2c_cum23")
calib_table(cum234, 10, "T2d P(2nd-4th), 4000-race sample", csv="t2d_cum234")

def logloss_gamma(g, mkts):
    ll = n = 0
    for mkt in mkts:
        win, rs = ordinal[mkt][0], ordinal[mkt][1]
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
        win, rs = ordinal[mkt][0], ordinal[mkt][1]
        p3 = p_third(win, g, d)
        for i, r in enumerate(rs):
            p = min(max(p3[i], 1e-9), 1 - 1e-9)
            y = 1 if r["fp"] == 3 else 0
            ll += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            n += 1
    return ll / n

def logloss_eps(g, d, e, mkts):
    ll = n = 0
    for mkt in mkts:
        win, rs = ordinal[mkt][0], ordinal[mkt][1]
        p4 = p_fourth(win, g, d, e)
        for i, r in enumerate(rs):
            p = min(max(p4[i], 1e-9), 1 - 1e-9)
            y = 1 if r["fp"] == 4 else 0
            ll += -(y * math.log(p) + (1 - y) * math.log(1 - p))
            n += 1
    return ll / n

all_ord = sorted(ordinal)
gam_mkts = sorted(random.sample(all_ord, min(6000, len(all_ord))))
grid = [round(0.50 + 0.025 * i, 3) for i in range(21)]
best_g = min(grid, key=lambda g: logloss_gamma(g, gam_mkts))
fine = [round(best_g - 0.025 + 0.005 * i, 3) for i in range(11)]
gscore = {g: logloss_gamma(g, gam_mkts) for g in fine}
best_g = min(gscore, key=gscore.get)
del_mkts = sorted(random.sample(all_ord, min(4000, len(all_ord))))
dgrid = [round(0.40 + 0.025 * i, 3) for i in range(21)]
dscore = {d: logloss_delta(best_g, d, del_mkts) for d in dgrid}
best_d = min(dscore, key=dscore.get)
eps_mkts = sorted(random.sample(all_ord, min(1000, len(all_ord))))
egrid = [round(0.30 + 0.05 * i, 2) for i in range(9)]  # 0.30..0.70
escore = {e: logloss_eps(best_g, best_d, e, eps_mkts) for e in egrid}
best_e = min(escore, key=escore.get)
print("\nT2e refit (LOW-POWER — flat surface; constrains loosely, does not 'confirm'):")
print("  gamma fitted=%.3f (cur 0.77) logloss cur=%.5f fit=%.5f"
      % (best_g, logloss_gamma(0.77, gam_mkts), gscore[best_g]))
print("  delta fitted=%.3f (cur 0.62) logloss cur=%.5f fit=%.5f"
      % (best_d, logloss_delta(best_g, 0.62, del_mkts), dscore[best_d]))
print("  eps   fitted=%.2f (cur 0.48) logloss cur=%.5f fit=%.5f (1000-race sample)"
      % (best_e, logloss_eps(best_g, best_d, 0.48, eps_mkts), escore[best_e]))
print("  joint engine pair (0.77,0.62) delta-logloss=%.5f vs fitted pair=%.5f"
      % (logloss_delta(0.77, 0.62, del_mkts), dscore[best_d]))

# ---- TEST 3 -----------------------------------------------------------------
print("\n================ TEST 3 — INSURANCE EV BACKTEST ($2-$10) ================")
print("NOTE: internal-consistency check — bets priced at Betfair-fair midpoint;")
print("real book shading is NOT modelled. Not an achievable historical return.")

def backtest(fb_rate, band=None, clean_only=False, csvname=None):
    acc = {"FB_2nd": [[], []], "FB_23": [[], []], "CASH_2nd": [[], []],
           "NOPROMO": [[], []]}
    for mkt, (win, rs, clean, isum) in ordinal.items():
        if clean_only and not clean:
            continue
        odds = [true_odds(r["back"], r["lay"]) for r in rs]
        p2, p3 = place_cache[mkt]
        for i, r in enumerate(rs):
            o, fp = odds[i], r["fp"]
            lo, hi = band if band else (2.0, 10.0)
            if not (lo <= o <= hi):
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
    f = open(f"{CSVDIR}/{csvname}.csv", "w") if csvname else None
    if f:
        f.write("promo,pred_ev_pct,real_ev_pct,n,se_pct\n")
    for name, (pred, real) in acc.items():
        n = len(pred)
        if n < 200:
            continue
        mp = sum(pred) / n * 100
        mr = sum(real) / n * 100
        var = sum((x * 100 - mr) ** 2 for x in real) / (n - 1)
        se = math.sqrt(var / n)
        print("  %-9s %+7.2f  %+7.2f  %-7d %.2f" % (name, mp, mr, n, se))
        if f:
            f.write("%s,%.4f,%.4f,%d,%.4f\n" % (name, mp, mr, n, se))
    if f:
        f.close()

for fb in (0.60, 0.65, 0.70, 0.748):
    print(f"\n  T3a all $2-$10, FB at {fb*100:.1f}%:")
    print("  promo      predEV%  realEV%   N       SE")
    backtest(fb, csvname=f"t3a_fb{int(fb*1000)}")

for lo, hi in ((2.0, 4.0), (4.0, 6.0), (6.0, 10.0)):
    print(f"\n  T3b band ${lo:g}-${hi:g}, FB at 65%:")
    print("  promo      predEV%  realEV%   N       SE")
    backtest(0.65, band=(lo, hi), csvname=f"t3b_band_{int(lo)}_{int(hi)}")

print("\n  T3c clean-lay races only (no fallback anywhere), $2-$10, FB 65%:")
print("  promo      predEV%  realEV%   N       SE")
backtest(0.65, clean_only=True, csvname="t3c_cleanlay")

# ---- TEST 4 — live snapshot feed vs BSP --------------------------------------
print("\n================ TEST 4 — LIVE FEED vs BSP ================")
con = sqlite3.connect(DB, uri=True)
rows = con.execute("""
  SELECT race_id, best_back_price b, best_lay_price l, bsp_price bsp
  FROM betfair_snapshots
  WHERE bsp_price > 1 AND best_back_price > 1 AND best_lay_price > 1
    AND is_final_snapshot = 1""").fetchall()
con.close()
live = defaultdict(list)
for r in rows:
    live[r[0]].append(r)
diffs = []
n_races4 = 0
f = open(f"{CSVDIR}/t4_live_feed.csv", "w")
f.write("metric,value\n")
for rid, rs in live.items():
    if len(rs) < 5:
        continue
    mid = [true_odds(x[1], x[2]) for x in rs]
    mi = normalise(mid)
    bi = normalise([x[3] for x in rs])
    n_races4 += 1
    diffs += [abs(a - b) * 100 for a, b in zip(mi, bi)]
diffs.sort()
n = len(diffs)
stats = [("races", n_races4), ("runners", n),
         ("mean_pts", sum(diffs) / n), ("median_pts", diffs[n // 2]),
         ("p90_pts", diffs[int(n * 0.9)]), ("p99_pts", diffs[int(n * 0.99)])]
for k, v in stats:
    f.write("%s,%.4f\n" % (k, v))
f.close()
print("races=%d runners=%d | midpoint-vs-BSP prob diff: mean=%.2f median=%.2f p90=%.2f p99=%.2f pts"
      % (n_races4, n, sum(diffs) / n, diffs[n // 2], diffs[int(n * 0.9)], diffs[int(n * 0.99)]))
print("\nDONE")
