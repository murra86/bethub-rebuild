# Router/SIM Proxy Gateway — Adversarial Review Dossier

**Prepared:** 2026-07-07 · **Purpose:** give an external reviewer (human or AI) everything
needed to attack this design and find isolation, leak, security, and reliability gaps.
**Snapshot source:** live-captured from the running Raspberry Pi this date (configs below
are the real files, not idealised). **Status of the system:** operational — 3 SIMs live
simultaneously, 2 accounts verified clean on ipleak.net, 1 more about to be provisioned.

> **How to use this doc:** §1–§6 describe the system as-built. §7 states the security model
> and the exact mechanism enforcing each guarantee — *challenge these*. §8 is a pre-loaded
> list of gaps we already know about; extend/prioritise it and find ones we missed. §9 lists
> concrete attack questions. Assume the reviewer is hostile and competent.

---

## 1. Goal & threat model

**What this is for.** Several online betting accounts, each operated from its own
AdsPower browser profile on one MacBook. Each account must reach the internet from a
**distinct, stable Australian mobile IP** on a **distinct carrier**, so the bookmakers
cannot link the accounts to each other or to the operator's home connection.

**The asset being protected** is *account non-attributability*: the bookmaker (and its
anti-fraud/device-fingerprinting vendors) must not be able to infer that accounts K, S,
and M are the same person, nor tie any of them to the home ISP.

**What "robust" means here — the properties a reviewer should try to break:**
1. **No cross-account linkage.** No two profiles may ever share an egress IP, a DNS
   resolver set, a WebRTC-exposed IP, or any network-layer fingerprint.
2. **No home-ISP leakage.** Nothing the bookmaker sees (IP, DNS, WebRTC, IPv6) may
   reveal the home Superloop connection.
3. **Sticky identity.** Each account keeps the *same* mobile IP/carrier over time
   (mobile IPs rotate slowly within a carrier; that is acceptable and even desirable —
   a *sudden carrier change* is the red flag, not a slow IP drift within one carrier).
4. **Fail-closed.** Any failure (modem down, proxy dead, Pi rebooting) must produce a
   *dead* connection for that profile, never a silent fallback to the home IP or the
   wrong SIM.
5. **Reliability / recoverability.** Survives reboots and modem replugs hands-free;
   a component failure is at worst a visible outage, never a silent leak.

**Security objective (restated crisply).** This document evaluates **network isolation only**.
It deliberately **excludes** behavioural linkage, payment linkage, browser/canvas/font
fingerprint linkage, and operator behaviour. Criticising those is out of scope — say so if
you think one shouldn't be.

**Trust boundary (where you are allowed to attack).**
- *Trusted:* the Raspberry Pi, the MacBook, the home LAN, the mobile routers. We assume the
  adversary **cannot directly compromise the Pi or the Mac** (no local malware) — otherwise
  "install malware on the Mac" trivially wins and teaches us nothing.
- *Untrusted / adversarial:* the Internet, the carrier networks, the bookmaker, and its
  fingerprinting/anti-fraud vendors. Attack from there.

**Additional isolation invariants** (beyond IP/DNS/WebRTC/IPv6):
- **No TCP connection may ever migrate between SIMs** (matters if connection pooling or a
  different proxy is later introduced).
- **No cross-lane host signature.** Distinct carrier IPs must not share a single-host
  fingerprint (TCP timestamps/clock skew, TCP-stack options). *(TCP timestamps now disabled
  — see remediation log §11.)*

**Fail-closed (tightened invariant):** any failure must **either preserve the intended SIM
identity or terminate the connection** — never silently fall back to home or the wrong SIM.

---

## 2. Hardware & topology

- **1× Raspberry Pi 5** (Debian 13 "trixie", kernel 6.18, hostname `murra86`), headless,
  on the home WiFi (`wlan0` → SSID `TP-LINK_C04A_5G`). Boots off a **microSD card**
  (`/dev/mmcblk0`, 117 GB, 7% used).
- **3× TP-Link M7350 4G mobile routers** (a 4th planned), each with a different carrier
  SIM. Connected to the Pi over **USB (RNDIS)** — each presents as an ethernet-like
  interface to the Pi.
- **1× Simplecom CHU810 powered USB hub** (48 W, per-port switches). The Pi cannot power
  more than one M7350 directly (overcurrent), so all modems hang off the powered hub.
  (Enumerates on the Pi as a cascade of Genesys Logic 4-port hub chips.)
