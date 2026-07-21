# Router/SIM Proxy Gateway — Status & Resume Point

**Session:** 2026-07-03 → 2026-07-04; hub bring-up session 2026-07-07 (see §9 — supersedes §7 where they differ)
**Status:** ✅ Hub arrived + proven; **all 3 routers verified end-to-end via hub** (one at a time — only ONE data-capable micro-USB cable found). Blocked on buying 2–3 micro-USB **data** cables, then it's plug-in-and-go.
**Related docs:** `router_sim_proxy_gateway_brief.md` (design), `router_sim_proxy_gateway_phase1_guide.md` (beginner build steps), `router_sim_proxy_gateway_hub_bringup.md` (hub bring-up pack, 2026-07-07).

---

## 1. What this is

Let each AdsPower betting-account profile egress the internet through its **own TP-Link M7350 4G router/SIM**, via a **Raspberry Pi 5** acting as a multi-homed SOCKS5 proxy. Goal: switch accounts by switching a browser window, not by juggling networks. Each account keeps a **sticky mobile IP**, which is safer than switching.

Path of a bet:
```
Laptop (AdsPower) --home WiFi--> Raspberry Pi --USB--> Router/SIM --4G--> Internet
```

## 2. What's DONE and WORKING

- ✅ **M7350 works over USB on the Pi** (RNDIS) — the big unknown, resolved.
- ✅ **Two accounts live end-to-end**, each pinned to its own SIM (see mapping below).
- ✅ **Reboot-proof** — proxies come back automatically on Pi restart.
- ✅ **Swap workflow is hands-off** — plug a router in, wait ~15s, open its profile; the proxy re-syncs itself.
- ✅ **Fail-closed & no IP creep** — a profile whose router isn't plugged gets a dead connection, never a leak or the wrong SIM.
- ✅ **Pi's own traffic stays on home WiFi** — only account browsing uses SIM data.

### The live mapping (immutable: Account → SIM → Router → Subnet → Port → Profile)

| Account | Router name | SIM | Router subnet | Proxy port | AdsPower profile | Verified egress |
|---|---|---|---|---|---|---|
| A | **Kate-Router** | Optus | `192.168.2.x` | 3001 | Profile A (Kate) | 49.178.215.115 (AS4804/Optus) |
| B | **Sarie-Router** | Vodafone | `192.168.3.x` | 3002 | Profile B (Sarie) | 120.20.7.155 (AS133612/Vodafone) |
| C | **Mads-Router** | Vocus MVNO (iPrimus/Dodo family) | `192.168.4.x` | 3003 | Profile C (Mads) *(being created)* | 58.178.145.222 (AS9443/Vocus Retail) |
| D | *(4th, future)* | — | `192.168.5.x` | 3004 | — | — |

