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

    def setup_trigger(self):
        self.device.generic_command("trigger 1 disable")

        self.device.generic_command("trigger dist 1 1 2400")

        self.device.generic_command("trigger 1 action a io do 1 toggle")

        self.device.generic_command("trigger dist 1 enable")

    def getBothToV(self):
        self.P_axis.home()
        self.A_axis.home()
        self.P_axis.move_relative(self.polarizer_offset)
        self.A_axis.move_relative(self.analyzer_offset)

    def start_Zaber(self, speed=39000):
        # Initialize the Zaber motors
        self.connection = Connection.open_serial_port(self.zaber_resource_name)

        self.device = self.connection.detect_devices()[0]
        #self.device.generic_command("lockstep 1 setup disable")

        self.P_axis = self.device.get_axis(1)
        self.A_axis = self.device.get_axis(2)

        self.setup_trigger()

        # Move both the analyzer and polarizer to the vertical polarization
        self.getBothToV()

        if self.mode == "V":
            self.P_axis.move_velocity(speed)

        elif self.mode == "H":
            self.A_axis.move_relative(0)
            self.P_axis.move_velocity(speed)
            time.sleep(5)
            self.P_axis.stop()

        elif self.mode == "SAME":
            self.lockstep = self.device.get_lockstep(1)
            self.lockstep.enable(1, 2)
            self.lockstep.move_velocity(speed)

        # elif self.mode == "OPPOSITE":
        #     self.A_axis.settings.set("system.axis.reverse", 0)
        #     self.lockstep = device.get_lockstep(1)
        #     self.lockstep.enable(1, 2)
        #     self.lockstep.move_velocity(speed)

        else:
            print("Invalid polarization mode")

    def close(self):
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
                print("not in lockstep")
            self.connection.close()


        

        

    



