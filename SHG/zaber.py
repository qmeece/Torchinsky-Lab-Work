#This is the file used to control the Zaber program, which moves the polarizer and analyzer
#This code was written using the Zaber software python api found at: https://software.zaber.com/motion-library/api/py
#Author(s): Quinn Meece, Josh Woznicki v

#Imports
import time
import config
from zaber_motion import Units
from zaber_motion.ascii import Connection
    

class Zaber:
    '''This class is for control of the Zaber stepper motors
    It has the following attributes:
    - zaber_resource_name: The COM port of the zaber device
    - mode: The polarization mode, either H, V, Same, or Opposite
    - analyzer_offset: The offset for the analyzer
    - polarizer_offset: The offset for the polarizer
    - p_motor: The polarizer motor
    - a_motor: The analyzer motor
    '''
    def __init__(self,
                ZABER_RESOURCE_NAME=config.ZABER_RESOURCE_NAME,
                POLARIZATION_MODE = config.POLARIZATION_MODE,
                ANALYZER_OFFSET = config.ANALYZER_OFFSET,
                POLARIZER_OFFSET = config.POLARIZER_OFFSET,
                P_MOTOR = config.P_MOTOR,
                A_MOTOR = config.A_MOTOR
                ):
        self.zaber_resource_name = ZABER_RESOURCE_NAME
        self.mode = POLARIZATION_MODE
        self.analyzer_offset = ANALYZER_OFFSET
        self.polarizer_offset = POLARIZER_OFFSET
        self.p_motor = P_MOTOR
        self.a_motor = A_MOTOR
    #Initializes the connection to the zaber
    def initialize_zaber(self):
        self.connection = Connection.open_serial_port(self.zaber_resource_name)

        self.device = self.connection.detect_devices()[0]

        #Defines the motors for the analyzer and polarizer
        self.P_axis = self.device.get_axis(self.p_motor)
        self.A_axis = self.device.get_axis(self.a_motor)

        # Lab view often leaves the two motors in lockstep, so this makes sure that the Zaber doesn't throw an error
        try:
            self.device.generic_command("lockstep 1 setup disable")
        except:
            pass

    #Initializes the SC trigger output from the zaber
    def setup_trigger(self):
        self.device.generic_command("trigger 1 disable")

        self.device.generic_command(f"trigger dist 1 {self.p_motor} 2400")

        self.device.generic_command("trigger 1 action a io do 1 toggle")

        self.device.generic_command("trigger dist 1 enable")

    #Homes both the polarizer and analyzer, sets both to vertical position using the defined offsets
    def getBothToV(self):

        self.P_axis.home()
        self.A_axis.home()
        self.P_axis.move_relative(self.polarizer_offset)
        self.A_axis.move_relative(self.analyzer_offset)
    #
    def move(self, motor, angle):
        if motor == "P":
            self.P_axis.move_relative(self.degrees_to_usteps(angle))
        elif motor == "A":
            self.A_axis.move_relative(self.degrees_to_usteps(angle))

    def run_polarization(self, speed=39000):

        if self.mode == "V":
            self.P_axis.move_velocity(speed)

        elif self.mode == "H":
            self.A_axis.move_relative(self.degrees_to_usteps(90))
            self.P_axis.move_velocity(speed)

        elif self.mode == "SAME":
            self.lockstep = self.device.get_lockstep(1)
            self.lockstep.enable(1, 2)
            self.lockstep.move_velocity(speed)

        elif self.mode == "OPPOSITE":
            self.A_axis.move_relative(self.degrees_to_usteps(90))
            self.lockstep = self.device.get_lockstep(1)
            self.lockstep.enable(1, 2)
            self.lockstep.move_velocity(speed)

        else:
            print("Invalid polarization mode")
    
    def degrees_to_usteps(self,degrees):
        # Zaber motors are in units of 4800 / 360 degrees
        return degrees / 360 * 4800

    def close(self):
        try:
            self.P_axis.home()
            self.A_axis.home()
        except:
            pass
        try:
            self.P_axis.stop()
        except:
            pass
        try:
            self.A_axis.stop()
        except:
            pass
        try:
            self.lockstep.disable()
        except:
            pass
        self.connection.close()

    def main(self, speed=39000):
        self.initialize_zaber()
        self.getBothToV()
        self.setup_trigger()
        self.run_polarization(speed)


        

        

    



