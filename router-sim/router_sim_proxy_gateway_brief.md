# Router/SIM Proxy Gateway — Build Brief

**Status:** Draft v2 (incorporates external AI critique)
**Date:** 2026-07-03
**Author:** Claude (design session with Tim)
**Scope:** Physical + network build. AdsPower profiles touched only at the boundary; account-operation workflow out of scope.

> ⚠️ **Review note:** Config snippets are *drafts to validate on the bench*, not tested-on-hardware truth. The RNDIS-on-Linux behaviour of the M7350 is assumed from docs + sibling-device reports, not yet confirmed on this firmware. Phase 1 exists to de-risk exactly that. Scrutinise §11 (open questions) hardest.

> 📄 **Document structure:** This brief deliberately keeps timeless architecture (objective, design, threat model) alongside draft implementation (commands, configs). Once Phase 1 validates the commands on real hardware, the implementation half (Phases 1–2 command blocks, §10 configs, Appendix A) will be **extracted into a separate Implementation Guide**, leaving this as a stable ~architecture brief. Splitting earlier would mean maintaining two documents full of unproven config.

> 🧱 **Critical assumptions — the four pillars.** The entire design rests on these. If any is false, the approach changes materially:
> 1. **The M7350 exposes usable USB networking on Linux** (RNDIS/ECM) — validated in Phase 1; WiFi fallback (§12) if not.
> 2. **The sportsbooks tolerate intra-carrier IP churn** on SIM reconnect — validated with dummy accounts early.
> 3. **AdsPower honours SOCKS5h + proxy-only WebRTC** and does not silently reset it on update — validated per profile and re-checked after updates.
> 4. **One SIM is permanently dedicated to one account** — an operational discipline, never violated.

---

## 1. Objective

Run **4 (later N) betting accounts simultaneously**, each in its own AdsPower profile, each egressing through its **own TP-Link M7350 4G router/SIM** — so switching accounts is *switching a window*, never closing a profile / flipping the laptop network / opening another.

A key secondary benefit: a **sticky account→SIM mapping** is safer for account longevity than today's switching, because each account presents a stable mobile IP instead of churning.

## 2. Current state vs. target state

| | Current | Target |
|---|---|---|
| Account switch | Close profile → switch laptop network → open other profile | Switch window (all profiles live) |
| Concurrency | One at a time | 4+ concurrent |
| IP↔account binding | Manual, error-prone | Fixed by physical slot, enforced in software |
| Failure mode | N/A | Fail-**closed** (dead SIM = no connection, never a wrong IP) |

## 3. The core reframe

This is **not** a "switch the laptop's network" problem. AdsPower supports a **per-profile proxy**, so the laptop's network never changes. The task is:

> Turn each M7350/SIM into an always-on SOCKS5 endpoint (`Pi_LAN_IP:port`), then point each profile at its matching one.

## 4. Hardware

- **Raspberry Pi 5** — dedicated always-on **multi-homed SOCKS5 gateway** (better USB bandwidth/power than Pi 4). Active cooling recommended.
- **4× TP-Link M7350** (LTE Cat4 MiFi, 2.4 GHz WiFi only, micro-USB, no Ethernet), one SIM each.
- **Powered USB hub** (own PSU — do not draw 4 modems from the Pi).
- **UPS** for Pi + hub (always-on reliability).
- Laptop (macOS) running AdsPower, reaches the Pi over LAN (GigE handles browser traffic easily).

## 5. Architecture

```
                         Raspberry Pi 5 (gateway appliance)
                     ┌──────────────────────────────────────────┐
[M7350 #1/SIM A]──USB┤ sim1  192.168.10.2  table sim1  :3001     ├──┐
[M7350 #2/SIM B]──USB┤ sim2  192.168.11.2  table sim2  :3002     ├──┤ LAN
[M7350 #3/SIM C]──USB┤ sim3  192.168.12.2  table sim3  :3003     ├──┤──► Laptop (AdsPower)
[M7350 #4/SIM D]──USB┤ sim4  192.168.13.2  table sim4  :3004     ├──┘   profileN → Pi:300N
                     │  one egress-bound 3proxy instance per SIM │
                     └──────────────────────────────────────────┘
```

