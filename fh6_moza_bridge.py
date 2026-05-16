"""
fh6_moza_bridge.py - Forza Horizon 6 -> MOZA Pit House telemetry bridge.

Pit House supports Forza Horizon 5 (UDP "Data Out", 324-byte "Car Dash"
layout) on UDP 30055 by default, but has no FH6 entry yet. FH6's "Data
Out" feature emits the same family of packets, so this bridge listens on
a port FH6 is told to send to, normalizes the payload to the FH5 layout
Pit House expects, and forwards to 127.0.0.1:30055.

Default flow:
    FH6  ---UDP--->  :4009 (this bridge)  ---UDP--->  127.0.0.1:30055 (Pit House)

In FH6: Settings -> HUD and Gameplay -> Data Out
    Enabled  : ON
    IP       : 127.0.0.1
    Port     : 4009          (matches --listen-port)
    Format   : Car Dash      (NOT Sled - we need the full layout)

Usage:
    python fh6_moza_bridge.py                  # default ports, quiet
    python fh6_moza_bridge.py --inspect        # decode + print first packet
    python fh6_moza_bridge.py --listen-port 4010 --pit-house-port 30055

Stdlib only. Python 3.8+.

License: MIT
Project : https://github.com/<you>/fh6-moza-bridge   (community project)
"""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time
from dataclasses import dataclass

# --- Forza Data Out v2 ("Car Dash") wire format ---------------------------
# Layout is identical across FH4 / FH5 / Forza Motorsport. FH6 is expected
# to inherit the same prefix; any new fields appended at the end can be
# safely truncated for Pit House (which only parses up through FH5 offsets).
SLED_SIZE = 232
FM7_DASH_SIZE = 311          # FM7 Car Dash (no HorizonPlaceholder pad)
FH5_DASH_SIZE = 324          # FH4 / FH5 Car Dash (Pit House expects this)


@dataclass
class Stats:
    received: int = 0
    forwarded: int = 0
    dropped_small: int = 0
    truncated: int = 0
    passthrough: int = 0
    last_size: int = 0
    last_log: float = 0.0


def normalize_for_pit_house(payload: bytes, stats: Stats) -> bytes | None:
    """
    Return a 324-byte payload Pit House can parse as FH5 Car Dash, or None
    if the input is unusable.

    Cases:
      len == 324 :  pass-through (FH5-identical, the expected happy path)
      len  > 324 :  truncate to first 324 bytes (FH6 likely appends fields)
      len == 311 :  FM7-style packet; not handled yet (would need re-pack)
      len  < 232 :  too small to be Forza Data Out at all, drop
    """
    n = len(payload)
    stats.last_size = n

    if n == FH5_DASH_SIZE:
        stats.passthrough += 1
        return payload

    if n > FH5_DASH_SIZE:
        stats.truncated += 1
        return payload[:FH5_DASH_SIZE]

    if n == FM7_DASH_SIZE:
        # FM7 omits the 12-byte HorizonPlaceholder between sled and dash.
        # If we ever see this from FH6 we'll need to inject 12 zero bytes
        # at offset 232. Not observed yet - log and drop for now.
        stats.dropped_small += 1
        return None

    stats.dropped_small += 1
    return None


def decode_sample(payload: bytes) -> str:
    """One-line human-readable decode of a Car Dash packet, for --inspect."""
    if len(payload) < FH5_DASH_SIZE:
        return f"(short packet, {len(payload)}B - cannot decode as Car Dash)"
    is_race_on, ts_ms = struct.unpack_from("<iI", payload, 0)
    cur_rpm = struct.unpack_from("<f", payload, 16)[0]
    speed = struct.unpack_from("<f", payload, 256)[0]
    accel = payload[315]
    brake = payload[316]
    gear = payload[319]
    return (
        f"race={is_race_on}  ts={ts_ms}ms  rpm={cur_rpm:6.0f}  "
        f"speed={speed*3.6:5.1f}kph  gear={gear}  throttle={accel:3d}  brake={brake:3d}"
    )


def run(listen_host: str, listen_port: int,
        targets: list[tuple[str, int]],
        inspect: bool, quiet: bool) -> int:

    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        rx.bind((listen_host, listen_port))
    except OSError as e:
        print(f"[fatal] cannot bind {listen_host}:{listen_port}  ({e})", file=sys.stderr)
        print("        another listener (FH6 itself, Pit House, SimHub) may already own this port.", file=sys.stderr)
        return 1

    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"FH6 -> MOZA Pit House bridge")
    print(f"  listening : udp {listen_host}:{listen_port}   (point FH6 'Data Out' here)")
    for h, p in targets:
        print(f"  forwarding: udp {h}:{p}")
    print(f"  inspect   : {inspect}")
    print("  Ctrl+C to stop.\n")

    stats = Stats()
    inspected = False

    try:
        while True:
            payload, _src = rx.recvfrom(4096)
            stats.received += 1

            out = normalize_for_pit_house(payload, stats)
            if out is None:
                continue

            for t in targets:
                tx.sendto(out, t)
            stats.forwarded += 1

            if inspect and not inspected:
                print(f"[inspect] first packet: {len(payload)}B  ->  forwarding {len(out)}B")
                print(f"[inspect] {decode_sample(out)}")
                print(f"[inspect] hex (first 64B): {payload[:64].hex()}")
                print()
                inspected = True

            if not quiet:
                now = time.time()
                if now - stats.last_log > 1.0:
                    sys.stdout.write(
                        f"\rrx={stats.received:>7}  tx={stats.forwarded:>7}  "
                        f"passthru={stats.passthrough}  trunc={stats.truncated}  "
                        f"drop={stats.dropped_small}  lastSz={stats.last_size}B    "
                    )
                    sys.stdout.flush()
                    stats.last_log = now
    except KeyboardInterrupt:
        print("\n\nstopped.")
        print(f"  received  : {stats.received}")
        print(f"  forwarded : {stats.forwarded}")
        print(f"  passthrough (324B exact): {stats.passthrough}")
        print(f"  truncated (>324B)       : {stats.truncated}")
        print(f"  dropped (too small)     : {stats.dropped_small}")
        return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Translate Forza Horizon 6 Data Out telemetry into the FH5 format MOZA Pit House understands.",
    )
    p.add_argument("--listen-host", default="0.0.0.0",
                   help="Interface to receive FH6 packets on (default 0.0.0.0)")
    p.add_argument("--listen-port", type=int, default=4009,
                   help="UDP port FH6 'Data Out' is configured to send to (default 4009)")
    p.add_argument("--pit-house-host", default="127.0.0.1",
                   help="Where Pit House is listening (default 127.0.0.1)")
    p.add_argument("--pit-house-port", default="30055",
                   help="Pit House FH5 listener port (default 30055). "
                        "Comma-separate to fan-out (e.g. '30055,40266').")
    p.add_argument("--inspect", action="store_true",
                   help="Decode and print the first packet, for verifying format")
    p.add_argument("--quiet", action="store_true",
                   help="Suppress the live counters line")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    targets = [(a.pit_house_host, int(p.strip())) for p in str(a.pit_house_port).split(",") if p.strip()]
    raise SystemExit(run(a.listen_host, a.listen_port,
                         targets,
                         a.inspect, a.quiet))
