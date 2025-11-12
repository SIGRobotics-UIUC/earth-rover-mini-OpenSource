import socket, struct, asyncio, time, contextlib, copy, threading
from typing import Any
from uart_cp import (
    UCP_KEEP_ALIVE,
    UCP_MOTOR_CTL,
    UCP_IMU_CORRECTION_START,
    UCP_IMU_CORRECTION_END,
    UCP_RPM_REPORT,
    UCP_IMU_WRITE,
    UCP_MAG_WRITE,
    UCP_IMUMAG_READ,
    UCP_OTA,
    UCP_STATE,
)
from uart_cp import (
    UcpErr,
    UcpImuCorrectionType,
    UcpHd,
    UcpAlivePing,
    UcpAlivePong,
    UcpCtlCmd,
    UcpImuCorrect,
    UcpImuCorrectAck,
    UcpRep,
    UcpMagW,
    UcpMagWAck,
    UcpImuW,
    UcpImuWAck,
    UcpImuR,
    UcpImuRAck,
    UcpOta,
    UcpOtaAck,
    UcpState,
)



UCP_KEEP_ALIVE           = 0x1
UCP_MOTOR_CTL            = 0x2
UCP_IMU_CORRECTION_START = 0x3
UCP_IMU_CORRECTION_END   = 0x4
UCP_RPM_REPORT           = 0x5
UCP_IMU_WRITE            = 0x6
UCP_MAG_WRITE            = 0x7
UCP_IMUMAG_READ          = 0x8
UCP_OTA                  = 0x9
UCP_STATE                = 0xA

PRINT_DEBUG = False
def debug_print(*args, **kwargs):
    if PRINT_DEBUG:
        print(*args, **kwargs)


