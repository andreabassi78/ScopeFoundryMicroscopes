from ScopeFoundry import HardwareComponent

from ni_ao_device import NI_AO_device

import nidaqmx.system as ni

class NI_AO_hw(HardwareComponent):
    
    name = 'NI_DAQ_AO_hw' 
    
    def setup(self):
        #create logged quantities, that are related to the graphical interface
        board, terminals=self.detect_channels()
        
        self.devices = self.add_logged_quantity('device',  dtype=str, initial=board)        
        self.channel = self.add_logged_quantity('channel', dtype=str, choices=terminals, initial=terminals[0])
        self.mode = self.add_logged_quantity('mode', dtype=str, choices=['ao_voltage', 'ao_waveform'], initial='ao_voltage')
        
        self.sample_mode = self.add_logged_quantity('sample_mode', dtype = str, choices=[ "continuous", "finite"], initial = 'continuous')
        self.num_periods = self.add_logged_quantity('num_periods', dtype = int , si = False, ro = 0, vmin=1, initial = 1)
        self.amplitude = self.add_logged_quantity('amplitude', dtype = float, si = False, ro = 0, initial = 0, vmin=-10, vmax=10, unit='V')
        self.waveform = self.add_logged_quantity('waveform', dtype=str, choices=[ "sine", "square","step"], initial='sine')
        self.frequency = self.add_logged_quantity('frequency', dtype = float, si = False, ro = 0, initial = 100, unit='Hz')
        self.offset = self.add_logged_quantity('offset', dtype = float, si = False, ro = 0, initial = 0, unit='V')
        self.oversampling = self.add_logged_quantity('oversampling', dtype = int, si = False, ro = 0, initial = 200)
        
        self.spike_amplitude = self.add_logged_quantity('spike_amplitude', dtype = float, si = False, ro = 0, initial = 0, unit='V')
        self.spike_duration = self.add_logged_quantity('spike_duration', dtype = float, si = False, ro = 0, initial = 0, unit='s')
        
        self.add_operation("start_waveform_task", self.start)
        self.add_operation("stop_waveform_task", self.stop)
        
    def connect(self):
        #open connection to hardware
        self.channel.change_readonly(True)
        self.mode.change_readonly(True)
        self.AO_device = NI_AO_device(self.channel.val)
        self.AO_device.create_task()
        
    def disconnect(self):
        self.mode.change_readonly(False)
        self.channel.change_readonly(False)
        #disconnect hardware
        if hasattr(self, 'AO_device'):
            self.AO_device.close()
            del self.AO_device
        
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
            
    def start(self):
        if not hasattr(self.AO_device, 'task'):
            self.AO_device.create_task()
        
        self.AO_device.write_signal(self.mode.val, self.sample_mode.val,
                                    self.waveform.val,  
                                    self.num_periods.val, # self.rate.val,
                                    self.amplitude.val, 
                                    self.frequency.val,
                                    self.spike_amplitude.val,
                                    self.spike_duration.val,
                                    self.oversampling.val,
                                    self.offset.val) 
        self.AO_device.start_task()
        
    def stop(self):
        self.AO_device.stop_task()
        
    def detect_channels(self):
        ''' Find a NI device and return board + do_terminals'''
        system = ni.System.local()
        device = system.devices[0]
        board = device.product_type + ' : ' + device.name
        terminals = []
        for line in device.ao_physical_chans:
            terminals.append(line.name)
        return board, terminals
        
                    