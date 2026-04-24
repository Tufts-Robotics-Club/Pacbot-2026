import zmq
import json

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


class IMUSimulator(_SimSensorBase):
    def __init__(self, host="localhost", port=5557):
        super().__init__("sensors.imu", host, port)

    def read(self):
        self._drain()
        return self._latest


# --- Physical (I2C) implementations ---
# ToFs: VL53L4CD behind a TCA9548A mux (channels 0-3 = N/S/E/W).
# IMU: BNO08X over I2C. Assumes sensor frame matches robot body frame
# (+X = right, +Y = forward, +Z = up) so linear_accel (x,y) = (ax,ay)
# and gyro_z = omega (+ CCW).

_i2c = None
_tca = None


def _get_i2c():
    global _i2c
    if _i2c is None:
        import board
        _i2c = board.I2C()
    return _i2c


def _get_tca():
    global _tca
    if _tca is None:
        import adafruit_tca9548a
        _tca = adafruit_tca9548a.TCA9548A(_get_i2c())
    return _tca


class ToFPhysical:
    """VL53L4CD on TCA9548A channel = sensor_id. Returns distance in meters."""

    def __init__(self, sensor_id, timing_budget=200, inter_measurement=0):
        if sensor_id not in ID_TO_WHEEL:
            raise ValueError(f"Invalid ToF sensor id {sensor_id}; expected 0-3")
        import adafruit_vl53l4cd
        self.sensor_id = sensor_id
        self.sensor = adafruit_vl53l4cd.VL53L4CD(_get_tca()[sensor_id])
        self.sensor.timing_budget = timing_budget
        self.sensor.inter_measurement = inter_measurement
        self.sensor.start_ranging()

    def read(self):
        if not self.sensor.data_ready:
            return None
        distance_cm = self.sensor.distance
        self.sensor.clear_interrupt()
        if distance_cm is None:
            return None
        return distance_cm / 100.0  # cm -> m to match simulator

    def close(self):
        try:
            self.sensor.stop_ranging()
        except Exception:
            pass


class IMUPhysical:
    """BNO055 IMU over I2C. Returns {'ax', 'ay', 'omega'} matching sim schema."""

    def __init__(self):
        import time
        from adafruit_bno055 import BNO055_I2C
        self.bno = BNO055_I2C(_get_i2c())
        time.sleep(1)

    def read(self):
        accel = self.bno.linear_acceleration
        gyro = self.bno.gyro
        if accel is None or gyro is None:
            return None
        ax, ay, _ = accel
        _, _, omega = gyro
        if ax is None or ay is None or omega is None:
            return None
        return {"ax": ax, "ay": ay, "omega": omega}

    def close(self):
        pass


# --- Factory functions ---

def get_tof_class(sensor_id, use_physical=False):
    if use_physical:
        return ToFPhysical(sensor_id)
    return ToFSimulator(sensor_id)


def get_imu_class(use_physical=False):
    if use_physical:
        return IMUPhysical()
    return IMUSimulator()
