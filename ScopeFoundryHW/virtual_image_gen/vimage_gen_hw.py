from ScopeFoundry import HardwareComponent
from vimage_gen_device import VirtualImageGenDevice
import numpy as np


class VirtualImageGenHW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'virtual_image_gen'
    
    def setup(self):
        # Define your hardware settings here.
        # These settings will be displayed in the GUI and auto-saved with data files
                
        self.settings.New(name='amplitude', initial=1.0, dtype=float, ro=False)
        self.settings.New(name='size', initial=200, dtype=int, ro=False)
        self.settings.New(name='signal_type', choices=('sine','rect'), initial = 'sine', dtype=str, ro=False)
        self.add_operation('change_type', self.change_to)
       
        self.image_data=  np.empty([self.settings['size'],self.settings['size']], dtype=np.uint16)
            
 
    def change_to(self, stype= 'sine'):
        
        print((self.settings.signal_type.choices))
        print((self.settings.signal_type.value))
        
        if self.settings.signal_type.val == 'sine':
            self.settings['signal_type'] = 'rect'
            print('changed to rect')
        else:
            self.settings['signal_type'] = 'sine'
            print('changed to sine')
 
    
 
    def connect(self):
        # Open connection to the device:
        self.vimage_gen_dev = VirtualImageGenDevice(amplitude=self.settings['amplitude'])
        
        # Connect settings to hardware:
        self.settings.amplitude.connect_to_hardware(
            write_func = self.vimage_gen_dev.write_amp
            )
        
        self.settings.size.connect_to_hardware(
            write_func  = self.vimage_gen_dev.write_size
            )
         
                            
        #Take an initial sample of the data.
        self.read_from_hardware()
        
    def disconnect(self):
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'vimage_gen_dev'):
            del self.vimage_gen_dev