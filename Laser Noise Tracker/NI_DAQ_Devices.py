import nidaqmx.system

system = nidaqmx.system.System.local()

for dev in system.devices:
    print(dev.name)