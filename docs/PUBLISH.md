# Publishing kit

Everything you need to paste into GitHub + community posts when you ship this.

---

## 1. Repo short description (the "About" field, ~110 chars)

> Drop-in UDP bridge that makes Forza Horizon 6 work with MOZA Pit House today — RPM LEDs, dashboard, and telemetry.

Alt:

> Get your MOZA wheel's RPM LEDs and Pit House dashboard working with Forza Horizon 6 — one batch file, no SimHub.

---

## 2. GitHub topics (for discovery)

```
forza-horizon-6
forza
moza
moza-pit-house
moza-r9
sim-racing
simracing
telemetry
udp-bridge
windows
```

---

## 3. Long description (paste into a repo description or wiki Home page)

**fh6-moza-bridge** is a tiny, zero-dependency Windows utility that makes Forza Horizon 6 work with MOZA Pit House while MOZA adds official support.

Pit House already supports Forza Horizon 5 — it expects Forza's "Data Out" UDP telemetry (the 324-byte "Car Dash" format) on port 30055, and only opens that listener when a process named `ForzaHorizon5.exe` is running. FH6 emits the **byte-for-byte identical** telemetry format on whatever port you configure, but Pit House doesn't recognize the game, so the listener never opens.

This project does two things:

1. Spawns a harmless dummy `ForzaHorizon5.exe` (a renamed copy of `ping.exe` pinging localhost) to satisfy Pit House's process-name check, so it opens its FH5 telemetry listener on UDP :30055.
2. Runs a 200-line UDP relay that receives FH6 telemetry on :4009 and forwards it to :30055 untouched. Pit House parses each packet as FH5 (because that's exactly what it looks like) and drives your wheel and dashboard normally.

End result: RPM LEDs sweep with engine revs, the in-app dashboard shows live speed/gear/lap, and force-feedback configs from your FH5 profile apply to FH6. **No SimHub. No game patching. Reversible the moment you close the apps.**

---

## 4. Release notes — v1.0.0

```markdown
## v1.0.0 — first public release

### What's in the box
- `fh6-moza-bridge.exe` — single-file Windows executable, no Python required.
- `start_all.bat` / `stop_all.bat` — one-click launch and cleanup.
- Pure pass-through bridge (FH6 → MOZA Pit House) verified against tens
  of thousands of live packets.
- Auto-spoof of `ForzaHorizon5.exe` to unlock Pit House's FH5 listener.
- Source code (~200 lines, stdlib only, MIT-licensed).
- Diagnostic tools: `recon.py`, `live_monitor.py`, `_find_inputs.py`.

### Verified setup
- Windows 11
- MOZA R9 base + pedals
- MOZA Pit House (latest as of 2026-05-16)
- Forza Horizon 6 (initial release build), "Data Out" → 127.0.0.1:4009,
  format "Car Dash"

### Confirmed working
- Wheel RPM shift LEDs (tune the curve in Pit House → RPM Lights)
- In-app dashboard fields: speed, gear, RPM, throttle, brake, lap times
- Force feedback profile inheritance from FH5

### Known caveats
- The bridge does NOT modify any Forza, MOZA, or system file.
- The spoof is a renamed `C:\Windows\System32\ping.exe`. It does nothing
  except idle and tell Pit House the FH5 process exists. Close it any
  time with `stop_all.bat` or Task Manager.
- If a future MOZA Pit House update adds real FH6 support, you can stop
  using this tool entirely — nothing to uninstall.

### Tested-on hardware
If you have a different MOZA base (R5, R12, R16, R21) and it works for
you, please open an issue confirming so I can extend this list.
```

---

## 5. Community post (Reddit / Moza Discord / forums)

```markdown
**Got FH6 + MOZA Pit House working — sharing a tiny one-click bridge for everyone stuck on the same problem**

If you've upgraded to Forza Horizon 6 and noticed your MOZA wheel's RPM
LEDs / dashboard / Pit House telemetry stopped working, here's why and
how to fix it without waiting for an official update:

- Pit House detects games by **process name**. It binds its FH5 telemetry
  listener (UDP :30055) only when it sees `ForzaHorizon5.exe` running.
- FH6 ships as `forzahorizon6.exe`, so Pit House never opens the listener.
- But FH6's "Data Out" UDP packets are **byte-for-byte identical** to
  FH5's Car Dash format. If Pit House just received them, it would parse
  them fine.

So I built a small open-source utility that:
1. Spawns a harmless dummy `ForzaHorizon5.exe` (renamed `ping.exe`
   pinging localhost) so Pit House opens its FH5 listener.
2. Forwards every FH6 packet from :4009 to :30055 untouched.

Result: RPM lights, dashboard, telemetry all work in FH6 today.

**Setup is literally:**
1. In FH6, turn on Data Out → 127.0.0.1:4009, format "Car Dash".
2. In Pit House, select Forza Horizon 5 once.
3. Double-click `start_all.bat`.

Zero dependencies (single Windows exe), MIT-licensed, ~200 lines of
Python, no game files touched, fully reversible.

Repo: https://github.com/satyajiit/forza-horizon-6-moza-bridge

Code review and issue reports very welcome — especially from anyone on
a different MOZA wheel base than the R9 I tested on.
```

---

## 6. Suggested first commit message

```
Initial public release: FH6 -> MOZA Pit House bridge v1.0.0

A small Windows utility that gets MOZA Pit House working with Forza
Horizon 6 today, while official support is pending. Pure UDP
pass-through (FH6's wire format = FH5 byte-for-byte) plus a
process-name spoof to satisfy Pit House's FH5 detection gate.

Verified on Windows 11, MOZA R9, FH6 launch build.
```

---

## 7. Pushing to GitHub

The exe is committed directly in the repo at `dist/fh6-moza-bridge.exe`. The README links to the raw URL on `main`, so the moment you push, the Download button works.

### Initial push

```powershell
git init
git branch -M main
git add .
git commit -m "Initial public release: FH6 -> MOZA Pit House bridge v1.0.0"
git remote add origin https://github.com/satyajiit/forza-horizon-6-moza-bridge.git
git push -u origin main
```

That's it — README's Download link starts working immediately, and the badges at the top will populate (license / last-commit / etc.) within a few seconds.

### Future updates

When you change the source:

```powershell
.\build.bat                  # rebuild dist\fh6-moza-bridge.exe
git add fh6_moza_bridge.py dist/fh6-moza-bridge.exe
git commit -m "Describe what changed"
git push
```

The rebuilt exe replaces the previous one in the repo, and everyone downloading the link gets the latest binary.
