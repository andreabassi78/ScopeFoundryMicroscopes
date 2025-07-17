"""Written by Andrea Bassi (Politecnico di Milano) 15-August-2018
to control the Analog Input of a  NI USB-6212 board (it should work for any NI-DAQmx board).
This is a Device class compatible with ScopeFoundry.
It use nidaqmx, that is the package maintained by National Instruments for controlling NI-DAQmx with Python 
Other packages (PyDAQmx) could have been used,but they are not maintained by National Instruments
"""
from __future__ import division, print_function
import nidaqmx
import time
import warnings
#import numpy as np


class NI_DAQ_AI_Device(object):

    def __init__(self, channel, debug=False, dummy=False):
        
        self.debug = debug
        self.dummy = dummy
        self.channel = channel
        
        if not self.dummy:

            #self.task= nidaqmx.Task()
            #self.task.close()
            
            self.task= nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(channel)
            
    def close(self):
        self.task.close()
        #print("NI DAQ task closed")
        
    def stop_NI_DAQ_AI(self):
        """Reads a certain number of samples from the board"""
        #suppress Warning that might occur when task is stopped during acquisition
        warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)
        resp=self.task.stop()
        warnings.filterwarnings('default', category=nidaqmx.DaqWarning)
        return resp
               
     
    def read_single_NI_DAQ_AI(self):
        """Reads a single sample from the board, on demand"""
        #suppress warnings that are due to 
        #warnings.filterwarnings('ignore', category=nidaqmx.DaqWarning)
       
        resp=self.task.read(number_of_samples_per_channel=1)
        return resp[0]
    
    def read_NI_DAQ_AI(self,num_samples):
        """Reads a certain number of samples from the board"""
        resp=self.task.read(number_of_samples_per_channel=num_samples)
        return resp
    
    def set_NI_DAQ_AI_freq(self, acq_rate):
        """Sets the AI acquisition rate"""
        
        #if self.task.is_task_done()==False:
        #    self.task.wait_until_done(10)      
        self.stop_NI_DAQ_AI()
        self.task.timing.cfg_samp_clk_timing(rate = acq_rate)
        
        #else:
            #self.set_NI_DAQ_AI_freq(acq_rate)
        #    print("waiting task to finish")
            
            
# The following is just to try if the device works properly          
if __name__ == '__main__':

    try:    
        
        board = NI_DAQ_AI_Device(channel="Dev1/ai1", debug = False)
        board.set_NI_DAQ_AI_freq(100)
        valueslist=board.read_NI_DAQ_AI(10)
        
        print(valueslist)
        
    except Exception as err:
        print(err)
    finally:
        board.close()
    
