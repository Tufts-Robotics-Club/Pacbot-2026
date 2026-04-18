import zmq
import json
import serial

# Goal is to have same interface as GPIO PhaseEnableMotor
# May change if using different library in real motor module
class MotorSimulator:
    """
    Client-side motor interface. Identifies a motor by a single numeric ID
    (0=north, 1=south, 2=east, 3=west by convention — see simulator config).
    """

    def __init__(self, motor_id):
        self.motor_id = motor_id

        # Set up ZeroMQ client
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def _send_command(self, command, params=None):
        message = {"command": command, "id": self.motor_id}
        if params:
            message["params"] = params
        self.socket.send_string(json.dumps(message))
        reply = self.socket.recv_string()
        return reply

    def forward(self, speed):
        return self._send_command("move", {"speed": speed})

    def backward(self, speed):
        return self._send_command("move", {"speed": -speed})

    def stop(self):
        return self._send_command("move", {"speed": 0})

    def close(self):
        self.socket.close()
        self.context.term()


class MotorUart():
    def __init__(self, motor_id):
        self.motor_id = motor_id

        self.ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)
        
    def forward(self, speed):
        self.ser.write(f"MOVE {self.motor_id} {speed}\n".encode())
    
    def backward(self, speed):
        self.ser.write(f"MOVE {self.motor_id} {-speed}\n".encode())
    
    def stop(self):
        self.ser.write(f"MOVE {self.motor_id} 0\n".encode())
    
    def close(self):
        self.ser.close()

def get_motor_class(motor_id, use_uart=False):
    # In real implementation, we would check for hardware availability
    # For now, we return the simulator class
    if use_uart:
        return MotorUart(motor_id)
    return MotorSimulator(motor_id)