#!/usr/bin/env python3
"""Post-probe analysis — read JSONL outputs and emit observations.

Run from the repo root or anywhere the data dir is reachable. Defaults
to ``dr029/2_1_race_data/api_probe_data/``. Prints a structured
report-skeleton block per section that ``api_probe_report.md`` consumes.

Sections covered:
- §1 execution summary (counts, errors)
- §2 field-availability matrix (top-level MarketBook keys + runner keys
  per phase, with non-null rates)
- §3.1 sp.actual_sp time-relative-to-jump curve per code
- §3.3 betfair field deltas vs the snapshot writer field set
- §3.4 1-second cadence-of-meaningful-change rates
- §3.5 Betfair ↔ Racing API identity alignment per race

§3.2 (cross-code shape parity) and §4 (anything surprising) are written
by hand against this output.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Snapshot writer field set per data_layer_current.md §4.4 + inspection §F
SNAPSHOT_WRITER_RUNNER_FIELDS = {
    "selection_id",      # selectionId
    "best_back_price",   # ex.availableToBack[0].price
    "best_back_size",    # ex.availableToBack[0].size
    "best_lay_price",    # ex.availableToLay[0].price
    "best_lay_size",     # ex.availableToLay[0].size
    "back_depth_json",   # top-3 ex.availableToBack
    "lay_depth_json",    # top-3 ex.availableToLay
    "total_matched",     # totalMatched (per runner)
    "runner_status",     # status
    "last_match_time",   # lastMatchTime (per runner where exposed)
    "matched_amount",    # matchedAmount
    "sp_near_price",     # sp.nearPrice
    "sp_far_price",      # sp.farPrice
    "bsp_price",         # sp.actualSP — column orphan, never populated
}

SNAPSHOT_WRITER_TOPLEVEL_FIELDS = {
    "market_status",         # status
    "num_priced_runners",    # numberOfActiveRunners
    "snapshot_time",         # writer timestamp (not from API)
    "minutes_to_start",      # writer-derived
    "snapshot_phase",        # writer-derived
}


def load_jsonl(path: Path):
    out = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def is_non_null(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)) and len(value) == 0:
        return False
    if isinstance(value, str) and value == "":
        return False
    return True


def collect_keys(obj, prefix="") -> set:
    """Flatten dict keys to dotted paths; include array element key sets."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            out.add(path)
            if isinstance(v, dict):
                out |= collect_keys(v, path)
            elif isinstance(v, list) and v:
                # use first non-null sample for nested keys
                for sample in v:
                    if isinstance(sample, dict):
                        out |= collect_keys(sample, f"{path}[]")
                        break
    return out


def field_availability_matrix(lines):
    """For each phase, count per-key non-null rate on top-level + runner objects."""
    phase_to_top_counts: dict = defaultdict(lambda: defaultdict(int))
    phase_to_top_total: dict = defaultdict(int)
    phase_to_runner_counts: dict = defaultdict(lambda: defaultdict(int))
    phase_to_runner_total: dict = defaultdict(int)
    phase_to_top_keys: dict = defaultdict(set)
    phase_to_runner_keys: dict = defaultdict(set)

    for line in lines:
        if line.get("api_error") and not line.get("response"):
            continue
        if line.get("projection_fallback_active") and line.get("projection_requested") == ["EX_LADDER"]:
            # Ladder-only fallback line — keep separate
            continue
        resp = line.get("response")
        if not isinstance(resp, dict):
            continue
        phase = line.get("phase_inferred", "UNKNOWN")
        # Top-level
        phase_to_top_total[phase] += 1
        for k, v in resp.items():
            if k == "runners":
                continue
            phase_to_top_keys[phase].add(k)
            if is_non_null(v):
                phase_to_top_counts[phase][k] += 1
        # Runners
        for r in resp.get("runners", []) or []:
            phase_to_runner_total[phase] += 1
            for rk, rv in r.items():
                phase_to_runner_keys[phase].add(rk)
                if is_non_null(rv):
                    phase_to_runner_counts[phase][rk] += 1
                # Recurse one level into sub-objects (sp, ex)
                if isinstance(rv, dict):
                    for sk, sv in rv.items():
                        path = f"{rk}.{sk}"
                        phase_to_runner_keys[phase].add(path)
                        if is_non_null(sv):
                            phase_to_runner_counts[phase][path] += 1
    return {
        "top_keys": phase_to_top_keys,
        "top_counts": phase_to_top_counts,
        "top_total": phase_to_top_total,
        "runner_keys": phase_to_runner_keys,
        "runner_counts": phase_to_runner_counts,
        "runner_total": phase_to_runner_total,
    }


