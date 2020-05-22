"""Written by Andrea Bassi (Politecnico di Milano) 1-August-2018
to control Coherent Sapphire Lasers (Hardware)
"""
from ScopeFoundry import HardwareComponent

from sapphire_laser.sapphire_device import SapphireLaserDevice
 
class SapphireLaserHW(HardwareComponent):
    
    name = 'SapphireLaser'
    
    def setup(self):
        self.port = self.add_logged_quantity('port', dtype=str, initial='COM14')     
        #ON OFF button
        self.powerON = self.add_logged_quantity('laserON', dtype=bool) 
        #shows and sets the laser power (the same panel is used for setting and reading!)
        self.power = self.add_logged_quantity('power', dtype=float, si=False, ro=0, unit='mW')
        #shows the diode temperature in deg Celsius
        self.temperature = self.add_logged_quantity('temperature', dtype=float, si=False, ro=0, unit=chr(176)+'C')  
        
    def connect(self):
        
        # open connection to hardware
        self.port.change_readonly(True)
        self.laser = SapphireLaserDevice(port=self.port.val, debug=self.debug_mode.val)
       
        # connect logged quantities        
        self.powerON.hardware_set_func = self.laser.turn_powerON
        self.power.hardware_set_func = self.laser.write_power
        self.power.hardware_read_func = self.laser.read_power
        self.temperature.hardware_read_func = self.laser.read_temperature

    def disconnect(self):
        self.port.change_readonly(False)
        #disconnect hardware
        #self.laser.close()
        if hasattr(self, 'laser'):
            self.laser.close()         
            del self.laser
        
        #disconnect logged quantities from hardware
        #for lq in self.logged_quantities.values():
        #    lq.hardware_read_func = None
        #    lq.hardware_set_func = None
        for lq in self.settings.as_list():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        # clean up hardware object
        # del self.laser

        