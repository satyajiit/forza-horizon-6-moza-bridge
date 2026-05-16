"""Listen for N seconds (default 10), then print the RPM envelope we observed."""
import socket
import struct
import sys
import time

duration = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1", 9999))
s.settimeout(0.5)

print(f"capturing for {duration:.0f} seconds — drive flat-out now")
end = time.time() + duration
n = 0
max_cur = 0.0
max_em = 0.0
idle_seen = 0.0
max_speed = 0.0
max_throttle = 0
samples = []

while time.time() < end:
    try:
        data, _ = s.recvfrom(4096)
    except socket.timeout:
        continue
    if len(data) < 324:
        continue
    n += 1
    is_race_on, _ = struct.unpack_from("<iI", data, 0)
    em, idle, cur = struct.unpack_from("<fff", data, 8)
    speed = struct.unpack_from("<f", data, 256)[0]
    accel = data[315]
    if cur > max_cur:
        max_cur = cur
    if em > max_em:
        max_em = em
    if idle > idle_seen:
        idle_seen = idle
    if speed > max_speed:
        max_speed = speed
    if accel > max_throttle:
        max_throttle = accel
    if n % 50 == 0:
        samples.append((cur, em, accel, speed * 3.6))

print(f"packets captured     : {n}")
print(f"highest current RPM  : {max_cur:.0f}")
print(f"highest EngineMaxRpm : {max_em:.0f}")
print(f"observed idle RPM    : {idle_seen:.0f}")
print(f"max speed            : {max_speed*3.6:.1f} kph")
print(f"max throttle byte    : {max_throttle}/255  ({max_throttle/255*100:.0f}%)")
if max_em > 0:
    print(f"% of EngineMaxRpm    : {max_cur/max_em*100:.1f}%")
print()
print("samples (cur RPM / max RPM / throttle / kph):")
for s in samples[-10:]:
    print(f"  {s[0]:6.0f}  /  {s[1]:6.0f}  /  {s[2]:3d}  /  {s[3]:6.1f}")
