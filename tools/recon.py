"""
recon.py - Inspect Forza Horizon 6 "Data Out" UDP telemetry.

Run while driving in FH6 (Settings -> HUD and Gameplay -> Data Out =
ON, IP 127.0.0.1, Port 4009). Reports packet size distribution, dumps
the first packet as hex, and attempts to decode it as the known Forza
Data Out v2 ("Car Dash") layout used by FH4 / FH5 / Forza Motorsport.

Goal: confirm whether FH6 keeps the existing 324-byte layout, appended
new fields, or restructured the packet entirely. The answer drives the
translator design in step 2.

Stdlib only - no install required. Python 3.8+.
"""

from __future__ import annotations

import socket
import struct
import sys
import time

PORT = 4009

SLED_SIZE = 232          # Forza Data Out v1
DASH_SIZE_FM7 = 311      # FM7 "Car Dash"
DASH_SIZE_FH = 324       # FH4 / FH5 "Car Dash" (12-byte HorizonPlaceholder)


def decode_known_layout(data: bytes) -> None:
    """Print decoded fields assuming FH5 'Car Dash' offsets."""
    if len(data) < SLED_SIZE:
        print(f"  [decode] packet too small ({len(data)}B) for Forza Data Out")
        return

    is_race_on, ts_ms = struct.unpack_from("<iI", data, 0)
    max_rpm, idle_rpm, cur_rpm = struct.unpack_from("<fff", data, 8)
    print(f"  IsRaceOn      = {is_race_on}")
    print(f"  TimestampMS   = {ts_ms}")
    print(f"  RPM           = cur {cur_rpm:7.1f}   idle {idle_rpm:6.1f}   max {max_rpm:6.1f}")

    # End of sled - CarOrdinal sits at offset 212
    if len(data) >= 216:
        car_ord, car_class, car_pi, drivetrain, cyls = struct.unpack_from("<iiiii", data, 212)
        print(f"  CarOrdinal    = {car_ord}   class={car_class}  PI={car_pi}  drive={drivetrain}  cyl={cyls}")

    if len(data) >= DASH_SIZE_FH:
        # Dash extension starts at offset 244 in FH layout
        # (sled 232 + 12-byte HorizonPlaceholder = 244)
        pos_x, pos_y, pos_z, speed, power, torque = struct.unpack_from("<ffffff", data, 244)
        boost, fuel, dist = struct.unpack_from("<fff", data, 244 + 24 + 16)  # after tireTemp[4]
        best_lap, last_lap, cur_lap, race_time = struct.unpack_from("<ffff", data, 292)
        lap_num = struct.unpack_from("<H", data, 308)[0]
        race_pos = data[310]
        accel = data[311]
        brake = data[312]
        clutch = data[313]
        hbrake = data[314]
        gear = data[315]
        steer = struct.unpack_from("<b", data, 316)[0]
        print(f"  Position      = ({pos_x:8.1f}, {pos_y:8.1f}, {pos_z:8.1f})")
        print(f"  Speed (m/s)   = {speed:7.2f}    (kph {speed*3.6:6.1f})")
        print(f"  Power / Torque= {power:8.1f} W  / {torque:7.1f} Nm")
        print(f"  Boost / Fuel  = {boost:.3f} / {fuel:.3f}    Distance = {dist:.1f}")
        print(f"  Lap           = #{lap_num}  cur {cur_lap:6.2f}s  last {last_lap:6.2f}s  best {best_lap:6.2f}s")
        print(f"  Inputs        = throttle {accel:3d}  brake {brake:3d}  clutch {clutch:3d}  hbrake {hbrake:3d}  gear {gear}  steer {steer:+d}")
        print(f"  RacePosition  = {race_pos}   RaceTime = {race_time:.2f}s")
    elif len(data) >= DASH_SIZE_FM7:
        print(f"  Looks like FM7-style Car Dash ({DASH_SIZE_FM7}B) - no HorizonPlaceholder pad")
    else:
        print(f"  Sled-only payload ({len(data)}B), no Dash extension")


def main() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", PORT))
    except OSError as e:
        print(f"Could not bind UDP :{PORT} - is another listener already on that port?  ({e})")
        return 1

    print(f"Listening on UDP :{PORT}.  Drive in FH6.  Ctrl+C to stop.\n")

    sizes: dict[int, int] = {}
    first_packet: bytes | None = None
    count = 0
    last_status = 0.0

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            count += 1
            sizes[len(data)] = sizes.get(len(data), 0) + 1

            if first_packet is None:
                first_packet = data
                print(f"First packet: {len(data)} bytes from {addr[0]}:{addr[1]}")
                print(f"  hex: {data.hex()}\n")
                decode_known_layout(data)
                print()

            now = time.time()
            if now - last_status > 1.0:
                hist = "  ".join(f"{sz}B x{n}" for sz, n in sorted(sizes.items()))
                sys.stdout.write(f"\rpackets={count}   sizes: {hist}   ")
                sys.stdout.flush()
                last_status = now
    except KeyboardInterrupt:
        print(f"\n\nStopped. Total packets: {count}")
        print(f"Size distribution: {sizes}")
        if first_packet is not None:
            with open("first_packet.bin", "wb") as f:
                f.write(first_packet)
            print("First packet saved to first_packet.bin for offline analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
