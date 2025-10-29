import socket, struct, asyncio, time, contextlib, copy
from typing import Any
from uart_cp import UCP_KEEP_ALIVE, UCP_MOTOR_CTL, UCP_IMU_CORRECTION_START, UCP_IMU_CORRECTION_END, UCP_RPM_REPORT, UCP_IMU_WRITE, UCP_MAG_WRITE, UCP_IMUMAG_READ, UCP_OTA, UCP_STATE
from uart_cp import UcpErr, UcpImuCorrectionType, UcpHd, UcpAlivePing, UcpAlivePong, UcpCtlCmd, UcpImuCorrect, UcpImuCorrectAck, UcpRep, UcpMagW, UcpMagWAck, UcpImuW, UcpImuWAck, UcpImuR, UcpImuRAck, UcpOta, UcpOtaAck, UcpState



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


# class api_structure:
#     def __init__(self, ip, port=5500):
#         self.__socket = self.connect_to_rover(ip, port)
#         # print("CREATED SOCKET")

#     def connect_to_rover(self, ip, port):
#         # socket structure:
#         sock = socket.create_connection((ip, port))  # make sure Rover IP and port aligns with tcp_bridge
#         sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
#         return sock

#     def make_header(self, packet, id):
#         # Header General Function
#         # header size: 4 bytes total
#         packet.hd.len   = len(bytes(packet))
#         packet.hd.id    = id
#         packet.hd.index = 0
#         # return packet

#     def read(self, frame):
#         # Read Header Function
#         pkt_id = frame[4] # why tf?
#         if pkt_id == UCP_KEEP_ALIVE:
#             self.pong()
#         if pkt_id == UCP_MOTOR_CTL:
#             # won't happen, motor ctrl has no ack
#             pass
#         if pkt_id == UCP_IMU_CORRECTION_START:
#             # not sure
#             pass
#         if pkt_id == UCP_IMU_CORRECTION_END:
#             self.IMU_calibrate_ACK()
#             pass
#         if pkt_id == UCP_RPM_REPORT:
#             self.get_report(frame)
#             pass
#         if pkt_id == UCP_IMU_WRITE:
#             # shouldn't recv this as host
#             pass
#         if pkt_id == UCP_MAG_WRITE:
#             # shouldn't recv this as host
#             pass
#         if pkt_id == UCP_IMUMAG_READ:
#             self.get_IMU()
#             pass
#         if pkt_id == UCP_OTA:
#             self.general_ACK()
#             pass
#         if pkt_id == UCP_STATE:
#             pass
    
#     def ping():
#         # pings rover
#         my_ping = uart_cp.UcpAlivePing()
#         self.make_header(my_ping, UCP_KEEP_ALIVE)
#         self.send_packet(my_ping)

#     def pong():
#         # receives pong
#         pass

#     def crc16(self, buf):
#         crc_hi = 0xFF
#         crc_lo = 0xFF
#         crc_hi_table = [0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
#             0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
#             0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
#             0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
#             0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81,
#             0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0,
#             0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
#             0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
#             0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
#             0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
#             0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01,
#             0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
#             0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
#             0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0,
#             0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01,
#             0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
#             0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81,
#             0x40]
#         crc_lo_table = [0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7, 0x05, 0xC5, 0xC4,
#             0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E, 0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09,
#             0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9, 0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD,
#             0x1D, 0x1C, 0xDC, 0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
#             0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32, 0x36, 0xF6, 0xF7,
#             0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D, 0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A,
#             0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38, 0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE,
#             0x2E, 0x2F, 0xEF, 0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
#             0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1, 0x63, 0xA3, 0xA2,
#             0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4, 0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F,
#             0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB, 0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB,
#             0x7B, 0x7A, 0xBA, 0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
#             0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0, 0x50, 0x90, 0x91,
#             0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97, 0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C,
#             0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E, 0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88,
#             0x48, 0x49, 0x89, 0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
#             0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83, 0x41, 0x81, 0x80,
#             0x40]
#         for b in buf:
#             index = crc_lo ^ b
#             crc_lo = crc_hi ^ crc_hi_table[index]
#             crc_hi = crc_lo_table[index]
#         return (crc_hi << 8) | crc_lo

