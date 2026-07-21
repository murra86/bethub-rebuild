# Phase 1 — Bench One Modem (Beginner Step-by-Step)

**Companion to:** `router_sim_proxy_gateway_brief.md`
**Goal:** Prove one TP-Link M7350 can give the Raspberry Pi internet over its USB cable, then turn it into a proxy your laptop can use. This is the go/no-go test for the whole project.
**Audience:** No Linux or hardware experience assumed.

---

## Before you start — what you need

- **Raspberry Pi 5** with its power supply, plugged into a **screen** (monitor/TV via the Pi's micro-HDMI), plus a **USB keyboard and mouse**. For Phase 1 we work *directly on the Pi*, not from the laptop.
- Raspberry Pi OS already installed and booting to the desktop. *(If your Pi doesn't boot to a desktop, stop here and tell me — we'll set that up first.)*
- **One M7350 modem** with a working SIM that has mobile data.
- The **micro-USB cable** that came with the modem (its charging cable — it also carries data).
- Your **home WiFi**, which the Pi normally connects to.
- Your **laptop** nearby (used only at the very end).

## Three golden rules

1. **Copy-paste commands exactly.** In the Pi's terminal you can paste with right-click (or Ctrl+Shift+V).
2. **After every command, compare what you see to the "YOU SHOULD SEE" note.** If it's different, or you're unsure — **stop and paste it to me.** Never guess.
3. The first time you run a `sudo` command it asks for your password. **As you type the password nothing appears on screen — that's normal.** Type it and press Enter.

**To open the terminal:** on the Pi desktop, click the black **Terminal** icon in the top bar (it looks like a little black screen `>_`).

---

## STAGE 1 — Does the modem give the Pi internet over USB? *(the make-or-break test)*

### Step 1 — Power on the modem
Switch the M7350 on and wait until its little screen shows it's connected to mobile data (signal bars and "LTE" or "4G"). **Give it a full minute.**

- [ ] Modem shows mobile data connected.

### Step 2 — Note your HOME internet identity
So we can tell home vs. modem apart later. In the Pi terminal, type:
```
curl https://ipinfo.io/json
```
**YOU SHOULD SEE** several lines including `"ip": "..."` and `"org": "..."`.
👉 **Write down** the `org` value (your home internet provider's name) and the `ip`.

- [ ] Home `org` = ________________   Home `ip` = ________________

### Step 3 — List the Pi's network devices *(before the modem)*
```
nmcli device status
```
**YOU SHOULD SEE** a short list. `wlan0` is your WiFi. There is no modem row yet. That's expected.

### Step 4 — Plug in the modem
Connect the **small (micro-USB) end** to the modem and the **big flat (USB) end** to any USB socket on the Pi. **Wait about 30 seconds.**

### Step 5 — List the devices again
```
nmcli device status
```
**YOU SHOULD SEE a NEW row** that wasn't there in Step 3 — usually named **`usb0`** or something starting with **`enx`**, with TYPE `ethernet` and STATE `connected`.
👉 **Write down that new name.** We'll call it **THE MODEM NAME** everywhere below.

- [ ] THE MODEM NAME = ________________

❗ **If no new row appears** after a minute: unplug, try a **different micro-USB cable** (some cables only charge and don't carry data), and redo Step 4. Still nothing? **Stop and paste me** what `nmcli device status` shows.

### Step 6 — Turn OFF the Pi's WiFi
This forces the modem to be the *only* way to the internet, so the next test is unambiguous. (Safe — we're working right on the Pi.)
```
nmcli radio wifi off
```

### Step 7 — Confirm only the modem is left
```
nmcli device status
```
**YOU SHOULD SEE** `wlan0` now `disconnected`, and THE MODEM NAME still `connected`.

### Step 8 — The big test
```
curl https://ipinfo.io/json
```
**YOU SHOULD SEE** `"ip"` and `"org"` again — but now the `org` should be your **mobile carrier's** name (the SIM's network), **not** your home provider from Step 2, and the `ip` should be **different**.

- ✅ **Carrier org + a new IP → SUCCESS.** The modem works over USB. **This single result de-risks the entire project.**
- ❌ **Hangs a long time, errors, or still shows your home provider →** the modem isn't giving internet over USB. Do Step 9, then tell me what you saw — we'll switch to the WiFi-adapter fallback plan.

- [ ] Modem `org` = ________________   Modem `ip` = ________________   **Pass? Y / N**

### Step 9 — Turn WiFi back on
We need it for the next stages.
```
nmcli radio wifi on
```

> 🎉 **If Stage 1 passed, the hard question is answered.** Stages 2–3 turn this into a usable proxy. They're a little more technical — go as far as you're comfortable and **paste outputs to me whenever anything looks off.**

---

## STAGE 2 — Steer chosen traffic through the modem *(on the Pi)*

Now WiFi (your normal internet + the link to your laptop) **and** the modem are both connected. We'll tell the Pi: *"anything that starts from the modem's address must leave through the modem."*

### Step 10 — Collect the modem's numbers
Replace `THE_MODEM_NAME` with your name from Step 5:
```
nmcli device show THE_MODEM_NAME | grep IP4
```
**YOU SHOULD SEE** lines like:
```
IP4.ADDRESS[1]:  192.168.0.100/24
IP4.GATEWAY:     192.168.0.1
```
👉 Write down:
- **PI_MODEM_IP** = the number *before* the `/` (example: `192.168.0.100`)
- **MODEM_GW** = the gateway (example: `192.168.0.1`)

- [ ] PI_MODEM_IP = ____________   MODEM_GW = ____________

### Step 11 — Add the routing rules
Type these **one line at a time**, substituting your own `MODEM_GW`, `THE_MODEM_NAME`, and `PI_MODEM_IP`:
```
echo "101 simtest" | sudo tee -a /etc/iproute2/rt_tables
sudo ip route add default via MODEM_GW dev THE_MODEM_NAME table simtest
sudo ip rule add from PI_MODEM_IP table simtest
sudo sysctl -w net.ipv4.conf.THE_MODEM_NAME.rp_filter=2
```
**Example** (if your values were the ones above and the modem name was `usb0`):
```
echo "101 simtest" | sudo tee -a /etc/iproute2/rt_tables
sudo ip route add default via 192.168.0.1 dev usb0 table simtest
sudo ip rule add from 192.168.0.100 table simtest
sudo sysctl -w net.ipv4.conf.usb0.rp_filter=2
```
Most of these print **nothing** when they work — that's fine (no news = good news). The first prints `101 simtest`.
❗ If any line prints an **error**, paste it to me. *(These rules are temporary and vanish on reboot, so nothing here is permanent.)*

### Step 12 — Test the steering
```
curl --interface PI_MODEM_IP https://ipinfo.io/json
```
**YOU SHOULD SEE** the **mobile carrier** `org` and the modem's IP — even though your WiFi is on and working.
- ✅ Proves the Pi can push one chosen stream out the modem while WiFi handles everything else.
- ❌ Shows your home provider, hangs, or errors → paste it to me.

- [ ] **Pass? Y / N**

---

## STAGE 3 — Turn the modem into a proxy your laptop can use *(the real acceptance test)*

### Step 13 — Find the Pi's home address
```
hostname -I
```
**YOU SHOULD SEE** one or more addresses. Pick the one that looks like your home network (usually starts `192.168.` and matches your laptop's WiFi). 👉 Call it **PI_LAN_IP**.

- [ ] PI_LAN_IP = ________________

### Step 14 — Install the proxy software
```
sudo apt update
sudo apt install -y 3proxy
```
**YOU SHOULD SEE** it download and install without errors.
❗ If it says **"Unable to locate package 3proxy"**, stop and tell me — I'll give you an alternative.

### Step 15 — Create the proxy's settings file
```
sudo nano /etc/3proxy/simtest.cfg
```
A simple text editor opens. Type (or paste) this, **replacing the three placeholders with your values**:
```
nserver MODEM_GW
auth none
external PI_MODEM_IP
socks -p3001 -iPI_LAN_IP -ePI_MODEM_IP
```
**Example** (using the sample numbers; note there is **no space** after `-i` and `-e`):
```
nserver 192.168.0.1
auth none
external 192.168.0.100
socks -p3001 -i192.168.1.50 -e192.168.0.100
```
Save and close: press **Ctrl+O** then **Enter** (saves), then **Ctrl+X** (exits).

*(“auth none” = no password, for this test only — we add a password before real use. `-i` means the proxy only listens on your home-network side.)*

### Step 16 — Start the proxy
```
sudo 3proxy /etc/3proxy/simtest.cfg &
```
The `&` lets it keep running in the background. **YOU SHOULD SEE** a number (its process id) and then your prompt come back. No error lines = good.

### Step 17 — Test from the LAPTOP *(this is the acceptance test)*
Go to your **laptop**. Open its Terminal (on Mac: press Cmd-Space, type "Terminal", press Enter). Type, replacing `PI_LAN_IP`:
```
curl --socks5-hostname PI_LAN_IP:3001 https://ipinfo.io/json
```
**YOU SHOULD SEE** the **mobile carrier** `org` and the modem's public IP.
- ✅ **This is the win.** Your laptop just reached the internet *through the Pi, out of the modem's SIM* — exactly what AdsPower will do for each account.
- ❌ Hangs or errors → paste it to me. *(Usually a laptop firewall or the proxy not listening — we'll sort it.)*

- [ ] **Pass? Y / N**

### Step 18 — Check DNS isn't leaking
We confirm that *name lookups* also travel through the SIM (not your home connection). **On the Pi**, start watching:
```
sudo tcpdump -ni THE_MODEM_NAME port 53
```
This sits and waits — leave it running. Now **on the laptop** run:
```
curl --socks5-hostname PI_LAN_IP:3001 https://example.com
```
Look back at the Pi's tcpdump window.
- ✅ **A line or two appears** right after → DNS is going out through the modem (no leak). 
- ❌ **Nothing appears** → DNS may be leaking; tell me and I'll add a small per-modem DNS helper.

Stop the watcher with **Ctrl+C**.

### Step 19 — Clean up and report
Stop the test proxy:
```
sudo pkill 3proxy
```
The routing rules from Stage 2 are temporary and clear on the next reboot. Nothing else needs undoing.

👉 **Send me:** your home `org`/`ip`, the modem `org`/`ip`, and a Y/N for Stage 1 (Step 8), Stage 2 (Step 12), Stage 3 (Step 17), and the DNS check (Step 18). From that I'll tell you whether we're clear to build all four, and turn these temporary steps into the permanent, reboot-proof setup for Phase 2.

---

## Quick reference — the values you collected
| Name | Your value | Found in |
|---|---|---|
| THE MODEM NAME | | Step 5 |
| PI_MODEM_IP | | Step 10 |
| MODEM_GW | | Step 10 |
| PI_LAN_IP | | Step 13 |
