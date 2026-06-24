#This is the file used to control the Zaber program, which moves the polarizer and analyzer
#This code was written using the Zaber software python api found at: https://software.zaber.com/motion-library/api/py
#Author(s): Quinn Meece, Josh Woznicki v

#Imports
import config
from zaber_motion import Units
from zaber_motion.ascii import Connection
    

class Zaber:
    '''This class is for control of the Zaber stepper motors
    '''
    def __init__(self,
                ZABER_RESOURCE_NAME=config.ZABER_RESOURCE_NAME,
                POLARIZATION_MODE = config.POLARIZATION_MODE,
                ANALYZER_OFFSET = config.ANALYZER_OFFSET,
                POLARIZER_OFFSET = config.POLARIZER_OFFSET
                ):
        self.zaber_resource_name = ZABER_RESOURCE_NAME
        self.mode = POLARIZATION_MODE
        self.analyzer_offset = ANALYZER_OFFSET
        self.polarizer_offset = POLARIZER_OFFSET

    def move(self):
        pass

    def getBothToV(self):
        self.P_axis.move_absolute(self.polarizer_offset, Units.ANGLE_DEGREES)
        self.A_axis.move_absolute(self.analyzer_offset, Units.ANGLE_DEGREES)

    def start_Zaber(self, speed=39000):
        # Initialize the Zaber motors
        self.connection = Connection.open_serial_port(self.zaber_resource_name)

        device = self.connection.detect_devices()[0]

        print(device)

        return

        self.P_axis = device.get_axis(1)
        self.A_axis = device.get_axis(2)

        # Move both the analyzer and polarizer to the vertical polarization
        self.getBothToV()

        if self.mode == "V":
            self.P_axis.move_velocity(speed)

        elif self.mode == "H":
            self.A_axis.move_relative(90, Units.ANGLE_DEGREES)
            self.P_axis.move_velocity(speed)

        elif self.mode == "SAME":
            self.axis_group = self.connection.get_axis_group([self.P_axis, self.A_axis])
            self.axis_group.move_velocity(speed)

        elif self.mode == "OPPOSITE":
            pass
        else:
            print("Invalid polarization mode")

    def close(self):
        self.connection.close()

        

        

    