#     def send_packet(self, packet):
#         head = 0xfffd
#         payload = bytes(packet)
#         print("PAYLOAD:", payload)
#         buf = struct.pack("<H", head) + payload
#         crc = self.crc16(buf)
#         buf += struct.pack("<H", crc)
#         print("Buf:", buf)
#         self.__socket.sendall(buf)
#         print("SENT DATA\n")
        
#     #buffer: b'\xfd\xff\x14\x00\x02\x00<\x00h\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00KN'
#     def ctrl_packet(self, speed, angular, front_led=0, back_led=0, version=0):
#         my_ctrl_packet = uart_cp.UcpCtlCmd()
#         self.make_header(my_ctrl_packet, UCP_MOTOR_CTL)
#         print("Header:", UCP_MOTOR_CTL)
#         print("Packet so far:", my_ctrl_packet)
#         my_ctrl_packet.speed     = speed
#         my_ctrl_packet.angular   = angular
#         # my_ctrl_packet.front_led = front_led
#         # my_ctrl_packet.back_led  = back_led
#         # my_ctrl_packet.version   = version

#         self.send_packet(my_ctrl_packet)

#     def IMU_calibrate(self, type):
#         # sends request to calibrate either:
#         # UICT_MAG (1) or UICT_IMU (2)
#         pass

#     def IMU_calibrate_ACK(self):
#         # used by imu_calbirate to see if request was successful
#         pass

#     def general_ACK(self, packet):
#         pass

#     def get_report(self, frame):
#         pass
    
#     def MAG_write(self, mag_bias_x, mag_bias_y, mag_bias_z):
#         pass

#     def IMU_write(self, acc_bias_x, acc_bias_y, acc_bias_z, mag_bias_x, mag_bias_y, mag_bias_z):
#         pass

#     def get_IMU(self):
#         pass

#     def OverTheAirUpdate(self, version):
#         pass

#     def disconnect():
#         self.__socket.close()

