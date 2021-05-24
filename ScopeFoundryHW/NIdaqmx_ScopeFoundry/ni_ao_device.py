import nidaqmx
import numpy as np

from nidaqmx import stream_writers

class NI_AO_device(object):
    
    def __init__(self, channel, debug = False, dummy = False):
        
        self.dummy = dummy
        self.debug = debug
        self.channel = channel
        self.sample_modes = {"continuous": nidaqmx.constants.AcquisitionType.CONTINUOUS,
                             "finite": nidaqmx.constants.AcquisitionType.FINITE,
                             "hw_timed": nidaqmx.constants.AcquisitionType.HW_TIMED_SINGLE_POINT
                             }           
        if not self.dummy:            
            self.create_task()
    
    def create_task(self):
        '''add an analog input channel'''            
        
        if hasattr(self, 'task'):
            self.close()
            
        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan(physical_channel=self.channel,
                                                  min_val=-10.0, max_val=10.0)    
            
    def write_signal(self, mode = 'ao_waveform', sample_mode_key = 'continuous',
                            waveform_type = 'sine',
                            num_periods = 6, 
                            amplitude = 1,        
                            frequency = 50,
                            spike_amplitude = 0, spike_duration = 0, 
                            oversampling = 100,
                            offset = 0):
        if not hasattr(self, 'task'):
            raise(AttributeError, 'AO task not active, unable to write signal')        
        
        self.mode = mode
        self.sample_mode = self.sample_modes[sample_mode_key]       
        self.num_periods = num_periods
        self.amplitude = amplitude
        self.waveform_type = waveform_type
        self.frequency = frequency
        self.rate=self.frequency * oversampling # 
        if self.rate >= 250000:
            raise(ValueError,'Frequency too high, unable to set NIDAQ analog output')
        self.offset = offset
        self.spike_duration = spike_duration
        self.spike_amplitude = spike_amplitude    
        
        self.stop_task()
        
        if self.mode =="ao_voltage":
            
            self.task.write(self.amplitude, auto_start = True)
        
        elif self.mode == "ao_waveform":
            
            samples = self.generate_signal()
            num_samples = len(samples) # self.num_periods * int(self.rate/self.frequency)
            
            try:
                self.task.timing.cfg_samp_clk_timing(rate = self.rate, 
                                                     sample_mode = self.sample_mode, 
                                                     samps_per_chan = num_samples)
                writer= stream_writers.AnalogSingleChannelWriter(self.task.out_stream, auto_start=False)
                writer.write_many_sample(samples)
            
            except Exception as err: 
                print ("Rate too low. Use a rate of at least twice the frequency", err)
    
    def generate_signal(self):
        
        T = 1/self.frequency # Hz 
        rate = self.rate
        dt = 1/rate
        
        Ncycles = self.num_periods
        epsilon = 1e-9 # 1ns delay to avoid approximation error in rect and step function
        t = np.arange(0, Ncycles*T, dt) + epsilon

        if self.waveform_type == "sine":
            samples = self.amplitude * np.sin(2*np.pi*t) + self.offset
        
        elif self.waveform_type == "rect": 
            width = 0.5
            samples =  self.amplitude * ( t%T < (width*T) )
        
        elif self.waveform_type == "step": 
            Nsteps = 3 # number of steps is set to 3 here
            deltaAmp = self.amplitude # the voltage increase in each step is deltaAmp
            samples =  deltaAmp * ( (t//T) % Nsteps )
        else:
            raise(ValueError,'Waveform not specified')
            
        if self.spike_amplitude > 0:
            # spikeT = 0.0005 #s
            # spikeT = 0.05/freq # percentage of the step duration
            samples += self.spike_amplitude * ( (t%T) < self.spike_duration)
        
        samples += self.offset
        return samples
              
    def start_task(self):
        
        if not hasattr(self, 'task'):
            raise(AttributeError,'Task not active, unable to start')
        
        if self.task.is_task_done()==True:
            self.task.start()
        
    def stop_task(self):
        if not hasattr(self, 'task'):
            raise(AttributeError,'Task not active, unable to stop')
        # suppress warning that might occurr when task i stopped during acquisition
        # warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)
        self.task.stop() #stop the task(different from the closing of the task, I suppose)
        # warnings.filterwarnings('default',category=nidaqmx.DaqWarning)      
            
    def close(self):
        if not hasattr(self, 'task'):
            raise(AttributeError,'Task not active, unable to close')
        self.task.close()

if __name__ == '__main__':
    import time   
       
    dev = NI_AO_device('Dev0/ao0')
    
    dev.create_task()
    try:
        dev.write_signal(mode = 'ao_waveform', 
                         sample_mode_key = 'continuous',
                         waveform_type = 'sine',
                         num_periods = 6, 
                         amplitude = 1,        
                         frequency = 50,
                         spike_amplitude = 0, spike_duration = 0, 
                         oversampling = 100,
                         offset = 0)
        dev.start_task()
        
        time.sleep(1)
        dev.stop_task()
    finally:
        dev.close()
    
    
    
        
        
        
