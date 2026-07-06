#!/usr/bin/env python3
"""Provision WiFi over the Improv Serial protocol.

Credentials are read from the IMPROV_SSID / IMPROV_PASSWORD environment
variables (so they never appear in the process list) and pushed to an ESPHome
device over USB serial. Driven by scripts/push.sh for bootstrap provisioning.

Protocol reference: https://www.improv-wifi.com/serial/
"""
import argparse
import os
import sys
import time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("error: pyserial not installed — run: pip install pyserial")

HEADER = b"IMPROV"
VERSION = 0x01

# Packet types
TYPE_CURRENT_STATE = 0x01
TYPE_ERROR_STATE = 0x02
TYPE_RPC = 0x03
TYPE_RPC_RESULT = 0x04

# Device states
STATE_PROVISIONING = 0x03
STATE_PROVISIONED = 0x04

# RPC commands
CMD_SEND_WIFI = 0x01

ERRORS = {
    0x00: "no error",
    0x01: "invalid RPC packet",
    0x02: "unknown RPC command",
    0x03: "unable to connect",
    0x05: "bad hostname",
    0xFF: "unknown error",
}


def _checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def build_packet(ptype: int, payload: bytes) -> bytes:
    packet = HEADER + bytes([VERSION, ptype, len(payload)]) + payload
    return packet + bytes([_checksum(packet)])


def build_set_wifi(ssid: str, password: str) -> bytes:
    ssid_b = ssid.encode()
    pwd_b = password.encode()
    inner = bytes([len(ssid_b)]) + ssid_b + bytes([len(pwd_b)]) + pwd_b
    payload = bytes([CMD_SEND_WIFI, len(inner)]) + inner
    return build_packet(TYPE_RPC, payload)


def parse_packets(buf: bytearray):
    """Pull complete Improv frames out of buf, returning (type, payload) pairs.

    Consumed bytes are removed from buf; a trailing partial frame is left in
    place for the next read.
    """
    out = []
    while True:
        idx = buf.find(HEADER)
        if idx < 0:
            # Drop everything except a possible partial header at the tail.
            del buf[: max(0, len(buf) - (len(HEADER) - 1))]
            break
        if idx > 0:
            del buf[:idx]
        if len(buf) < len(HEADER) + 3:
            break  # not enough for version+type+length yet
        length = buf[len(HEADER) + 2]
        total = len(HEADER) + 3 + length + 1  # trailing checksum byte
        if len(buf) < total:
            break
        frame = bytes(buf[:total])
        del buf[:total]
        if _checksum(frame[:-1]) != frame[-1]:
            continue  # coincidental "IMPROV" in log text, not a real frame
        ptype = frame[len(HEADER) + 1]
        payload = frame[len(HEADER) + 3 : len(HEADER) + 3 + length]
        out.append((ptype, payload))
    return out


def decode_result_strings(payload: bytes):
    """RPC result payload: [cmd][data_len][str_len][str]..."""
    if len(payload) < 2:
        return []
    data = payload[2 : 2 + payload[1]]
    strings, i = [], 0
    while i < len(data):
        n = data[i]
        i += 1
        strings.append(data[i : i + n].decode(errors="replace"))
        i += n
    return strings


def autodetect_port() -> str:
    candidates = [
        p.device
        for p in list_ports.comports()
        if any(k in p.device.lower() for k in ("usbserial", "usbmodem", "ttyusb", "ttyacm"))
    ]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        sys.exit("error: no USB serial device found — pass --port")
    sys.exit(f"error: multiple serial ports found, pass --port: {', '.join(candidates)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Provision WiFi over Improv Serial.")
    ap.add_argument("--port", help="serial port (autodetected if omitted)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--settle", type=float, default=2.0, help="boot settle delay after opening the port")
    args = ap.parse_args()

    ssid = os.environ.get("IMPROV_SSID")
    password = os.environ.get("IMPROV_PASSWORD", "")
    if not ssid:
        sys.exit("error: IMPROV_SSID not set")

    port = args.port or autodetect_port()
    print(f"Provisioning WiFi '{ssid}' via {port} ...")

    packet = build_set_wifi(ssid, password)
    with serial.Serial(port, args.baud, timeout=0.2) as ser:
        time.sleep(args.settle)  # opening the port resets the ESP; let it boot
        ser.reset_input_buffer()
        deadline = time.time() + args.timeout
        last_send = 0.0
        buf = bytearray()
        provisioning = False
        while time.time() < deadline:
            now = time.time()
            # Resend periodically until the device acknowledges (it may still
            # be booting when we first write).
            if not provisioning and now - last_send > 3.0:
                ser.write(packet)
                ser.flush()
                last_send = now
            chunk = ser.read(256)
            if not chunk:
                continue
            buf.extend(chunk)
            for ptype, payload in parse_packets(buf):
                if ptype == TYPE_ERROR_STATE and payload and payload[0] != 0x00:
                    sys.exit(f"error: device reported '{ERRORS.get(payload[0], payload[0])}'")
                elif ptype == TYPE_CURRENT_STATE and payload:
                    if payload[0] == STATE_PROVISIONING:
                        provisioning = True
                        print("device connecting to WiFi ...")
                    elif payload[0] == STATE_PROVISIONED:
                        print("✅ provisioned")
                        return
                elif ptype == TYPE_RPC_RESULT and payload and payload[0] == CMD_SEND_WIFI:
                    urls = decode_result_strings(payload)
                    if urls:
                        print("device URL(s):", ", ".join(urls))
                    print("✅ provisioned")
                    return
        sys.exit("error: timed out waiting for the device to connect")


if __name__ == "__main__":
    main()
