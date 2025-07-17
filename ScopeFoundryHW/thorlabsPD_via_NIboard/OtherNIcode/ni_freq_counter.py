from ctypes import byref, c_uint32, c_int32
import numpy as np

import PyDAQmx
from PyDAQmx import DAQmx_Val_Rising, DAQmx_Val_CountUp, DAQmx_Val_ContSamps, DAQmxSetDigEdgeStartTrigSrc
from PyDAQmx import DAQmx_Val_Hz, DAQmx_Val_Low, DAQmx_Val_LargeRng2Ctr, DAQmx_Val_OverwriteUnreadSamps
from PyDAQmx import DAQmx_Val_DMA, DAQmx_Val_HighFreq2Ctr


SAMPLE_BUFFER_SIZE = 32768

class NI_FreqCounter(object):
    """ National Instruments DAQmx interface to a frequency counter
        Tested on an X-series PCIe DAQ card
    """
    
    def __init__(self, counter_chan="Dev1/ctr0", input_terminal = "/Dev1/PFI0", mode = "large_range", debug=False):
    
        self.counter_chan = counter_chan
        self.input_terminal = input_terminal
        self.debug = debug
        self.mode = mode
    
        assert mode in ['large_range', 'high_freq']
        
        self.create_task()
    
    def create_task(self):
    
        # need to check if task exists and fail
    
        self.task = PyDAQmx.Task()
        
        if self.mode == 'large_range':
            self.task.CreateCIFreqChan(
                counter = self.counter_chan ,
                nameToAssignToChannel="",
                minVal = 1e2, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                maxVal = 1e8, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                units = DAQmx_Val_Hz,
                edge = DAQmx_Val_Rising,
                measMethod = DAQmx_Val_LargeRng2Ctr,
                measTime = 0.01, # applies measMethod is DAQmx_Val_HighFreq2Ctr
                divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                customScaleName = None,
                )
        elif self.mode == 'high_freq':
            self.task.CreateCIFreqChan(
                counter = self.counter_chan ,
                nameToAssignToChannel="",
                minVal = 1e1, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                maxVal = 1e7, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                units = DAQmx_Val_Hz,
                edge = DAQmx_Val_Rising,
                measMethod = DAQmx_Val_HighFreq2Ctr,
                measTime = 0.01, # applies measMethod is DAQmx_Val_HighFreq2Ctr
                divisor = 100, # applies measMethod is DAQmx_Val_LargeRng2Ctr
                customScaleName = None,
                )
            
        
        data = c_int32(0)
        self.task.GetCIDataXferMech(channel=self.counter_chan, data=data )
        print ("XFmethod" , data.value)
        
        # set DMA
        #self.task.SetCIDataXferMech(channel=self.counter_chan, data=DAQmx_Val_DMA)
        
        self.task.GetReadOverWrite(data=byref(data))
        print ("overwrite", data.value)
        
        
        self.task.SetCIFreqTerm(
            channel = self.counter_chan,
            data = self.input_terminal)

        self.task.CfgImplicitTiming(
            sampleMode = DAQmx_Val_ContSamps,
            sampsPerChan = 1000)
            
        self.task.SetReadOverWrite(DAQmx_Val_OverwriteUnreadSamps)

        self.task.GetReadOverWrite(data=byref(data))
        print ("overwrite", data.value)
            
        self._sample_buffer_count = c_int32(0)
        self.sample_buffer = np.zeros((SAMPLE_BUFFER_SIZE,), dtype=np.float64)
        
        #self.task.StartTask()
    
    
    def start(self):
        self.task.StartTask()
    
    def stop(self):
        self.task.StopTask()
    
    def reset(self):
        self.task.StopTask()
        self.task.ClearTask()
        self.create_task()
        self.start()

    def read_freq_buffer(self):
        self.task.ReadCounterF64(
            numSampsPerChan = -1,
            timeout = 2.0,
            readArray = self.sample_buffer,
            arraySizeInSamps = SAMPLE_BUFFER_SIZE,
            sampsPerChanRead = byref(self._sample_buffer_count),
            reserved = None
            )
        
        return self._sample_buffer_count.value, self.sample_buffer

    def read_average_freq_in_buffer(self):
        num_samples, _buffer = self.read_freq_buffer()
        if self.debug: print (num_samples, _buffer)
        result =  np.average(_buffer[:num_samples])
        if np.isnan(result):
            return -1
        else:
            return result

    def close(self):
        if hasattr(self,'task'):
            self.task.StopTask()
            self.task.ClearTask()
    
    def __exit__(self, type_, value, traceback):
        self.close()
        return False
        
    def __enter__(self):
        return self
        
if __name__ == '__main__':
    import time
    
    with NI_FreqCounter(debug=True) as fc:

        for i in range(10):
            fc.start()
            time.sleep(0.1)
            hz = fc.read_average_freq_in_buffer()
            fc.stop()
            print ("%i: %e Hz" % (i, hz))
