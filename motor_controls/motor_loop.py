# This file contains the main control loop for motor operations.
# Receives commands, passes them to the motor controller

from time import sleep
import zmq
from MotorModule import MotorModule

motor_module = MotorModule()

while True:
    # handle incoming motor commands (non-blocking)
    try:
        command = zmq.recv()
        motor_module.update(command)
    except zmq.Again:
        pass

    sleep(0.01)
    