from ScopeFoundry import HardwareComponent
from FakeCameraDevice import FakeCameraDevice


class FakeCameraHardware(HardwareComponent):
    
    name = "FakeCameraHardware"
    
    def setup(self):
        
        
        self.number_frames = self.add_logged_quantity("number_frames", dtype = int, si = False, ro = 0, 
                                                      initial = 200, vmin = 1)
        
        #For subarray we have imposed float, since otherwise I cannot modify the step (I should modify the logged quantities script, but I prefer left it untouched)
        self.subarrayh = self.add_logged_quantity("subarray_hsize", dtype=float, si = False, ro= 0,
                                                   spinbox_step = 4, spinbox_decimals = 0, initial = 406, vmin = 4, vmax = 406, reread_from_hardware_after_write = True)
        
        self.subarrayv = self.add_logged_quantity("subarray_vsize", dtype=float, si = False, ro= 0, 
                                                  spinbox_step = 4, spinbox_decimals = 0, initial = 447, vmin = 4, vmax = 447, reread_from_hardware_after_write = True)
    
        self.path = self.add_logged_quantity('path', 
                                             dtype = str, si = False, ro = 0,
                                             initial = 'C:\\Users\\Andrea Bassi\\OneDrive - Politecnico di Milano\\Data\\PROCHIP\\Throughput_video\\'
                                             #initial = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
                                             )
        self.filename = self.add_logged_quantity('filename', 
                                             dtype = str, si = False, ro = 0,
                                             initial = 'selected_stack'
                                             )
        
    
    def connect(self):
        """
        The initial connection does not update the value in the device,
        since there is no set_from_hardware function, so the device has
        as initial values the values that we initialize in the HamamatsuDevice
        class. I'm struggling on how I can change this. There must be some function in
        ScopeFoundry
        """
        
        self.fakecamera = FakeCameraDevice(self.path.val+self.filename.val) #maybe with more cameras we have to change
                
        self.subarrayv.hardware_read_func = self.fakecamera.get_v_size
        self.subarrayh.hardware_read_func = self.fakecamera.get_h_size
                
        self.read_from_hardware() #read from hardware at connection
        
   
    def disconnect(self):
        
        self.settings.disconnect_all_from_hardware()
        
        if hasattr(self, 'fakecamera'):
            del self.fakecamera

            