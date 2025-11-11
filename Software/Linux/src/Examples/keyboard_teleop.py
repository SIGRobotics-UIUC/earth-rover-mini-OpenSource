#!/usr/bin/env python3
import time
import threading
import sys
import termios
import tty

from api import EarthRoverMiniBlocking

UPDATE_RATE = 0.03 #every num of seconds send command  

class KeyboardTeleop:
    def __init__(self, rover_ip="192.168.11.1", rover_port=8888):
        self.rover_ip = rover_ip
        self.rover_port = rover_port
     
        self.rover = EarthRoverMiniBlocking(self.rover_ip, self.rover_port)

        self.speed = 0
        self.turn = 0
        self.running = True

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
        print(f"Connected to Rover at {self.rover_ip}:{self.rover_port}")

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
                self.turn = -40
            elif key == "d":
                self.turn = 40
            elif key == " ":
                self.speed = 0
                self.turn = 0

            print(f"[KEY] speed={self.speed}, turn={self.turn}")

    def command_loop(self):
        while self.running:
            self.rover.move(1, self.speed, self.turn) #change with ctl_packet, move_continously
            time.sleep(UPDATE_RATE)

    def start(self):
        self.rover.connect()

        threading.Thread(target=self.input_loop, daemon=True).start()
        self.command_loop()

        # Stop rover on exit
        self.rover.move(0, 0, 1) #change with ctl_packet, move_continously
        self.rover.disconnect()
        print("Teleop stopped")


if __name__ == "__main__":
    teleop = KeyboardTeleop("192.168.11.1", 8888)  
    teleop.start()
