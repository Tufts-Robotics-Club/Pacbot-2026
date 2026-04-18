# This file contains the MotorModule class which handles motor operations.


import Motor

NORTH_ID = 0
SOUTH_ID = 1
EAST_ID = 2
WEST_ID = 3

class MotorModule:
    def __init__(self):
        # Initialize motor module
        self.north_motor = Motor.get_motor_class(NORTH_ID)
        self.south_motor = Motor.get_motor_class(SOUTH_ID)
        self.east_motor = Motor.get_motor_class(EAST_ID)
        self.west_motor = Motor.get_motor_class(WEST_ID)

    def update(self, command):
        # Update motor state based on command
        # LATER: Implement motor control logic
        if command.upper() == "W":
            self.west_motor.forward(0.6)
            self.east_motor.backward(0.6)
        elif command.upper() == "S":
            self.west_motor.backward(0.6)
            self.east_motor.forward(0.6)
        elif command.upper() == "A":
            self.north_motor.backward(0.6)
            self.south_motor.forward(0.6)
        elif command.upper() == "D":
            self.north_motor.forward(0.6)
            self.south_motor.backward(0.6)
        else:
            self.north_motor.stop()
            self.south_motor.stop()
            self.east_motor.stop()
            self.west_motor.stop()
            
        pass

    def close(self):
        # Clean up motor module resources
        for motor in [self.north_motor, self.south_motor, self.east_motor, self.west_motor]:
            motor.stop()
            motor.close()