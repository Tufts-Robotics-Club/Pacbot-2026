# This file contains the MotorModule class which handles motor operations.


import time
from collections import deque

import Motor

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3

# Maze geometry — tune for the real maze.
TILE_SIZE = 0.16              # meters the bot must travel to cross one tile
WALL_SAFETY_DISTANCE = 0.04   # bail out of driving if front ToF drops below this
CENTER_TOLERANCE = 0.01       # side-distance imbalance (m) we consider "centered"
ANGLE_TOLERANCE = 0.05        # integrated heading error (rad) we consider "aligned"
SETTLING_TIMEOUT = 1.5        # seconds to spend trying to fine-tune before giving up

# Control gains — tune on hardware.
KP_LATERAL = 4.0
KP_HEADING = 2.0
DRIVE_SPEED = 0.5             # nominal forward speed (unitless motor command)
NOMINAL_SPEED_MPS = 0.25      # rough calibration: what DRIVE_SPEED maps to in m/s
BASELINE_WAIT = 0.5           # seconds to wait for front ToF before falling back to timed drive

TILE_DIRECTIONS = {"north", "south", "east", "west"}

# For each movement direction: (body_vx, body_vy, front_tof, pos_side, neg_side).
# Body frame: +x east, +y north, +omega CCW (matches IMU convention).
# pos_side / neg_side: when pos_side distance > neg_side distance we are too close
# to neg_side, so the lateral correction pushes toward pos_side (positive sign).
DIRECTION_INFO = {
    "north": (0,  1, "north", "east", "west"),
    "south": (0, -1, "south", "east", "west"),
    "east":  (1,  0, "east",  "north", "south"),
    "west":  (-1, 0, "west",  "north", "south"),
}