(Router naming per operator 2026-07-07: **Kate-Router** = Optus/3001, **Sarie-Router** = Vodafone/3002, **Mads-Router** = Vocus/3003.
Egress IPs are the SIMs' current mobile IPs — they rotate with carrier leases; the AS is the constant.)

Home network = `192.168.0.x` (Pi = `192.168.0.162`, laptop = `192.168.0.196`).

## 3. Interim workflow (until the powered hub arrives)

The Pi can only power **one** M7350 at a time directly (overcurrent with 2+). So for now:

**To switch accounts:** close current profile's browser → unplug its router → plug the other router → **wait ~15 seconds** → open the matching profile. That's it (the auto-refresh handles the rest). Only ever have open the profile whose router is plugged in.

## 4. As-built configuration (on the Pi)

- **OS:** Raspberry Pi OS "trixie" (Debian 13). Headless, controlled via **TigerVNC over home WiFi (`wlan0`)**.
- **Proxy software:** **`3proxy`** (built from source 2026-07-07 — not in trixie repos; needed
  `libssl-dev`; binary at `/usr/local/bin/3proxy`). Replaced microsocks to get **per-lane DNS**
  (`nserver <gateway>` per instance) after ipleak.net showed proxy DNS leaking via home ISP
  (Superloop). Each lane now resolves through its own SIM's carrier resolver. microsocks-era
  script kept at `/usr/local/bin/sim-proxy.sh.microsocks.bak` for instant revert.
- **Identity fix** `/etc/systemd/network/10-rndis-modems.link` — the M7350s ship with **identical serial (`c53795b3`) and MAC (`3a:3d:dc:fd:d1:29`)**, so they'd collide. This gives each a distinct name+MAC by physical port:
  ```
  [Match]
  Driver=rndis_host
  [Link]
  NamePolicy=path
  MACAddressPolicy=random
  ```
- **Proxy script** `/usr/local/bin/sim-proxy.sh <subnet-prefix> <table> <port>` — finds the interface on that subnet, sets policy routing (`ip rule from <ip> table <N>` + default route in table N via `<prefix>.1`), deletes that interface's default from the main table (so Pi stays on WiFi), sets `rp_filter=2`, then runs `microsocks -p <port> -b <ip>`. Robust to the modem's IP changing.
- **Services** (systemd, `Restart=always`, enabled):
  - `sim-proxy.service`  → `sim-proxy.sh 192.168.2 101 3001` (Optus)
  - `sim-proxy2.service` → `sim-proxy.sh 192.168.3 102 3002` (Vodafone)
- **Auto-refresh** `/etc/NetworkManager/dispatcher.d/60-sim-refresh` — restarts `sim-proxy sim-proxy2 sim-proxy3` on any modem interface `up`/`down`/`dhcp4-change`, so a replug/IP-change re-syncs automatically. (`sim-proxy3` in the loop is harmless until that service exists.)
- **AdsPower profiles:** proxy = SOCKS5, host `192.168.0.162`, port `3001`/`3002`, no auth. WebRTC disabled; timezone/location/language "Based on IP". AdsPower fails **closed** by default (dead proxy = error, never the real IP) — no toggle needed; only risk is a system-wide VPN over the top.

## 5. Hardware notes

- **Powered hub being bought: Simplecom CHU810** (48W, 12V/4A, 10-port, per-port switches). From **Bunnings** (click-and-collect in Adelaide) or PC Case Gear (~$65) / Amazon AU.
  - ⚠️ **Plug modems into the BLUE ports only** (USB 3.0 data). The **RED** ports are charge-only (no data) — a modem there charges but won't be seen by the Pi. 6 blue ports = plenty for 4 modems.
- Need **one data-capable micro-USB cable per modem** (test: plug a modem alone, `lsusb | grep M7350` should show it).
- Modems must stay **powered** (hub feeds them) and, if ever used over WiFi, in range.

## 6. Key gotchas learned (DO NOT repeat)

1. **Never turn the Pi's WiFi off** to "isolate" a modem — it kills VNC and locks you out. (Recovery that worked: join the laptop to a modem's own WiFi, then VNC to the Pi at its modem-side IP.)
2. **Never kernel-disable IPv6** (`net.ipv6.conf.*.disable_ipv6=1`) — it broke microsocks (it tries IPv6 dests and won't fall back to IPv4 → all traffic dies). Reverted. See §7 for the correct IPv6 plan.
3. **Modems have identical serial+MAC** — must be distinguished by physical USB port (the `.link` file). Don't rely on MAC.
4. **Plug modems in slowly / one at a time** to avoid the inrush overcurrent (the hub's per-port switches solve this — flip them on sequentially).
5. **Replug changes a modem's IP** (random MAC → new DHCP lease); the auto-refresh dispatcher handles it, so don't hand-restart unless the dispatcher is missing.

## 7. WHERE TO PICK UP (next session)

### A. When the CHU810 hub arrives — the main next step
1. Plug hub into wall + Pi (USB-A upstream). Modems into **blue** ports, powered on **one at a time** via the per-port switches.
2. Verify all modems enumerate together (we've only ever run one at a time): `lsusb | grep M7350` (expect one line per modem), `ip -4 -o addr show` (expect each subnet `.2/.3/.4`), and test each port from the laptop returns the right carrier.
3. **Watch for netplan `match: {}` contention** — the `netplan-eth0` connection matches all ethernet devices; with several modems + the real `eth0`, one may not configure. If a modem enumerates but gets no IP, we'll add per-device handling.
4. Once all up: it's true **window-switching**, no swapping.

### B. Add Router #3 (Account C)
- Create `sim-proxy3.service` → `sim-proxy.sh 192.168.4 103 3003`, `daemon-reload`, `enable --now`.
- Create/point its **AdsPower profile** (this is the new profile that still needs making) → SOCKS5 `192.168.0.162:3003`.

### C. Proper IPv6 lockdown (needed once multiple modems run at once)
- With several modems live, IPv4 (policy-routed per SIM) and IPv6 (uncontrolled, one default path) could point at **different** SIMs → red flag. In single-modem mode it's the SIM's own IPv6 (consistent), so it's fine for now.
- **Correct fix:** an **AAAA-filtering local resolver** (e.g. `dnsmasq` with `filter-AAAA`) so microsocks only ever gets IPv4 addresses. **Test that it doesn't break traffic** (unlike the kernel-disable, which did).

### D. Hardening / polish (optional, not urgent)
- **Stable Pi home IP** — set a DHCP reservation on the home router for the Pi (`192.168.0.162`) so AdsPower always finds it.
- **Firewall** the proxy ports (nftables) to the laptop's IP only.
- **Monitoring** — a heartbeat that checks each port's egress IP + alerts on failure/wrong-IP.
- **Docs:** the `..._brief.md` still describes 3proxy/systemd-networkd; reality is microsocks + boot-script + numeric routing tables + NM dispatcher. Update when convenient.

## 8. Quick-reference commands (on the Pi)

```bash
# What modems are physically seen / addressed
lsusb | grep M7350
ip -4 -o addr show

# Proxy service health / logs
systemctl --no-pager status sim-proxy sim-proxy2
sudo journalctl -u sim-proxy2 -n 20 --no-pager

# Which way the Pi itself reaches the internet (should be dev wlan0)
ip route get 1.1.1.1
```
```bash
# Test a port from the LAPTOP (expect the SIM's carrier)
curl --socks5-hostname 192.168.0.162:3001 https://ipinfo.io/json   # Optus
curl --socks5-hostname 192.168.0.162:3002 https://ipinfo.io/json   # Vodafone
curl --socks5-hostname 192.168.0.162:3003 https://ipinfo.io/json   # Vocus MVNO (router C)
```

## 9. Session 2026-07-07 — hub bring-up (supersedes §7 where they differ)

**Result: the CHU810 hub + all 3 routers are PROVEN end-to-end.** Each router was tested
one at a time through a blue hub port: correct subnet came up, proxy self-synced, laptop
egress showed the right carrier (Optus AS4804 / Vodafone AS133612 / Vocus AS9443).
Router #3 was already pre-configured on `192.168.4.x` — no admin work needed.

**LATER SAME DAY: cables found → ALL THREE MODEMS LIVE SIMULTANEOUSLY. System OPERATIONAL.**
(Cable lesson stands for router #4: most micro-USB cables are charge-only and fail
*silently* — zero kernel events. Test any new cable: plug modem in → `lsusb | grep M7350`.)

**Simultaneous verification (2026-07-07 ~15:15):** 3001→Optus AS4804, 3002→Vodafone
AS133612, 3003→Vocus AS9443 — all at the same instant; Pi's own traffic on wlan0;
dual-stack sites fine via IPv4 through the proxies; v6-only hosts unreachable (good).

**Multi-modem fixes applied same session (all persistent):**
- `netplan-eth0` NM profile: `ipv4.never-default yes`, `ipv6.never-default yes`,
  **`ipv6.method disabled`** → modems never hijack the Pi's default route (was
  routing Pi OS traffic via the Vocus SIM), and the §C IPv6 cross-SIM leak is
  CLOSED at the config level (no v6 addr/route on any modem — NOT the kernel
  disable that broke microsocks). **dnsmasq AAAA-filter plan no longer needed.**
  ⚠️ Side-effect: if the Pi is ever wired via real `eth0`, that profile now gives
  it no default route/IPv6 — revisit then.
- All 3 services got a drop-in `no-start-limit.conf` (`StartLimitIntervalSec=0`):
  a dispatcher restart-storm (replug/reconnect flurry) tripped systemd's start
  rate-limit and stranded all proxies in `failed` — can't happen again.

**DNS leak found + fixed (2026-07-07, ipleak.net in Kate profile):** browsing IP was pure
Optus, IPv6 dead, WebRTC clean — but DNS showed **Superloop (home ISP)** resolvers: the Pi
resolved proxy lookups via home WiFi's DNS, a cross-account linkage fingerprint. Fixed twice
over: (1) Pi resolv order → carrier gateways `192.168.2.1/.3.1/.4.1` first (all three modems
DO serve DNS; Sarie's 1.1.1.1 DHCP advert was cosmetic), home ISP demoted to 4th (beyond
glibc's 3-server use); (2) **microsocks → 3proxy migration** for true per-lane DNS: each
lane's `nserver` = its own SIM gateway, so Kate resolves via Optus, Sarie via Vodafone,
lane C via Vocus — no shared resolver fingerprint across accounts at all. Config template
is generated per-start by `sim-proxy.sh` into `/run/3proxy-<port>.cfg`. All 3 lanes verified
post-migration (right carrier each + v6-only host unreachable). **PHASE 1 HARDENING APPLIED (2026-07-07, after 3-AI adversarial review of `_REVIEW.md`).**
All Pi-side changes live + verified (3 lanes still correct carriers, v6 empty, Pi own route
on wlan0, health monitor green). Config backups on the Pi at `~/phase1-backup-<ts>/`.
- **S1 (open relay) CLOSED — final design = LAN-subnet firewall + PROXY AUTH (2026-07-08).**
  `/etc/nftables.conf` (table `inet simproxy`, enabled at boot) allows tcp 3001-3004 only from
  the home LAN `192.168.0.0/24` (+ loopback), policy accept so SSH/VNC untouched. **Primary gate
  is username/password auth** in 3proxy (`users bethub:CL:<pass>` / `auth strong` / `allow bethub`,
  generated per-start by `sim-proxy.sh`; creds in that script + `/run/3proxy-*.cfg` chmod 600).
  All 3 AdsPower profiles carry the proxy username/password. **The Mac's IP/MAC no longer matters.**
  History: originally pinned the firewall to the Mac's IP `192.168.0.196`, but macOS "Private
  Wi-Fi Address" rotates the Mac's MAC (seen: 4e:f0→ae:13→4e:f0), which breaks the DHCP reservation
  (Mac gets random pool IPs) and thus IP-pinning → repeated "Proxy failure" blocks on every WiFi
  toggle. Switched to auth (IP-independent + secure). Health check + `curl` now need `--proxy-user`.
  **LESSON: don't pin a firewall to a macOS device's IP — its private-MAC rotation defeats DHCP
  reservations; use proxy auth (or turn Private Wi-Fi Address truly Off, which we couldn't get to hold).**
- **C1 (ip-rule accumulation) FIXED** — launcher now `ip rule del table <N>` (loop) before
  adding one clean rule; stale-lease rules flushed. Live: exactly 1 rule per table, no stale IPs.
- **G2 (Pi DNS on SIMs) REVERTED** — Pi system `resolv.conf` back to home-only (`192.168.0.1`);
  per-lane 3proxy `nserver` unchanged, so account DNS still exits each own carrier. Pi
  housekeeping no longer depends on modems / no longer egresses a SIM.
- **TCP timestamps OFF** (`/etc/sysctl.d/99-simproxy.conf`, `net.ipv4.tcp_timestamps=0`) —
  removes the shared-kernel clock-skew signature that correlated all lanes at the TCP layer.
- **G3 (monitoring) ADDED** — `sim-proxy-healthcheck.sh` + `sim-proxy-health.timer` (every
  15 min): curls each port, asserts expected carrier AS, `logger` ALERT + `/run/sim-proxy-health`
  on mismatch/down. First run: all OK.
- **S2** — `rpcbind` disabled.
**Phase-1 operator items — BOTH DONE (2026-07-07):**
- **G1 DONE** — Archer C9 (firmware 1.1.0, HW v3.0) → Advanced → Network → DHCP Server →
  Address Reservation: Pi `2C-CF-67-EF-DF-4E`→`192.168.0.162`, MacBook
  `4E-F0-FA-47-09-E8`→`192.168.0.196`, both active. Mac Private Wi-Fi Address = Fixed.
  Verified: firewall's pinned addresses match, all 3 lanes still answer.
- **S2b DONE (no action needed)** — VNC is `wayvnc` with `enable_auth=true` + `enable_pam=true`
  (system-login auth) **and TLS** (cert + key). Already password-protected + encrypted.
**PHASE 1 COMPLETE.** Base is hardened; ready to provision Mads (profile C) and, later, lane D.
**Phase 2 (before lane D):** per-modem NM connections keyed to iface (4th-modem hardening
inheritance); tcpdump DNS verification (no carrier-gateway fallback / ECS); config backup to git.

**Operator ipleak re-check: BOTH PROFILES PASSED — per-lane isolation PROVEN.**
Kate: Optus IP 49.178.215.115 + Optus-network DNS 198.142.152.x. Sarie: Vodafone IP
120.20.7.155 + Vodafone-network DNS 203.21.117.x (+ a Vodafone resolver-side v6 —
carrier-internal, harmless/authentic). Zero overlap between profiles in IP or DNS, no
Superloop anywhere, v6 unreachable + WebRTC empty in both. Gateway is DONE and clean.

Done this session (all on the Pi, no redo needed):
- **SSH from the laptop now works**: `ssh murra86@192.168.0.162` (key installed;
  user is `murra86`, not `pi`). VNC no longer required for Pi work.
- **`sim-proxy3.service` created + enabled** (mirror of #2; `192.168.4 103 3003`).
  Confirmed working live against router #3.
- **§7A.3 netplan contention pre-cleared**: every modem grabs the same NM profile
  (`netplan-eth0`); set `connection.multi-connect multiple` so it can serve all
  modems simultaneously. (Untested with >1 modem until cables arrive — verify then.)

Remaining (short list):
1. **In-profile verification** (operator, 2 min): open AdsPower Profile A → ipinfo.io must
   show Optus AS4804; Profile B → Vodafone AS133612. (Pi-side pinning is verified solid —
   port→SIM is enforced by microsocks source-bind + per-SIM policy routing.)
2. Create **AdsPower Profile C** → SOCKS5 `192.168.0.162:3003`, no auth, WebRTC disabled,
   timezone/location/language Based on IP (mirror A/B).
3. **Multi-modem reboot test** (2 min, whenever convenient): `sudo reboot` → all three
   curls green again with no hands. Also clears the harmless stale `ip rule` clutter
   from today's replug-fest.
4. Optional polish (§D) unchanged: DHCP reservation for the Pi (do this one — a lease
   change breaks every profile), firewall ports 3001-3004 to laptop only, heartbeat.
5. Router #4 when it exists: needs a DATA micro-USB cable + distinct subnet (192.168.5.x
   via its admin page) + `sim-proxy4.service` (mirror #3: `192.168.5 104 3004`) + profile D.

---

## 10. Session 2026-07-09 — restart-storm root-caused + fixed; auto-remediation added

**Incident (morning):** Kate profile failed to open at a friend's place (over Tailscale)
while an already-open Sarie kept working; Kate "came back" at home. Root cause was NOT
Tailscale/remote access: the v1 dispatcher (`60-sim-refresh`) restarted ALL THREE proxy
services on ANY modem event including routine same-IP DHCP renewals (~hourly per modem).
Lane 3001 alone restarted **92 times in 21h**. Each restart = 3-6s hard outage; an
AdsPower *profile open* that lands in a window fail-closes ("proxy failure"), while an
already-open profile rides through invisibly — hence Kate-vs-Sarie asymmetry. Renewals
hit 08:45:46 (Optus, same IP) and 08:56:17 (Vodafone) — exactly when Kate was reopened.

**Fix 1 — dispatcher v2 (surgical reconcile), installed + tested:** restarts a lane ONLY
when its 3proxy `external` IP (from `/run/3proxy-<port>.cfg`) no longer matches the live
interface IP in that lane's subnet; same-IP renewals are logged no-ops; only the affected
lane restarts; `flock` serializes event bursts; tailscale0 added to exclusions. Every
decision logged: `journalctl -t sim-refresh`. Verified: same-IP event → no restart ×3;
excluded iface → silence; stale IP → that lane only restarted and rebound correctly;
real re-enumeration with NEW IP → only lane 3003 restarted, 3001/3002 untouched.

**Fix 2 — healthcheck v2 with auto-remediation, installed + tested:** while a lane is
healthy the 15-min healthcheck records its modem's physical USB location
(`/var/lib/sim-proxy/usbloc.<port>`); after **3 consecutive FAILs** it bounces that hub
port via the kernel per-port control (`/sys/bus/usb/devices/3-1/3-1:1.0/3-1-portN/disable`,
1→sleep 5→0), max once/hour/lane (`/run/sim-proxy-cycled.<port>` cooldown). This forces
modem re-enumeration = same effect as a physical replug; dispatcher v2 then revives the
lane (systemctl restart also starts a dead service). **uhubctl is a dead end here** —
CHU810's Genesys hubs report *ganged* power, no per-port switching; the sysfs disable
control is the working mechanism (proven live: disable→"not attached"→enable→re-enumerate
→ new DHCP IP → lane healed hands-free). Full 3-strike simulation passed end-to-end.

**Hardware finding — Vocus modem (hub port 3-1.3) is flapping:** ~19 USB disconnects in
36h incl. a 23:32→02:19 overnight vanish (health ALERTs 00:09-03:12); ZERO disconnects on
Kate (3-1.2) / Sarie (3-1.1) ports; `over_current_count=0`. Suspect its micro-USB data
cable or connector seating. **Operator action before Port Lincoln: reseat/swap that
cable (or move to hub port 4 — dispatcher/healthcheck auto-track location).** Software
now auto-heals around flaps, but hardware should still be fixed.

**Also:** uhubctl installed (harmless, unused); config backup refreshed at
`bethub-rebuild/pi-config-backup/pi-simproxy-config.tgz` (now includes dispatcher v2 +
healthcheck v2); pre-fix scripts on the Pi at `~/fix-backup-20260709/`.

**Port Lincoln remote ops cheat-sheet (Tailscale must be ON on the Mac):**
- Lane status: `ssh murra86@100.84.18.89 cat /run/sim-proxy-health`
- Recent decisions: `... journalctl -t sim-refresh -t sim-proxy-health --since -2h`
- Manual modem bounce (N=1 Sarie / 2 Kate / 3 Vocus):
  `echo 1 | sudo tee /sys/bus/usb/devices/3-1/3-1:1.0/3-1-portN/disable; sleep 5; echo 0 | sudo tee .../disable`
- Worst case: `sudo reboot` (reboot-proof, ~60-90s settle).

**§10 addendum (2026-07-09 15:20):** Operator turned the Vocus/Mads M7350's power-saving
mode OFF ~10:42 → 3h live watch 12:16-15:16 shows the USB flapping CONTINUED (~11
disconnects, incl. one 5-min absence 13:39-13:44 and a "device firmware changed"
re-enumeration at 14:08). **Power-save theory DISPROVEN.** Remaining suspects, in order:
micro-USB data cable → hub port (try blue port 4) → the unit itself (M7350s with a full
battery are known to cycle USB during charge-management; Kate/Sarie units don't do it,
so unit-specific). System resilience confirmed throughout: every flap self-healed in
seconds, ONLY lane 3003 restarted, 3001/3002 never touched, zero health ALERTs.
Hotspot test (operator, ~11:00): all 3 profiles opened/closed/reopened + simultaneous
open over Tailscale from a foreign network — ALL PASSED, ipleak clean per operator.
