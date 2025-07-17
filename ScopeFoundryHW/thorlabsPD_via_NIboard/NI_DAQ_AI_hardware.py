"""Written by Andrea Bassi (Politecnico di Milano) 15-August-2018
to control the Analog Input of a  NI USB-6212 board (it should work for any NI-DAQmx board)
This is a Hardware class compatible with ScopeFoundry
"""
#import numpy as np

from ScopeFoundry import HardwareComponent

from thorlabsPD_via_NIboard.NI_DAQ_AI_device import NI_DAQ_AI_Device
 
class NI_DAQ_AI_HW(HardwareComponent):
    
    name = 'NI_DAQ_AI_HW'
    
    def setup(self):
        
        self.channel = self.add_logged_quantity('channel', dtype=str, initial='Dev1/ai1')     
        self.readout = self.add_logged_quantity('readout', dtype=float, si=False, ro=1, unit='V',initial=0)
        self.multiple = self.add_logged_quantity('multiple_samples', dtype=bool, si=False, ro=0, initial=True)
        self.sampling_freq = self.add_logged_quantity('sampling_freq', dtype=float, si=False, ro=0, unit='Hz',initial=1000)
        self.samples_size = self.add_logged_quantity('samples_size', dtype=int, si=False, ro=0, initial=100)
        
        self.data= [] # data will be in a list, initially empty
        # np.empty(self.samples_size.val, dtype=float)
        
        
    def connect(self):
        
        # open connection to hardware
        self.channel.change_readonly(True)
        self.AI_device = NI_DAQ_AI_Device(channel=self.channel.val, debug=self.debug_mode.val)
       
        # connect logged quantities        
        self.readout.hardware_read_func = self.AI_device.read_single_NI_DAQ_AI
        
        self.sampling_freq.hardware_set_func=self.AI_device.set_NI_DAQ_AI_freq       
        
    def disconnect(self):
        self.channel.change_readonly(False)
        #disconnect hardware
        #self.laser.close()
        if hasattr(self, 'AI_device'):
            self.AI_device.close()         
            del self.AI_device
        
        #disconnect logged quantities from hardware
        #for lq in self.logged_quantities.values():
        #    lq.hardware_read_func = None
        #    lq.hardware_set_func = None
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        # del self.laser

        