**The design philosophy in one line:** the mapping **Account → SIM → Hub Port → Interface → Routing Table → Proxy Port is immutable.** Every safeguard below exists to keep any one link in that chain from ever shifting relative to the others.

Each SIM is an independent lane: its own interface, static IP, routing table, 3proxy instance, port, and DNS. Nothing is shared between lanes except the Pi's CPU and the LAN listen socket.

## 6. Key design decisions & rationale

### 6.1 Uplink = USB/RNDIS, not WiFi
The M7350 supports internet-over-USB (RNDIS); the Pi kernel has `rndis_host`/`cdc_ether`, so each modem should enumerate as an interface. WiFi is rejected because the M7350 is **2.4 GHz-only** and 4 hotspots inches apart on a 3-channel band is a *reliability* problem (random drops), not just a speed one. USB removes all RF contention. Phase 1 gates on this assumption (§11.1).

### 6.2 Distinct LAN subnet per M7350 — **mandatory, do first**
Every TP-Link MiFi ships on `192.168.0.1`; four on one host collide. Reconfigure each unit's LAN **before** wiring:

| Unit | LAN subnet | Gateway | Pi static IP |
|---|---|---|---|
| #1 | 192.168.10.0/24 | 192.168.10.1 | 192.168.10.2 |
| #2 | 192.168.11.0/24 | 192.168.11.1 | 192.168.11.2 |
| #3 | 192.168.12.0/24 | 192.168.12.1 | 192.168.12.2 |
| #4 | 192.168.13.0/24 | 192.168.13.1 | 192.168.13.2 |

Physically **label each unit** with subnet + SIM + account, and **record its firmware version** (§11.1 — TP-Link USB behaviour varies by revision).

### 6.3 Static Pi-side addressing
Static IP inside each M7350's subnet (not DHCP) → deterministic source IPs, reboot-safe policy rules, no DHCP race.

