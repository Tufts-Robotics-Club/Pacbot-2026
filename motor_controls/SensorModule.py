# This file contains the SensorModule class which aggregates all sensors.


import Sensor

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3


class SensorModule:
    def __init__(self, use_physical=False):
        self.tofs = {
            "north": Sensor.get_tof_class(NORTH_ID, use_physical=use_physical),
            "south": Sensor.get_tof_class(SOUTH_ID, use_physical=use_physical),
            "east": Sensor.get_tof_class(EAST_ID, use_physical=use_physical),
            "west": Sensor.get_tof_class(WEST_ID, use_physical=use_physical),
        }
        self.imu = Sensor.get_imu_class(use_physical=use_physical)

    def read_all(self):
        return {
            "tof": {name: s.read() for name, s in self.tofs.items()},
            "imu": self.imu.read(),
        }

    def close(self):
        for s in self.tofs.values():
            s.close()
        self.imu.close()
