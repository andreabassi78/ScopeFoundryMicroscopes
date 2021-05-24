from ScopeFoundry import HardwareComponent

from NIdaqmx_ScopeFoundry.ni_co_device import NI_CO_device

import nidaqmx.system as ni

class NI_CO_hw(HardwareComponent):
    
    name = 'NI_CO_hw' 
    
    def setup(self):
        #create logged quantities, that are related to the graphical interface
        board, terminals, trig=self.update_channels()
        
        self.devices = self.add_logged_quantity('device',  dtype=str, initial=board)        
        self.channel = self.add_logged_quantity('channel', dtype=str, choices=terminals, initial=terminals[0])
        self.initial_delay = self.add_logged_quantity('initial_delay', dtype=float, initial=0, vmin=0, spinbox_decimals=6, unit='s')
        self.freq = self.add_logged_quantity('freq', dtype = float, si = False, ro = 0, initial = 100, vmin=1, spinbox_decimals=6, unit='Hz')
        self.duty_cycle = self.add_logged_quantity('duty_cycle', dtype=float, initial=0.5, vmin=0, vmax=1)
        self.trigger=self.add_logged_quantity('trigger',dtype=bool, initial=False)
        self.trigger_source= self.add_logged_quantity('trigger_source', dtype=str, choices=trig, initial=trig[0])
        self.trigger_edge= self.add_logged_quantity('trigger_edge', dtype=str, choices=['rising', 'falling'], initial='rising')
       
        
        self.add_operation("start_task", self.start)
        self.add_operation("stop_task", self.stop)
        
    def connect(self):
        #continuous_to_constant = {False:10178, True:10123} #create a dictionary for mapping the mode with the corresponding constants in nidaqmx
            
        #open connection to hardware
        self.channel.change_readonly(True)
        self.CO_device = NI_CO_device(channel=self.channel.val, initial_delay=self.initial_delay.val, freq=self.freq.val, duty_cycle=self.duty_cycle.val, trigger=self.trigger.val,
                                      trigger_source=self.trigger_source.val, trigger_edge=self.trigger_edge.val, debug=self.debug_mode.val)
        
        #connect logged quantities
        self.initial_delay.hardware_set_func = self.CO_device.set_initial_delay
        self.freq.hardware_set_func = self.CO_device.set_freq
        self.duty_cycle.hardware_set_func = self.CO_device.set_duty_cycle
        self.trigger.hardware_set_func = self.CO_device.set_trigger
        self.trigger_source.hardware_set_func = self.CO_device.set_trigger_source
        self.trigger_edge.hardware_set_func = self.CO_device.set_trigger_edge
        
        self.initial_delay.hardware_read_func = self.get_initial_delay
        self.freq.hardware_read_func = self.get_freq
        self.duty_cycle.hardware_read_func = self.get_duty_cycle
        self.trigger.hardware_read_func = self.get_trigger
        self.trigger_source.hardware_read_func = self.get_trigger_source
        self.trigger_edge.hardware_read_func = self.get_trigger_edge
        
        
        
    def disconnect(self):
        self.channel.change_readonly(False)
        #disconnect hardware
        if hasattr(self, 'CO_device'):
            self.CO_device.close()
            del self.CO_device
        
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
            
    def start(self):
        
        self.CO_device.start_task()
        
    def stop(self):
        
        self.CO_device.stop_task()
    
    def update_channels(self):
        ''' Find a NI device and return board + do_terminals + trigger terminals'''
        system = ni.System.local()
        device=system.devices[0]
        board=device.product_type + ' : ' + device.name
        terminals=[]
        trig=[]
        for line in device.co_physical_chans:
            terminals.append(line.name)
        for j in device.terminals:
            if 'PFI' in j:
                trig.append(j)
                
        return board, terminals, trig
    
    def get_initial_delay(self):

        return float("{0:.6f}".format(self.initial_delay.val))
    
    def get_freq(self):

        return float("{0:.6f}".format(self.freq.val))
    
    def get_duty_cycle(self):
        
        return float("{0:.2f}".format(self.duty_cycle.val))
    
    def get_trigger(self):
        
        return self.trigger.val
    
    def get_trigger_source(self):

        return self.trigger_source.val
    
    def get_trigger_edge(self):
        
        return self.trigger_edge.val
            
        
                    