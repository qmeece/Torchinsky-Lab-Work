import nidaqmx
import nidaqmx.constants

with nidaqmx.Task() as di_task:
    # Add a digital input channel
    di_task.di_channels.add_di_chan("Dev1/port0/line0")
    
    # Read the digital value
    data = di_task.read()
    print(data)