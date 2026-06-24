#Test for SHG - Eventually this will become the DAQ controller file for the program
#Author(s): Josh Woznicki, Quinn Meece

#Imports
import config
from nidaqmx.constants import AcquisitionType, TerminalConfiguration, Edge
import nidaqmx
import numpy as np

class PulseData:
    '''The class which defines the output pulses peaks recorded by the PMT
    Attributes: ai_channel - the input channel on the DAQ
                trigger_source - the input channel of DAQ with SDG
                sample_rate - how many samples are taken per second
                samples_per_event - the total number of samples taken after triggering
    '''
    def _init_(self,
               PMT_channel = config.PMT_CHANNEL,
               counter_channel = config.COUNTER_CHANNEL,
               trigger_source = config.CLOCK_CHANNEL,
               sample_rate = config.SAMPLE_RATE,
               samples_per_channel= config.SAMPLES_PER_CHANNEL,
               SC_channel = config.SC_CHANNEL,
               Enc_A_channel = config.ENC_A_CHANNEL,
               Enc_B_channel = config.ENC_B_CHANNEL,
               averages = config.AVERAGES
               ):
        self.PMT_channel = PMT_channel
        self.counter_channel = counter_channel
        self.trigger_source = trigger_source
        self.sample_rate = sample_rate
        self.samples_per_channel = samples_per_channel
        self.SC_channel = SC_channel
        self.Enc_A_channel =Enc_A_channel
        self.Enc_B_channel = Enc_B_channel
        self.averages = averages
        self.single_shot = []
        self.average_shot = []
        
    def update(self):
        """
        This method is called to scan for data.
        It initializes the counter and PMT input tasks to create single shot and averaged data.
        """
        #Starts a DAQ task for PMT and Counter
        with nidaqmx.Task() as task_PMT, nidaqmx.Task() as task_Counter:
            # Adds the input channel to the PMT task
            task_PMT.ai_channels.add_ai_voltage_chan(physical_channel=self.PMT_channel,
                                                     terminal_config=TerminalConfiguration.DIFF,
                                                     )
            #Tells PMT task to start when SC tells it to
            task_PMT.triggers.start_trigger.cfg_dig_edge_start_trig(
                trigger_source = self.SC_channel,
                trigger_edge=Edge.RISING
            )
            #Tells PMT to take samps_per_chan number of points at each falling edge of the SDG
            task_PMT.timing.cfg_samp_clk_timing(
                rate= 5000,
                source=self.trigger_source,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=self.samples_per_channel*self.averages,
                trigger_edge=Edge.FALLING
            )
            
            #Adds the input channel to the Counter task
            task_Counter.ci_channels.add_ci_ang_encoder(counter=self.counter_channel,
                                                        pulses_per_rev=config.PULSES_PER_REV)
            #Adds the encoder input channels
            task_Counter.ci_channels.ci_encoder_a_input_term_cfg(self.Enc_A_channel)
            task_Counter.ci_channels.ci_encoder_a_input_term_cfg(self.Enc_B_channel)
            
            #Times the counter to only take points when the pulse data is taken
            task_Counter.timing.cfg_samp_clk_timing(
                source=self.trigger_source,
                sample_mode = AcquisitionType.FINITE,
                rate=5000,
                samps_per_chan = self.samples_per_channel * self.averages
            )
            
            task_Counter.start()
            task_PMT.start()
            
            average_shots = []
            #For every single shot data set
            for i in range(self.averages):
                #Read the pulse channel
                PMT_peaks_raw =np.array(task_PMT.read(number_of_samples_per_channel=self.samples_per_channel))
                #SPECIAL- WE HAVE NO IDEA WHY THIS OFFSET IS SUBTRACTED FROM THE PMT SIGNAL, ASK ABOUT THIS
                PMT_peaks_offset= [a - 0.00111 for a in PMT_peaks_raw]
                #Read the corresponding degree from the counter
                # Note that this creates an array with absolute degrees, including values greater than 360
                angle_unwrapped = np.array(task_Counter.read(number_of_samples_per_channel=self.samples_per_channel))
                #This wraps all angles to be between 0 and 360
                angle_wrapped = [d % 360 for d in angle_unwrapped]
                #This sorts the peak values by angle
                #This is the result that we could display as the single shot data
                self.single_shot= PMT_peaks_offset[np.argsort(angle_wrapped)]
                
                #If we haven't added a single shot yet
                if i==0:
                    #Set the average shots to the first single shot
                    self.average_shot = self.single_shot
                else:
                    #Otherwise, just average them element wise.
                    self.average_shot = (self.single_shot + i*(self.average_shot ))/(i+1)
                  

                
                
                

                
                
            
                
            
        
            
    
            