### 6.4 One egress-bound 3proxy instance per SIM
A systemd template `3proxy@sim1..4`, each with a tiny per-SIM config. Gives isolation (one crash ≠ all down), **correct per-SIM DNS** (`nserver` = that SIM's gateway → DNS egresses the same SIM), and clean fail-closed behaviour.

### 6.5 Physical-slot pinning via udev — the anti-crossed-wires safeguard
A udev rule keys each interface name to its **physical USB hub port path** (`KERNELS`, from `udevadm info -a`), not plug order or MAC. "Hub port 3" is *always* `sim3` → `table sim3` → `:3003` → the one profile for SIM C. Reboots/reconnects cannot scramble the mapping. Label the hub ports to match.

### 6.6 Policy routing overrides interface metrics — main table intentionally unused
Linux sometimes selects routes by interface metric. **This design deliberately does not rely on the main routing table for SIM traffic at all.** Source-based policy rules (`ip rule from <src> lookup <table>`) send each lane's locally-originated traffic to its own table, overriding any metric-based default selection. This is the intended behaviour, not an accident — heading off the common "but which default route wins?" criticism.

### 6.7 Application-level proxy ⇒ no NAT, no ip_forward
3proxy originates the outbound connection itself, so packets originate locally on the Pi. Not packet forwarding — no `ip_forward`, no NAT. Source-based policy routing on locally-originated traffic is the whole mechanism.

### 6.8 Listen sockets bound + firewalled to the laptop only
Each 3proxy binds its listen socket to the Pi's LAN IP (`-i`, never `0.0.0.0`), and an nftables ruleset permits the proxy ports **only from the laptop's IP** (Appendix A). Strong auth on top. The proxy farm is never exposed to the wider LAN.

### 6.9 Containerise monitoring, not networking
The networking layer — routing, udev, systemd-networkd, 3proxy — runs **directly on the host**, where it's cleanest and least surprising. Only the **monitoring/alerting/dashboard** stack is a candidate for containerisation (or at minimum kept modular), since that's the part that benefits from isolation and independent iteration. Do not containerise the network path.

## 7. Threat model — the only thing that "pollutes" a profile

The connection method cannot pollute a profile. Only **IP bleed** does, via three modes, each designed against:

| # | Bleed mode | Consequence | Defense |
|---|---|---|---|
| 1 | **Crossed wires** — profile egresses wrong SIM | Two accounts share an IP → linked | §6.5 slot-pinning; per-port egress-IP verification before a profile is attached (§9) |
| 2 | **Fail-open** — SIM drops, profile uses real IP | Real IP on account | §6.4 egress-bound, no alternate route → connection *refused*, not rerouted; AdsPower "don't fall back to local IP" on |
| 3 | **DNS / WebRTC leak** | Deanonymisation / geo mismatch | SOCKS5**h**; per-SIM `nserver`; AdsPower WebRTC = proxy; timezone/geo/language matched to SIM |

**Anti-detect note:** mobile/CGNAT IPs are residential-grade and generally *good* for trust. Open risk: on reconnect a SIM may pull a different in-range IP (same ASN/geo, usually fine) — confirm the sportsbooks tolerate it (§11.3). Never share one SIM across two accounts.

## 8. Build plan (phased — de-risk before scale)

### Phase 0 — Prep
1. Reconfigure all 4 M7350 LAN subnets per §6.2. Label units, **record firmware versions**.
2. Confirm each SIM has data + a stable public IP via the M7350 admin page.
3. Have a **spare USB-Ethernet dongle / WiFi adapter** on hand in case RNDIS fails.

### Phase 1 — **Bench one modem** (go/no-go gate)
Purpose: prove RNDIS-on-Linux on this firmware before scaling.
1. Set M7350 #1 to `192.168.10.0/24`, plug into Pi via USB.
2. Confirm enumeration — check thoroughly, not just `ip link`:
   ```
   lsusb; usb-devices                     # is the device seen at USB level?
   ip link                                # new usbX / cdc interface?
   dmesg | grep -iE 'rndis|cdc|usb'       # which driver bound?
   sudo modprobe rndis_host cdc_ether     # force modules if not auto-bound
   ```
   If it appears at USB level but no interface, check whether `usb_modeswitch` is needed.
3. Static-address the Pi's side (see §10 for the persistent form):
   ```
   sudo ip addr add 192.168.10.2/24 dev sim1
   ```
4. Routing table + rule + default route:
   ```
   echo "101 sim1" | sudo tee -a /etc/iproute2/rt_tables
   sudo ip route add default via 192.168.10.1 dev sim1 table sim1
   sudo ip rule  add from 192.168.10.2 table sim1
   ```
5. Loose reverse-path filtering (multi-homing footgun):
   ```
   sudo sysctl -w net.ipv4.conf.sim1.rp_filter=2    # test 2 vs 0
   ```
6. One 3proxy instance (draft `/etc/3proxy/sim1.cfg`):
   ```
   nserver 192.168.10.1        # DNS egresses SIM1
   nscache 65536
   auth strong
   users sim1:CL:<password1>
   external 192.168.10.2       # bind egress explicitly
   socks -p3001 -i<PI_LAN_IP> -e192.168.10.2
   ```
7. **Verify from the laptop** (the acceptance test):
   ```
   curl --socks5-hostname sim1:<password1>@<PI_LAN_IP>:3001 https://api.ipify.org
   # must return M7350 #1's public IP — not the laptop's, not the Pi's
   ```
8. **DNS validation — test, don't reason:**
   - `sudo tcpdump -ni sim1 port 53` during a lookup → confirm DNS packets leave `sim1`.
   - Load a **DNS-leak-checker site** through the proxy → confirm resolver = SIM's, not the laptop's.
   - Fallback if DNS bypasses the lane: a per-lane `unbound` (or `dnsmasq`) resolver listening on the `simX` IP, with 3proxy's `nserver` pointed at it.

**Gate:** proceed only if enumeration (2), egress IP (7), and DNS (8) all pass. Else → §12 fallback.

### Phase 2 — Scale to 4
1. Repeat §6.2 for #2–4.
2. udev slot-pinning by physical hub port (draft — confirm real `KERNELS` paths via `udevadm info -a`):
   ```
   # /etc/udev/rules.d/10-sims.rules
   SUBSYSTEM=="net", ACTION=="add", KERNELS=="1-1.1", NAME="sim1"
   SUBSYSTEM=="net", ACTION=="add", KERNELS=="1-1.2", NAME="sim2"
   SUBSYSTEM=="net", ACTION=="add", KERNELS=="1-1.3", NAME="sim3"
   SUBSYSTEM=="net", ACTION=="add", KERNELS=="1-1.4", NAME="sim4"
   ```
3. systemd-networkd `.network` per lane (§10).
4. `3proxy@.service` template; `systemctl enable 3proxy@sim{1..4}`.
5. Verify **all four** ports return four **distinct, correct** public IPs.

### Phase 3 — Monitoring & health (elevated to its own phase)
In production this is nearly as important as the proxy itself. A systemd timer (target: **detect failure within 60 s**) runs a per-lane check script that records:

- **proxy alive** — listen socket accepting connections
- **public IP** — matches the expected SIM (mismatch = crossed wire or churn → alert)
- **DNS server** — resolving via the correct SIM
- **latency** — round-trip through each lane
- **SIM reconnect detection** — egress IP changed since last check
- **history log** — append every check result (see §9)
- **optional alert** — Telegram / Pushover on failure or wrong IP

**Implementation sketch:** timer at `OnUnitActiveSec=30s`; the script curls each port's egress IP and compares against a **baseline `expected-sims.json`** (SIM→IP mapping, updated deliberately on detected churn); history in an append-only log or small SQLite DB with timestamps; alert on wrong public IP, high latency, interface down, or 3proxy not listening. Ship a `check-all-proxies.sh` for quick manual spot-checks (each port's egress IP + latency, plus `ip link` / `ping` per `simX`).

