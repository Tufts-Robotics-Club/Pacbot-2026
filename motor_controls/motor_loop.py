# This file contains the main control loop for motor operations.
# Receives commands, passes them to the motor controller

from time import sleep
import zmq
from MotorModule import MotorModule

motor_module = MotorModule()

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5556")
socket.setsockopt(zmq.RCVTIMEO, 0)

while True:
    # handle incoming motor commands (non-blocking)
    try:
        command = socket.recv_string()
        motor_module.update(command)
    except zmq.Again:
        pass

    sleep(0.01)
    