# This file contains the SensorModule class which aggregates all sensors.


import Sensor

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3


class SensorModule:
    def __init__(self, use_uart=False):
        self.tofs = {
            "north": Sensor.get_tof_class(NORTH_ID, use_uart=use_uart),
            "south": Sensor.get_tof_class(SOUTH_ID, use_uart=use_uart),
            "east": Sensor.get_tof_class(EAST_ID, use_uart=use_uart),
            "west": Sensor.get_tof_class(WEST_ID, use_uart=use_uart),
        }
        self.encoders = {
            "north": Sensor.get_encoder_class(NORTH_ID, use_uart=use_uart),
            "south": Sensor.get_encoder_class(SOUTH_ID, use_uart=use_uart),
            "east": Sensor.get_encoder_class(EAST_ID, use_uart=use_uart),
            "west": Sensor.get_encoder_class(WEST_ID, use_uart=use_uart),
        }
        self.imu = Sensor.get_imu_class(use_uart=use_uart)

    def read_all(self):
        return {
            "tof": {name: s.read() for name, s in self.tofs.items()},
            "encoders": {name: s.read() for name, s in self.encoders.items()},
            "imu": self.imu.read(),
        }

    def close(self):
        for s in self.tofs.values():
            s.close()
        for s in self.encoders.values():
            s.close()
        self.imu.close()