**Cross-check test (validate the safety story, not just liveness):** once monitoring runs, *deliberately swap two MiFis between hub ports* and confirm monitoring **alerts on the IP mismatch** before you correct it. This proves the crossed-wire defense (§7.1) actually fires, rather than assuming it would.

### Phase 4 — AdsPower binding
1. Per profile: SOCKS5 `<PI_LAN_IP>:300X`, creds `simX:<passwordX>`, SOCKS5h / remote DNS.
2. WebRTC = proxy; timezone/geo/language matched to SIM. **Re-verify after AdsPower updates** — confirm updates don't silently reset WebRTC/leak behaviour.
3. Enable "do not use local IP if proxy unavailable."
4. Label each profile with its SIM/subnet.
5. Final check: leak-test page in each profile → correct SIM IP, no DNS/WebRTC leak.

## 9. Logging

Invaluable if an account ever has an unexplained issue — you can reconstruct exactly what egressed when.

- **networkd** — journald; watch carrier up/down per lane.
- **3proxy** — per-instance access/error logs via a `log /var/log/3proxy/simN.log D` directive (the `@.service` template must expand `%i` into the instance name so each lane logs separately), **with `logrotate`**.
- **udev events** — `udevadm monitor` / journal, to catch any interface rename or re-enumeration.
- **IP history** — append-only log of each SIM's observed public IP per monitoring check (the audit trail for "which IP did account X use last Tuesday?").
- **Rotation** across all of the above; the Pi's storage is finite.

## 10. Persistence (survives reboots & reconnects)

- **Interfaces:** udev `NAME=` pins `sim1..4` to physical hub ports.
- **Addressing + routing:** one systemd-networkd `.network` per lane (draft):
  ```
  # /etc/systemd/network/10-sim1.network
  [Match]
  Name=sim1
  [Link]
  RequiredForOnline=no          # one dead lane must not mark the box offline
  [Network]
  Address=192.168.10.2/24
  [Route]
  Gateway=192.168.10.1
  Table=101
  [RoutingPolicyRule]
  From=192.168.10.2
  Table=101
  ```
