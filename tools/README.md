# tools/

Optional diagnostic scripts. You only need them if something looks off — the main bridge has no dependency on any of them.

All are stdlib-only Python 3.8+. Run from this folder.

| Script              | What it does                                                                                          |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| `recon.py`          | Listens on :4009 and hex-dumps the first FH6 packet. Use this if your FH6 install emits a packet size other than 324 B and we need to see the bytes. |
| `test_bridge.py`    | Fires synthetic 324 B / 400 B / 100 B packets at a running bridge and checks they arrive on :30055 correctly. No game required. |
| `live_monitor.py`   | Subscribes to the bridge's fan-out (start bridge with `--pit-house-port 30055,9999`) and prints live RPM / speed / gear / throttle with a percent-of-redline bar. |
| `capture_burst.py`  | Captures N seconds (default 10) from the bridge fan-out and prints the RPM envelope you reached (`python capture_burst.py 15`). Useful for tuning the LED curve in Pit House. |
| `find_inputs.py`    | Auto-paced 3-phase diagnostic (idle → mash gas → mash brake) that identifies which byte offsets hold Accel / Brake / Gear / Steer. Used to verify the FH6 layout matches FH5. |

## Typical usage

```powershell
# In one terminal, start the bridge with the diagnostic fan-out port:
..\dist\fh6-moza-bridge.exe --pit-house-port 30055,9999

# In another:
python live_monitor.py
```

## When you might want each

- **You think FH6 might have changed its format in a patch** → `recon.py` first (hex dump), then `find_inputs.py` to find the new input-byte offsets.
- **Your RPM LEDs aren't lighting evenly** → `capture_burst.py` while flat-out to see what `EngineMaxRpm` is for that car, then dial the Pit House LED curve.
- **You don't have FH6 installed but want to verify the bridge works** → `test_bridge.py`.
- **You want to watch live telemetry numbers** → `live_monitor.py`.