# ===========================================================
# ---- Async API Structure Class ----------------------------
# ===========================================================
class API:
    HEADER = b"\xFD\xFF"
    # HEADER = b"\xFF\xFD"

    def __init__(self, ip: str, port: int = 5500):
        self.ip = ip
        self.port = port
        self.reader = None
        self.writer = None
        self.running = False
        self.ack_event = asyncio.Event()
        self.last_ack = None
        self.last_telemetry = None
        self.telemetry_event = asyncio.Event()
        self.DECODE_MAP = {
            0x01: self.decode_pong,
            0x04: self.decode_imu_correct_ack,
            0x05: self.decode_rpm_report,
            0x08: self.decode_imu_read_ack,
            0x09: self.decode_ota_ack,
            0x0A: self.decode_state,
        }
        self.last_rpm_log_time = 0.0

    # Connection Handling
    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.ip, self.port)
        print(f"[API] Connected to rover at {self.ip}:{self.port}")
        self.running = True
        self.reader_task = asyncio.create_task(self.reader_loop())  # background read loop

    async def disconnect(self):
        if self.writer:
            self.running = False
            self.writer.close()
            await self.writer.wait_closed()
            print("[API] Disconnected from rover")
        if hasattr(self, "reader_task"):
            self.reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.reader_task
        self.running = False

    # Frame & Header Helpers
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

    # Async Sender
    async def send_packet(self, packet):
        if not self.writer:
            raise ConnectionError("Rover not connected")

        buf = self.build_frame(packet)
        self.writer.write(buf)
        await self.writer.drain()
        # print(f"[SEND] ID={packet.hd.id:02X}, Len={len(buf)}, CRC=0x{self.crc16(buf[:-2]):04X}")

    # Async Reader
    async def reader_loop(self):
        buf = b""
        print("[READER] Started async read loop")

        # Always run; exit when self.running becomes False or connection closes
        while True:
            if not self.running:
                break
            try:
                data = await self.reader.read(512)
                if not data:
                    print("[READER] Rover closed connection")
                    break

                buf += data
                frames, buf = self.extract_frames(buf)

                if frames:
                    print(f"[DEBUG] Got {len(frames)} frame(s), buf_remain={len(buf)} bytes")

                for frame in frames:
                    await self.read(frame)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[READER] Error: {e}")
                continue

        print("[READER] Exiting...")


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
                print(f"[FRAME] Bad CRC @ {sync_index}: expected={expected_crc:04X}, got={computed_crc:04X}")
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
        print(f"[WARN] Unknown packet ID 0x{pkt_id:02X}, payload={payload.hex()}")
        return {"raw_payload": payload.hex()}

    


    # Incoming Packet Parser
    async def read(self, frame):
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


    # API Commands

    #need function to read telemetry data:rpm report 0x5
    # async def get_telemetry(self) -> dict[str, Any]:
        
    #     self.telemetry_event.clear()
    #     try:
    #         await asyncio.wait_for(self.telemetry_event.wait(), timeout=2)
    #         if self.last_telemetry is None:
    #             return None
            
    #         data = self.last_telemetry
            
    #         # Motor RPMs: [Fl, Fr, Bl, Br] -> [Fl, Fr, Br, Bl]
    #         motor_rpms = {
    #             "motor_Fl": data["rpm"][0],
    #             "motor_Fr": data["rpm"][1],
    #             "motor_Br": data["rpm"][3],
    #             "motor_Bl": data["rpm"][2],
    #         }
            
    #         # Speed and heading (speed is average RPM converted to speed)
    #         avg_rpm = sum(data["rpm"]) / 4.0
    #         speed_and_heading = {
    #             "speed": avg_rpm,  
    #             "heading": data["heading_deg"],
    #         }
            
    #         # IMU data
    #         imu = {
    #             "accel_x": data["acc_ms2"][0],
    #             "accel_y": data["acc_ms2"][1],
    #             "accel_z": data["acc_ms2"][2],
    #             "gyro_x": data["gyro_dps"][0],
    #             "gyro_y": data["gyro_dps"][1],
    #             "gyro_z": data["gyro_dps"][2],
    #             "mag_x": data["mag_uT"][0],
    #             "mag_y": data["mag_uT"][1],
    #             "mag_z": data["mag_uT"][2],
    #         }
            
    #         # Merge all observations
    #         return {**motor_rpms, **speed_and_heading, **imu}
            
    #     except asyncio.TimeoutError:
    #         print("[TELEMETRY] Timeout waiting for telemetry data")
    #         return None

    async def get_telemetry(self) -> dict[str, Any]:
        """
        Non-blocking snapshot of the most recent telemetry data.
        Returns a shallow copy of the latest parsed 0x05 frame,
        or waits briefly if none is available yet.
        """
        # If no telemetry yet, wait briefly (but don't interfere with move())
        if self.last_telemetry is None:
            try:
                await asyncio.wait_for(self.telemetry_event.wait(), timeout=2)
            except asyncio.TimeoutError:
                print("[TELEMETRY] Timeout waiting for first telemetry data")
                return None

        # Shallow copy to avoid shared-state mutation
        data = copy.deepcopy(self.last_telemetry)

        if not data:
            return None

        motor_rpms = {
            "motor_Fl": data["rpm"][0],
            "motor_Fr": data["rpm"][1],
            "motor_Br": data["rpm"][3],
            "motor_Bl": data["rpm"][2],
        }

        avg_rpm = sum(data["rpm"]) / 4.0
        speed_and_heading = {
            "speed": avg_rpm,
            "heading": data["heading_deg"],
        }

        imu = {
            "accel_x": data["acc_ms2"][0],
            "accel_y": data["acc_ms2"][1],
            "accel_z": data["acc_ms2"][2],
            "gyro_x": data["gyro_dps"][0],
            "gyro_y": data["gyro_dps"][1],
            "gyro_z": data["gyro_dps"][2],
            "mag_x": data["mag_uT"][0],
            "mag_y": data["mag_uT"][1],
            "mag_z": data["mag_uT"][2],
        }

        return {**motor_rpms, **speed_and_heading, **imu}

    async def ping(self):
        ping_pkt = UcpAlivePing()
        self.make_header(ping_pkt, UCP_KEEP_ALIVE)
        self.ack_event.clear()
        print(f"[DEBUG] hdr.len={ping_pkt.hd.len}, sizeof(packet)={len(bytes(ping_pkt))}")

        await self.send_packet(ping_pkt)
        try:
            await asyncio.wait_for(self.ack_event.wait(), timeout=1.0)
            print(f"[PING] ACK received: {self.last_ack}")
        except asyncio.TimeoutError:
            print("[PING] Timeout waiting for ACK")
    
    async def safe_ping(self, retries=3):
        for attempt in range(1, retries + 1):
            await self.ping()
            if self.last_ack and self.last_ack.get("ack") == 0:
                return True
            print(f"[PING] Retry {attempt}/{retries} failed")
            await asyncio.sleep(0.5)
        print("[PING] Failed after retries")
        return False

    async def ctrl_packet(self, speed, angular):
        ctrl_pkt = UcpCtlCmd()
        self.make_header(ctrl_pkt, UCP_MOTOR_CTL)
        ctrl_pkt.speed = speed
        ctrl_pkt.angular = angular
        print(f"[DEBUG] hdr.len={ctrl_pkt.hd.len}, sizeof(packet)={len(bytes(ctrl_pkt))}")
        await self.send_packet(ctrl_pkt)
        print(f"[CTRL] speed={speed}, angular={angular}")
    
    async def move(self, duration, speed, angular):
        print(f"[MOVE] speed={speed}, angular={angular}")
        start = time.time()
        while time.time() - start < duration:
            await self.ctrl_packet(speed, angular)
            await asyncio.sleep(0.1)

            try:
                await asyncio.wait_for(self.telemetry_event.wait(), timeout=0.5)
                data = self.last_telemetry
                print(f"[MOVE] Telemetry update: RPM={data['rpm']}")
                self.telemetry_event.clear()
            except asyncio.TimeoutError:
                print("[MOVE] No telemetry update")
            
        await self.ctrl_packet(0, 0)
        print("[MOVE] stop")

    async def imu_calibrate(self, mode=1):
        imu_pkt = UcpImuCorrect()
        self.make_header(imu_pkt, UCP_IMU_CORRECTION_START)
        imu_pkt.mode = mode
        self.ack_event.clear()
        await self.send_packet(imu_pkt)
        print(f"[IMU] Calibration start (mode={mode})")
        try:
            await asyncio.wait_for(self.ack_event.wait(), timeout=3)
            print(f"[IMU] ACK: {self.last_ack}")
        except asyncio.TimeoutError:
            print("[IMU] Timeout waiting for ACK")

    async def over_the_air_update(self, version):
        ota_pkt = UcpOta()
        self.make_header(ota_pkt, UCP_OTA)
        ota_pkt.version = version
        await self.send_packet(ota_pkt)
        print(f"[OTA] Requested update to version {version}")

    async def imu_write(self, acc_bias, gyro_bias, mag_bias):
        pkt = UcpImuW()
        self.make_header(pkt, UCP_IMU_WRITE)
        pkt.acc_bias_x, pkt.acc_bias_y, pkt.acc_bias_z = acc_bias
        pkt.gyro_bias_x, pkt.gyro_bias_y, pkt.gyro_bias_z = gyro_bias
        pkt.mag_bias_x, pkt.mag_bias_y, pkt.mag_bias_z = mag_bias
        await self.send_packet(pkt)
        print(f"[IMU_WRITE] Sent IMU bias values")
    
    async def mag_write(self, mag_bias):
        pkt = UcpMagW()
        self.make_header(pkt, UCP_MAG_WRITE)
        pkt.mag_bias_x, pkt.mag_bias_y, pkt.mag_bias_z = mag_bias
        await self.send_packet(pkt)
        print(f"[MAG_WRITE] Sent MAG bias values")

    async def imu_mag_read(self):
        pkt = UcpImuR()
        self.make_header(pkt, UCP_IMUMAG_READ)
        self.ack_event.clear()

        await self.send_packet(pkt)
        print("[IMU_READ] Requested IMU/MAG data")

        try:
            await asyncio.wait_for(self.ack_event.wait(), timeout=2)
            print(f"[IMU_READ] Data: {self.last_ack}")
            return self.last_ack
        except asyncio.TimeoutError:
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
#     await rover.move(3, 60, 360)
#     await asyncio.sleep(1)
#     await rover.imu_mag_read()

