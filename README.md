# FH6 → MOZA Pit House bridge

![License](https://img.shields.io/github/license/satyajiit/forza-horizon-6-moza-bridge?color=blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6?logo=windows)
![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![Works with FH6](https://img.shields.io/badge/works%20with-Forza%20Horizon%206-7B2CBF)
![MOZA Pit House](https://img.shields.io/badge/MOZA-Pit%20House-E10600)
![Last commit](https://img.shields.io/github/last-commit/satyajiit/forza-horizon-6-moza-bridge)
[![YouTube](https://img.shields.io/badge/YouTube-%40GamesPatch-FF0000?logo=youtube&logoColor=white)](https://www.youtube.com/@GamesPatch?sub_confirmation=1)

A tiny UDP relay that makes **Forza Horizon 6** work with **MOZA Pit House** today, while we wait for official FH6 support.

Pit House supports Forza Horizon 5 ("Data Out", Car Dash format) on UDP **:30055** by default — but it only opens that listener when it sees a process named `ForzaHorizon5.exe` running, and it doesn't recognise FH6 at all. FH6 emits the same Data Out packets, just on a different name and (by default) a different port. So we sit a thin relay in the middle:

```
   FH6  ──UDP──▶  :4009 (this bridge)  ──UDP──▶  127.0.0.1:30055 (Pit House, FH5 mode)
```

Plus a harmless dummy `ForzaHorizon5.exe` (a renamed copy of `ping.exe`) that runs in the background to satisfy Pit House's process-name check.

**Confirmed:** FH6's Car Dash payload is **byte-for-byte identical** to FH5. Every packet is exactly 324 B; the bridge runs in pure pass-through mode. The truncate path exists as a safety net only.

## Download

The prebuilt Windows binary lives in this repo at [`dist/fh6-moza-bridge.exe`](https://github.com/satyajiit/forza-horizon-6-moza-bridge/raw/main/dist/fh6-moza-bridge.exe) — click that link and your browser will download it directly. No Python install needed.

If you'd rather run from source, every script is stdlib-only Python 3.8+:

```powershell
git clone https://github.com/satyajiit/forza-horizon-6-moza-bridge.git
cd forza-horizon-6-moza-bridge
.\start_all.bat
```

## Quick start (3 steps)

### 1. Configure FH6 (one time)

In-game: **Settings → HUD and Gameplay → Data Out**

| Field    | Value                       |
| -------- | --------------------------- |
| Enabled  | **ON**                      |
| IP       | `127.0.0.1`                 |
| Port     | `4009`                      |
| Format   | **Car Dash** (not "Sled")   |

### 2. Configure Pit House (one time)

Open MOZA Pit House and select **Forza Horizon 5** as the active game. You can tune your wheel's RPM LEDs and FFB profile here; everything you set will apply when FH6 telemetry starts flowing.

### 3. Every session: double-click `start_all.bat`

It does both pieces of the workaround for you:

1. Spawns the dummy `ForzaHorizon5.exe` process so Pit House opens UDP :30055.
2. Starts the bridge — receives FH6 packets on :4009, forwards them to :30055 untouched.

A console window stays open with live counters (`rx / tx / passthru / trunc / drop`). **Ctrl+C** to stop the bridge. Run **`stop_all.bat`** afterwards to clean up the dummy process.

### Verifying it works

After running `start_all.bat`, drive a few seconds and check:

- Wheel RPM LEDs respond to engine revs (tune the curve in Pit House → RPM Lights if needed).
- The Pit House dashboard shows live speed / gear / lap times.
- From a PowerShell window:
  ```powershell
  Get-NetUDPEndpoint | Where-Object { $_.LocalPort -in 4009,30055 }
  ```
  Both ports should show up — :4009 owned by the bridge, :30055 owned by `MOZA Pit House`. If :30055 is missing, the spoof didn't take — re-run `start_all.bat`.

## CLI options

```
fh6-moza-bridge.exe --help
```

| Flag                  | Default          | Purpose                                                |
| --------------------- | ---------------- | ------------------------------------------------------ |
| `--listen-port`       | `4009`           | UDP port FH6 sends to                                  |
| `--pit-house-port`    | `30055`          | Where Pit House listens (comma-separate for fan-out)   |
| `--pit-house-host`    | `127.0.0.1`      | Useful if Pit House is on another LAN machine          |
| `--inspect`           | off              | Decode and print the first packet (for verification)   |
| `--quiet`             | off              | Hide the live counters                                 |

## Project layout

```
forza-horizon-6-moza-bridge/
├── start_all.bat           ← double-click to run a session
├── stop_all.bat            ← double-click to clean up
├── build.bat               ← rebuild the exe with PyInstaller
├── fh6_moza_bridge.py      ← source (~200 lines, stdlib only)
├── dist/
│   └── fh6-moza-bridge.exe ← the downloadable Windows binary
├── spoof/                  ← ForzaHorizon5.exe spoof scripts
│   ├── start_spoof.ps1
│   └── stop_spoof.ps1
└── tools/                  ← optional diagnostics (see tools/README.md)
    ├── recon.py
    ├── live_monitor.py
    ├── test_bridge.py
    ├── capture_burst.py
    └── find_inputs.py
```

## Troubleshooting

**`cannot bind 0.0.0.0:4009`** — something else (SimHub, an old bridge instance) already owns the port. Change FH6's Data Out port to e.g. 4010 and start with `--listen-port 4010`.

**Bridge receives packets but Pit House isn't reacting** — confirm Pit House opened the FH5 listener:

```powershell
Get-NetUDPEndpoint | Where-Object { $_.LocalPort -eq 30055 }
```

If nothing returns, the `ForzaHorizon5.exe` spoof isn't running. Re-run `start_all.bat`, or manually:

```powershell
.\spoof\start_spoof.ps1
```

**RPM LEDs only light near redline** — that's not a bridge problem; Forza reports `EngineMaxRpm` as the engine's *absolute ceiling*, and cars redline well below that. Open Pit House → R9 → RPM Lights and move the "first LED" threshold down to ~40-50%. The Pit House FH5 profile is the one being used.

**Packet size in counters is not 324 B** — either FH6 changed the format in a patch or you have "Sled" selected instead of "Car Dash". Recheck FH6's Data Out setting, and if the size is consistent but different, capture with `tools/recon.py` and open an issue with the hex.

## How this was reverse-engineered

1. Found `GameForwardingInfo.xml` inside Pit House's install (`C:\Program Files (x86)\MOZA Pit House\bin\GameConfigs\`). It declared `<_Forza_Horizon_5 ListeningPort="30055">` — our target.
2. Selecting FH5 in Pit House did **nothing** until a process named `ForzaHorizon5.exe` actually existed in the system. Verified with `Get-NetUDPEndpoint` before and after — the listener opens the instant the spoof process appears.
3. Live capture from FH6 confirmed the Forza "Data Out" wire format hasn't changed since FH5 (324 B Car Dash, all standard offsets including input bytes at 315/316/319). 100 % pass-through across tens of thousands of packets, zero translation needed.

## License

MIT. Take it, fork it, ship it.

## Contributing

Especially welcome:

- Reports from MOZA bases other than R9 (R5, R12, R16, R21).
- Reports that FH6 emitted a packet size other than 324 B — that means a patch changed the wire format and we need real translation logic, not pass-through. Capture a packet with `tools/recon.py` and attach the hex.
- LED curve recommendations for popular car classes in FH6.

---

## Stay in the loop

If this got your sim-racing weekend back on track, consider subscribing on YouTube — I post sim-racing tools, fixes, and hardware reviews on **@GamesPatch**:

<p align="center">
  <a href="https://www.youtube.com/@GamesPatch?sub_confirmation=1">
    <img src="https://img.shields.io/badge/YouTube-Subscribe%20to%20%40GamesPatch-FF0000?logo=youtube&logoColor=white&style=for-the-badge" alt="Subscribe to @GamesPatch on YouTube"/>
  </a>
</p>
