# This file contains the main control loop for motor operations.
# Receives commands, passes them to the motor controller.
# Ticks the tile-drive state machine every iteration and prints sensor data once per second.

import argparse
from time import sleep, monotonic
import zmq
from MotorModule import MotorModule
from SensorModule import SensorModule

parser = argparse.ArgumentParser(description="Pacbot motor/sensor control loop")
parser.add_argument("--physical", action="store_true",
                    help="Use physical robot hardware (UART motors, I2C sensors) instead of simulator")
parser.add_argument("--sensors", action="store_true",
                    help="Enable sensor polling (ToF + IMU) and print readings once per second. "
                         "Required for tile-drive mode (north/south/east/west commands).")
parser.add_argument("--verbose", action="store_true",
                    help="Print verbose output including command processing and sensor readings.")
args = parser.parse_args()

print(f"Running in {'physical' if args.physical else 'simulator'} mode"
      f" (sensors {'ON' if args.sensors else 'OFF'})")

sensor_module = SensorModule(use_physical=args.physical) if args.sensors else None
motor_module = MotorModule(use_physical=args.physical, sensor_module=sensor_module)

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5556")
socket.setsockopt(zmq.RCVTIMEO, 0)

SENSOR_POLL_INTERVAL = 1.0
last_sensor_poll = monotonic()

try:
    while True:
        try:
            command = socket.recv_string()
            motor_module.update(command)
        except zmq.Again:
            pass

        motor_module.tick()

        if sensor_module is not None:
            now = monotonic()
            if now - last_sensor_poll >= SENSOR_POLL_INTERVAL:
                last_sensor_poll = now
                readings = sensor_module.read_all()
                if args.verbose:
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
