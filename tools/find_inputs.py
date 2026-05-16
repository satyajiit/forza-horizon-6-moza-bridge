"""
Diagnostic: find where FH6 *actually* puts Accel / Brake / Gear / Steer.

In FH5, the input bytes sit at offsets 311-316. Our captures show FH6
maxing offset-311 at ~66 even at WOT, which means the layout shifted or
the scale changed. This script scans every byte in the dash region while
the user floors the pedal, and reports which byte positions track the
input.

Run after starting the bridge with fan-out to 9999.

Phase 1: idle/zero baseline (5s)  - press nothing, stay in menu or pit
Phase 2: full-throttle (10s)      - mash accelerator pedal
Phase 3: full-brake (5s)          - mash brake pedal

The script prints, for each byte offset 200..323, the (min, max) value
seen across each phase. The Accel byte will be one that's ~0 in phases
1+3 and high in phase 2. Brake mirrors that.
"""
import socket
import struct
import sys
import time

PORT = 9999
BYTES_START = 200
BYTES_END = 324


def phase(s: socket.socket, name: str, seconds: float):
    print(f"\n{'='*60}")
    print(f">>>>>>>>>>  {name}  ({seconds:.0f}s)  <<<<<<<<<<")
    print(f"{'='*60}", flush=True)
    mins = [255] * (BYTES_END - BYTES_START)
    maxs = [0] * (BYTES_END - BYTES_START)
    end = time.time() + seconds
    n = 0
    last_tick = 0.0
    while time.time() < end:
        remaining = end - time.time()
        if time.time() - last_tick > 0.5:
            print(f"  ... {remaining:4.1f}s remaining", flush=True)
            last_tick = time.time()
        try:
            data, _ = s.recvfrom(4096)
        except socket.timeout:
            continue
        if len(data) < BYTES_END:
            continue
        n += 1
        for i, off in enumerate(range(BYTES_START, BYTES_END)):
            b = data[off]
            if b < mins[i]:
                mins[i] = b
            if b > maxs[i]:
                maxs[i] = b
    print(f"  captured {n} packets in this phase", flush=True)
    return mins, maxs


def main() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", PORT))
    s.settimeout(0.2)

    print("FH6 byte-layout finder. Auto-paced.")
    print("Total runtime ~21s. Follow the phase banners.\n", flush=True)
    time.sleep(1)

    p1_min, p1_max = phase(s, "PHASE 1: RELEASE ALL PEDALS (idle)", 5)
    p2_min, p2_max = phase(s, "PHASE 2: MASH GAS - FULL THROTTLE NOW", 10)
    p3_min, p3_max = phase(s, "PHASE 3: MASH BRAKE - FULL BRAKE NOW", 5)

    # Score: byte is "interesting" if it varies a lot between phases
    print("\n\nOffsets where the byte was LOW at idle and HIGH at full throttle (Accel candidates):")
    print(f"{'offset':>6}  {'idle min/max':>15}  {'gas min/max':>15}  {'brake min/max':>15}")
    for i, off in enumerate(range(BYTES_START, BYTES_END)):
        # candidate accel: p2_max significantly higher than p1_max and p3_max
        if p2_max[i] >= 200 and p1_max[i] < 30 and p3_max[i] < 30:
            print(f"   {off:>4}    {p1_min[i]:3d}/{p1_max[i]:3d}        {p2_min[i]:3d}/{p2_max[i]:3d}        {p3_min[i]:3d}/{p3_max[i]:3d}    <-- accel?")

    print("\nOffsets where the byte was LOW at idle and HIGH at full brake (Brake candidates):")
    print(f"{'offset':>6}  {'idle min/max':>15}  {'gas min/max':>15}  {'brake min/max':>15}")
    for i, off in enumerate(range(BYTES_START, BYTES_END)):
        if p3_max[i] >= 200 and p1_max[i] < 30 and p2_max[i] < 30:
            print(f"   {off:>4}    {p1_min[i]:3d}/{p1_max[i]:3d}        {p2_min[i]:3d}/{p2_max[i]:3d}        {p3_min[i]:3d}/{p3_max[i]:3d}    <-- brake?")

    # Also show top-10 byte positions ranked by total range across phases
    print("\nTop 10 most-varying bytes (range across all phases):")
    ranges = []
    for i, off in enumerate(range(BYTES_START, BYTES_END)):
        all_min = min(p1_min[i], p2_min[i], p3_min[i])
        all_max = max(p1_max[i], p2_max[i], p3_max[i])
        ranges.append((all_max - all_min, off, p1_min[i], p1_max[i], p2_min[i], p2_max[i], p3_min[i], p3_max[i]))
    ranges.sort(reverse=True)
    for rng, off, p1mi, p1ma, p2mi, p2ma, p3mi, p3ma in ranges[:10]:
        print(f"   off {off:>3}  range={rng:>3}   idle {p1mi}/{p1ma}   gas {p2mi}/{p2ma}   brake {p3mi}/{p3ma}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