def sp_actual_curve(lines):
    """Return per-(phase, minute_bucket) actual_sp non-null rate."""
    bucket_counts = defaultdict(lambda: [0, 0])  # [observed, with_actual_sp]
    for line in lines:
        if line.get("api_error") and not line.get("response"):
            continue
        resp = line.get("response")
        if not isinstance(resp, dict):
            continue
        mts = line.get("minutes_to_start", 0.0)
        # 5-min buckets
        bucket = int(mts // 5) * 5
        phase = line.get("phase_inferred", "UNKNOWN")
        for r in resp.get("runners", []) or []:
            sp = r.get("sp") or {}
            if not isinstance(sp, dict):
                continue
            bucket_counts[(phase, bucket)][0] += 1
            actual = sp.get("actualSP")
            if isinstance(actual, (int, float)) and actual > 0:
                bucket_counts[(phase, bucket)][1] += 1
    return bucket_counts


def cadence_change_rates(lines):
    """For best_back_price, best_lay_price, total_matched, market_status,
    runner_status: compute the rate at which value changes per second across
    consecutive snapshots, broken down by phase."""
    by_phase = defaultdict(lambda: {
        "samples": 0,
        "best_back_changes": 0,
        "best_lay_changes": 0,
        "total_matched_changes": 0,
        "market_status_changes": 0,
        "runner_status_changes": 0,
    })
    prev = None
    prev_phase = None
    prev_market_status = None
    prev_runner_status_by_id: dict = {}
    prev_best_back_by_id: dict = {}
    prev_best_lay_by_id: dict = {}
    prev_total_matched: float | None = None
    for line in lines:
        if line.get("projection_fallback_active") and line.get("projection_requested") == ["EX_LADDER"]:
            continue
        if line.get("api_error") and not line.get("response"):
            continue
        resp = line.get("response")
        if not isinstance(resp, dict):
            continue
        phase = line.get("phase_inferred", "UNKNOWN")
        # Market level
        market_status = resp.get("status")
        total_matched = resp.get("totalMatched")
        # Per-runner aggregate: count any change across any active runner
        any_back_change = False
        any_lay_change = False
        any_runner_status_change = False
        for r in resp.get("runners", []) or []:
            sid = r.get("selectionId")
            ex = r.get("ex") or {}
            atb = (ex.get("availableToBack") or [None])
            atl = (ex.get("availableToLay") or [None])
            bb_price = atb[0]["price"] if atb and atb[0] else None
            bl_price = atl[0]["price"] if atl and atl[0] else None
            if sid in prev_best_back_by_id and prev_best_back_by_id[sid] != bb_price:
                any_back_change = True
            if sid in prev_best_lay_by_id and prev_best_lay_by_id[sid] != bl_price:
                any_lay_change = True
            prev_best_back_by_id[sid] = bb_price
            prev_best_lay_by_id[sid] = bl_price
            rs = r.get("status")
            if sid in prev_runner_status_by_id and prev_runner_status_by_id[sid] != rs:
                any_runner_status_change = True
            prev_runner_status_by_id[sid] = rs

        if prev is not None:
            stats = by_phase[phase]
            stats["samples"] += 1
            if any_back_change:
                stats["best_back_changes"] += 1
            if any_lay_change:
                stats["best_lay_changes"] += 1
            if total_matched is not None and prev_total_matched is not None and total_matched != prev_total_matched:
                stats["total_matched_changes"] += 1
            if prev_market_status is not None and market_status != prev_market_status:
                stats["market_status_changes"] += 1
            if any_runner_status_change:
                stats["runner_status_changes"] += 1
        prev = line
        prev_market_status = market_status
        prev_total_matched = total_matched
    return by_phase


def betfair_runner_keys_observed(matrix):
    """Combined set of all runner keys ever observed across phases."""
    out = set()
    for ks in matrix["runner_keys"].values():
        out |= ks
    return out


def main(data_dir: Path) -> int:
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"manifest missing at {manifest_path}", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text())

    print("=" * 70)
    print("DR-029 §2.1 probe — analysis output")
    print("=" * 70)

    print(f"probe_run_id: {manifest.get('probe_run_id')}")
    print(f"started_at_utc: {manifest.get('started_at_utc')}")
    print(f"completed_at_utc: {manifest.get('completed_at_utc')}")
    print(f"projection_set_initial: {manifest.get('projection_set_initial')}")
    print(f"races: {len(manifest.get('races', []))}")
    print(f"api_events: {len(manifest.get('api_events', []))}")
    print()

    print("=== §1 — Probe execution summary ===")
    for r in manifest.get("races", []):
        print(
            f"  race={r['race_index']} {r['race_code']}/{r['venue']}/R{r['race_number']} "
            f"sched={r['scheduled_start_utc']} "
            f"bf_snaps={r.get('betfair_snapshots_count')} "
            f"ra_snaps={r.get('racingapi_snapshots_count')}"
        )
    print()
    print("api_events log:")
    for e in manifest.get("api_events", []):
        print(f"  [{e['ts_utc']}] race={e.get('race_index')} {e['event_type']}: {e.get('note', '')[:200]}")

    print()
    print("=== §2/§3.3 — Field availability per code per phase ===")
    code_to_lines = defaultdict(list)
    for r in manifest.get("races", []):
        bf_path = data_dir / r["betfair_data_file"]
        if not bf_path.exists():
            continue
        lines = load_jsonl(bf_path)
        code_to_lines[r["race_code"]].extend(lines)
        # Per-race section
        m = field_availability_matrix(lines)
        print(f"\n--- race={r['race_index']} {r['race_code']}/{r['venue']}/R{r['race_number']} ---")
        for phase in ("STANDARD", "INTENSIVE", "POST_START", "SUSPENDED", "CLOSED", "UNKNOWN"):
            if m["top_total"].get(phase, 0) == 0 and m["runner_total"].get(phase, 0) == 0:
                continue
            print(f"  phase={phase} (n_top={m['top_total'][phase]}, n_runner={m['runner_total'][phase]})")
            # Top-level non-null rates
            print("    top:")
            for k in sorted(m["top_keys"][phase]):
                rate = (m["top_counts"][phase].get(k, 0) / m["top_total"][phase]) if m["top_total"][phase] else 0
                print(f"      {k}: {rate * 100:.1f}%")
            # Runner non-null rates
            print("    runner:")
            for k in sorted(m["runner_keys"][phase]):
                rate = (m["runner_counts"][phase].get(k, 0) / m["runner_total"][phase]) if m["runner_total"][phase] else 0
                # Only list non-zero or always-present keys
                print(f"      {k}: {rate * 100:.1f}%")

    print()
    print("=== §3.1 — sp.actualSP time-relative-to-jump curve per code ===")
    for code, lines in code_to_lines.items():
        print(f"\nrace_code={code} (n_lines={len(lines)})")
        curve = sp_actual_curve(lines)
        # group by phase, then bucket
        per_phase = defaultdict(list)
        for (phase, bucket), (obs, with_sp) in curve.items():
            per_phase[phase].append((bucket, obs, with_sp))
        for phase in ("STANDARD", "INTENSIVE", "POST_START", "SUSPENDED", "CLOSED", "UNKNOWN"):
            buckets = sorted(per_phase.get(phase, []), key=lambda t: t[0])
            if not buckets:
                continue
            print(f"  phase={phase}")
            for bucket, obs, with_sp in buckets:
                rate = (with_sp / obs * 100) if obs else 0
                print(f"    minute_bucket=[{bucket},{bucket + 5}): observed={obs} with_actual_sp={with_sp} rate={rate:.1f}%")

    print()
    print("=== §3.3 — Field deltas vs snapshot writer ===")
    all_runner_keys = set()
    all_top_keys = set()
    for r in manifest.get("races", []):
        bf_path = data_dir / r["betfair_data_file"]
        if not bf_path.exists():
            continue
        lines = load_jsonl(bf_path)
        m = field_availability_matrix(lines)
        for ks in m["runner_keys"].values():
            all_runner_keys |= ks
        for ks in m["top_keys"].values():
            all_top_keys |= ks
    print(f"runner-level API keys observed (any phase, any race): {len(all_runner_keys)}")
    for k in sorted(all_runner_keys):
        print(f"  {k}")
    print()
    print(f"top-level API keys observed (any phase, any race): {len(all_top_keys)}")
    for k in sorted(all_top_keys):
        print(f"  {k}")

    print()
    print("=== §3.4 — Cadence-of-meaningful-change per phase ===")
    for code, lines in code_to_lines.items():
        print(f"\nrace_code={code}")
        cad = cadence_change_rates(lines)
        for phase, st in cad.items():
            n = st["samples"]
            if n == 0:
                continue
            print(f"  phase={phase} samples={n}")
            print(f"    best_back_change_rate: {st['best_back_changes'] / n * 100:.1f}%")
            print(f"    best_lay_change_rate: {st['best_lay_changes'] / n * 100:.1f}%")
            print(f"    total_matched_change_rate: {st['total_matched_changes'] / n * 100:.1f}%")
            print(f"    market_status_change_rate: {st['market_status_changes'] / n * 100:.1f}%")
            print(f"    runner_status_change_rate: {st['runner_status_changes'] / n * 100:.1f}%")

    print()
    print("=== §3.5 — Betfair ↔ Racing API identity alignment ===")
    for r in manifest.get("races", []):
        bf_path = data_dir / r["betfair_data_file"]
        ra_path = data_dir / r["racingapi_data_file"]
        if not bf_path.exists():
            continue
        bf_lines = load_jsonl(bf_path)
        ra_lines = load_jsonl(ra_path) if ra_path.exists() else []
        # Latest Betfair snapshot with runners
        bf_runners = []
        for line in reversed(bf_lines):
            resp = line.get("response")
            if isinstance(resp, dict) and resp.get("runners"):
                bf_runners = resp["runners"]
                break
        # Latest RA — find target race within the meet
        ra_runners = []
        ra_race_obj = None
        for line in reversed(ra_lines):
            resp = line.get("response")
            if not isinstance(resp, dict):
                continue
            races = resp.get("races") or []
            target_rn = str(r["race_number"])
            for rr in races:
                if str(rr.get("race_number")) == target_rn:
                    ra_race_obj = rr
                    ra_runners = rr.get("runners") or []
                    break
            if ra_runners:
                break
        print(f"\nrace={r['race_index']} {r['race_code']}/{r['venue']}/R{r['race_number']}")
        print(f"  bf_runners={len(bf_runners)} ra_runners={len(ra_runners)}")
        if ra_race_obj is not None:
            print(f"  ra off_time: {ra_race_obj.get('off_time')}  bf scheduled: {r['scheduled_start_utc']}")
            print(f"  ra venue: {ra_race_obj.get('course')}  bf venue: {r['venue']}")
        # Try to map bf selectionId → bf runnerName (from RUNNER_DESCRIPTION) → ra horse name
        # In our captures runner objects have selectionId but not name (catalogue not requeried in book).
        # Use ra runner-name list to align.
        ra_names = sorted([rn.get("horse") or "" for rn in ra_runners])
        print(f"  ra runners: {ra_names[:10]}{'...' if len(ra_names)>10 else ''}")
        # Scratch info
        ra_scratched = [rn.get("horse") for rn in ra_runners if rn.get("scratched") or rn.get("position") == "109"]
        bf_removed = [rr.get("selectionId") for rr in bf_runners if rr.get("status") == "REMOVED"]
        print(f"  ra_scratched={len(ra_scratched)} bf_removed_selection_ids={len(bf_removed)}")
        # Bookmaker odds shape
        if ra_runners:
            sample_odds = (ra_runners[0].get("odds") or [])
            book_names = [o.get("bookmaker") for o in sample_odds]
            print(f"  ra bundled bookmakers: {book_names}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default=str(Path(__file__).parent / "api_probe_data"),
        help="Directory containing JSONL files + manifest.json",
    )
    args = parser.parse_args()
    sys.exit(main(Path(args.data_dir)))
