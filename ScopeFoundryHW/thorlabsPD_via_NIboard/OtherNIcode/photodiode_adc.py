'''
Created on 07/31, 2018

@author: Schuck Lab M1
'''
from ScopeFoundry import HardwareComponent
from PyDAQmx.DAQmxTypes import bool32
try:
    from ScopeFoundryEquipment.NI_Daq import Adc
except Exception as err:
    print("Cannot load required modules for photodiode read by NI:", err)
    
import time
import random

class PhotodiodeADCHW(HardwareComponent):

    name = "photodiode_adc"

    def setup(self):

        # Create logged quantities
        self.adc_voltage = self.add_logged_quantity(
                                name = 'adc voltage', 
                                initial = 0,
                                dtype=float, fmt="%e", ro=True,
                                si=False, unit="mV",
                                vmin=-1e4, vmax=1e4)
        
        self.adc_rate = self.add_logged_quantity(
                                name = 'adc_rate',
                                initial= 1e3,
                                dtype=float, fmt="%e", ro=False,
                                unit = "Hz",
                                vmin = 1, vmax=1e4)
        
        self.adc_count = self.add_logged_quantity(
                                name = 'adc_count',
                                initial= 1e3,
                                dtype=float, fmt="%e", ro=False,
                                vmin = 1, vmax=1e5)
        
        self.adc_finite = self.add_logged_quantity(
                                name = 'adc_finite',
                                initial = True,
                                dtype = bool, ro= False )
        

        self.dummy_mode = self.add_logged_quantity(name='dummy_mode', dtype=bool, initial=False, ro=False)
        

    def connect(self):
        
        if self.debug_mode.val: print("Connecting to photodiode NI ADC")
        
        # Open connection to hardware

        if not self.dummy_mode.val:
            # Normal APD:  "/Dev1/PFI0"
            # APD on monochromator: "/Dev1/PFI2"
            self.pd_adc = Adc(channel =  '/Dev1/AI0', range = 10.0, name = 'test', terminalConfig='default'  )
            #self.ni_counter = NI_FreqCounterUSB(debug = self.debug_mode.val, mode='large_range', input_terminal = "/Dev1/PFI0")
        else:
            if self.debug_mode.val: print("Connecting to photodiode NI ADC (Dummy Mode)")

        # connect logged quantities
        if self.adc_finite:
            self.set_ADC_finite()
        else:
            self.set_ADC_continous()
            
        self.adc_voltage.hardware_read_func = self.read_single_voltage
        self.adc_rate.hardware_set_func = self.set_adc_rate
        self.adc_rate.hardware_read_func = self.read_adc_rate
        self.adc_count.hardware_set_func = self.set_adc_count
        
        self.read_from_hardware()
        
    def set_ADC_continous(self):
        self.adc_finite_val = False
        self.adc_rate_val = self.adc_rate.value
        self.adc_count_val = self.adc_count.value
        self.pd_adc.set_rate(rate = self.adc_rate_val, count = self.adc_count_val, finite = self.adc_finite_val)
        
    def set_ADC_finite(self):
        self.adc_finite_val = True
        self.adc_rate_val = self.adc_rate.value
        self.adc_count_val = self.adc_count.value
        self.pd_adc.set_rate(rate = self.adc_rate_val, count = self.adc_count_val, finite = self.adc_finite_val)
    
    def read_single_voltage(self):
        self.pd_adc.set_single()
        data_voltage = 1e3*self.pd_adc.get() # in mV
        return data_voltage 
    
    def set_adc_rate(self, rate_to_set):
        self.adc_rate_val = rate_to_set
        self.adc_count_val = self.adc_count.value
        self.adc_finite_val = self.adc_finite.value
        new_rate = self.pd_adc.set_rate(rate = self.adc_rate_val, count = self.adc_count_val, finite = self.adc_finite_val)
        return new_rate
    
    def read_adc_rate(self):
        self.adc_rate_val = self.adc_rate.value
        self.adc_count_val = self.adc_count.value
        self.adc_finite_val = self.adc_finite.value
        new_rate = self.pd_adc.set_rate(rate = self.adc_rate_val, count = self.adc_count_val, finite = self.adc_finite_val)
        return new_rate
        
    def set_adc_count(self, count_to_set):
        self.adc_rate_val = self.adc_rate.value
        self.adc_count_val = count_to_set
        self.adc_finite_val = self.adc_finite.value
        new_rate = self.pd_adc.set_rate(rate = self.adc_rate_val, count = self.adc_count_val, finite = self.adc_finite_val)
        return new_rate
        
        

    def disconnect(self):
        
        #disconnect logged quantities from hardware
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None

        if hasattr(self, 'pd_adc'):
            #disconnect hardware
            self.pd_adc.close()
    
            # clean up hardware object
            del self.pd_adc
        