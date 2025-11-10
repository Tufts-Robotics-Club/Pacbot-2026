# This file contains the PiMessager class for sending messages to the Pi via ZeroMQ.

import zmq

class PiMessager:
    def __init__(self, address="tcp://localhost:5555"):
        # Initialize ZeroMQ context and socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.connect(address)

    def send_message(self, message):
        # Send a message to the Pi
        print("Sending message to Pi:", message)
        self.socket.send_string(message)