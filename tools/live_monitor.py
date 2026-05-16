"""
live_monitor.py - subscribe to the bridge's fan-out and print live
RPM / speed / throttle so we can see exactly what Pit House is seeing.

Run alongside the bridge after adding 127.0.0.1:9999 to its fan-out:
    python fh6_moza_bridge.py --pit-house-port 30055,9999

Then in another window:
    python live_monitor.py
"""
import socket
import struct
import sys
import time

PORT = 9999


def main() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", PORT))
    print(f"listening on udp 127.0.0.1:{PORT}  (drive in FH6, Ctrl+C to stop)\n")

    max_rpm_seen = 0.0
    max_engine_max = 0.0
    last_print = 0.0
    n = 0

    while True:
        try:
            data, _ = s.recvfrom(4096)
        except KeyboardInterrupt:
            print("\nstopped.")
            print(f"  max RPM observed (current) : {max_rpm_seen:.0f}")
            print(f"  highest EngineMaxRpm seen  : {max_engine_max:.0f}")
            print(f"  % of EngineMaxRpm reached  : {(max_rpm_seen/max_engine_max*100) if max_engine_max else 0:.1f} %")
            return 0

        if len(data) < 324:
            continue
        n += 1

        is_race_on, _ts = struct.unpack_from("<iI", data, 0)
        engine_max, idle, cur = struct.unpack_from("<fff", data, 8)
        speed = struct.unpack_from("<f", data, 256)[0]
        accel = data[315]
        brake = data[316]
        gear = data[319]

        max_rpm_seen = max(max_rpm_seen, cur)
        max_engine_max = max(max_engine_max, engine_max)

        now = time.time()
        if now - last_print > 0.1:
            pct = (cur / engine_max * 100) if engine_max > 0 else 0
            bar_len = 40
            bar_fill = int(pct / 100 * bar_len) if pct < 100 else bar_len
            bar = "#" * bar_fill + "-" * (bar_len - bar_fill)
            sys.stdout.write(
                f"\rrace={is_race_on}  rpm {cur:5.0f}/{engine_max:5.0f}  "
                f"idle {idle:5.0f}  [{bar}] {pct:5.1f}%  "
                f"gear {gear}  spd {speed*3.6:5.1f}kph  thr {accel:3d}  brk {brake:3d}  "
            )
            sys.stdout.flush()
            last_print = now


if __name__ == "__main__":
    raise SystemExit(main())