- **1× MacBook** — the operator's laptop, runs AdsPower, also on the home WiFi.
- **Home router** — TP-Link, home LAN `192.168.0.0/24`, gateway `192.168.0.1`.

**Addressing (immutable mapping — this table is the spec):**

| Account | Router name | Carrier (AS) | Modem LAN | Pi iface* | SIM-side Pi IP | Route table | SOCKS port | AdsPower profile |
|---|---|---|---|---|---|---|---|---|
| A | **Kate-Router** | Optus (AS4804) | `192.168.2.0/24` | `enu1u2` | `192.168.2.162` | 101 | **3001** | Kate |
| B | **Sarie-Router** | Vodafone (AS133612) | `192.168.3.0/24` | `enu1u1` | `192.168.3.196` | 102 | **3002** | Sarie |
| C | **Mads-Router** | Vocus MVNO (AS9443) | `192.168.4.0/24` | `enu1u3` | `192.168.4.127` | 103 | **3003** | Mads *(to create)* |
| D | *(future)* | *(TBD)* | `192.168.5.0/24` | — | — | 104 | 3004 | — |

\* Interface names are assigned by USB path via a systemd `.link` file (see §4). **But the
proxy binding keys off the modem's *subnet*, not the interface name — so which physical
hub port a modem occupies does not change its account mapping** (the SIM's subnet travels
with the modem, because each M7350 hands out its own distinct subnet via its own DHCP).
Pi-side IPs (`.162/.196/.127`) are DHCP leases from each modem and **change on every
replug/reboot** (see §4 MAC randomisation) — nothing is pinned to them except transient
runtime state.

**Data path of one request:**
```
AdsPower profile (MacBook)
  --home WiFi--> Pi SOCKS5 listener :300X
  --policy routing (table 10X)--> modem enu1uY
  --USB/RNDIS--> M7350 --4G--> carrier --> Internet
DNS for that request: resolved by the Pi-side proxy via that SIM's carrier resolver (192.168.X.1)
```

---

## 3. Home / WiFi facts

- Home LAN `192.168.0.0/24`, gateway/DNS `192.168.0.1` (Superloop upstream).
- Pi = `192.168.0.162` — **DHCP, NOT reserved** (lease ~85 min; see §8-G1).
- MacBook = `192.168.0.196` (also DHCP, not reserved).
- The Pi's *own* traffic (apt, ntp, ssh, its own curl) egresses via `wlan0`/home — verified:
  `ip route get 1.1.1.1 → via 192.168.0.1 dev wlan0`. Only *proxied account* traffic uses SIMs.

---

## 4. Pi software stack (as-built, real configs)

### 4a. Proxy software: `3proxy` (built from source)
`3proxy` is not in the trixie repos; built from source (git `de5acb2`, needs `libssl-dev`),
installed at `/usr/local/bin/3proxy`. Replaced `microsocks` on 2026-07-07 specifically to
get **per-lane DNS** (`nserver`), which microsocks cannot do. (microsocks-era script kept as
`/usr/local/bin/sim-proxy.sh.microsocks.bak`.)

### 4b. Per-lane launcher: `/usr/local/bin/sim-proxy.sh`
Called once per lane by systemd as `sim-proxy.sh <subnet-prefix> <table> <port>`:
```bash
#!/bin/bash
export PATH=/usr/sbin:/sbin:/usr/bin:/bin
PREFIX="$1"; TABLE="$2"; PORT="$3"

SIMIP=""; IFACE=""
for i in $(seq 1 30); do                       # wait up to 60s for the modem to appear
  LINE=$(ip -4 -o addr show | grep "inet ${PREFIX}\." | head -1)
  if [ -n "$LINE" ]; then
    IFACE=$(echo "$LINE" | awk '{print $2}')
    SIMIP=$(echo "$LINE" | awk '{print $4}' | cut -d/ -f1)
    break
  fi
  sleep 2
done
[ -z "$SIMIP" ] && { echo "no interface on this network yet; retrying"; exit 1; }

GW="${PREFIX}.1"
ip route replace default via "$GW" dev "$IFACE" table "$TABLE"   # per-SIM default route
ip rule add from "$SIMIP" table "$TABLE" 2>/dev/null || true     # policy rule (see §8-C1: never deleted)
while ip route del default dev "$IFACE" 2>/dev/null; do :; done  # strip modem default from MAIN table (Pi stays on WiFi)
sysctl -w net.ipv4.conf.${IFACE}.rp_filter=2 >/dev/null 2>&1 || true  # loose RPF for asymmetric per-SIM routing

CFG="/run/3proxy-${PORT}.cfg"
cat > "$CFG" <<CFGEOF
nserver ${GW}          # DNS = this SIM's carrier resolver
nscache 65536
maxconn 300
auth none              # <-- see §8-S1
internal 0.0.0.0       # <-- listens on ALL interfaces; see §8-S1
external ${SIMIP}      # egress bound to this SIM's IP
socks -p${PORT}
CFGEOF
exec /usr/local/bin/3proxy "$CFG"
```