class EarthRoverMiniBlocking:
    HEADER = b"\xFD\xFF"

    def __init__(self, ip: str, port: int = 5500):
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = False
        self.last_ack = None
        self.last_telemetry = None
        self.ack_event = threading.Event()
        self.telemetry_event = threading.Event()
        self.reader_thread = None
        self.last_rpm_log_time = 0.0
        self.moving = False
        self.move_thread = None

        self.DECODE_MAP = {
            0x01: self.decode_pong,
            0x04: self.decode_imu_correct_ack,
            0x05: self.decode_rpm_report,
            0x08: self.decode_imu_read_ack,
            0x09: self.decode_ota_ack,
            0x0A: self.decode_state
        }
    
    # --- Connection ---
    def connect(self):
        self.sock = socket.create_connection((self.ip, self.port))
        self.sock.settimeout(1.0)
        debug_print(f"[API] Connected to rover at {self.ip}:{self.port}")
        self.running = True
        self.reader_thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.reader_thread.start()

    def disconnect(self):
        self.running = False
        if self.sock:
            with contextlib.suppress(Exception):
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1)
        debug_print("[API] Disconnected from rover")

    # --- Send / Receive ---
    def send_packet(self, packet):
        if not self.sock:
            raise ConnectionError("Rover not connected")
        buf = self.build_frame(packet)
        self.sock.sendall(buf)

    def reader_loop(self):
        buf = b""
        debug_print("[READER] Started blocking read loop")
        while self.running:
            try:
                data = self.sock.recv(512)
                if not data:
                    debug_print("[READER] Connection closed by rover")
                    break
                buf += data
                frames, buf = self.extract_frames(buf)
                for frame in frames:
                    self.read(frame)
            except socket.timeout:
                continue
            except Exception as e:
                debug_print(f"[READER] Error: {e}")
                break
        debug_print("[READER] Exiting...")

    # --- Helper Methods ---
    def make_header(self, packet, pkt_id):
        packet.hd.len = len(bytes(packet))
        packet.hd.id = pkt_id
        packet.hd.index = 0

    def crc16(self, buf: bytes) -> int:
        crc_hi = 0xFF
        crc_lo = 0xFF
        crc_hi_table = [0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
        0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
        0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
        0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
        0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
        0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
        0x40]
        crc_lo_table = [0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4,
        0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09,
        0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD,
        0x1D, 0x1C, 0xDC, 0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
        0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7,
        0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A,
        0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38, 0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE,
        0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
        0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2,
        0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4, 0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F,
        0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB,
        0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
        0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0, 0x50, 0x90, 0x91,
        0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C,
        0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88,
        0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
        0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80,
        0x40]
        for b in buf:
            idx = crc_lo ^ b
            crc_lo = crc_hi ^ crc_hi_table[idx]
            crc_hi = crc_lo_table[idx]
        return (crc_hi << 8) | crc_lo

    def build_frame(self, packet):
        head = 0xFFFD
        payload = bytes(packet)
        buf = struct.pack("<H", head) + payload
        crc = self.crc16(buf)
        return buf + struct.pack("<H", crc)

    def extract_frames(self, buf: bytes):
        HEADER = self.HEADER  # b"\xFD\xFF"
        frames = []
        i = 0

        while i + 4 <= len(buf):
            sync_index = buf.find(HEADER, i)
            if sync_index == -1:
                # No header in the remaining buffer; drop what we’ve scanned
                return frames, buf[i:]

            # Need at least 4 bytes after sync to read the length field from payload
            if sync_index + 4 > len(buf):
                return frames, buf[sync_index:]

            # The 2-byte length we read here is *the payload size*, which already includes
            # the 2-byte len field itself (plus id/index/fields), but excludes the CRC.
            length = buf[sync_index + 2] | (buf[sync_index + 3] << 8)

            # Sanity checks: minimal payload is len(2) + id(1) + index(1) = 4
            if length < 4 or length > 1024:
                # Bad length → skip this byte and resync
                i = sync_index + 1
                continue

            total_len = 2 + length + 2  # SYNC(2) + PAYLOAD(length) + CRC(2)

            if sync_index + total_len > len(buf):
                # Incomplete frame; wait for more bytes
                return frames, buf[sync_index:]

            frame = buf[sync_index : sync_index + total_len]

            # CRC is over SYNC + PAYLOAD (i.e., the first 2 + length bytes)
            expected_crc = struct.unpack("<H", frame[-2:])[0]
            computed_crc = self.crc16(frame[: 2 + length])

            if expected_crc == computed_crc:
                frames.append(frame)
                i = sync_index + total_len
            else:
                debug_print(f"[FRAME] Bad CRC @ {sync_index}: expected={expected_crc:04X}, got={computed_crc:04X}")
                i = sync_index + 1  # resync one byte forward

        return frames, buf[i:]

    # Decoders
    def decode_pong(self, frame):
        pkt = UcpAlivePong.from_buffer_copy(frame[2:-2])
        decoded = {"ack": pkt.err}
        self.last_ack = decoded
        self.ack_event.set()
        return decoded
    
    def decode_imu_correct_ack(self, frame: bytes):
        pkt = UcpImuCorrectAck.from_buffer_copy(frame[2:-2])
        decoded = {"type": pkt.type, "err": pkt.err}
        self.last_ack = decoded
        self.ack_event.set()
        return decoded

    def decode_rpm_report(self, frame: bytes):
        pkt = UcpRep.from_buffer_copy(frame[2:-2])
        decoded = {
            "voltage": pkt.voltage / 100.0,
            "rpm": [pkt.rpm[i] for i in range(4)],
            "acc_g": [v / 16384.0 for v in pkt.acc],
            "acc_ms2": [v / 16384.0 * 9.80665 for v in pkt.acc],
            "gyro_dps": [v / 131.0 for v in pkt.gyros],
            "mag_uT": [v * 0.083 for v in pkt.mag],
            "heading_deg": pkt.heading / 100.0,
            "stop_switch": pkt.stop_switch,
            "error_code": pkt.error_code,
            "version": pkt.version,
        }
        self.last_telemetry = decoded
        self.telemetry_event.set()
        return decoded

    def decode_imu_read_ack(self, frame: bytes):
        pkt = UcpImuRAck.from_buffer_copy(frame[2:-2])
        decoded = {
            "err": pkt.err,
            "acc_bias": (pkt.acc_bias_x, pkt.acc_bias_y, pkt.acc_bias_z),
            "gyro_bias": (pkt.gyro_bias_x, pkt.gyro_bias_y, pkt.gyro_bias_z),
            "mag_bias": (pkt.mag_bias_x, pkt.mag_bias_y, pkt.mag_bias_z),
        }
        self.last_ack = decoded
        self.ack_event.set()
        return decoded

    def decode_ota_ack(self, frame: bytes):
        pkt = UcpOtaAck.from_buffer_copy(frame[2:-2])
        decoded = {"err": pkt.err}
        self.last_ack = decoded
        self.ack_event.set()
        return decoded

    def decode_state(self, frame: bytes):
        pkt = UcpState.from_buffer_copy(frame[2:-2])
        return {"state": pkt.state}

    def decode_unknown(self, frame: bytes):
        pkt_id = frame[4]
        payload = frame[6:-2]
        debug_print(f"[WARN] Unknown packet ID 0x{pkt_id:02X}, payload={payload.hex()}")
        return {"raw_payload": payload.hex()}

    # Incoming Packet Parser
    def read(self, frame):
        pkt_id = frame[4]
        decoder = self.DECODE_MAP.get(pkt_id)
        if decoder:
            decoded = decoder(frame)
            if pkt_id == 0x05:
                now = time.time()
                if now - self.last_rpm_log_time >= 1.0:
                    self.last_rpm_log_time = now
                    print(f"[PKT {pkt_id:02X}] {decoded}")
            else:
                print(f"[PKT {pkt_id:02X}] {decoded}")
        else:
            self.decode_unknown(frame)

    def get_telemetry(self, wait=True, timeout=1.0):
        """
        Blocking getter for telemetry.
        If wait=True, blocks up to `timeout` seconds for new telemetry.
        Returns the last known telemetry dict (or None if no update).
        """
        if wait:
            if not self.telemetry_event.wait(timeout=timeout):
                print("[GET_TELEMETRY] Timeout waiting for telemetry")
                return self.last_telemetry  # May be stale or None
            self.telemetry_event.clear()

        data = self.last_telemetry
        if data:
            print(f"[GET_TELEMETRY] Latest: RPM={data['rpm']}")
        else:
            print("[GET_TELEMETRY] No telemetry available")
        return data

    def ping(self):
        ping_pkt = UcpAlivePing()
        self.make_header(ping_pkt, UCP_KEEP_ALIVE)
        self.ack_event.clear()
        print(f"[DEBUG] hdr.len={ping_pkt.hd.len}, sizeof(packet)={len(bytes(ping_pkt))}")

        self.send_packet(ping_pkt)
        if self.ack_event.wait(timeout=1.0):
            print(f"[PING] ACK received: {self.last_ack}")
            return True
        else:
            print("[PING] Timeout waiting for ACK")
            return False

    def safe_ping(self, retries=3):
        for attempt in range(1, retries + 1):
            if self.ping():
                return True
            print(f"[PING] Retry {attempt}/{retries} failed")
            time.sleep(0.5)
        print("[PING] Failed after retries")
        return False

    def ctrl_packet(self, speed, angular): #sends the command packet to the rover
        ctrl_pkt = UcpCtlCmd()
        self.make_header(ctrl_pkt, UCP_MOTOR_CTL)
        ctrl_pkt.speed = speed
        ctrl_pkt.angular = angular
        print(f"[DEBUG] hdr.len={ctrl_pkt.hd.len}, sizeof(packet)={len(bytes(ctrl_pkt))}")
        self.send_packet(ctrl_pkt)
        print(f"[CTRL] speed={speed}, angular={angular}")

    def move(self, duration, speed, angular):
        """Blocking ‘timed’ move; keeps printing telemetry if it arrives."""
        print(f"[MOVE] speed={speed}, angular={angular}")
        start = time.time()
        while time.time() - start < duration:
            self.ctrl_packet(speed, angular)
            # give the rover some time; interleave with telemetry checks
            if self.telemetry_event.wait(timeout=0.5):
                data = self.last_telemetry
                print(f"[MOVE] Telemetry update: RPM={data['rpm']}")
                self.telemetry_event.clear()
            else:
                print("[MOVE] No telemetry update")
            time.sleep(0.1)

        self.ctrl_packet(0, 0)
        print("[MOVE] stop")

    # ---------- Continuous move in background thread ----------
    def move_continuous_loop(self, speed, angular):
        print(f"[MOVE_CONTINUOUS] speed={speed}, angular={angular}")
        self.moving = True
        try:
            while self.moving:
                self.ctrl_packet(speed, angular)
                # if self.telemetry_event.wait(timeout=0.5):
                #     data = self.last_telemetry
                #     print(f"[MOVE_CONTINUOUS] Telemetry update: RPM={data['rpm']}")
                #     self.telemetry_event.clear()
                # else:
                #     print("[MOVE_CONTINUOUS] No telemetry update")
                # time.sleep(0.1)
        finally:
            # Always send a stop at the end of the loop
            self.ctrl_packet(0, 0)
            print("[MOVE_CONTINUOUS] Exiting cleanly")
        
        self.ctrl_packet(speed, angular)

    def move_continuous(self, speed, angular): #debug look at how calling a second move_continuous is handled by the thread already running 
        """Non-blocking starter; returns immediately and keeps moving until stop()."""
        if getattr(self, "_move_thread", None) and self.move_thread.is_alive():
            print("[MOVE_CONTINUOUS] Already running")
            return
        self.moving = True
        self.move_thread = threading.Thread(
            target=self.move_continuous_loop, args=(speed, angular), daemon=True
        )
        self.move_thread.start()
        self.move_continuous_loop(speed, angular)

    def stop(self):
        """Stops continuous motion (if running) and sends a zero command."""
        if not getattr(self, "moving", False):
            print("[STOP] Rover already stopped")
            # still ensure a zero command hits the motors
            self.ctrl_packet(0, 0)
            return
        self.moving = False
        # Optionally join for a short time so the stop packet is sent
        if getattr(self, "_move_thread", None):
            self.move_thread.join(timeout=1.0)
        self.ctrl_packet(0, 0)
        print("[STOP] Rover stopped")

    def imu_calibrate(self, mode=1):
        imu_pkt = UcpImuCorrect()
        self.make_header(imu_pkt, UCP_IMU_CORRECTION_START)
        imu_pkt.mode = mode
        self.ack_event.clear()
        self.send_packet(imu_pkt)
        print(f"[IMU] Calibration start (mode={mode})")

        if self.ack_event.wait(timeout=3.0):
            print(f"[IMU] ACK: {self.last_ack}")
            return self.last_ack
        else:
            print("[IMU] Timeout waiting for ACK")
            return None

    def over_the_air_update(self, version, wait_for_ack=False, timeout=3.0):
        ota_pkt = UcpOta()
        self.make_header(ota_pkt, UCP_OTA)
        ota_pkt.version = version
        if wait_for_ack:
            self.ack_event.clear()
        self.send_packet(ota_pkt)
        print(f"[OTA] Requested update to version {version}")

        if wait_for_ack:
            if self.ack_event.wait(timeout=timeout):
                print(f"[OTA] ACK: {self.last_ack}")
                return self.last_ack
            else:
                print("[OTA] Timeout waiting for ACK")
                return None

    def imu_write(self, acc_bias, gyro_bias, mag_bias):
        pkt = UcpImuW()
        self.make_header(pkt, UCP_IMU_WRITE)
        pkt.acc_bias_x, pkt.acc_bias_y, pkt.acc_bias_z = acc_bias
        pkt.gyro_bias_x, pkt.gyro_bias_y, pkt.gyro_bias_z = gyro_bias
        pkt.mag_bias_x, pkt.mag_bias_y, pkt.mag_bias_z = mag_bias
        self.send_packet(pkt)
        print(f"[IMU_WRITE] Sent IMU bias values")
        # If your firmware sends UcpImuWAck, you can wait on self.ack_event here.

    def mag_write(self, mag_bias):
        pkt = UcpMagW()
        self.make_header(pkt, UCP_MAG_WRITE)
        pkt.mag_bias_x, pkt.mag_bias_y, pkt.mag_bias_z = mag_bias
        self.send_packet(pkt)
        print(f"[MAG_WRITE] Sent MAG bias values")
        # If your firmware sends UcpMagWAck, you can wait on self.ack_event here.

    def imu_mag_read(self):
        pkt = UcpImuR()
        self.make_header(pkt, UCP_IMUMAG_READ)
        self.ack_event.clear()

        self.send_packet(pkt)
        print("[IMU_READ] Requested IMU/MAG data")

        if self.ack_event.wait(timeout=2.0):
            print(f"[IMU_READ] Data: {self.last_ack}")
            return self.last_ack
        else:
            print("[IMU_READ] Timeout waiting for IMU/MAG data")
            return None

