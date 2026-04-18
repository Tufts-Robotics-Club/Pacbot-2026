# This file contains the main control loop for motor operations.
# Receives commands, passes them to the motor controller.
# Also polls sensor data once per second and prints it.

import argparse
from time import sleep, monotonic
import zmq
from MotorModule import MotorModule
from SensorModule import SensorModule

parser = argparse.ArgumentParser(description="Pacbot motor/sensor control loop")
parser.add_argument("--uart", action="store_true",
                    help="Use UART (physical robot) instead of simulator")
args = parser.parse_args()

print(f"Running in {'UART' if args.uart else 'simulator'} mode")

motor_module = MotorModule(use_uart=args.uart)
sensor_module = SensorModule(use_uart=args.uart)

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5556")
socket.setsockopt(zmq.RCVTIMEO, 0)

SENSOR_POLL_INTERVAL = 1.0
last_sensor_poll = monotonic()

try:
    while True:
        # handle incoming motor commands (non-blocking)
        try:
            command = socket.recv_string()
            motor_module.update(command)
        except zmq.Again:
            pass

        # poll sensors once per second
        now = monotonic()
        if now - last_sensor_poll >= SENSOR_POLL_INTERVAL:
            last_sensor_poll = now
            readings = sensor_module.read_all()
            print(f"[sensors] ToF: {readings['tof']}")
            print(f"[sensors] Encoders: {readings['encoders']}")
            print(f"[sensors] IMU: {readings['imu']}")

        sleep(0.01)
except KeyboardInterrupt:
    print("Shutting down motor loop...")
finally:
    motor_module.close()
    sensor_module.close()
    socket.close()
