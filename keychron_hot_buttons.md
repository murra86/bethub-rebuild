# Keychron hot buttons — one key per browser (S257 write-up)

What you asked for (S253 feedback item 3): press one key on the Q6 Max
and the right browser jumps to the front — no mouse, no Cmd-Tab hunting
mid-burst. Nothing in BetHub changes; this is keyboard + macOS only.
Total setup ~15 minutes, once.

## How it works (one sentence)

The keyboard sends a combo no app uses (Control+Option+Command+number),
and macOS turns that combo into "bring this browser to the front —
launch it if it isn't running".

## Part 1 — macOS side (do this first; no installs, built-in Shortcuts app)

For EACH browser you want a key for:

1. Open the **Shortcuts** app (it's in Applications).
2. Click **+** (new shortcut).
3. In the search box on the right, type **Open App**, double-click it.
4. Click the pale word **App** in the action and pick the browser
   (e.g. Google Chrome).
5. Click the shortcut's name at the top and rename it (e.g. "Focus
   Chrome").
6. Click the ⓘ info button (right side) → **Add Keyboard Shortcut** →
   press **Control+Option+Command+1** (hold all three modifiers, tap 1).
7. Repeat for the next browser with …+2, …+3, etc.

Suggested layout (adjust to your real set):

| Combo | Browser |
|---|---|
| Ctrl+Opt+Cmd+1 | Chrome (BetHub lives here) |
| Ctrl+Opt+Cmd+2 | AdsPower |
| Ctrl+Opt+Cmd+3 | Safari |
| Ctrl+Opt+Cmd+4 | (whatever you use for Betfair) |

Test now from the normal keyboard: press a combo — the browser should
come to the front (first use may ask permission once; click Allow).
"Open App" focuses the app if it's already running, launches it if not —
exactly the launch-or-focus behaviour you wanted.

## Part 2 — Keychron side (put each combo on one key)

The Q6 Max is configured in the browser at **usevia.app** (Chrome):

1. Plug the keyboard in **by cable**, open **usevia.app** in Chrome,
   click **Authorize device** and pick the Keychron.
2. Go to the **MACROS** tab, select **M0**, click **Record**, press
   **Control+Option+Command+1**, click **Stop**, then **Save**.
3. Repeat: M1 = …+2, M2 = …+3, M3 = …+4.
4. Go back to the **KEYMAP** tab. Pick a layer you don't type on
   (layer 1 is fine — hold Fn to reach it) or sacrifice keys you never
   use (F13-style spares, or the knob-adjacent keys).
5. Click the physical key you want, then in the keycode list choose
   **MACRO → M0**. Repeat for M1–M3 on neighbouring keys.

That's it — settings live in the keyboard itself, so they survive
reboots and work on any Mac.

## Notes

- **One key = one browser app.** If you later want one key per
  *AdsPower profile* (not just the AdsPower app), that's a different,
  fiddlier setup — say so and I'll scope it separately.
- The Ctrl+Opt+Cmd+digit combos clash with nothing standard on macOS.
- If a combo ever stops working, the usual cause is macOS permissions:
  System Settings → Privacy & Security → Accessibility → make sure
  Shortcuts is on.
- This pairs with DR-012 (keyboard-first hot path): BetHub-side
  shortcuts (log bet, next persona, etc.) are a separate build item and
  will use plain single keys inside the app, not these combos.

---

## AS BUILT — S258, 29 Jul 2026 (COMPLETE, operator-confirmed)

The plan above was superseded during setup — final working shape:

- **One key per AdsPower PROFILE** (not per browser app), via the
  AdsPower local API.
- Launcher: `~/bin/adspower_hotkey.sh <profile_id>` — focuses the
  profile's browser if open (found by its debug port, title-proof),
  starts it if closed, cold-starts AdsPower itself if needed. Contains
  the AdsPower local API key (Bearer auth) — LOCAL MACHINE ONLY, never
  copy into a repo/report.
- Bound through **Automator Quick Actions** (`~/Library/Services/
  Focus {Sarie,Kate,Mads}.workflow`) + System Settings → Keyboard →
  Keyboard Shortcuts → Services → General. (Shortcuts app was a dead
  end on this Mac: Run Shell Script / Open App actions never appeared
  despite Allow Running Scripts being on.)
- Keys (VIA remap on layer 0 where noted):
  | Button | Sends | Profile |
  |---|---|---|
  | circle | F13 (factory) | Sarie (k1eecqw0) |
  | triangle | F17 (remapped — factory F14 = macOS brightness) | Kate (k1bcbwis) |
  | square | F18 (remapped — factory F15 = macOS brightness) | Mads (k1eeeq6i) |
  | cross | free | reserved for the Mango profile — remap to F19,
  one more Quick Action + Services bind when it exists |
- Wireless note: assignments live in the keyboard; works over the
  2.4G dongle. VIA config needs cable mode + a DATA USB-C cable
  (charge-only cables enumerate nothing).
