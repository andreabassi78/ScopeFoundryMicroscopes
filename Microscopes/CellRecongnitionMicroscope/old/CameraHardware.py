

from ScopeFoundry import HardwareComponent
#import CameraDevice
from CameraDevice import HamamatsuDevice


class HamamatsuHardware(HardwareComponent):
    
    name = "HamamatsuHardware"
    
    def setup(self):
        
        
       
        
        self.exposure_time = self.add_logged_quantity('exposure_time', dtype = float, si = False, ro = 0, 
                                                       spinbox_step = 0.01, spinbox_decimals = 6, initial = 0.01, unit = 's', reread_from_hardware_after_write = True,
                                                       vmin = 0)
        
        self.internal_frame_rate = self.add_logged_quantity('internal_frame_rate', dtype = float, si = False, ro = 1,
                                                            initial = 0, unit = 'fps')
        
        self.acquisition_mode = self.add_logged_quantity('acquisition_mode', dtype = str, ro = 0, 
                                                         choices = ["fixed_length", "run_till_abort"], initial = "run_till_abort")
        
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, 
                                                      initial = 200, vmin = 1)
        
        #For subarray we have imposed float, since otherwise I cannot modify the step (I should modify the logged quantities script, but I prefer left it untouched)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=float, si = False, ro= 0,
                                                   spinbox_step = 4, spinbox_decimals = 0, initial = 406, vmin = 4, vmax = 406, reread_from_hardware_after_write = True)
        
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=float, si = False, ro= 0, 
                                                  spinbox_step = 4, spinbox_decimals = 0, initial = 447, vmin = 4, vmax = 447, reread_from_hardware_after_write = True)
        
        self.submode = self.add_logged_quantity("subarray_mode", dtype=str, si = False, ro = 1, choices = ["ON", "OFF"],
                                                initial = 'ON')
        
        self.subarrayh_pos = self.add_logged_quantity('subarrayh_pos', dtype = float, si = False, ro = 0,
                                                      spinbox_step = 4, spinbox_decimals = 0, initial = 0, vmin = 0, vmax = 402, reread_from_hardware_after_write = True,
                                                      description = "The default value 0 corresponds to the first pixel starting from the left")
        
        self.subarrayv_pos = self.add_logged_quantity('subarrayv_pos', dtype = float, si = False, ro = 0,
                                                      spinbox_step = 4, spinbox_decimals = 0, initial = 0, vmin = 0, vmax = 443, reread_from_hardware_after_write = True,
                                                      description = "The default value 0 corresponds to the first pixel starting from the top")
        
        
        
        self.binning = self.add_logged_quantity('binning', dtype = int, ro = 0,
                                                choices = [1, 2, 4], initial = 1, reread_from_hardware_after_write = True )
        
        self.trigger = self.add_logged_quantity('trigger', dtype=bool, si=False, ro=0, 
                                                 initial = 'True', reread_from_hardware_after_write = True)
        
        
        
        # self.extract_roi = self.add_logged_quantity ('extract_roi', dtype=bool, ro=0, initial=False, reread_from_hardware_after_write = True)
        # self.dim_roi = self.add_logged_quantity ('dim_roi', dtype=float, si = False, ro= 0,
        #                                            spinbox_step = 4, spinbox_decimals = 0, initial = 150, vmin = 4, vmax = 300, reread_from_hardware_after_write = True)
        # self.min_cell_size = self.add_logged_quantity ('min_cell_size', dtype=float, si = False, ro= 0,
        #                                            spinbox_step = 4, spinbox_decimals = 0, initial = 1600, vmin = 4, vmax = 22500, reread_from_hardware_after_write = True)

        
        
