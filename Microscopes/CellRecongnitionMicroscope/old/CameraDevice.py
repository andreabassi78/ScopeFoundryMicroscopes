
from PIL import Image
#import cv2
#import pyqtgraph as pg
import numpy as np
import time
#import CameraHardware
#from numpy import log2
# Hamamatsu constants.


class HamamatsuDevice(object):
    """
    Basic camera interface class.
    
    This version uses the Hamamatsu library to allocate camera buffers.
    Storage for the data from the camera is allocated dynamically and
    copied out of the camera buffers.
    """
    def __init__(self, frame_x, frame_y, acquisition_mode, number_frames, exposure, trigger,
                 subarrayh_pos, subarrayv_pos, binning, hardware):#extract_roi, dim_roi, min_cell_size, hardware): #camera_id = None, **kwds):
        """
        Open the connection to the camera specified by camera_id.
        """
        
        #self.frame_x = 0
        #self.frame_y = 0
        #self.last_frame_number = 0
        
        self.hardware = hardware #to have a communication between hardware and device, I create this attribute
        
        self.acquisition_mode = acquisition_mode
        self.number_frames = number_frames

        
       
        # Get camera max width, height.
        self.max_width = 406
        self.max_height = 447
        
        # Here we set the values in order to change these properties before the connection
        
        if __name__ != "__main__":
            
            self.setExposure(exposure)
            self.setSubarrayH(frame_x)
            self.setSubarrayV(frame_y)
            #self.setSubArrayMode()
            self.setTrigger(trigger)
            self.setSubarrayHpos(subarrayh_pos)
            self.setSubarrayVpos(subarrayv_pos)
            self.setBinning(binning)
            
            # self.setExtract_roi(extract_roi)
            # self.setDim_roi(dim_roi)
            # self.set_min_cell_size(min_cell_size)




    '''
    def captureSetup(self):
        """
        Capture setup (internal use only). This is called at the start
        of new acquisition sequence to determine the current ROI and
        get the camera configured properly.
        """
        #self.buffer_index = -1
        #self.last_frame_number = 0

        # Set sub array mode.
        self.setSubArrayMode()

        # Get frame properties.
        #self.frame_x = 406
        #self.frame_y = 447
        #self.frame_bytes = self.getPropertyValue("image_framebytes")[0]
        '''

    '''
    def getPropertiesValues(self):
        
        for i in self.properties:
            prop_attr = self.getPropertyValue(i)
            print("{} : {}".format(i, prop_attr[0]))
            '''

    def setExposure(self, exposure):
        
        self.exposure_time=exposure
        #if self.hardware.internal_frame_rate.hardware_read_func: #otherwise, if we have not defined yet the function, we have an error...
            #self.hardware.internal_frame_rate.read_from_hardware()
        
        
    def setSubarrayH(self, hsize):
        
        if hsize > self.max_width:
            print("Bigger than max range")
            return None
        
        if hsize % 4 != 0: #If the size is not a multiple of four, is not an allowed value
            hsize = hsize - hsize%4 #make the size a multiple of four
            
        """
        We must reset the value of the offset since sometimes it could happen that
        the program want to write a value of the offset while it's keeping in memory
        previous values of size, this could lead to an error if the sum of offset 
        and size overcome 2048
        """
        
        self.subarray_hpos=0 
        self.subarray_hsize=hsize
        
    
    
    def setSubarrayHpos(self, hpos):
        
        if hpos == 0: #Necessary for not showing the below message when we are at 2048 (subarray OFF)
            self.subarray_hpos=hpos
            return None
        
        
        if self.setSubArrayMode() == "OFF":
            print("You must be in subarray mode to change position")
            return None
        
        if hpos % 4 != 0: #If the size is not a multiple of four, is not an allowed value
            hpos = hpos - hpos%4 #make the size a multiple of four
        
        maximum = self.subarray_hpos #max value
        #if vpos > 1020: #If we have 4 pixel of size, the algorithm for the optimal position fails,
        # since the max value for the offset is 1020 (while with 4 pixels it tries to write 1022)
        if hpos > maximum:
            hpos = maximum
            
        self.subarray_hpos=hpos
    
    
    def setSubarrayV(self, vsize):
        
        if vsize > self.max_height:
            print("Bigger than max range")
            return None
        
        if vsize % 4 != 0:
            vsize = vsize - vsize%4
        
        """
        We must reset the value of the offset since sometimes it could happen that
        the program want to write a value of the offset while it's keeping in memory
        previous values of size, this coulde lead to an error if the sum of offset 
        and size overcome 2048
        """
        
        self.subarray_vpos=0 
        self.subarray_vsize=vsize
        

        
    
    def setSubarrayVpos(self, vpos):
        
        if vpos == 0: #Necessary for not showing the below message when we are at 2048 (subarray OFF)
            self.subarray_vpos=vpos
            return None
        
        
        if self.setSubArrayMode() == "OFF":
            print("You must be in subarray mode to change position")
            return None
        
        if vpos % 4 != 0: #If the size is not a multiple of four, is not an allowed value
            vpos = vpos - vpos%4 #make the size a multiple of four
            
        maximum = self.subarray_vpos #max value
        # if vpos > 1020: #If we have 4 pixel of size, the algorithm for the optimal position fails,
        # since the max value for the offset is 1020 (while with 4 pixels it tries to write 1022)
        if vpos > maximum:
            vpos = maximum
        
        self.subarray_vpos=vpos
        
    
    def setSubArrayMode(self):
        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.subarray_hsize
        roi_h = self.subarray_vsize

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            #self.subarray_mode='OFF'
            return "OFF"
        else:
            #self.subarray_mode='ON'
            return "ON"
        '''
        if self.getPropertyValue("subarray_mode")[0] == 1:
            return "OFF"
        else:
            return "ON"
    '''
    
    def setAcquisition(self, mode, number_frames = None):
