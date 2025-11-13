#!/usr/bin/env python3
import time
import threading
import sys
import pynput
import logging

from api import EarthRoverMiniBlocking

UPDATE_RATE = 0.03 #every num of seconds send command

class KeyboardTeleop:
    def __init__(self, rover_ip="192.168.11.1", rover_port=8888):
        self.rover_ip = rover_ip
        self.rover_port = rover_port
        self.rover = EarthRoverMiniBlocking(self.rover_ip, self.rover_port)

        self.running = True
        self.key_pressed = {}
        self.listener = pynput.keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def on_press(self, key):
        try:
            self.key_pressed[key.char] = True
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key.char in self.key_pressed:
                del self.key_pressed[key.char]
        except AttributeError:
            pass

    def command_loop(self):
        print("Keyboard Teleop Controls:")
        print("    W: forward   S: backward")
        print("    A: turn left D: turn right")
        print("    SPACE: stop  Q: quit\n")
        print(f"Connected to Rover at {self.rover_ip}:{self.rover_port}")

        last_show_rpm_time = time.time()

        while self.running:
            actions = self.key_pressed
            turn = 0
            speed = 0
            for key in actions:
                if key == 'w':
                    speed = 40
                elif key == 's':
                    speed = -40
                elif key == 'a':
                    turn = -40
                elif key == 'd':
                    turn = 40
            self.rover.move(speed, turn)
            # show rpm every second
            if time.time() - last_show_rpm_time > 1.0:
                print(f"\nRPM: {self.rover.get_telemetry(wait=0.01)['rpm']}")
                last_show_rpm_time = time.time()

            time.sleep(UPDATE_RATE)

    def start(self):
        # Connect to rover
        self.rover.connect()
        # Start keyboard listener
        self.listener.start()

        self.command_loop()

        # Stop keyboard listener
        self.listener.stop()
        # Stop rover and disconnect
        self.rover.move(0, 0)
        self.rover.disconnect()


if __name__ == "__main__":
    teleop = KeyboardTeleop("192.168.11.1", 8888)
    teleop.start()
