#!/usr/bin/env python3
import time
import threading
import sys
import termios
import tty

from api import EarthRoverMiniBlocking

UPDATE_RATE = 0.05  # 50ms = 20Hz

class KeyboardTeleop:
    def __init__(self, rover_ip="192.168.11.1", port=8888):
        self.rover = EarthRoverMiniBlocking(rover_ip    , port)
        self.speed = 0      # integer for speed
        self.turn = 0       # integer for turning
        self.running = True

    # ---------- Terminal Key Helpers ----------
    def getch(self):
        fd = sys.stdin.fileno()
        old_attr = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attr)
        return ch

    def input_loop(self):
        print("\nKeyboard Teleop Controls:")
        print("    W: forward   S: backward")
        print("    A: turn left D: turn right")
        print("    SPACE: stop  Q: quit\n")

        while self.running:
            key = self.getch().lower()

            if key == "q":
                self.running = False
                break

            if key == "w":
                self.speed = 60
            elif key == "s":
                self.speed = -60
            elif key == "a":
                self.turn = 40
            elif key == "d":
                self.turn = -40
            elif key == " ":
                self.speed = 0
                self.turn = 0

            print(f"[KEY] speed={self.speed}, turn={self.turn}")

    def command_loop(self):
        while self.running:
            self.rover.move(self.speed, self.turn)
            time.sleep(UPDATE_RATE)

    def start(self):
        self.rover.connect()

        # Start input thread
        threading.Thread(target=self.input_loop, daemon=True).start()

        # Start sending commands
        self.command_loop()

        # Cleanup once user quits
        self.rover.ctrl_packet(0, 0)
        self.rover.disconnect()
        print("Teleop stopped")


if __name__ == "__main__":
    teleop = KeyboardTeleop()  # change IP if needed
    teleop.start()
