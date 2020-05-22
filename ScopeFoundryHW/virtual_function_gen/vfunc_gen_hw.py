from ScopeFoundry import HardwareComponent
from vfunc_gen_device import VirtualFunctionGenDevice


class VirtualFunctionGenHW(HardwareComponent):
    
    ## Define name of this hardware plug-in
    name = 'virtual_function_gen'
    
    def setup(self):
        # Define your hardware settings here.
        # These settings will be displayed in the GUI and auto-saved with data files
        self.settings.New(name='amplitude', initial=1.0, dtype=float, ro=False)
        self.settings.New(name='rand_data', initial=0, dtype=float, ro=True)
        self.settings.New(name="sine_data", initial=0, dtype=float, ro=True)
        self.settings.New(name="square_data", initial=0, dtype=float, ro=True)
    
    def connect(self):
        # Open connection to the device:
        self.vfunc_gen_dev = VirtualFunctionGenDevice(amplitude=self.settings['amplitude'])
        
        # Connect settings to hardware:
        self.settings.amplitude.connect_to_hardware(
            write_func = self.vfunc_gen_dev.write_amp
            )
        self.settings.rand_data.connect_to_hardware(
            read_func  = self.vfunc_gen_dev.read_rand_num
            )
        self.settings.sine_data.connect_to_hardware(
            read_func  = self.vfunc_gen_dev.read_sine_wave
            )
        
        self.settings.square_data.connect_to_hardware(
            read_func = self.vfunc_gen_dev.read_square_wave
            )
        
        #Take an initial sample of the data.
        self.read_from_hardware()
        
    def disconnect(self):
        # remove all hardware connections to settings
        self.settings.disconnect_all_from_hardware()
        
        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'vfunc_gen_dev'):
            del self.vfunc_gen_dev