class MotorModule:
    def __init__(self, use_physical=False, sensor_module=None):
        self.sensor_module = sensor_module
        self.north_motor = Motor.get_motor_class(NORTH_ID, use_physical=use_physical)
        self.south_motor = Motor.get_motor_class(SOUTH_ID, use_physical=use_physical)
        self.east_motor = Motor.get_motor_class(EAST_ID, use_physical=use_physical)
        self.west_motor = Motor.get_motor_class(WEST_ID, use_physical=use_physical)

        self._queue = deque()
        self._state = "IDLE"
        self._move = None
        self._start_front = None
        self._move_start_time = None
        self._heading = 0.0
        self._last_tick_time = None
        self._settle_start = None

    def update(self, command):
        cmd = command.strip().lower()
        if cmd in TILE_DIRECTIONS:
            self._queue.append(cmd)
            return
        # Direct WASDQE drive — interrupts any tile move in progress.
        self._reset_tile_state()
        self._direct_drive(command)

    def tick(self):
        now = time.monotonic()
        dt = (now - self._last_tick_time) if self._last_tick_time else 0.0
        self._last_tick_time = now

        if self.sensor_module is None:
            return

        readings = self.sensor_module.read_all()
        imu = readings.get("imu") or {}
        tof = readings.get("tof") or {}

        omega = imu.get("omega") if imu else None
        if omega is not None and self._state != "IDLE":
            self._heading += omega * dt
        
        if self._state == "IDLE":
            if self._queue:
                self._enter_driving(self._queue.popleft(), tof, now)
            return

        if self._state == "DRIVING":
            self._tick_driving(tof, now)
        elif self._state == "SETTLING":
            self._tick_settling(tof, now)

    def _enter_driving(self, direction, tof, now):
        self._move = direction
        front_name = DIRECTION_INFO[direction][2]
        self._start_front = tof.get(front_name)
        self._move_start_time = now
        self._heading = 0.0
        self._state = "DRIVING"
        print(f"[tile] start {direction}, baseline front={self._start_front}")

    def _tick_driving(self, tof, now):
        direction = self._move
        if direction is None:
            return
        vx_dir, vy_dir, front_name, pos_side, neg_side = DIRECTION_INFO[direction]
        front = tof.get(front_name)

        # If we never captured a baseline, keep trying briefly before committing to timed fallback.
        if self._start_front is None:
            if front is not None:
                self._start_front = front
                self._move_start_time = now
            elif now - self._move_start_time < BASELINE_WAIT:
                self._stop_motors()
                return

        # Termination: traveled one tile, hit a wall, or timed fallback expired.
        done = False
        if self._start_front is not None and front is not None:
            if self._start_front - front >= TILE_SIZE:
                done = True
            elif front < WALL_SAFETY_DISTANCE:
                done = True
        elif (now - self._move_start_time) * NOMINAL_SPEED_MPS >= TILE_SIZE:
            done = True

        if done:
            self._stop_motors()
            self._settle_start = now
            self._state = "SETTLING"
            print(f"[tile] reached target, settling (heading_err={self._heading:.3f})")
            return

        lateral = self._lateral_correction(tof, pos_side, neg_side, clamp=0.3)
        omega_cmd = max(-0.3, min(0.3, -KP_HEADING * self._heading))

        if direction in ("north", "south"):
            vy = vy_dir * DRIVE_SPEED
            vx = lateral
        else:
            vx = vx_dir * DRIVE_SPEED
            vy = lateral

        self._drive(vx, vy, omega_cmd)

    def _tick_settling(self, tof, now):
        direction = self._move
        if direction is None:
            self._state = "IDLE"
            return
        _, _, _, pos_side, neg_side = DIRECTION_INFO[direction]
        pos = tof.get(pos_side)
        neg = tof.get(neg_side)

        lateral = self._lateral_correction(tof, pos_side, neg_side, clamp=0.2)
        omega_cmd = max(-0.2, min(0.2, -KP_HEADING * self._heading))

        lateral_ok = (pos is None or neg is None) or abs(pos - neg) < CENTER_TOLERANCE
        angle_ok = abs(self._heading) < ANGLE_TOLERANCE
        timed_out = (now - self._settle_start) > SETTLING_TIMEOUT

        if (lateral_ok and angle_ok) or timed_out:
            self._stop_motors()
            print(f"[tile] settled (timeout={timed_out}); returning to IDLE")
            self._state = "IDLE"
            self._move = None
            return

        if direction in ("north", "south"):
            self._drive(lateral, 0.0, omega_cmd)
        else:
            self._drive(0.0, lateral, omega_cmd)

    def _lateral_correction(self, tof, pos_side, neg_side, clamp):
        pos = tof.get(pos_side)
        neg = tof.get(neg_side)
        if pos is None or neg is None:
            return 0.0
        value = KP_LATERAL * (pos - neg)
        return max(-clamp, min(clamp, value))

    def _reset_tile_state(self):
        self._queue.clear()
        self._state = "IDLE"
        self._move = None
        self._start_front = None
        self._heading = 0.0

    def _drive(self, vx, vy, omega):
        # Holonomic mixer derived from the existing per-key mappings in _direct_drive:
        # N = vx + omega, S = -vx + omega, E = -vy + omega, W = vy + omega.
        n = vx + omega
        s = -vx + omega
        e = -vy + omega
        w = vy + omega
        scale = max(1.0, abs(n), abs(s), abs(e), abs(w))
        self._command_motor(self.north_motor, n / scale)
        self._command_motor(self.south_motor, s / scale)
        self._command_motor(self.east_motor, e / scale)
        self._command_motor(self.west_motor, w / scale)

    def _command_motor(self, motor, speed):
        if abs(speed) < 0.01:
            motor.stop()
        elif speed >= 0:
            motor.forward(speed)
        else:
            motor.backward(-speed)

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
        motors = [self.north_motor, self.south_motor, self.east_motor, self.west_motor]
        for motor in motors:
            motor.stop()
        for motor in motors:
            motor.close()