### 4c. systemd services (one per lane)
`sim-proxy.service` / `sim-proxy2.service` / `sim-proxy3.service`, each:
```
[Service]
Type=simple
ExecStart=/usr/local/bin/sim-proxy.sh 192.168.<2|3|4> <101|102|103> <3001|3002|3003>
Restart=always
RestartSec=5
```
Plus a drop-in `StartLimitIntervalSec=0` (added 2026-07-07 after a replug restart-storm
tripped systemd's default start-rate-limit and stranded all three proxies in `failed`).

### 4d. Modem identity fix: `/etc/systemd/network/10-rndis-modems.link`
```
[Match]
Driver=rndis_host
[Link]
NamePolicy=path
MACAddressPolicy=random
```
**Why:** all M7350 units ship with **identical USB serial (`c53795b3`) and identical RNDIS
MAC (`3a:3d:dc:fd:d1:29`)**. Without this they collide (all try to be `usb0` with the same
MAC) and only one works. This gives each a name by physical USB path and a random MAC.
**Side effect:** random MAC → new DHCP lease each boot/replug (root cause of §8-C1).

### 4e. Auto-resync: `/etc/NetworkManager/dispatcher.d/60-sim-refresh` (root, +x)
On any non-home interface `up`/`down`/`dhcp4-change`, restarts all three sim-proxy services
(so a replug or lease change re-binds the proxy to the modem's new IP). Excludes
`wlan0|eth0|lo|p2p-dev-wlan0`.

### 4f. Routing / DNS / IPv6 config (NetworkManager, connection `netplan-eth0`)
All modems share the single NM connection profile `netplan-eth0` (matches all ethernet;
`connection.multi-connect = multiple`). Key props set 2026-07-07:
- `ipv4.never-default = yes` — a modem may **never** install a default route in the main
  table (stops the Pi's own traffic and DNS from riding a SIM).
- `ipv6.method = disabled`, `ipv6.never-default = yes` — **no IPv6 on any modem**. Closes
  the cross-SIM v6 leak (only one carrier offered v6; it would have owned the single v6
  default and leaked that one carrier's IP into *every* profile). This is a *config-level*
  disable, **not** the kernel `disable_ipv6=1` that previously broke the proxy.
- `ipv4.ignore-auto-dns = yes`, `ipv4.dns = 192.168.2.1,192.168.3.1,192.168.4.1`,
  `ipv4.dns-priority = 50` — carrier resolvers populate the Pi's own `resolv.conf` ahead
  of home (home `192.168.0.1` demoted to priority 200). **See §8-G2 for the trade-off.**

Live `resolv.conf`:
```
search lan
nameserver 192.168.2.1     # Optus
nameserver 192.168.3.1     # Vodafone
nameserver 192.168.4.1     # Vocus
nameserver 192.168.0.1     # home (4th — beyond glibc's 3-nameserver limit, effectively unused)
```

### 4g. Client side (MacBook / AdsPower)
Each profile: proxy = **SOCKS5**, host `192.168.0.162`, port `300X`, no auth. WebRTC
disabled; timezone/geolocation/language = "Based on IP". **AdsPower resolves DNS remotely
through the proxy** (confirmed empirically — ipleak showed *carrier* DNS, not the Mac's) —
i.e. it behaves as SOCKS5h. AdsPower fails **closed** by default (dead proxy = error, not
real IP). Profiles are created with *independent* fingerprints (not clones of each other).

---

## 5. Verification evidence (what we've actually observed)

- **Simultaneous 3-lane egress** (curl from the MacBook, same minute):
  3001 → `49.178.215.115` Optus AS4804 · 3002 → `120.20.7.155` Vodafone AS133612 ·
  3003 → `58.178.x` Vocus AS9443.
- **ipleak.net inside the actual AdsPower profiles:**
  - *Kate:* IP Optus AS4804 · DNS `198.142.152.x` (Optus network) · IPv6 unreachable · WebRTC empty.
  - *Sarie:* IP Vodafone AS133612 · DNS `203.21.117.x` (Vodafone network) · IPv6 unreachable · WebRTC empty.
  - **Zero overlap** between the two profiles in either IP or DNS; no Superloop anywhere.
- Pi's own route stays on `wlan0` with all 3 modems up.
- IPv6: no global v6 address and no v6 default route on the Pi (leak surface empty).

---

## 6. What enforces each isolation guarantee (the mechanism, so you can attack it)

| Guarantee | Mechanism | Where it could fail (attack surface) |
|---|---|---|
| Egress IP = correct SIM | `3proxy external <SIMIP>` + `ip rule from <SIMIP> table 10X` + table 10X default via that modem | Wrong/duplicate `ip rule`; two modems sharing a subnet; rp_filter dropping return path |
| Return path not dropped | `rp_filter=2` (loose) on each modem iface | If ever set to 1 (strict), asymmetric per-SIM routing breaks |
| Pi own traffic stays home | `ipv4.never-default` + script strips modem default from main table | An NM reapply that restores auto defaults; a modem on a *different* NM profile |
| No IPv6 leak | `ipv6.method disabled` on the modem NM profile | A 4th modem binding a different NM profile; IPv6 arriving some other way |
| No shared DNS fingerprint | `3proxy nserver <carrier gw>` per lane | If a profile is set to local-DNS SOCKS5 (not 5h); if carrier gw forwards to a shared upstream that's identifiable |
| No WebRTC real-IP | AdsPower WebRTC disabled | Client-side only — outside the Pi's control |
| Fail closed | AdsPower default + dead proxy on failure | A system-wide VPN/extension on the Mac over the top; proxy bound but pointing at a stale IP |
| Correct SIM after replug | NM dispatcher restarts proxies on iface events | Dispatcher missing/non-exec; event not firing; restart-storm (mitigated by §4c) |

---

## 7. Design decisions worth challenging

1. **One shared NM profile (`netplan-eth0`, multi-connect) for all modems.** Simple, and
   the v4/v6/DNS hardening applies uniformly — but every modem is at the mercy of one
   profile's correctness, and a 4th modem could race onto a different profile. Should each
   modem have its own explicit NM connection keyed to interface name instead?
2. **Policy routing by source IP, not by interface.** Elegant (survives interface renames)
   but depends on DHCP leases being unique per subnet and on `ip rule` hygiene (§8-C1).
3. **DNS via the carrier's own gateway resolver (`192.168.X.1`).** Maximally "native"
   per carrier — but is a modem's built-in DNS forwarder a *distinguishing* fingerprint
   itself (e.g. does it forward to a recognisable upstream, add ECS, or behave oddly)?
   Would a neutral public resolver *per lane* (e.g. different resolver per account, still
   egressing that SIM) be less identifiable, or more?
4. **`auth none` + `internal 0.0.0.0` + no firewall.** Chosen for zero-friction on a
   trusted home LAN. This makes each lane an **open SOCKS relay to anything on the LAN**
   (§8-S1). Is "trusted home LAN" an acceptable assumption?
5. **3proxy from source, unmanaged by apt.** No automatic security updates for the one
   internet-facing daemon. Acceptable, or package/pin/monitor?
6. **Single Pi, single SD card, single WiFi uplink.** Whole system is one box. Is that
   acceptable for the value at risk, or does it need redundancy/backup?

---

## 8. Known gaps (pre-loaded — extend, reprioritise, and find more)

**Severity is our guess; challenge it.**

### Security
- **S1 (HIGH): Proxy ports are an open relay on the home LAN.** 3001–3003 listen on
  `0.0.0.0` with `auth none` and no firewall (`nft`/`ufw` both inactive). *Any* device on
  `192.168.0.0/24` (or anything that reaches the Pi) can egress through any betting
  account's SIM, burn its data, or worse — attribute traffic to that account's IP.
  **Proposed fix:** nftables allowing 3001–3004 only from the MacBook's IP (needs the Mac
  on a reserved IP first), and/or `internal 192.168.0.162` + 3proxy `users`/`allow` ACL.
- **S2 (LOW/MED): Extra listening services.** `rpcbind` on `:111` (v4+v6) and **VNC on
  `*:5900`** are exposed on the LAN. VNC in particular (remote desktop) — is it
  password-protected and is 5900 acceptable on the LAN? rpcbind is unused here; remove it.
- **S3 (LOW): SSH on `0.0.0.0:22`.** Key-only (good) but consider limiting to the LAN.

### Correctness / isolation
- **C1 (MED — real design smell): `ip rule` accumulates and never cleans up.** The
  launcher does `ip rule add ... || true` on every start but never deletes old rules.
  Live capture shows **50+ duplicate rules**, including entries for *stale DHCP leases*
  from earlier today (`192.168.4.150/.149/.113/.195/.187`, `192.168.2.131/.102`,
  `192.168.3.193`). Currently harmless (every stale IP still points to the *same* table as
  its subnet) and a reboot clears them — but it grows unbounded across replugs, and it is
  exactly the kind of state where a future change (subnet reuse, table renumber) turns
  latent into a mis-route. **Proposed fix:** `ip rule del from <old> ...` before add, or
  flush the lane's rules by a marker, or key rules to subnet not lease-IP.
- **C2 (MED): Subnet-collision assumption is load-bearing and unenforced.** Isolation
  relies on every modem being on a *distinct* subnet (2/3/4/5). If a modem is ever
  factory-reset or a new one defaults to a duplicate subnet (or to `192.168.0.x`, clashing
  with home), the source-routing model silently breaks. Nothing detects or prevents this.
- **C3 (LOW): No positive proof of per-lane DNS at the packet level.** We infer correct DNS
  from ipleak's reported resolver network. We haven't packet-captured to confirm a given
  lane's DNS *only ever* exits its own SIM (vs. occasionally the Pi's resolv.conf path).

### Reliability / robustness
- **G1 (MED): Pi home IP is not DHCP-reserved.** If the lease changes, every AdsPower
  profile (hard-coded to `192.168.0.162`) breaks at once. Reserve it on the home router.
- **G2 (MED — trade-off from the DNS fix): the Pi's *own* system DNS now depends on the
  SIMs.** resolv.conf lists the three carrier resolvers first and home 4th; glibc uses only
  the first 3, so **if all modems are down the Pi cannot resolve DNS at all** (home
  resolver is never reached). Also the Pi's own lookups now egress a SIM (minor data). Is
  the carrier-first ordering worth this? (Proxy DNS is independent — 3proxy has its own
  `nserver` — so this only affects the Pi's housekeeping, not account traffic.)
- **G3 (MED): No monitoring/alerting.** Failures are fail-closed but **silent**. A dead
  proxy, a dropped SIM, a wrong-carrier egress, or a home-IP leak would not raise any
  alarm — the operator finds out by manually checking. Proposed: a heartbeat that curls
  each port's egress IP on a schedule and alerts on down/wrong-AS.
- **G4 (LOW/MED): SD card is a single point of failure**, and **no config backup exists**.
  All the bespoke config (§4) lives only on the card. Card death = rebuild from these docs.
  Proposed: back up the config files to git / another host; consider config-as-code.
- **G5 (LOW): No unattended-upgrades.** OS security patches are manual.
- **G6 (LOW): 3proxy `maxconn 300` per lane** — probably fine for one browser, but
  unverified under real load / many tabs.

### Scaling to the 4th modem / new accounts
- **X1:** Does a 4th modem inherit the `netplan-eth0` hardening (v6 disabled, never-default)
  or race onto a different profile? (See §7-1.) Verify before trusting lane D.
- **X2:** `sim-proxy4.service` + subnet `192.168.5.x` + a data-capable micro-USB cable are
  all still needed. (Most micro-USB cables on hand were **charge-only** and failed
  *silently* — a modem charges but the Pi sees zero USB events. Non-obvious failure mode.)

### Client-side (outside the Pi, but part of the threat model)
- **P1:** A system-wide VPN or a misbehaving browser extension on the MacBook would sit
  *over* AdsPower and could defeat the whole scheme. Nothing on the Pi can prevent this.
- **P2:** Confirm every AdsPower profile uses **remote** DNS (SOCKS5h). Empirically true
  for Kate/Sarie; make it a checklist item for new profiles.
- **P3:** Fingerprint independence between profiles is assumed (created fresh, not cloned).
  Worth an explicit audit that no two profiles share canvas/WebGL/font fingerprints.

---

## 9. Concrete questions for the reviewer to attack

1. **Can you construct a sequence of replugs/reboots/lease-changes that lands a profile on
   the wrong SIM** given the `ip rule` accumulation (C1) and source-IP routing? We believe
   no (subnet→table is stable) — try to prove otherwise.
2. **Is the carrier gateway DNS (`192.168.X.1`) a linkage vector?** If Optus and Vocus both
   forward to the same recognisable upstream, or stamp EDNS Client Subnet, could a
   bookmaker correlate lanes despite different resolver IPs?
3. **What single failure produces a *silent* leak** (not fail-closed)? We think none at the
   network layer, with the client-side VPN/extension case (P1) as the main hole — agree?
4. **Is loose `rp_filter=2` the right call**, or does it open a spoofing/mis-route path we
   haven't considered?
5. **Given S1 (open LAN relay), what's the realistic risk** on a home network, and what's
   the minimal fix that doesn't reintroduce replug fragility?
6. **Rank G1–G4 for a setup where the value at risk is real betting balances.** What would
   you fix before provisioning more accounts?
7. **Is there a leak vector we haven't listed at all** — MTU/MSS fingerprinting, TCP
   timestamps/clock skew across lanes revealing one host, TLS ClientHello uniformity, time
   zone vs IP mismatches, etc.?

---

## 10. Appendix — quick commands to reproduce the snapshot

```bash
# from the MacBook
ssh murra86@192.168.0.162

# on the Pi
ip -4 -o addr show                       # modem IPs per subnet
ip route show default                    # must be ONLY wlan0
ip rule show                             # policy rules (note C1 accumulation)
for t in 101 102 103; do ip route show table $t; done
ip -6 route show default                 # must be empty
grep -v '^#' /etc/resolv.conf
ps -o pid,args -C 3proxy; cat /run/3proxy-*.cfg
ss -tln | grep ':300'                    # proxy listeners (note 0.0.0.0 — S1)
systemctl status sim-proxy sim-proxy2 sim-proxy3

# from the MacBook — per-lane egress (expect distinct carriers)
for p in 3001 3002 3003; do curl -s --socks5-hostname 192.168.0.162:$p https://ipinfo.io/json | grep -E '"ip"|org'; done
```

---

## 11. Remediation log — Phase 1 applied 2026-07-07 (post 3-AI review)

Reviews by ChatGPT, Grok, Gemini were triaged (high consensus on the operational HIGHs).
Applied, live-verified:
- **S1 CLOSED** — nftables restricts proxy ports to the MacBook + Pi + loopback; 3proxy
  `allow`/`deny` ACLs as a second layer. *(Depends on G1 — IPs must be reserved.)*
- **C1 FIXED** — launcher deletes the lane's rules before adding one clean rule; no more
  unbounded accumulation. Live: 1 rule/table, no stale-lease IPs.
- **G2 REVERTED** — Pi system DNS back to home-only; per-lane 3proxy `nserver` unchanged.
  (Also resolves the "locally-generated Pi traffic on a SIM" concern — that was the DNS path.)
- **TCP timestamps DISABLED** (`net.ipv4.tcp_timestamps=0`) — kills the shared-clock
  cross-lane signature. *(Residual: TCP-stack sameness (MSS/window/options) across lanes is
  unaddressed — deeper p0f-style fingerprinting; judged low practical likelihood, documented.)*
- **G3 ADDED** — 15-min health timer asserts each port's carrier AS, alerts on mismatch/down.
- **S2** — rpcbind disabled.

**Reviewer recommendation we DECLINED (with reason):** switching per-lane DNS from the
carrier gateway to public resolvers (1.1.1.1/9.9.9.9/8.8.8.8). Carrier-native DNS is the
*authentic* signal (a real Optus mobile user resolves via Optus), and our ipleak evidence
shows genuinely distinct carrier resolvers per lane (Optus 198.142.152.x vs Vodafone
203.21.117.x) — i.e. **no** shared-public-resolver fallback, refuting the premise. Public
resolvers would be *less* native and, if shared, *more* linkable. Instead we keep carrier
DNS and will **verify by packet capture** (no fallback, ECS behaviour) in Phase 2.

**Still open:** G1 (reserve Pi + Mac IPs — operator/home-router), S2b (VNC :5900 auth),
G4 (config backup to git), X1 (4th-modem NM-profile inheritance — per-modem connections),
C3 (tcpdump DNS verification), P1/P2 (Mac no-VPN discipline; confirm SOCKS5h per new profile),
G5 (unattended-upgrades), 3proxy supply-chain (pin/document commit `de5acb2`, monitor CVEs).

---

*End of dossier. Related: `router_sim_proxy_gateway_status.md` (operational status/history),
`router_sim_proxy_gateway_brief.md` (original design — note: predates the microsocks→3proxy
change and describes systemd-networkd, now superseded by the NetworkManager reality above).*
