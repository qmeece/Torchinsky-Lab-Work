#Global Configuration variables - Eventually will connect to GUI

#DAQ INPUTS
#The SDG Trigger input
#This is a TTL Pulse which is timed to the arrival of the laser to the PMT
#The rising edge should be timed to peak pulse height
CLOCK_CHANNEL = "/Dev1/PFI1"
#The Counter Channel
#This is a TTL which is timed to count the steps from the encoders
#This pulses each time the stepper motors on the Polarizer/analyzer move a step
COUNTER_CHANNEL = "/Dev1/ctr0"
#The Encoder for the polarizer
#This keeps track of the angle of the polarizer
ENCODER_CHANNEL = "/Dev1/PFI3"
#The output of the PMT (From the Integrator and Shaper output)
PMT_CHANNEL = "/Dev1/ai0"
#This is the channel for the SC, which tells the program that the polarizer has begun a rotation
SC_CHANNEL = "/Dev1/PFI12"


#PULSE READING CONFIGURATIONS
#Number of samples recorded from the PMT input per second
SAMPLE_RATE = 1000000
#The number of peaks taken per rotation
SAMPLES_PER_CHANNEL = 10007
#Number of times we rescan
AVERAGES = 5

#COUNTER INPUTS
#Pulses per revolution- this is set by the physical limits of the stepper motor
PULSES_PER_REV=3000

#ENCODER CHANNELS
ENC_A_CHANNEL= "/Dev1/PFI8"
ENC_B_CHANNEL= "/Dev1/PFI14"

#ZABER INPUTS
ZABER_RESOURCE_NAME = "COM7"
P_MOTOR = "1 2"
A_MOTOR = "1 1"
# H = 0
# V = 1
# SAME = 2
# OPPOSITE = 3

# Offset in degrees for both the analyzer and polarizer to get to vertical polarization
ANALYZER_OFFSET = 0
POLARIZER_OFFSET = 0

#Sets the polarization mode that the Zaber runs in.
# H is for the analyzer horizontally polarized and the polarizer spinning.
# V is for the analyzer vertically polarized and the polarizer spinning.
# SAME is for polarizer and analyzer lockstep spinning in the same direction.
# OPPOSITE is for polarizer and analyzer lockstep spinning in opposite directions.
POLARIZATION_MODE = "SAME"
