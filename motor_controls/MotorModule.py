# This file contains the MotorModule class which handles motor operations.


import Motor

NORTH_PINS = (17, 27)
SOUTH_PINS = (22, 23)
EAST_PINS = (24, 25)
WEST_PINS = (5, 6)

class MotorModule:
    def __init__(self):
        # Initialize motor module
        self.north_motor = Motor.get_motor_class(*NORTH_PINS)
        self.south_motor = Motor.get_motor_class(*SOUTH_PINS)
        self.east_motor = Motor.get_motor_class(*EAST_PINS)
        self.west_motor = Motor.get_motor_class(*WEST_PINS)
        
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