#        self.stopAcquisition()
        '''
        Set the acquisition mode to either run until aborted or to 
        stop after acquiring a set number of frames.

        mode should be either "fixed_length" or "run_till_abort"

        if mode is "fixed_length", then number_frames indicates the number
        of frames to acquire.
        '''

        

        if mode is "fixed_length" or \
                mode is "run_till_abort":
            self.acquisition_mode = mode
            self.number_frames = number_frames

        else:
            print("Mode not valid")

            
        
    
    def setBinning(self, binning):
        
        self.binning=binning
    

    def setNumberImages(self, num_images):
#       self.stopAcquisition()
        if num_images < 1:
            print("The number of frames can't be less than 1.")
            return None
        else:
            self.number_frames = num_images
            
    def setTrigger(self, trigger):
        self.trigger=trigger
        
        
        
    # def setExtract_roi(self, extract_roi):
    #     self.extract_roi=extract_roi
        
    # def setDim_roi(self, dim_roi):        
    #     self.dim_roi=dim_roi
        
    # def set_min_cell_size(self,min_cell_size):
    #     self.min_cell_size=min_cell_size
        
        
        
        

    def read_image(self, path, filename):
        
        #path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
        #filename = 'selected_stack'
        img = Image.open(path+filename+'.tif')
        return img
        
    def get_image(self, img, i):
        '''
        self.setSubArrayMode()
        
        n_images = self.number_frames
        
        if self.acquisition_mode is "run_till_abort":
        
        else self.acquisition_mode is "fixed_length":
        '''
        
        #FORSE FUNZIONE NON è AUTORIZZATA A CAMBIARE i...PROVARE!
        if i == img.n_frames:
            i=0
            
        img.seek(i)
        return np.uint16(img)





#======================================================================================================================================================
    

if __name__ == "__main__":
    
    import sys
    import pyqtgraph as pg
    import qtpy
    from qtpy.QtWidgets import QApplication 

    path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
    filename = 'selected_stack'           
    
    hamamatsu = HamamatsuDevice(frame_x=406, frame_y=447, acquisition_mode="fixed_length", 
                                           number_frames=1, exposure=0.01, 
                                           trigger="TRUE",
                                           subarrayh_pos=0, subarrayv_pos = 0,
                                           binning = 1, #extract_roi="TRUE", 
                                           #dim_roi=150, min_cell_size=1600,
                                           hardware = None)
    
    np_data = hamamatsu.read_image(path, filename)
    im=hamamatsu.get_image(np_data, i=1)
    print (im)
    pg.image(np.reshape(np_data,(406, 447)).T)
    
    
    
    











