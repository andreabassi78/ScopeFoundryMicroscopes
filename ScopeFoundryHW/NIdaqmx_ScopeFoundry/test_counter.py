import nidaqmx
from nidaqmx import stream_writers
import time

dict={"continuous": nidaqmx.constants.AcquisitionType.CONTINUOUS,
      "finite": nidaqmx.constants.AcquisitionType.FINITE,
      "hw_timed": nidaqmx.constants.AcquisitionType.HW_TIMED_SINGLE_POINT}
system = nidaqmx.system.System.local() 
for device in system.devices:
    print(device.name)
    for att in dir(device):
        try:
            print (att, getattr(device,att))
        except:
            pass

channel = 'Dev2/ctr0'
try:
    Task = nidaqmx.Task()
    Task.co_channels.add_co_pulse_chan_freq(counter=channel, idle_state=nidaqmx.constants.Level.LOW, freq=100, duty_cycle=0.5)
    Task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS) 
    Task.triggers.start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE
    Task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = '/Dev2/PFI0', trigger_edge = nidaqmx.constants.Edge.RISING)
    Task.start()
    time.sleep(15)
finally:
    Task.close()