"""Self-test: send synthetic Forza Data Out packets at the bridge and
listen on the Pit House port to confirm forwarding works."""
import socket
import struct
import threading
import time

BRIDGE_PORT = 4009
PIT_HOUSE_PORT = 30055

received = []
done = threading.Event()


def listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2.0)
    try:
        s.bind(("127.0.0.1", PIT_HOUSE_PORT))
    except OSError as e:
        print(f"  could not bind {PIT_HOUSE_PORT} for test: {e}")
        done.set()
        return
    print(f"  listener bound to :{PIT_HOUSE_PORT}")
    start = time.time()
    while time.time() - start < 3.0:
        try:
            data, src = s.recvfrom(4096)
            received.append((len(data), src))
        except socket.timeout:
            break
    done.set()


def make_fh5_packet(size: int = 324) -> bytes:
    """Build a Forza Data Out 'Car Dash' packet with believable values."""
    buf = bytearray(size)
    struct.pack_into("<iI", buf, 0, 1, 12345)        # IsRaceOn=1, ts=12345ms
    struct.pack_into("<fff", buf, 8, 8000.0, 1000.0, 4500.0)  # max/idle/cur RPM
    if size >= 324:
        struct.pack_into("<f", buf, 256, 60.0)       # speed m/s -> 216 kph
        buf[311] = 200                                # throttle
        buf[312] = 0                                  # brake
        buf[315] = 4                                  # gear
    return bytes(buf)


def main() -> int:
    t = threading.Thread(target=listener, daemon=True)
    t.start()
    time.sleep(0.2)

    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("  sending 5 x 324B (FH5-shape)")
    for _ in range(5):
        tx.sendto(make_fh5_packet(324), ("127.0.0.1", BRIDGE_PORT))
        time.sleep(0.05)

    print("  sending 3 x 400B (simulated FH6-extended)")
    for _ in range(3):
        tx.sendto(make_fh5_packet(324) + b"\xaa" * 76, ("127.0.0.1", BRIDGE_PORT))
        time.sleep(0.05)

    print("  sending 2 x 100B (garbage, should be dropped)")
    for _ in range(2):
        tx.sendto(b"\x00" * 100, ("127.0.0.1", BRIDGE_PORT))
        time.sleep(0.05)

    done.wait(timeout=3.5)

    print(f"\n  packets received on :{PIT_HOUSE_PORT} = {len(received)}")
    for i, (n, src) in enumerate(received[:10]):
        print(f"    [{i}] {n}B from {src}")
    expected = 8  # 5 passthrough + 3 truncated, 2 dropped
    ok = len(received) == expected and all(n == 324 for n, _ in received)
    print(f"  PASS" if ok else f"  FAIL  (expected {expected} forwarded, all 324B)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
