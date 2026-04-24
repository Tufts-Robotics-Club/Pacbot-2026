# This file contains the MotorModule class which handles motor operations.


import time
from collections import deque

import Motor

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3

# Timing-based tile movement — tune on hardware.
TILE_DURATION = 0.8  # seconds of driving per tile move

TILE_DIRECTIONS = {"north", "south", "east", "west"}


class MotorModule:
    def __init__(self, use_physical=False):
        # Initialize motor module
        self.north_motor = Motor.get_motor_class(NORTH_ID, use_physical=use_physical)
        self.south_motor = Motor.get_motor_class(SOUTH_ID, use_physical=use_physical)
        self.east_motor = Motor.get_motor_class(EAST_ID, use_physical=use_physical)
        self.west_motor = Motor.get_motor_class(WEST_ID, use_physical=use_physical)

        self._queue = deque()
        self._move_end_time = None

    def update(self, command):
        cmd = command.strip().lower()
        if cmd in TILE_DIRECTIONS:
            self._queue.append(cmd)
            return
        # Direct WASDQE drive — interrupts any tile move in progress.
        self._queue.clear()
        self._move_end_time = None
        self._direct_drive(command)

    def tick(self):
        now = time.monotonic()

        # Stop the current tile move when its duration has elapsed.
        if self._move_end_time is not None and now >= self._move_end_time:
            self._stop_motors()
            self._move_end_time = None

        # Start the next queued tile move if we're idle.
        if self._move_end_time is None and self._queue:
            direction = self._queue.popleft()
            self._start_tile_move(direction)
            self._move_end_time = now + TILE_DURATION

    def _start_tile_move(self, direction):
        print(f"[tile] driving {direction} for {TILE_DURATION}s")
        if direction == "north":
            self.west_motor.forward(1.0)
            self.east_motor.backward(1.0)
        elif direction == "south":
            self.west_motor.backward(1.0)
            self.east_motor.forward(1.0)
        elif direction == "east":
            self.north_motor.forward(1.0)
            self.south_motor.backward(1.0)
        elif direction == "west":
            self.north_motor.backward(1.0)
            self.south_motor.forward(1.0)

    def _stop_motors(self):
        self.north_motor.stop()
        self.south_motor.stop()
        self.east_motor.stop()
        self.west_motor.stop()

    def _direct_drive(self, command):
        if command.upper() == "W":
            self.west_motor.forward(1.0)
            self.east_motor.backward(1.0)
        elif command.upper() == "S":
            self.west_motor.backward(1.0)
            self.east_motor.forward(1.0)
        elif command.upper() == "A":
            self.north_motor.backward(1.0)
            self.south_motor.forward(1.0)
        elif command.upper() == "D":
            self.north_motor.forward(1.0)
            self.south_motor.backward(1.0)
        elif command.upper() == "Q":
            for m in (self.north_motor, self.east_motor, self.south_motor, self.west_motor):
                m.forward(0.5)
        elif command.upper() == "E":
            for m in (self.north_motor, self.east_motor, self.south_motor, self.west_motor):
                m.backward(0.5)
        else:
            self._stop_motors()

    def close(self):
        # Stop all motors first, then close (physical motors share serial state).
        motors = [self.north_motor, self.south_motor, self.east_motor, self.west_motor]
        for motor in motors:
            motor.stop()
        for motor in motors:
            motor.close()
