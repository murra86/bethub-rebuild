# Pi SIM-proxy config — backup & restore

Backup of all bespoke config for the Router/SIM SOCKS gateway (Pi `192.168.0.162`, user `murra86`).
Taken 2026-07-08. Closes the SD-card single-point-of-failure. Re-pull after any config change.

## What's here
- `pi-simproxy-config.tgz` — all config files, rooted at `/` (extract with paths).
- `nm-and-notes.txt` — NetworkManager DNS/route settings (not plain files) + 3proxy build info.

Contents of the tarball:
- `usr/local/bin/sim-proxy.sh` — per-lane launcher (3proxy config gen + policy routing + C1 rule cleanup)
- `usr/local/bin/sim-proxy-healthcheck.sh` — 15-min egress/AS monitor
- `etc/systemd/system/sim-proxy{,2,3}.service` (+ `.d/no-start-limit.conf` drop-ins)
- `etc/systemd/system/sim-proxy-health.{service,timer}`
- `etc/systemd/network/10-rndis-modems.link` — distinct name+MAC per modem (they ship identical)
- `etc/NetworkManager/dispatcher.d/60-sim-refresh` — auto-resync proxies on modem replug
- `etc/nftables.conf` — restrict proxy ports 3001-3004 to the MacBook
- `etc/sysctl.d/99-simproxy.conf` — tcp_timestamps=0

NOT in the tarball (rebuild separately):
- `/usr/local/bin/3proxy` — binary; rebuild from source: `git clone https://github.com/3proxy/3proxy`
  (commit `de5acb2`), `sudo apt install libssl-dev`, `make -f Makefile.Linux`, copy `bin/3proxy`.

## Restore onto a fresh Pi (Debian trixie, NetworkManager)
1. Rebuild 3proxy (above) → `/usr/local/bin/3proxy`.
2. Extract config: `sudo tar xzf pi-simproxy-config.tgz -C /`
3. `sudo chmod +x /usr/local/bin/sim-proxy.sh /usr/local/bin/sim-proxy-healthcheck.sh /etc/NetworkManager/dispatcher.d/60-sim-refresh`
4. Re-apply the NetworkManager settings from `nm-and-notes.txt`:
   ```
   sudo nmcli con modify netplan-eth0 ipv4.ignore-auto-dns yes ipv4.dns "" ipv4.dns-priority 200 \
        ipv4.never-default yes ipv6.method disabled ipv6.never-default yes connection.multi-connect multiple
   sudo nmcli con modify netplan-wlan0-<SSID> ipv4.dns-priority 10
   ```
   (Connection names differ per install; list with `nmcli con show`.)
5. `sudo systemctl daemon-reload`
6. `sudo systemctl enable --now nftables sim-proxy sim-proxy2 sim-proxy3 sim-proxy-health.timer`
7. Verify: `curl --socks5-hostname 192.168.0.162:3001 https://ipinfo.io/json` (Optus), :3002 (Vodafone),
   :3003 (Vocus); `ip rule show` (one rule/table); `cat /proc/sys/net/ipv4/tcp_timestamps` (0);
   `grep nameserver /etc/resolv.conf` (home only); `ip route get 1.1.1.1` (dev wlan0).

Also needed on a fresh install: SSH key for the laptop in `~/.ssh/authorized_keys`; DHCP reservations
on the home router (Pi `192.168.0.162`, Mac `192.168.0.196`); the M7350 modems on distinct subnets
(192.168.2/3/4.x). Full design + history: `../router_sim_proxy_gateway_status.md`.
