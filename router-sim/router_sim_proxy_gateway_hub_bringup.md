# Router/SIM Gateway — Hub Bring-Up Pack (prepared 2026-07-07)

Everything pre-written so the CHU810 session is plug → paste → verify.
Companion to `router_sim_proxy_gateway_status.md` (§7 is the plan this executes).

**State when prepared:** Pi up at `192.168.0.162` (ping OK, SSH port open), but ports
3001/3002/3003 all closed → no modem plugged in at prep time. SSH is key-only and the
laptop's key isn't authorized yet (previous sessions were VNC-driven).

---

## Step 0 — One-time: let the laptop SSH in (do via VNC, ~30s)

On the Pi (VNC terminal), run:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB9ZqtBaa+leAEseERHxGqc7CeKyK1A2cIQIv3NMTWk0 tim@racing-vps' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
whoami   # note the username — the laptop needs it
```

Then from the laptop: `ssh <username>@192.168.0.162` should log straight in.
After this, Claude Code can drive the whole bring-up remotely — no more VNC needed
for this project.

## Step 1 — Hub physical setup

1. CHU810 into wall power. USB-A upstream cable → Pi.
2. Modems into **BLUE ports only** (red = charge-only, invisible to the Pi).
3. All per-port switches **OFF** first, then flip on **one at a time**, ~15s apart
   (avoids the inrush overcurrent that tripped the Pi's own ports).
4. Each modem must be powered on (screen alive) with a **data-capable** micro-USB cable.

## Step 2 — Verify all modems enumerate together (first time ever)

On the Pi:

```bash
lsusb | grep -c M7350          # expect = number of modems plugged
ip -4 -o addr show             # expect 192.168.2.2-ish AND 192.168.3.2-ish (and .4 later)
systemctl --no-pager status sim-proxy sim-proxy2
ip route get 1.1.1.1           # must still say "dev wlan0" (Pi itself on home WiFi)
```

**Known risk to watch (status doc §7A.3):** the `netplan-eth0` NetworkManager
connection matches *all* ethernet devices. With several RNDIS modems + real eth0
present at once, one modem may enumerate in `lsusb` but never get an IP. Diagnosis:

```bash
nmcli device                   # look for a modem iface stuck in "connecting"/"disconnected"
journalctl -u NetworkManager -n 50 --no-pager
```

Fix if it bites: give each modem interface its own NM connection keyed to interface
name (names are stable — the `.link` file sets NamePolicy=path):

```bash
nmcli con add type ethernet ifname <modem-ifname> con-name sim-a ipv4.method auto ipv6.method disabled
```

(one per modem; `ipv6.method disabled` here also does most of the §C IPv6 lockdown
at the source — see Step 5.)

## Step 3 — From the laptop: both accounts at once (the point of the hub)

```bash
curl --socks5-hostname 192.168.0.162:3001 https://ipinfo.io/json   # expect Optus AS4804
curl --socks5-hostname 192.168.0.162:3002 https://ipinfo.io/json   # expect Vodafone AS133612
```

Both returning their own carrier **simultaneously** = hub milestone done. True
window-switching from here.

## Step 4 — Add Router #3 (Account C) — paste-ready

On the Pi:

```bash
sudo tee /etc/systemd/system/sim-proxy3.service > /dev/null <<'EOF'
[Unit]
Description=SOCKS5 proxy for SIM C (192.168.4.x)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/sim-proxy.sh 192.168.4 103 3003
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now sim-proxy3
```

> Before pasting, sanity-check the unit shape against the working one:
> `systemctl cat sim-proxy2` — if it differs from the above (env vars, User=, etc.),
> mirror sim-proxy2 exactly and only change `192.168.4 103 3003`.

The dispatcher (`60-sim-refresh`) already restarts `sim-proxy3` on modem events —
no change needed there.

Then plug Router #3 (blue port, switch on, ~15s) and test:

```bash
curl --socks5-hostname 192.168.0.162:3003 https://ipinfo.io/json   # note carrier/IP for the mapping table
```

AdsPower: create Profile C → SOCKS5 `192.168.0.162:3003`, no auth, WebRTC disabled,
timezone/location/language "Based on IP" (mirror Profiles A/B).

## Step 5 — IPv6 lockdown (required once ≥2 modems run at once)

Why: IPv4 is policy-routed per SIM, but IPv6 would ride one uncontrolled default →
a profile's v4 and v6 could exit **different SIMs**. (Do NOT kernel-disable IPv6 —
that killed microsocks last time.)

Two acceptable fixes, in order of preference:

**5a. Per-connection disable (simplest, try first):** if Step 2 ended up creating
per-modem NM connections, `ipv6.method disabled` on each modem connection means the
Pi never gets a modem-side IPv6 route at all. Verify microsocks still works after
(`curl` tests above) — this disables v6 on the *interface config* level, not the
kernel level that broke things before. Also confirm the Pi has no default v6 route
via any modem: `ip -6 route show default`.

**5b. AAAA-filtering resolver (the status doc's plan):**

```bash
sudo apt install dnsmasq
sudo tee /etc/dnsmasq.d/filter-aaaa.conf > /dev/null <<'EOF'
filter-AAAA
# serve DNS to localhost only
listen-address=127.0.0.1
bind-interfaces
EOF
sudo systemctl enable --now dnsmasq
# point the Pi's resolver at dnsmasq (NetworkManager owns resolv.conf):
sudo tee /etc/NetworkManager/conf.d/dns.conf > /dev/null <<'EOF'
[main]
dns=none
EOF
sudo sh -c 'echo "nameserver 127.0.0.1" > /etc/resolv.conf'
sudo systemctl restart NetworkManager
```

**Caveat:** AAAA-filtering only helps for `--socks5-hostname`-style (proxy-side DNS)
lookups, which is what AdsPower/browsers do through SOCKS5 — that's the case that
matters. Test immediately after: both curls in Step 3 must still work, and inside a
profile `https://test-ipv6.com` should show **no IPv6** connectivity.

**Rollback if anything breaks:** `sudo systemctl disable --now dnsmasq`, delete the
two files above, `sudo systemctl restart NetworkManager`.

## Step 6 — Polish (optional, same session if time permits)

- **DHCP reservation** for the Pi (`192.168.0.162`) on the home router — do this one;
  a lease change silently breaks every AdsPower profile.
- nftables: restrict 3001–3004 to the laptop (`192.168.0.196`). Note the laptop has
  no reservation either — reserve both or skip the firewall for now.
- Heartbeat: cron on the Pi curling each port's egress IP, alert on wrong-carrier.
  (Can be built later from the laptop once SSH works.)

## Success checklist

- [ ] `lsusb` shows all modems at once; each has its subnet IP
- [ ] 3001 = Optus and 3002 = Vodafone **simultaneously** from the laptop
- [ ] `ip route get 1.1.1.1` on the Pi still via `wlan0`
- [ ] sim-proxy3 live, port 3003 returns Router #3's carrier; mapping table updated
      in `router_sim_proxy_gateway_status.md` (SIM carrier, egress IP, profile name)
- [ ] Replug test: switch one modem's hub port off/on → proxy self-recovers ≤30s
- [ ] Reboot test: `sudo reboot` → all three proxies come back with no hands
- [ ] IPv6: no modem-side v6 default route / test-ipv6.com shows v4-only in a profile
- [ ] Update status doc §2 mapping + flip §3 interim workflow to "obsolete"