- **Proxies:** `3proxy@.service` template, enabled per lane.
- **rp_filter / bind:** persist via `/etc/sysctl.d/`; nftables ruleset persisted.
- **Reconnect churn:** static addressing removes the DHCP race; udev re-applies names and networkd re-applies addr/routes on link-up. **Open item:** confirm networkd re-runs the policy rule on carrier bounce — if not, a small idempotent `networkd-dispatcher` (or systemd `oneshot` on link-up) re-adds the `ip rule`. **Test explicitly** by unplug/replug and full power-cycle of everything.
- **Config backups:** the Pi is an appliance — keep all of `/etc/systemd/network/*`, the udev rules, 3proxy configs, nftables ruleset, and monitoring scripts in a **git repo (or off-box backup)**. Rebuilding a dead Pi then becomes a ~10-minute restore, not an afternoon of reconstruction.

## 11. Open questions (please critique)

1. **RNDIS on Linux for M7350 (this firmware)** — highest risk. Clean enumeration, or `usb_modeswitch` needed? RNDIS or CDC-ECM? Success reports for this exact model are sparse/mixed. Phase 1 gates on it; spare adapter ready.
2. **DNS egress correctness** — is `nserver` = SIM gateway enough, or can 3proxy's resolver bypass the policy rule? Validate with `tcpdump` + leak checker (§8); per-lane `unbound` as backup.
3. **Intra-carrier IP churn** — do the sportsbooks tolerate an in-range IP change on reconnect for a persistent account? Test with real accounts early.
4. **USB power/heat at 4 modems** — bus resets under concurrent load? Monitor `dmesg`, `lsusb -t`. Active cooling + spacing the MiFis.
5. **rp_filter 2 vs 0** — loose assumed sufficient; test both.
6. **Monitoring latency** — can the Phase 3 timer reliably detect+alert within 60 s?
7. **Interface naming** — `sim1..4` ≤15 chars, confirm no clash with predictable-names.
8. **Fingerprint beyond IP** — locale/fonts/UA to match SIM geo, not just timezone/WebRTC.
9. **Heat management** for 4 MiFis in close proximity.
10. **Backup power** — UPS sizing for Pi + hub + modems.
11. **Scaling N>4** — Pi 5 is CPU-fine (3proxy is light). USB hub power/port limits are the real ceiling; beyond that, a **second Pi with its own port set** is cleaner than one monster hub.
12. **SD-card wear** — journald + 3proxy + IP-history logging will grind an SD card over time. Put `/var/log` on a **USB SSD**, or use aggressive rotation + `Storage=volatile`-style journald limits.

## 12. Fallback if Phase 1 gate fails

WiFi uplink with **4× USB WiFi adapters**, each joined to one M7350's SSID. Same routing/proxy design downstream; only the uplink changes. Downsides: 2.4 GHz self-interference (set channels 1/6/11), more USB devices, more fragile. Documented fallback only.

## 13. Success criteria

### Immediate acceptance (build complete)
- [ ] 4 profiles run concurrently, each egressing its own SIM's public IP (verified per profile).
- [ ] Switching accounts = switching windows.
- [ ] Killing any one SIM produces a *refused* connection in its profile — never another SIM or the real IP.
- [ ] Mapping survives a Pi reboot and a modem reconnect without manual re-wiring.
- [ ] No DNS/WebRTC/geo leak in any profile.

### Operational goals — judged after ~6 months
- [ ] **Zero** accidental IP crossover events.
- [ ] **Zero** manual remapping required.
- [ ] Automatic recovery after any reboot or power cycle.
- [ ] Adding a 5th SIM takes **under 10 minutes** (template + one hub port).
- [ ] Monitoring detects any lane failure **within 60 seconds**.
- [ ] **Mean recovery time from a failed modem < 5 minutes** (detect → swap/reconnect → verified back on correct IP).

---

## Appendix A — draft nftables ruleset

Restrict the proxy ports to the laptop only; drop everything else to them. Confirm the real interface/IPs before applying.

```
# /etc/nftables.conf (fragment)
table inet filter {
  chain input {
    type filter hook input priority 0; policy drop;

    ct state established,related accept
    iif "lo" accept

    # SSH / admin from LAN as you require (tighten to admin host)
    tcp dport 22 ip saddr <ADMIN_IP> accept

    # proxy ports: laptop only
    ip saddr <LAPTOP_IP> tcp dport 3001-3004 accept

    # everything else to the box: dropped by policy
  }
}
```

```
