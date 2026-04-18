import zmq
import json
import struct


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


class MotorPhysical:
    """
    Sends commands to the STM32 over UART. All 4 motor speeds are packed into
    one 8-byte packet ('>hhhh', front/right/back/left scaled to ±32767). Per-motor
    API is preserved by sharing speed state across instances and re-sending all
    four on every update.

    ID convention (matches simulator): 0=north=front, 1=south=back, 2=east=right,
    3=west=left.
    """

    _serial = None
    _speeds = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}

    @classmethod
    def _get_serial(cls):
        if cls._serial is None:
            import time
            import serial
            cls._serial = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
            time.sleep(2)  # let STM32 bootloader settle
        return cls._serial

    def __init__(self, motor_id):
        if motor_id not in (0, 1, 2, 3):
            raise ValueError(f"Invalid motor id {motor_id}; expected 0-3")
        self.motor_id = motor_id
        self._get_serial()

    def _flush(self):
        def scale(v):
            return int(max(-32767, min(32767, v * 32767)))
        speeds = MotorPhysical._speeds
        packet = struct.pack(
            '>hhhh',
            scale(speeds[0]),  # front = north
            scale(speeds[2]),  # right = east
            scale(speeds[1]),  # back  = south
            scale(speeds[3]),  # left  = west
        )
        ser = self._get_serial()
        if ser is not None:
            ser.write(packet)

    def forward(self, speed):
        MotorPhysical._speeds[self.motor_id] = speed
        self._flush()

    def backward(self, speed):
        MotorPhysical._speeds[self.motor_id] = -speed
        self._flush()

    def stop(self):
        MotorPhysical._speeds[self.motor_id] = 0
        self._flush()

    def close(self):
        # First caller closes the shared serial; subsequent calls are no-ops.
        if MotorPhysical._serial is not None:
            try:
                MotorPhysical._serial.close()
            except Exception:
                pass
            MotorPhysical._serial = None


def get_motor_class(motor_id, use_physical=False):
    if use_physical:
        return MotorPhysical(motor_id)
    return MotorSimulator(motor_id)
