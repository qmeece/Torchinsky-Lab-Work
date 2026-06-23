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

    def move():
        pass

    def getBothToV():
        pass

    def start_Zaber(self):
        
        #First move both the analyzer and polarizer to the vertical polarization
        self.getBothToV()

        if self.mode == "V":

            pass
        elif self.mode == "H":
            pass
        elif self.mode == "SAME":
            pass
        elif self.mode == "OPPOSITE":
            pass
        else:
            print("Invalid polarization mode")

        

        

    