#         self.preset_sizes = self.add_logged_quantity('preset_sizes', dtype=str, si=False, ro = 0, 
#                                                      choices = ["2048x2048",
#                                                                 "2048x1024",
#                                                                 '2048x512'
#                                                                 '2048x256'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 '2048x'
#                                                                 ''
#                                                                 ''
#                                                                 ''
#                                                                 ''
#                                                                 ''
#                                                                 ''
#                                                                 ])

    
    def connect(self):
        """
        The initial connection does not update the value in the device,
        since there is no set_from_hardware function, so the device has
        as initial values the values that we initialize in the HamamatsuDevice
        class. I'm struggling on how I can change this. There must be some function in
        ScopeFoundry
        """
        
        #self.trsource.change_readonly(True)
        #self.trmode.change_readonly(True)
        #self.trpolarity.change_readonly(True)
        #self.acquisition_mode.change_readonly(True) #if we change from run_till_abort to fixed_length while running it crashes
        
        
        self.hamamatsu = HamamatsuDevice(frame_x=self.subarrayh.val, frame_y=self.subarrayv.val, acquisition_mode=self.acquisition_mode.val, 
                                           number_frames=self.number_frames.val, exposure=self.exposure_time.val, 
                                           trigger=self.trigger.val, 
                                           subarrayh_pos=self.subarrayh_pos.val, subarrayv_pos = self.subarrayv_pos.val,
                                           binning = self.binning.val, 
                                           #extract_roi = self.extract_roi.val, dim_roi = self.dim_roi.val,
                                           #min_cell_size = self.min_cell_size.val,
                                           hardware = self) #maybe with more cameras we have to change
        
        print(self.hamamatsu.number_frames)
        '''
        self.submode.hardware_read_func = self.hamamatsu.setSubArrayMode
        self.exposure_time.hardware_read_func = self.hamamatsu.exposure_time
        self.trigger.hardware_read_func = self.hamamatsu.trigger
        self.subarrayh.hardware_read_func = self.hamamatsu.subarray_hsize
        self.subarrayv.hardware_read_func = self.hamamatsu.subarray_vsize
        self.subarrayh_pos.hardware_read_func = self.hamamatsu.subarray_hpos
        self.subarrayv_pos.hardware_read_func = self.hamamatsu.subarray_vpos
        self.binning.hardware_read_func = self.hamamatsu.binning
        '''
        
        #SE DECOMMENTO PARTE SOPRA MI DA ERRORE -> RIMETTERE I GETBLABLABLA (vedi codice originale)
        
        
        self.subarrayh.hardware_set_func = self.hamamatsu.setSubarrayH
        self.subarrayv.hardware_set_func = self.hamamatsu.setSubarrayV
        self.subarrayh_pos.hardware_set_func = self.hamamatsu.setSubarrayHpos
        self.subarrayv_pos.hardware_set_func = self.hamamatsu.setSubarrayVpos
        self.exposure_time.hardware_set_func = self.hamamatsu.setExposure
        #self.acquisition_mode.hardware_set_func = self.hamamatsu.setAcquisition
        self.number_frames.hardware_set_func = self.hamamatsu.setNumberImages
        self.trigger.hardware_set_func = self.hamamatsu.setTrigger
        self.binning.hardware_set_func = self.hamamatsu.setBinning
        
        # self.extract_roi.hardware_set_func = self.hamamatsu.setExtract_roi
        # self.dim_roi.hardware_set_func = self.hamamatsu.setDim_roi
        # self.min_cell_size.hardware_set_func = self.hamamatsu.set_min_cell_size
        
        
        self.read_from_hardware() #read from hardware at connection
        
#         self.subarrayh.update_value(2048)
#         self.subarrayv.update_value(2048)
#         self.exposure_time.update_value(0.01)
#         self.acquisition_mode.update_value("fixed_length")
#         self.number_frames.update_value(2)
   
    def disconnect(self):
        
        #self.trsource.change_readonly(False)
        #self.trmode.change_readonly(False)
        #self.trpolarity.change_readonly(False)
        
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'hamamatsu'):
            del self.hamamatsu

            