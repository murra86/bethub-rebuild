#!/usr/bin/env python3
"""DR-029 §2.1 follow-up — Saturday Betfair API observation probe.

Standalone, read-only. Runs from /home/racing/probe_output/ using
/home/racing/racing-data-capture/venv/bin/python3. Captures four AU WIN
markets sequentially (T-60min through CLOSED+45min): Betfair MarketBook
once per second with every priceProjection combined, plus Racing API
meet snapshot once per 30 seconds (carries Sportsbet/Ladbrokes odds
inside each runner). Writes raw JSONL per race + manifest.json. No
edits to analytical-line files; never opens capture.db.

See dr029/2_1_race_data/api_probe_brief.md for the full spec.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv("/home/racing/racing-data-capture/.env")

import betfairlightweight  # noqa: E402
import requests  # noqa: E402
from betfairlightweight.filters import market_filter, price_projection  # noqa: E402

PROBE_DIR = Path("/home/racing/probe_output")
DATA_DIR = PROBE_DIR / "api_probe_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = DATA_DIR / "manifest.json"
LOG_PATH = PROBE_DIR / "probe.log"

PROJECTIONS_FULL = [
    "EX_BEST_OFFERS",
    "EX_ALL_OFFERS",
    "EX_LADDER",
    "SP_AVAILABLE",
    "SP_TRADED",
]
PROJECTIONS_REDUCED = [
    "EX_BEST_OFFERS",
    "EX_ALL_OFFERS",
    "SP_AVAILABLE",
    "SP_TRADED",
]
PROJECTIONS_LADDER_ONLY = ["EX_LADDER"]

BETFAIR_CADENCE_S = 1.0
BETFAIR_SLOW_CADENCE_S = 2.0
RACING_API_CADENCE_S = 30.0
LADDER_FALLBACK_CADENCE_S = 10.0
PRE_RACE_LEAD_S = 60 * 60
POST_CLOSE_TAIL_S = 45 * 60

RACING_API_BASE = "https://api.theracingapi.com/v1"

ACST = timezone(timedelta(hours=9, minutes=30))

METRO_TB = {
    "Hawkesbury",
    "Eagle Farm",
    "Morphettville",
    "Bendigo",
    "Ascot",
    "Newcastle",
    "Caulfield",
    "Flemington",
    "Randwick",
    "Rosehill",
    "Moonee Valley",
    "Sandown",
    "Doomben",
    "Belmont",
    "Gold Coast",
}
METRO_HARNESS = {
    "Menangle",
    "Albion Park",
    "Melton",
    "Gloucester Park",
    "Mowbray",
    "Globe Derby",
}
METRO_GH = {
    "Wentworth Park",
    "The Meadows",
    "Albion Park",
    "Cannington",
    "Angle Park",
    "Q1 Lakeside",
    "Sandown Park",
    "Gosford",
    "Ballarat",
    "Q Straight",
}


def log(msg: str) -> None:
    line = f"[{datetime.now(timezone.utc).isoformat()}] {msg}"
    print(line, flush=True)
    try:
        with LOG_PATH.open("a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ts_pair(now: datetime | None = None) -> dict:
    now = now or utcnow()
    return {
        "ts_utc": now.isoformat().replace("+00:00", "Z"),
        "ts_acst": now.astimezone(ACST).isoformat(),
    }


def infer_race_code(event_name: str, market_name: str) -> str:
    text = f"{event_name} {market_name}".lower()
    if "pace" in text or "trot" in text:
        return "harness"
    return "thoroughbred"


def parse_event_venue(ev_name: str) -> str:
    return ev_name.split("(")[0].strip() if ev_name else ""


def parse_race_number(market_name: str) -> int | None:
    if not market_name:
        return None
    try:
        token = market_name.split()[0]
        return int(token.lstrip("Rr"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

state_lock = threading.Lock()
shutdown_evt = threading.Event()
manifest: dict = {
    "probe_run_id": None,
    "started_at_utc": None,
    "completed_at_utc": None,
    "races": [],
    "projection_set_initial": PROJECTIONS_FULL,
    "api_events": [],
}


def write_manifest() -> None:
    with state_lock:
        tmp = MANIFEST_PATH.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(manifest, f, indent=2, default=str)
        tmp.replace(MANIFEST_PATH)


def add_event(event_type: str, race_index: int | None = None, note: str = "") -> None:
    ev = {
        **ts_pair(),
        "race_index": race_index,
        "event_type": event_type,
        "note": note,
    }
    with state_lock:
        manifest["api_events"].append(ev)
    write_manifest()
    log(f"event {event_type} race_index={race_index}: {note}")


# ---------------------------------------------------------------------------
# Betfair login
# ---------------------------------------------------------------------------


def betfair_login() -> betfairlightweight.APIClient:
    trading = betfairlightweight.APIClient(
        username=os.getenv("BETFAIR_USERNAME"),
        password=os.getenv("BETFAIR_PASSWORD"),
        app_key=os.getenv("BETFAIR_APP_KEY"),
    )
    trading.login_interactive()
    return trading


# ---------------------------------------------------------------------------
# Race discovery and selection
# ---------------------------------------------------------------------------


def discover_races(trading) -> list[dict]:
    now = utcnow()
    from_dt = now
    end_of_day = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if end_of_day < now:
        end_of_day = now + timedelta(hours=14)
    to_dt = end_of_day + timedelta(hours=2)

    def _fetch(event_type_id: str):
        return trading.betting.list_market_catalogue(
            filter=market_filter(
                event_type_ids=[event_type_id],
                market_countries=["AU"],
                market_type_codes=["WIN"],
                market_start_time={
                    "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            ),
            market_projection=[
                "EVENT",
                "MARKET_START_TIME",
                "RUNNER_DESCRIPTION",
            ],
            sort="FIRST_TO_START",
            max_results=200,
        )

    horse_cats = _fetch("7")
    grey_cats = _fetch("4339")

    candidates = []
    for c in horse_cats:
        ev_name = c.event.name if c.event else ""
        venue = parse_event_venue(ev_name)
        market_name = c.market_name or ""
        rnum = parse_race_number(market_name)
        code = infer_race_code(ev_name, market_name)
        is_metro = venue in METRO_TB if code == "thoroughbred" else venue in METRO_HARNESS
        sched = c.market_start_time.replace(tzinfo=timezone.utc) if c.market_start_time else None
        candidates.append(
            dict(
                market_id=c.market_id,
                venue=venue,
                race_number=rnum,
                race_code=code,
                scheduled_start_dt=sched,
                is_metro=is_metro,
                runner_count=len(c.runners or []),
                market_name=market_name,
                event_name=ev_name,
            )
        )
    for c in grey_cats:
        ev_name = c.event.name if c.event else ""
        venue = parse_event_venue(ev_name)
        market_name = c.market_name or ""
        rnum = parse_race_number(market_name)
        is_metro = venue in METRO_GH
        sched = c.market_start_time.replace(tzinfo=timezone.utc) if c.market_start_time else None
        candidates.append(
            dict(
                market_id=c.market_id,
                venue=venue,
                race_number=rnum,
                race_code="greyhound",
                scheduled_start_dt=sched,
                is_metro=is_metro,
                runner_count=len(c.runners or []),
                market_name=market_name,
                event_name=ev_name,
            )
        )

    # Filter to future races (scheduled_start > now + small buffer).
    candidates = [c for c in candidates if c["scheduled_start_dt"] and c["scheduled_start_dt"] > now + timedelta(minutes=2)]
    candidates.sort(key=lambda c: c["scheduled_start_dt"])
    return candidates


def select_races(candidates: list[dict]) -> list[dict]:
    """Pick 4 races, sequential capture, ≥110min spacing, code mix.

    Quotas: 2 thoroughbred, 1 harness, 1 greyhound. Metro-priority within code.
    Falls back to any-quality if metros don't fit the schedule.
    """
    # Minimum gap between scheduled starts. race_N capture ends ~100min after
    # race_N_sched (5min suspended/closed + 45min POST_CLOSE_TAIL + settlement
    # variance). race_N+1 capture starts at race_N+1_sched - 60min. So gap
    # ≥ 160min keeps captures fully sequential without truncation.
    sep = timedelta(minutes=160)
    desired = {"thoroughbred": 2, "harness": 1, "greyhound": 1}

    def _filter(code: str, after_dt: datetime, used_ids: set, metro_only: bool, min_runners: int):
        out = []
        for c in candidates:
            if c["race_code"] != code:
                continue
            if c["market_id"] in used_ids:
                continue
            if c["scheduled_start_dt"] < after_dt:
                continue
            if metro_only and not c["is_metro"]:
                continue
            if c["runner_count"] < min_runners:
                continue
            out.append(c)
        return out

    selected: list[dict] = []
    used_ids: set = set()
    code_taken: dict = defaultdict(int)
    now = utcnow()

    # Priority among codes when the relax tier ties: thoroughbred first
    # (anchor code per brief §4.1), then harness, then greyhound.
    code_rank = {"thoroughbred": 0, "harness": 1, "greyhound": 2}

    while len(selected) < 4:
        after_dt = (selected[-1]["scheduled_start_dt"] + sep) if selected else now
        deficits = {k: desired[k] - code_taken[k] for k in desired if desired[k] - code_taken[k] > 0}
        if not deficits:
            break
        # At each relax tier, gather the EARLIEST eligible race per code in
        # deficit, then take the earliest across codes — breaks ties by
        # code rank (TB > harness > greyhound).
        picked = None
        for metro, min_r in ((True, 8), (True, 6), (False, 6), (False, 0)):
            per_code_first = []
            for code in deficits:
                pool = _filter(code, after_dt, used_ids, metro, min_r)
                if pool:
                    per_code_first.append((pool[0]["scheduled_start_dt"], code_rank[code], pool[0]))
            if per_code_first:
                per_code_first.sort(key=lambda t: (t[0], t[1]))
                picked = per_code_first[0][2]
                break
        if not picked:
            # Cross-code fallback: any race after after_dt at all (still future-spaced).
            pool = [c for c in candidates if c["scheduled_start_dt"] >= after_dt and c["market_id"] not in used_ids]
            if not pool:
                break
            picked = pool[0]
        selected.append(picked)
        used_ids.add(picked["market_id"])
        code_taken[picked["race_code"]] += 1

    return selected


# ---------------------------------------------------------------------------
# Racing API helpers
# ---------------------------------------------------------------------------


def racing_api_auth() -> tuple[str, str] | None:
    u = os.getenv("RACING_API_USERNAME")
    p = os.getenv("RACING_API_PASSWORD")
    if not u or not p:
        return None
    return (u, p)


def racing_api_get(endpoint: str, params: dict | None = None, timeout: int = 30):
    auth = racing_api_auth()
    if not auth:
        raise RuntimeError("Racing API credentials missing")
    url = f"{RACING_API_BASE}{endpoint}"
    r = requests.get(url, params=params, auth=auth, timeout=timeout)
    r.raise_for_status()
    return r.json()


def find_racing_api_meet(date_str: str, betfair_venue: str, race_code: str) -> tuple[str | None, dict | None]:
    """Find a Racing API meet matching the Betfair venue.

    Racing API venues use raw course names (e.g. "Eagle Farm", "Albion Park").
    Betfair event names use the same. Match case-insensitively, prefer exact.
    """
    try:
        data = racing_api_get("/australia/meets", params={"date": date_str})
    except Exception as e:
        log(f"racing_api meets fetch failed: {e}")
        return None, None
    meets = data["meets"] if isinstance(data, dict) and "meets" in data else (data if isinstance(data, list) else [])
    norm_target = betfair_venue.lower().strip()
    # Exact match first
    for m in meets:
        if (m.get("course") or "").lower().strip() == norm_target:
            return m.get("meet_id"), m
    # Prefix / contains fallback (e.g. "Q1 Lakeside" -> "Q1 Lakeside Park" type variations)
    for m in meets:
        course = (m.get("course") or "").lower().strip()
        if norm_target and (norm_target in course or course in norm_target):
            return m.get("meet_id"), m
    return None, None


# ---------------------------------------------------------------------------
# Per-race capture loops
# ---------------------------------------------------------------------------


def write_jsonl(path: Path, payload: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(payload, default=str) + "\n")


def betfair_loop(trading, race_entry: dict, stop_evt: threading.Event, race_state: dict) -> None:
    market_id = race_entry["market_id"]
    sched = race_entry["scheduled_start_dt"]
    out_path = DATA_DIR / race_entry["betfair_data_file"]
    consecutive_errors = 0
    consecutive_slow = 0
    fallback_active = False
    ladder_only_consec_errors = 0
    ladder_only_disabled = False
    last_ladder_only_call = 0.0
    cadence = BETFAIR_CADENCE_S
    snapshots = 0
    first_ts = None
    last_ts = None
    closed_observed_at = None

    while not stop_evt.is_set():
        loop_start = time.monotonic()
        now = utcnow()

        proj = PROJECTIONS_REDUCED if fallback_active else PROJECTIONS_FULL
        api_error = None
        response_obj = None
        request_ms = None
        try:
            t0 = time.monotonic()
            books = trading.betting.list_market_book(
                market_ids=[market_id],
                price_projection=price_projection(price_data=proj),
                lightweight=True,
            )
            request_ms = int((time.monotonic() - t0) * 1000)
            response_obj = books[0] if books else None
            consecutive_errors = 0
            if request_ms is not None and request_ms > 2000:
                consecutive_slow += 1
            else:
                consecutive_slow = 0
        except Exception as e:
            api_error = str(e)
            consecutive_errors += 1
            log(f"race={race_entry['race_index']} bf err {api_error}")

        # Phase inference
        market_status = (response_obj or {}).get("status") if isinstance(response_obj, dict) else None
        minutes_to_start = (now - sched).total_seconds() / 60.0
        # we want minutes_to_start to be negative pre-jump
        minutes_to_start = round((sched - now).total_seconds() / 60.0 * -1, 3)
        # Actually: minutes_to_start is "minutes since start"; pre-jump it's negative.
        minutes_to_start = round((now - sched).total_seconds() / 60.0, 3)
        if market_status == "CLOSED" and closed_observed_at is None:
            closed_observed_at = now
            race_state["closed_at"] = now
            add_event("market_closed", race_entry["race_index"], f"first CLOSED at {now.isoformat()}")
        if market_status == "OPEN":
            phase = "STANDARD" if minutes_to_start < -5 else "INTENSIVE" if minutes_to_start < 0 else "POST_START"
        elif market_status == "SUSPENDED":
            phase = "SUSPENDED"
        elif market_status == "CLOSED":
            phase = "CLOSED"
        else:
            phase = "UNKNOWN"

        line = {
            **ts_pair(now),
            "source": "betfair",
            "race_code": race_entry["race_code"],
            "venue": race_entry["venue"],
            "race_number": race_entry["race_number"],
            "scheduled_start_utc": sched.isoformat().replace("+00:00", "Z"),
            "minutes_to_start": minutes_to_start,
            "phase_inferred": phase,
            "market_id": market_id,
            "projection_requested": proj,
            "projection_fallback_active": fallback_active,
            "request_duration_ms": request_ms,
            "api_error": api_error,
            "response": response_obj,
        }
        write_jsonl(out_path, line)
        snapshots += 1
        if first_ts is None:
            first_ts = line["ts_utc"]
        last_ts = line["ts_utc"]

        # Adaptive: TOO_MUCH_DATA + EX_LADDER -> drop ladder. Fail fast (1
        # consecutive error is enough — if combined-with-ladder fails once,
        # this market does not allow EX_LADDER on this app key).
        if api_error and not fallback_active and (
            "TOO_MUCH_DATA" in api_error
            or "DSC-0018" in api_error
            or "INVALID_INPUT_DATA" in api_error
        ):
            fallback_active = True
            add_event(
                "ex_ladder_fallback",
                race_entry["race_index"],
                f"dropping EX_LADDER from combined call: {api_error[:200]}",
            )
            consecutive_errors = 0

        # Rate-limit guard
        if consecutive_errors > 3 or consecutive_slow > 5:
            if cadence < BETFAIR_SLOW_CADENCE_S:
                cadence = BETFAIR_SLOW_CADENCE_S
                add_event(
                    "cadence_halved",
                    race_entry["race_index"],
                    f"errors={consecutive_errors} slow={consecutive_slow}",
                )

        # If fallback active, periodically attempt an EX_LADDER-only line.
        # On 5 consecutive failures, mark ladder unsupported on this key and
        # stop attempting it (logged in api_events). One successful capture
        # resets the failure counter.
        if fallback_active and not ladder_only_disabled:
            now_mono = time.monotonic()
            if now_mono - last_ladder_only_call >= LADDER_FALLBACK_CADENCE_S:
                ladder_err = None
                ladder_obj = None
                rms = None
                try:
                    t0 = time.monotonic()
                    books2 = trading.betting.list_market_book(
                        market_ids=[market_id],
                        price_projection=price_projection(price_data=PROJECTIONS_LADDER_ONLY),
                        lightweight=True,
                    )
                    rms = int((time.monotonic() - t0) * 1000)
                    ladder_obj = books2[0] if books2 else None
                    ladder_only_consec_errors = 0
                except Exception as e:
                    ladder_err = str(e)
                    ladder_only_consec_errors += 1
                # Always write the line — even an error is observation-bonus
                line2 = {
                    **ts_pair(),
                    "source": "betfair",
                    "race_code": race_entry["race_code"],
                    "venue": race_entry["venue"],
                    "race_number": race_entry["race_number"],
                    "scheduled_start_utc": sched.isoformat().replace("+00:00", "Z"),
                    "minutes_to_start": round((utcnow() - sched).total_seconds() / 60.0, 3),
                    "phase_inferred": phase,
                    "market_id": market_id,
                    "projection_requested": PROJECTIONS_LADDER_ONLY,
                    "projection_fallback_active": True,
                    "request_duration_ms": rms,
                    "api_error": ladder_err[:500] if ladder_err else None,
                    "response": ladder_obj,
                }
                write_jsonl(out_path, line2)
                snapshots += 1
                if ladder_only_consec_errors >= 5:
                    ladder_only_disabled = True
                    add_event(
                        "ex_ladder_unsupported",
                        race_entry["race_index"],
                        "ladder-only call rejected 5x consecutively — disabling for remainder of race",
                    )
                last_ladder_only_call = now_mono

        # End condition: 45min past first CLOSED observation
        if closed_observed_at is not None and (now - closed_observed_at).total_seconds() >= POST_CLOSE_TAIL_S:
            log(f"race={race_entry['race_index']} betfair loop done — {snapshots} snapshots")
            break

        # Safety hard stop: 4h after sched (covers protests/photo finishes)
        if (now - sched).total_seconds() >= 4 * 3600:
            log(f"race={race_entry['race_index']} betfair safety stop @ 4h after sched")
            break

        elapsed = time.monotonic() - loop_start
        sleep_for = max(0.0, cadence - elapsed)
        if shutdown_evt.wait(sleep_for):
            break

    race_state["betfair_snapshots"] = snapshots
    race_state["betfair_first_ts"] = first_ts
    race_state["betfair_last_ts"] = last_ts


def racing_api_loop(race_entry: dict, stop_evt: threading.Event, race_state: dict) -> None:
    sched = race_entry["scheduled_start_dt"]
    date_str = sched.strftime("%Y-%m-%d")
    venue = race_entry["venue"]
    race_code = race_entry["race_code"]

    # Find meet (Racing API only covers thoroughbred AU; for harness/greyhound we still try)
    meet_id, meet_obj = find_racing_api_meet(date_str, venue, race_code)
    if not meet_id:
        add_event(
            "racing_api_meet_missing",
            race_entry["race_index"],
            f"no Racing API meet for venue={venue!r} date={date_str} code={race_code}",
        )
        race_state["racing_api_snapshots"] = 0
        return

    out_path = DATA_DIR / race_entry["racingapi_data_file"]
    snapshots = 0
    first_ts = None
    last_ts = None
    consecutive_errors = 0

    while not stop_evt.is_set():
        loop_start = time.monotonic()
        api_error = None
        request_ms = None
        response_obj = None
        try:
            t0 = time.monotonic()
            response_obj = racing_api_get(f"/australia/meets/{meet_id}/races")
            request_ms = int((time.monotonic() - t0) * 1000)
            consecutive_errors = 0
        except Exception as e:
            api_error = str(e)
            consecutive_errors += 1
            log(f"race={race_entry['race_index']} racing_api err {api_error}")

        line = {
            **ts_pair(),
            "source": "racing_api",
            "endpoint": f"/australia/meets/{meet_id}/races",
            "race_code": race_entry["race_code"],
            "venue": race_entry["venue"],
            "race_number": race_entry["race_number"],
            "scheduled_start_utc": sched.isoformat().replace("+00:00", "Z"),
            "minutes_to_start": round((utcnow() - sched).total_seconds() / 60.0, 3),
            "meet_id": meet_id,
            "request_duration_ms": request_ms,
            "api_error": api_error,
            "response": response_obj,
        }
        write_jsonl(out_path, line)
        snapshots += 1
        if first_ts is None:
            first_ts = line["ts_utc"]
        last_ts = line["ts_utc"]

        if consecutive_errors >= 5:
            add_event(
                "racing_api_persistent_error",
                race_entry["race_index"],
                f"5 consecutive errors, halting RA stream for this race: {api_error}",
            )
            break

        elapsed = time.monotonic() - loop_start
        sleep_for = max(0.0, RACING_API_CADENCE_S - elapsed)
        if shutdown_evt.wait(sleep_for):
            break

    race_state["racing_api_snapshots"] = snapshots
    race_state["racing_api_first_ts"] = first_ts
    race_state["racing_api_last_ts"] = last_ts


# ---------------------------------------------------------------------------
# Per-race orchestration
# ---------------------------------------------------------------------------


def capture_race(trading, race_entry: dict) -> None:
    sched = race_entry["scheduled_start_dt"]
    capture_start = sched - timedelta(seconds=PRE_RACE_LEAD_S)
    log(
        f"race={race_entry['race_index']} {race_entry['race_code']}/"
        f"{race_entry['venue']}/R{race_entry['race_number']} "
        f"sched={sched.isoformat()} capture_start={capture_start.isoformat()}"
    )

    # Idle wait until T-60min
    while utcnow() < capture_start:
        if shutdown_evt.is_set():
            return
        time.sleep(min(30.0, max(1.0, (capture_start - utcnow()).total_seconds())))

    add_event("race_capture_start", race_entry["race_index"], f"market_id={race_entry['market_id']}")

    stop_evt = threading.Event()
    race_state: dict = {}
    bf_thread = threading.Thread(
        target=betfair_loop,
        args=(trading, race_entry, stop_evt, race_state),
        name=f"bf-{race_entry['race_index']}",
        daemon=True,
    )
    ra_thread = threading.Thread(
        target=racing_api_loop,
        args=(race_entry, stop_evt, race_state),
        name=f"ra-{race_entry['race_index']}",
        daemon=True,
    )
    bf_thread.start()
    ra_thread.start()

    # Betfair thread is the master: when it ends (45min post-CLOSED), stop RA
    bf_thread.join()
    stop_evt.set()
    ra_thread.join(timeout=60)

    # Update manifest
    with state_lock:
        for r in manifest["races"]:
            if r["race_index"] == race_entry["race_index"]:
                r["betfair_captured"] = bool(race_state.get("betfair_snapshots", 0))
                r["betfair_snapshots_count"] = race_state.get("betfair_snapshots", 0)
                r["racingapi_captured"] = bool(race_state.get("racing_api_snapshots", 0))
                r["racingapi_snapshots_count"] = race_state.get("racing_api_snapshots", 0)
                r["first_snapshot_ts_utc"] = race_state.get("betfair_first_ts")
                r["last_snapshot_ts_utc"] = race_state.get("betfair_last_ts")
                break
    write_manifest()
    add_event(
        "race_capture_done",
        race_entry["race_index"],
        f"bf_snaps={race_state.get('betfair_snapshots', 0)} ra_snaps={race_state.get('racing_api_snapshots', 0)}",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def install_signal_handlers() -> None:
    def _handler(signum, frame):
        log(f"signal {signum} received — shutting down gracefully")
        shutdown_evt.set()

    signal.signal(signal.SIGTERM, _handler)
    signal.signal(signal.SIGINT, _handler)


def keep_alive_loop(trading) -> None:
    """Renew Betfair session every ~3h."""
    while not shutdown_evt.is_set():
        if shutdown_evt.wait(3 * 3600):
            return
        try:
            trading.keep_alive()
            log("betfair keep_alive ok")
        except Exception as e:
            log(f"betfair keep_alive err: {e}")


def main() -> int:
    install_signal_handlers()
    log("=== probe.py start ===")
    manifest["probe_run_id"] = "2026-05-02_saturday_metros"
    manifest["started_at_utc"] = utcnow().isoformat().replace("+00:00", "Z")
    write_manifest()

    log("logging in to Betfair...")
    trading = betfair_login()
    log("betfair login ok")

    keep_alive_thread = threading.Thread(target=keep_alive_loop, args=(trading,), name="bf-keepalive", daemon=True)
    keep_alive_thread.start()

    log("discovering Saturday races...")
    candidates = discover_races(trading)
    log(f"discovered {len(candidates)} candidate markets")
    selections = select_races(candidates)
    if not selections:
        log("no races selected — exiting")
        manifest["completed_at_utc"] = utcnow().isoformat().replace("+00:00", "Z")
        write_manifest()
        return 1

    # Populate manifest race entries
    for i, s in enumerate(selections, start=1):
        venue_safe = s["venue"].replace(" ", "_").replace("/", "_")
        bf_file = f"race_{i}_{s['race_code']}_{venue_safe}_{s['race_number']}_betfair.jsonl"
        ra_file = f"race_{i}_{s['race_code']}_{venue_safe}_{s['race_number']}_racingapi.jsonl"
        s["race_index"] = i
        s["betfair_data_file"] = bf_file
        s["racingapi_data_file"] = ra_file
        manifest_entry = {
            "race_index": i,
            "race_code": s["race_code"],
            "venue": s["venue"],
            "race_number": s["race_number"],
            "scheduled_start_utc": s["scheduled_start_dt"].isoformat().replace("+00:00", "Z"),
            "market_id": s["market_id"],
            "is_metro": s["is_metro"],
            "runner_count_at_discovery": s["runner_count"],
            "betfair_captured": False,
            "betfair_snapshots_count": None,
            "betfair_data_file": bf_file,
            "racingapi_captured": False,
            "racingapi_snapshots_count": None,
            "racingapi_data_file": ra_file,
            "first_snapshot_ts_utc": None,
            "last_snapshot_ts_utc": None,
        }
        manifest["races"].append(manifest_entry)
        log(
            f"selected #{i}: {s['race_code']} {s['venue']} R{s['race_number']} "
            f"@ {s['scheduled_start_dt'].isoformat()} (metro={s['is_metro']}, runners={s['runner_count']})"
        )
    write_manifest()

    # Capture each race in order
    for s in selections:
        if shutdown_evt.is_set():
            break
        try:
            capture_race(trading, s)
        except Exception as e:
            log(f"capture_race exception: {e}\n{traceback.format_exc()}")
            add_event(
                "race_capture_exception",
                s.get("race_index"),
                f"{type(e).__name__}: {e}",
            )

    manifest["completed_at_utc"] = utcnow().isoformat().replace("+00:00", "Z")
    write_manifest()
    log("=== probe.py complete ===")

    try:
        trading.logout()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
