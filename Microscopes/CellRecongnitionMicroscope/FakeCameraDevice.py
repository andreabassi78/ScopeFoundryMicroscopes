from PIL import Image
import numpy as np
#import time

class FakeCameraDevice(object):
    """
    Basic fake camera interface class.
    """
    
    def __init__(self, filename):#extract_roi, dim_roi, min_cell_size, hardware): #camera_id = None, **kwds):
        self.img = Image.open(filename+'.tif')
        self.image_index = 0
       
    def get_image(self):
        
        #print(self.image_index)
        
        if self.image_index == self.img.n_frames:
            self.image_index=0
            
        self.img.seek(self.image_index)
        self.image_index +=1
        
        return np.uint16(self.img)

    def get_v_size(self):
        return self.img.size[0]
            
    def get_h_size(self):
        return self.img.size[1]
        

if __name__ == "__main__":
    
    #import pyqtgraph as pg
    path = 'C:\\Users\\Andrea Bassi\\OneDrive - Politecnico di Milano\\Data\\PROCHIP\\Throughput_video\\'  
    #path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
    filename = 'selected_stack'           
    #filename = 'dual_color_stack'
    camera = FakeCameraDevice(path+filename)
   
    np_data = camera.get_image()
    #print (np_data)
    print(camera.get_v_size())
    
    











