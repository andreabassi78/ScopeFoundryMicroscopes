"""Written by Andrea Bassi (Politecnico di Milano) 1-August-2018
to control Coherent Sapphire Lasers (Device)
"""
from __future__ import division, print_function
import serial

class SapphireLaserDevice(object):

    def __init__(self, port, debug=False, dummy=False): #change port according to device listing in windows.
        
        self.debug = debug
        self.dummy = dummy
        self.port = port
        
        if not self.dummy:

            self.ser = ser = serial.Serial(port=self.port, baudrate=19200, 
                                           bytesize=8, parity='N', 
                                           stopbits=1, xonxoff=False, timeout=3.0)
            ser.flush()
            ser.flush()
            
    def close(self):
        self.ser.close()

    def write_cmd(self, cmd):
        serialcmd = cmd+'\r\n'
        self.ser.write(serialcmd.encode())
        echo = self.ser.readline()
        response = self.ser.readline()
        
        if self.debug:
            print ('write:', repr(serialcmd))
            print ('echo:', echo)
            print ('response:', response)
        if 'Error'.encode() in response:
            raise IOError('Sapphire laser command error:' + repr(response))
        return response
    
    def read_power(self):
        """Reads the actual power"""
        fullresp = self.write_cmd('?P')
        resp=float(fullresp.decode('utf-8'))
        return resp
    
    def write_power(self,power):
        """Sets the laser power"""
        pw=str(int(power))
        #print(self.write_cmd('?L'))
        return self.write_cmd('P='+pw)
    
    def read_temperature(self):
        """Reads the diode temperature"""
        fullresp = self.write_cmd('?DT')
        resp=float(fullresp.decode('utf-8'))      
        return resp
    
    def turn_powerON(self,active=False):
        """Allows user to turn the laser on or off"""
        if active:
            return self.write_cmd('L=1')
        else:
            return self.write_cmd('L=0')
      
if __name__ == '__main__':

    try:    
        laser = SapphireLaserDevice(port='COM14', debug=False)
        
        print(laser.read_temperature())
        print(laser.read_power())
        #print(laser.turn_powerON(True))
        #print(laser.write_power(10))
        
        
    except Exception as err:
        print(err)
    finally:
        laser.close()
    
