import nidaqmx
from nidaqmx import stream_writers

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

channel = 'Dev2/port1/line0'
try:
    Task = nidaqmx.Task()
    Task.do_channels.add_do_chan(lines=channel)
    #Task.timing.cfg_samp_clk_timing(rate=100, sample_mode=dict.get("continuous"))
    Task.write([bool(0)], auto_start=True)
finally:
    Task.close()
# try:
#     trig_task = nidaqmx.Task()
#     trig_task.do_channels.add_do_chan(lines=channel)
#     trig_writer = stream_writers.DigitalSingleChannelWriter(trig_task.in_stream)
#     trig_task.triggers.start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE
#     trig_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = "Dev2/port1/line1")
#     trig_task.start()
#     trig_writer.write_one_sample_one_line(data=True)
# finally:
#     trig_task.close()