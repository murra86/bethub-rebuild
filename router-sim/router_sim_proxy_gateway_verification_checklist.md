# Profile Verification Checklist — run inside each AdsPower profile

Run every test **from inside the profile's own browser window** (open the profile, then
navigate). Do the full set per profile: **Kate**, **Sarie**, **Mads** (and lane D later).
Paste anything ambiguous to Claude and it'll interpret + watch the Pi side.

**Expected egress per lane** (the anchor every test must agree with):
| Profile | Carrier / AS | Region → Timezone the profile should show |
|---|---|---|
| Kate | Optus AS4804 | Adelaide → `Australia/Adelaide` |
| Sarie | Vodafone AS133612 | Adelaide → `Australia/Adelaide` |
| Mads | Vocus AS9443 | Melbourne → `Australia/Melbourne` |

> Timezones legitimately **differ** between profiles (they follow each SIM's IP city) — that's
> correct, not a fault. What matters is each profile is *internally* consistent: its timezone
> matches its own IP's city.

---

## A. Core leak tests (MUST pass)

1. **ipleak.net**
   - IP = the lane's carrier (AS above), Australian, mobile.
   - DNS servers = that carrier's network, **no Superloop, no other carrier**.
   - IPv6 = "not reachable".
   - WebRTC = **empty** (no IP shown).
2. **browserleaks.com/webrtc** — dedicated WebRTC. Must show **no local (192.168.x / 10.x)
   and no public home IP**. Blank or only the SIM IP is fine.
3. **dnsleaktest.com** → click **Extended test** — every resolver listed must be on the
   lane's carrier network. Any Superloop/home entry = fail.

## B. "Does it look like a real device?" (anti-detect consistency)

4. **whoer.net** — anonymity score. Look for: no red mismatches; IP, DNS, timezone,
   language all agree; WebRTC clean. (A high % is nice but the *mismatch flags* matter more.)
5. **pixelscan.net** — should read **"consistent" / fingerprint looks natural**, no
   automation/anti-detect detected.
6. **iphey.com** — wants **"Trustworthy"** on each row (IP, WebRTC, location, hardware,
   software). Any "Suspicious" → note which and paste it.

## C. Deep fingerprint + cross-profile uniqueness (the non-linkage test)

7. **abrahamjuliot.github.io/creepjs** — the strict one. Check:
   - **Trust Score** reasonable; **no / few "lies"** flagged (lies = spoofing inconsistencies).
   - Record the **fingerprint hash** (and glance at canvas/WebGL/audio).
8. **Cross-profile compare:** run creepjs (or **amiunique.org**) in **all three** profiles and
   confirm the **fingerprint hashes DIFFER** between Kate, Sarie, Mads. Two profiles sharing a
   hash = they'd look like the same device = linkage risk (would mean cloned/identical FP).

## D. Spot-checks

9. **WebGL renderer** (browserleaks.com/webgl or in creepjs): should be a plausible GPU
   string, **not** `llvmpipe` / `SwiftShader` / "Google software" (those scream VM/headless).
10. **Timezone vs IP:** confirm the profile's timezone matches its IP city (table above).
11. **Language:** `en-AU` (or consistent AU English) across the profile.

---

## Known residuals these browser tests will NOT catch (documented, accepted)
- **TCP/OS mismatch:** the profiles claim Windows; the underlying Pi TCP stack is Linux
  (same MSS/options on every lane). Only deep *passive TCP* fingerprinting sees this — rare
  for bookmakers. All the JS-layer tests above will still pass clean.
- **Same-host TCP stack across lanes:** mitigated for the clock-skew vector (TCP timestamps
  disabled, verified on the wire); the static stack pattern remains identical across lanes.

## Pass criteria summary
A profile is "sound" when: A1–A3 clean (right carrier IP+DNS, no WebRTC/IPv6/home leak),
B4–B6 show no mismatch/"suspicious", C7 few/no lies, C8 unique vs the other profiles,
D9 a real GPU, D10 timezone matches IP. Record results per profile below.

| Test | Kate | Sarie | Mads |
|---|---|---|---|
| A1 ipleak IP/DNS/WebRTC/IPv6 | ✅ Optus AS4804, DNS dnsmob02.adl.optusnet, WebRTC empty, v6 unreachable | | |
| A2 browserleaks WebRTC | ✅ No Leak, local/public blank | | |
| A3 dnsleak extended | ✅ all Optus, no Superloop | | |
| B4 whoer | ✅ Proxy No / Anonymizer No / Blacklist No | | |
| B5 pixelscan | ✅ consistent, no proxy/masking/automation | | |
| B6 iphey | ✅ Trustworthy, hw+sw fine | | |
| C7 creepjs | ✅ 0% headless / 0% stealth; Win10/11 label = non-issue | | |
| C8 FP hashes (must differ) | Canvas `53d6dcdd` · WebGL `9b74bde5`/px`d3c1d40a` · Audio `f8a04acb` · Fonts `fa9049d1` | | |
| D9 WebGL renderer | ✅ ANGLE Intel UHD (real, not llvmpipe) | | |
| D10 timezone vs IP | ✅ Australia/Adelaide = IP | | |

### ✅ Sarie RE-SEEDED & RE-TESTED (2026-07-08): fingerprint now UNIQUE
Root cause was duplication copying Kate's noise SEEDS (Canvas 250167CA etc. identical on both).
Fix = in-place **"New fingerprint"** button in AdsPower (kept cookies/logins, no delete needed).
Re-seed changed everything: Canvas `53d6dcdd`→`e5427004`, WebGL `9b74bde5`→`72fccca4`,
Audio `f8a04acb`→`2c9149c2`, Fonts `fa9049d1`→`a68d8fa2` (all now DIFFER from Kate); also GPU
UHD 610 (0x00003EA1) vs Kate's 0x00009BA4, CPU 12 vs 4 cores, new device name/MAC, fonts 96 vs 551.
creepjs C8 now PASSES. Network unchanged/correct (Vodafone AS133612, port 3002). **Still TODO for
Sarie: re-run pixelscan + iphey (both flagged the old dup — confirm they now go green).**
**LESSON: never Duplicate; if a dup already exists, hit "New fingerprint" to re-seed in place.**
**OPEN ISSUE (2026-07-08): iphey on re-seeded Sarie = ONE red flag "Detected anti-detect browser
environment (ads)"** — all else green (location/IP/hardware/software/bot all pass). This is
anti-detect-browser DETECTABILITY (iphey can tell it's AdsPower SunBrowser), NOT linkage (linkage
fixed). Likely tension: per-profile noise (needed for uniqueness) is what specialist detectors
(iphey/MixVisit, pixelscan "masking") flag. **pixelscan on re-seeded Sarie = NOW FULLY GREEN** (consistent, No masking detected, no proxy,
no bot) — the re-seed also fixed the old "inconsistent/masking" pixelscan fail. So the ONLY
remaining flag in the whole battery is iphey's "anti-detect browser environment." Since pixelscan
(equally specialist) sees NO masking + full consistency, the iphey flag is almost certainly
signature detection of AdsPower's SunBrowser KERNEL itself, not a Sarie misconfig → would apply to
ALL AdsPower profiles incl. Kate. Diagnostic pending: re-test KATE on iphey 2-3× (detection is
non-deterministic). If Kate also flags → AdsPower-wide; decide whether this class matters for the
target AU bookmakers (TAB/Sportsbet etc.) and whether to try a different browser kernel to dodge
iphey's signature. If Kate stays clean across runs → compare Kate vs Sarie configs. Core
protections all intact regardless: per-account unique device FP (no linkage), correct mobile
carrier IP+DNS, no WebRTC/IPv6/home leak, no bot/automation signals.

**RESOLVED-ish 2026-07-08: iphey flag is Sarie-CONFIG-specific, NOT AdsPower-wide.** Kate re-test
= "Trustworthy / Not detected" (clean). Root cause = IMPLAUSIBLE HARDWARE COMBO from the random
re-seed: Sarie got Intel **UHD 610** (entry-level iGPU, only ships with 2-core Celeron/Pentium/i3)
+ **12 CPU cores** + 8GB RAM — a machine that doesn't exist → iphey's hardware-plausibility check
flags it as fabricated/anti-detect. Kate's combo (mid UHD + 4 cores + 8GB) = normal laptop → passes.
FIX ATTEMPT (hardware) FAILED/DISPROVEN: re-rolled Sarie to discrete NVIDIA GT 1030 + 16 cores —
iphey STILL flagged identically. So the fingerprint VALUES are NOT the cause; the hardware-combo
hypothesis is dead. **Actual pattern: fresh-created Kate = clean; duplicated-then-reseeded Sarie =
flagged 3/3 across totally different fingerprints → trigger is STRUCTURAL to the Sarie profile,
untouched by re-seeding.** Leading hypotheses: (a) a masking TOGGLE/setting Sarie has that Kate
doesn't (operator changed Sarie's settings post-duplication) — supporting clue: "SVG Computed Style"
is stable 129.5313 on BOTH Sarie re-rolls vs 124.4063 on Kate (a config diff re-seed doesn't touch);
(b) iphey non-determinism (Kate n=1). NEXT: (A) diff Kate's Fingerprint/Advanced settings vs Sarie's
(have Sarie's) to find the toggle; (B) run Kate iphey 2-3× more to confirm reliably clean. If real
diff found → match Sarie to Kate. If not resolvable → decisive experiment = create a TRULY FRESH
profile on 3002 (every Sarie tested so far is the re-seeded DUPLICATE) and test it; if fresh passes,
the fix is recreate-fresh + migrate cookies. **Still likely a real lesson: prefer fresh New Profile
over duplicate+reseed.**

**2026-07-08 SETTINGS DIFF DONE — Kate & Sarie settings are IDENTICAL** (every toggle: WebRTC
Disabled, TZ/Loc/Lang Based-on-IP, Screen 3840×2160, Fonts Custom, all 6 hardware-noise ON, WebGL
metadata Custom, WebGPU Disabled, Random-FP OFF). So NOT a settings diff. Kate now 2/2 clean, Sarie
3/3 flagged → real difference, not non-determinism. "SVG Computed Style" varies run-to-run on Kate
too (124.4063→129.5313) = noise, not signal. **ELIMINATED: fingerprint values, settings, non-determinism.
Remaining differentiator = Sarie is a DUPLICATE, Kate is FRESH.** Duplication copies the whole browser
data dir (cache/service-workers/localStorage/profile state); "New fingerprint" only re-rolls the FP,
not that inherited data. iphey/MixVisit runs in a service worker → almost certainly detects a
copied-data artifact. **FIX: recreate Sarie as a genuinely FRESH New Profile (not dup, not re-seed).**
Confirm cheaply first with a throwaway fresh "TEST" profile → iphey; if clean, recreate Sarie fresh
+ preserve logins (cookie export/import OR re-login, passwords known). Mads unaffected (will be fresh).

**2026-07-08 CONFIRMED: fresh TEST profile = iphey CLEAN ("Not detected").** So: fresh=clean,
duplicate=flagged, definitively. Root cause = DUPLICATE ORIGIN (copied browser-data-dir artifact),
not fixable by re-seeding. **FIX: delete duplicated Sarie → create genuinely FRESH New Profile
(proxy 3002/Vodafone, WebRTC off, tz/lang Based-on-IP, sanity-check hardware) → re-login (passwords
known; expect new-device verification). Delete the TEST profile after (no proxy, leaked home IP).**
OS note: TEST was NATIVE MAC (no spoofing) and clean — recommend making Sarie native Mac (more
robust than Windows-on-Mac spoofing + more distinct from Kate/Windows). Kate proves Windows also OK.
**HARDENED RULE: "never Duplicate" — a duplicated profile is itself iphey-detectable via inherited
browser data, independent of fingerprint. Always create fresh. (Kate=fresh clean; Mads=create fresh.)**

**2026-07-08 RESOLVED: fresh native-Mac Sarie = iphey CLEAN ("Not detected").** Recreated Sarie as
a genuinely fresh New Profile: **native macOS** (Apple OS selected, not Windows-spoof), proxy 3002
(Vodafone, verified), WebRTC Disabled, tz/loc/lang Based-on-IP, all 6 Hardware-noise ON (Canvas
Noise FD0D5CF8 / WebGL 6A2051CF etc.), hardware fixed to coherent combo (8 cores + Intel HD 630 +
MacBook Pro; was an impossible 20-core roll). iphey now Trustworthy. **PROVEN RECIPE for every new
profile: fresh New Profile (never duplicate) + native OS + all noise ON + sanity-checked hardware
combo + correct proxy port.** NOTE: iphey's per-component "Canvas" hash is NOT render-unique (same
across different-OS profiles) — use **creepjs** for the authoritative canvas/webgl/audio uniqueness
check. Remaining for Sarie: creepjs 4-hash vs Kate + ipleak/browserleaks/pixelscan + re-login.
Then build Mads fresh (native OS, all noise ON, coherent hardware, port 3003) + 3-way creepjs.

**2026-07-08 Sarie fresh-Mac FULL BATTERY (pixelscan pending):** creepjs UNIQUE vs Kate — Canvas
`3225273c` / WebGL `1f1491ac` / Audio `e8601166` / Fonts `3ed14632` (Kate: 53d6dcdd/9b74bde5/
f8a04acb/fa9049d1) — all differ; device = macOS Catalina/MacIntel/8-core/Intel HD630 (vs Kate
Win/4-core/UHD), Mac voice Karen, 0% headless/stealth, gpu confidence high. ipleak = Vodafone IP+DNS,
no Superloop, v6 unreachable, Sec-Ch-Ua-Platform macOS (DNS "101 errors" = mobile-DNS latency, not a
leak). browserleaks WebRTC = no leak. **3-profile creepjs baseline now: Kate Canvas 53d6dcdd; Sarie
Canvas 3225273c; Mads TBD.** **pixelscan on fresh-Mac Sarie = GREEN (consistent / no masking / no proxy / no bot). → SARIE FULLY
CLEARED, all tests pass.** (Portrait-screen non-issue: 2160×3840 is just Retina 2× of 1080×1920,
pixelscan reports "consistent" — leave it.) Remaining for Sarie: re-login only. Then build Mads.
**PROVEN RECIPE (confirmed on Sarie): New Profile (never dup) → native OS → all 6 hardware-noise ON
→ coherent hardware combo → correct proxy port → run battery → creepjs uniqueness vs other profiles.**

**2026-07-08 MADS BUILT + VERIFIED — 3-ACCOUNT SETUP COMPLETE.** Mads = fresh native-Mac, port 3003
Vocus (verified Melbourne IP), all noise ON, CPU fixed 10→8 (was implausible with Intel HD 630).
Full battery PASS: iphey "Not detected", pixelscan consistent/no-masking, ipleak Vocus IP+DNS no-Superloop
v6-unreachable, browserleaks no-leak, creepjs 0% headless/high GPU confidence, timezone Melbourne.
**3-WAY creepjs uniqueness — Canvas/WebGL/Audio ALL differ across Kate/Sarie/Mads:**
Kate 53d6dcdd/9b74bde5/f8a04acb ; Sarie 3225273c/1f1491ac/e8601166 ; Mads b5bf0029/2dac0597/0995f4d9.
FONTS: Kate fa9049d1 (Windows) unique; **Sarie=Mads 3ed14632 — EXPECTED & CORRECT** (two Macs, same
macOS version = identical system font set; do NOT force apart — a Mac with non-standard fonts is MORE
suspicious). Shared low-entropy Mac specs (HD630/8-core/screen) between Sarie&Mads = "two people with
the same MacBook model, different cities (Adelaide vs Melbourne), different render hashes + carrier IPs"
= realistic, NOT linkage (render fingerprints + IP + city all differ). **All 3 accounts sound: distinct
devices, distinct carriers, no leaks, no anti-detect flags.** Remaining: Sarie re-login; use Mads.
Residual (all profiles, low pri): Screen Resolution spoof 3840×2160 vs real Mac 1920×1080 seam.

#### (superseded) Sarie verdict (2026-07-07): NETWORK PASS, FINGERPRINT FAIL — provisioning PAUSED

- **Network layer: PASS.** Vodafone AS133612; DNS 203.21.117.134 Vodafone (no Superloop/Optus);
  WebRTC clean (ipleak + browserleaks); IPv6 unreachable; timezone Adelaide = IP; effectiveType 4g.
- **FAIL C8 — device fingerprint IDENTICAL to Kate:** Canvas `53d6dcdd`, WebGL `9b74bde5`
  (px `d3c1d40a`), Audio `f8a04acb` (data `8249f4de`), Fonts `fa9049d1` — all match Kate,
  and underlying values byte-identical (canvas textMetrics, audio sum/gain/freq, GPU Intel UHD
  0x00009BA4, cores 4/ram 8). → cross-account **device-linkage** vector: a device-fingerprinting
  vendor would see Kate & Sarie as the same machine despite different carrier IPs.
- **FAIL B5/B6:** pixelscan "inconsistent / Masking detected" (Kate was "consistent/no masking");
  iphey "Unreliable" (Kate "Trustworthy"). Composite creepjs FP IDs DIFFER (Kate
  `a945fb7b64677a0a…`, Sarie `dc9e3322fa6854ae…`) — but only because of SOFT/volatile signals
  (speech voice Kate en-IE vs Sarie en-GB; color depth 30 vs 24; audio "trap" timing). The
  DURABLE hardware vectors (canvas/webgl/audio/fonts) still collide → the composite difference
  does NOT clear the linkage; it just localises it to the high-value stable vectors. Pattern =
  canvas/webgl/audio noise effectively OFF/shared (all profiles fall back to the same underlying
  render) while cosmetic params differ.
- **Root cause (to confirm): AdsPower fingerprint config, NOT the Pi/network.** Likely Canvas/
  WebGL/Audio/Fonts not set to per-profile Noise, or profiles cloned from a shared template.
- **ACTION:** fix per-profile fingerprints (each unique + each passes pixelscan/iphey) BEFORE
  creating Mads or using real balances. Diagnose via AdsPower Local API (read each profile's
  fingerprint config) or GUI settings audit. Then re-run this whole battery on all profiles.

**Kate verdict (2026-07-07): PASS, all tests.** Notes: creepjs "Win10" label vs userAgentData
"Win11 [15.0.0]" is expected (Chrome UA always says NT 10.0; platformVersion 15 = real Win11).
"25% like headless" is benign (0% actual headless/stealth). GPU = Intel UHD 0x00009BA4;
cores 4 / ram 8; network effectiveType "4g" (nicely consistent with a mobile story).