# ===========================================================
# ---- Example usage ----------------------------------------
# ===========================================================
# async def main():
#     rover = API("192.168.11.1", 8888)
#     await rover.connect()

#     await rover.safe_ping()
#     # await rover.ctrl_packet(60, 0)
#     await asyncio.sleep(2)
#     # await rover.ctrl_packet(0, 0)
#     await rover.move(3, -100, 0)
#     await asyncio.sleep(1)
#     await rover.imu_mag_read()

#     await rover.disconnect()

# async def main():
#     rover = EarthRoverMini("192.168.11.1", 8888)
#     await rover.connect()

#     # # --- 1️⃣ Connection + Ping Test ---
#     print("\n[TEST] Pinging rover...")
#     await rover.safe_ping()
#     await asyncio.sleep(1)

#    # --- 2️⃣ Continuous Move Test with Live Telemetry ---
#     print("\n[TEST] Starting continuous motion (speed=60, angular=360)...")

#     # Start motion in the background
#     move_task = asyncio.create_task(rover.move_continuous(60, 360))

#     # Collect telemetry while the rover is moving
#     try:
#         start_time = time.time()
#         duration = 5  # seconds
#         while time.time() - start_time < duration:
#             telemetry = await rover.get_telemetry()
#             if telemetry:
#                 print(
#                     f"[TELEMETRY] Speed={telemetry['speed']:.1f} RPM, "
#                     f"Heading={telemetry['heading']:.1f}°, "
#                     f"Accel=({telemetry['accel_x']:.2f}, {telemetry['accel_y']:.2f}, {telemetry['accel_z']:.2f})"
#                 )
#             else:
#                 print("[TELEMETRY] No data received")
#             await asyncio.sleep(0.5)

