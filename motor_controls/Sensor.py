import zmq
import json
import serial

ID_TO_WHEEL = {0: "north", 1: "south", 2: "east", 3: "west"}


# --- Simulator (ZeroMQ SUB) implementations ---

class _SimSensorBase:
    """Base class for simulator sensor subscribers (ZMQ PUB/SUB on port 5557)."""

    def __init__(self, topic, host="localhost", port=5557):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{host}:{port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        self.socket.setsockopt(zmq.RCVTIMEO, 0)
        self._latest = None

    def _drain(self):
        while True:
            try:
                msg = self.socket.recv_string()
                _, payload = msg.split(" ", 1)
                self._latest = json.loads(payload)
            except zmq.Again:
                break

    def close(self):
        self.socket.close()
        self.context.term()


class ToFSimulator(_SimSensorBase):
    def __init__(self, sensor_id, host="localhost", port=5557):
        super().__init__("sensors.tof", host, port)
        if sensor_id not in ID_TO_WHEEL:
            raise ValueError(f"Invalid ToF sensor id {sensor_id}; expected 0-3")
        self.sensor_id = sensor_id
        self._wheel = ID_TO_WHEEL[sensor_id]

    def read(self):
        self._drain()
        if self._latest is None:
            return None
        return self._latest[self._wheel]


class EncoderSimulator(_SimSensorBase):
    def __init__(self, sensor_id, host="localhost", port=5557):
        super().__init__("sensors.encoders", host, port)
        if sensor_id not in ID_TO_WHEEL:
            raise ValueError(f"Invalid encoder id {sensor_id}; expected 0-3")
        self.sensor_id = sensor_id
        self._wheel = ID_TO_WHEEL[sensor_id]

    def read(self):
        self._drain()
        if self._latest is None:
            return None
        return self._latest[self._wheel]


class IMUSimulator(_SimSensorBase):
    def __init__(self, host="localhost", port=5557):
        super().__init__("sensors.imu", host, port)

    def read(self):
        self._drain()
        return self._latest


# --- UART (physical robot) placeholder implementations ---

class ToFUart:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)

    def read(self):
        # Placeholder: request distance reading over UART
        self.ser.write(f"TOF {self.sensor_id}\n".encode())
        return None

    def close(self):
        self.ser.close()


class EncoderUart:
    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        self.ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)

    def read(self):
        # Placeholder: request encoder tick count over UART
        self.ser.write(f"ENC {self.sensor_id}\n".encode())
        return None

    def close(self):
        self.ser.close()


class IMUUart:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=1)

    def read(self):
        # Placeholder: request IMU reading over UART
        self.ser.write(b"IMU\n")
        return None

    def close(self):
        self.ser.close()


# --- Factory functions ---

def get_tof_class(sensor_id, use_uart=False):
    if use_uart:
        return ToFUart(sensor_id)
    return ToFSimulator(sensor_id)


def get_encoder_class(sensor_id, use_uart=False):
    if use_uart:
        return EncoderUart(sensor_id)
    return EncoderSimulator(sensor_id)


def get_imu_class(use_uart=False):
    if use_uart:
        return IMUUart()
    return IMUSimulator()