#     await rover.disconnect()

async def main():
    rover = API("192.168.11.1", 8888)
    await rover.connect()

    # --- 1️⃣ Connection + Ping Test ---
    print("\n[TEST] Pinging rover...")
    await rover.safe_ping()
    await asyncio.sleep(1)

    # --- 2️⃣ Move / Control Packet Test ---
    print("\n[TEST] Moving rover (speed=60, angular=360) for 3s...")

    # Start the movement task (async)
    move_task = asyncio.create_task(rover.move(3, 60, 360))

    # Take 5 telemetry samples spaced evenly across the movement duration
    x = 5
    vals = {}
    for i in range(x):
        telemetry = await rover.get_telemetry()  # snapshot (non-blocking)
        vals[time.time()] = telemetry

        if telemetry:
            print(f"[TELEMETRY {i+1}/5] RPM={telemetry.get('speed'):.1f}, Heading={telemetry.get('heading'):.1f}")
        else:
            print(f"[TELEMETRY {i+1}/5] No data received")

        await asyncio.sleep(3 / x)  # space samples across ~3 seconds

    # Wait for the move() to finish cleanly
    await move_task

    await asyncio.sleep(1)

    print(vals)

    # --- 3️⃣ IMU Calibration ---
    print("\n[TEST] Starting IMU calibration...")
    await rover.imu_calibrate(mode=1)
    await asyncio.sleep(2)

    # --- 4️⃣ IMU / MAG Read ---
    print("\n[TEST] Requesting IMU/MAG read...")
    imu_data = await rover.imu_mag_read()
    print(f"[RESULT] IMU/MAG Data: {imu_data}")
    await asyncio.sleep(1)

    # --- 5️⃣ IMU Write (Test Bias Values) ---
    print("\n[TEST] Writing IMU bias values...")
    acc_bias  = (100, 200, 300)
    gyro_bias = (10, 20, 30)
    mag_bias  = (1, 2, 3)
    await rover.imu_write(acc_bias, gyro_bias, mag_bias)
    await asyncio.sleep(1)

    # --- 6️⃣ MAG Write (Test Bias Values) ---
    print("\n[TEST] Writing MAG bias values...")
    await rover.mag_write((5, 6, 7))
    await asyncio.sleep(1)

    # --- 7️⃣ OTA Update Simulation ---
    print("\n[TEST] Requesting OTA update to version 42...")
    await rover.over_the_air_update(42)
    await asyncio.sleep(2)

    # --- ✅ Done ---
    print("\n[TEST] All commands sent. Disconnecting...")
    await rover.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