#     except KeyboardInterrupt:
#         print("\n[TEST] Interrupted by user — stopping rover safely...")

#     # Stop motion cleanly
#     await rover.stop()

#     # Wait for the continuous motion loop to end
#     await move_task

#     # # --- 3️⃣ IMU Calibration ---
#     print("\n[TEST] Starting IMU calibration...")
#     await rover.imu_calibrate(mode=1)
#     await asyncio.sleep(2)

#     # # --- 4️⃣ IMU / MAG Read ---
#     print("\n[TEST] Requesting IMU/MAG read...")
#     imu_data = await rover.imu_mag_read()
#     print(f"[RESULT] IMU/MAG Data: {imu_data}")
#     await asyncio.sleep(1)

#     # # --- 5️⃣ IMU Write (Test Bias Values) ---
#     print("\n[TEST] Writing IMU bias values...")
#     acc_bias  = (100, 200, 300)
#     gyro_bias = (10, 20, 30)
#     mag_bias  = (1, 2, 3)
#     await rover.imu_write(acc_bias, gyro_bias, mag_bias)
#     await asyncio.sleep(1)

#     # # --- 6️⃣ MAG Write (Test Bias Values) ---
#     print("\n[TEST] Writing MAG bias values...")
#     await rover.mag_write((5, 6, 7))
#     await asyncio.sleep(1)

#     # # --- 7️⃣ OTA Update Simulation ---
#     # print("\n[TEST] Requesting OTA update to version 42...")
#     # await rover.over_the_air_update(42)
#     # await asyncio.sleep(2)

#     # # --- ✅ Done ---
#     print("\n[TEST] All commands sent. Disconnecting...")
#     await rover.disconnect()


if __name__ == "__main__":
    rover = EarthRoverMiniBlocking("192.168.11.1", 8888)
    rover.connect()

    print("\n[TEST] Ping test:")
    rover.safe_ping()

    print("\n[TEST] Move test (3s at speed=60, angular=360):")
    rover.move(1, 60, 0)

    rover.disconnect()

