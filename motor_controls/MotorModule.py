# This file contains the MotorModule class which handles motor operations.

import math

import Motor
from PID import PID

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3

# Modes
IDLE = "IDLE"
TRANSLATE_W = "TRANSLATE_W"
TRANSLATE_A = "TRANSLATE_A"
TRANSLATE_S = "TRANSLATE_S"
TRANSLATE_D = "TRANSLATE_D"
ROTATE_CCW = "ROTATE_CCW"
ROTATE_CW = "ROTATE_CW"

TRANSLATE_MODES = (TRANSLATE_W, TRANSLATE_A, TRANSLATE_S, TRANSLATE_D)

# Heading-hold PID gains (untuned — start conservative, adjust on hardware).
# Input: yaw error in radians. Output: per-wheel rotational-bias duty cycle.
HEADING_KP = 150.0
HEADING_KI = 0.0
HEADING_KD = 0.1
HEADING_OUT_CLAMP = 0.5

TRANSLATE_SPEED = 1.0
ROTATE_OPEN_LOOP_SPEED = 0.5


class MotorModule:
    def __init__(self, use_physical=False):
        self.north_motor = Motor.get_motor_class(NORTH_ID, use_physical=use_physical)
        self.south_motor = Motor.get_motor_class(SOUTH_ID, use_physical=use_physical)
        self.east_motor = Motor.get_motor_class(EAST_ID, use_physical=use_physical)
        self.west_motor = Motor.get_motor_class(WEST_ID, use_physical=use_physical)

        self.mode = IDLE
        self.integrated_yaw = 0.0
        self.heading_target = 0.0
        self.heading_pid = PID(
            HEADING_KP, HEADING_KI, HEADING_KD,
            i_clamp=1.0, out_clamp=HEADING_OUT_CLAMP,
        )

    def tick(self, command, sensor_readings, dt):
        """Run one control step. `command` may be None (no new input this tick)."""
        imu = sensor_readings.get("imu") if sensor_readings else None
        if imu is not None:
            omega = imu.get("omega", 0.0) or 0.0
            self.integrated_yaw += omega * dt

        if command is not None:
            self._handle_command(command)

        if self.mode == IDLE:
            self._drive_wheels(0, 0, 0, 0)
        elif self.mode in TRANSLATE_MODES:
            self._run_translate(dt)
        elif self.mode == ROTATE_CCW:
            s = ROTATE_OPEN_LOOP_SPEED
            self._drive_wheels(s, s, s, s)
        elif self.mode == ROTATE_CW:
            s = -ROTATE_OPEN_LOOP_SPEED
            self._drive_wheels(s, s, s, s)

    def _handle_command(self, command):
        mapping = {
            "W": TRANSLATE_W,
            "A": TRANSLATE_A,
            "S": TRANSLATE_S,
            "D": TRANSLATE_D,
            "Q": ROTATE_CCW,
            "E": ROTATE_CW,
        }
        new_mode = mapping.get(command.upper(), IDLE)

        entering_translate = new_mode in TRANSLATE_MODES and new_mode != self.mode
        if entering_translate:
            self.heading_target = self.integrated_yaw
            self.heading_pid.reset()

        if new_mode == IDLE and self.mode != IDLE:
            self.heading_pid.reset()

        self.mode = new_mode

    def _run_translate(self, dt):
        # Wrap target to within pi of current yaw (shortest-path error).
        while self.heading_target - self.integrated_yaw > math.pi:
            self.heading_target -= 2 * math.pi
        while self.heading_target - self.integrated_yaw < -math.pi:
            self.heading_target += 2 * math.pi

        correction = self.heading_pid.update(self.heading_target, self.integrated_yaw, dt)

        v = TRANSLATE_SPEED
        if self.mode == TRANSLATE_W:
            n, s, e, w = 0.0, 0.0, -v, v
        elif self.mode == TRANSLATE_S:
            n, s, e, w = 0.0, 0.0, v, -v
        elif self.mode == TRANSLATE_A:
            n, s, e, w = -v, v, 0.0, 0.0
        elif self.mode == TRANSLATE_D:
            n, s, e, w = v, -v, 0.0, 0.0
        else:
            n = s = e = w = 0.0

        # Positive correction rotates CCW (same sign convention as Q): add to all wheels.
        n += correction
        s += correction
        e += correction
        w += correction

        self._drive_wheels(n, s, e, w)

    def _drive_wheels(self, n, s, e, w):
        self._apply(self.north_motor, n)
        self._apply(self.south_motor, s)
        self._apply(self.east_motor, e)
        self._apply(self.west_motor, w)

    @staticmethod
    def _apply(motor, signed_speed):
        v = max(-1.0, min(1.0, signed_speed))
        if v > 0:
            motor.forward(v)
        elif v < 0:
            motor.backward(-v)
        else:
            motor.stop()

    def close(self):
        motors = [self.north_motor, self.south_motor, self.east_motor, self.west_motor]
        for motor in motors:
            motor.stop()
        for motor in motors:
            motor.close()
