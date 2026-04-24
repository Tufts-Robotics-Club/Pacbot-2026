# This file contains the main control loop for motor operations.
# Receives commands, reads sensors every tick, and runs the motor controller.

import argparse
from time import sleep, monotonic
import zmq
from MotorModule import MotorModule
from SensorModule import SensorModule

parser = argparse.ArgumentParser(description="Pacbot motor/sensor control loop")
parser.add_argument("--physical", action="store_true",
                    help="Use physical robot hardware (UART motors, I2C sensors) instead of simulator")
parser.add_argument("--verbose", action="store_true",
                    help="Enable verbose output (ToF + IMU) at 1 Hz")
args = parser.parse_args()

print(f"Running in {'physical' if args.physical else 'simulator'} mode"
      f" (verbose output {'ON' if args.verbose else 'OFF'})")
motor_module = MotorModule(use_physical=args.physical)
sensor_module = SensorModule(use_physical=args.physical)

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5556")
socket.setsockopt(zmq.RCVTIMEO, 0)

VERBOSE_PRINT_INTERVAL = 1.0
last_verbose_print = monotonic()
last_tick = monotonic()

try:
    while True:
        command = None
        try:
            command = socket.recv_string()
        except zmq.Again:
            pass

        now = monotonic()
        dt = now - last_tick
        last_tick = now

        readings = sensor_module.read_all()
        motor_module.tick(command, readings, dt)

        if args.verbose and now - last_verbose_print >= VERBOSE_PRINT_INTERVAL:
            last_verbose_print = now
            print(f"[sensors] ToF: {readings['tof']}")
            print(f"[sensors] IMU: {readings['imu']}")

        sleep(0.01)
except KeyboardInterrupt:
    print("Shutting down motor loop...")
finally:
    motor_module.close()
    if sensor_module is not None:
        sensor_module.close()
    socket.close()
