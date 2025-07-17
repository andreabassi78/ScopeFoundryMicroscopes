import nidaqmx
import warnings
import math
import numpy as np

from nidaqmx import stream_writers

class NI_CO_device(object):
    
    def __init__(self, channel, initial_delay, freq, duty_cycle, trigger, trigger_source, trigger_edge, debug=False):
        
        
        self.dict={"rising": nidaqmx.constants.Edge.RISING,
                   "falling": nidaqmx.constants.Edge.FALLING}
        self.debug = debug 
        self.channel = channel
        self.initial_delay = initial_delay
        self.freq = freq
        self.duty_cycle = duty_cycle
        self.trigger= trigger
        self.trigger_source = trigger_source
        self.trigger_edge= trigger_edge
                 
        self.Task()
    
    def Task(self):
        if hasattr(self, 'task'):
            self.close()
            
        self.task = nidaqmx.Task()
        self.task.co_channels.add_co_pulse_chan_freq(counter=self.channel, initial_delay=self.initial_delay, freq=self.freq, duty_cycle=self.duty_cycle)
        #self.task.co_channels.add_co_pulse_chan_time(counter=self.channel, units=nidaqmx.constants.TimeUnits.SECONDS, idle_state=nidaqmx.constants.Level.LOW, initial_delay=0, low_time=0.01, high_time=0.01)
        self.task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=round(self.freq))
        #samps_per_chan(*or/)freq must be an integer! (maybe) 
        if self.trigger:
            self.task.triggers.start_trigger.trig_type = nidaqmx.constants.TriggerType.DIGITAL_EDGE
            self.task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = self.trigger_source, trigger_edge = self.dict.get(self.trigger_edge))
        
    def start_task(self):
        
        self.Task()
        self.task.start()
            
    def set_initial_delay(self, initial_delay):
        
        self.initial_delay = initial_delay
    
  
    def set_freq(self, freq):
        
        self.freq = freq
        

        
    def set_duty_cycle(self, duty_cycle):
        
        self.duty_cycle = duty_cycle
    

        
    def set_trigger(self, trigger):
        
        self.trigger = trigger
        

        
    def set_trigger_source(self,trigger_source):
        
        self.trigger_source = trigger_source
        
        
    def set_trigger_edge(self,trigger_edge):
        
        self.trigger_edge = trigger_edge
        

        
    def stop_task(self):
        #suppress warning that might occur when task i stopped during acquisition
        #warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)
        self.task.stop() #stop the task(different from the closing of the task, I suppose)
        #warnings.filterwarnings('default',category=nidaqmx.DaqWarning)
        
            
    def close(self):
        
        self.task.close() #close the task
        