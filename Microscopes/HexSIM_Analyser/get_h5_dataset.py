"""Written by Andrea Bassi (Politecnico di Milano) 10 August 2018
to find the location of datasets in a h5 file.
"""

import h5py
import numpy as np

def get_dataset(fname, dataset_index=0):
        """Returns the DataSet within the HDF5 file and its shape. Found gives the number of dataset found"""
        
        try:
            f = h5py.File(fname,'r')
        
            name,shape,found = get_h5_item_structure(f, name=[], shape=[], found = 0)
            
            assert found > 0, "Specified h5 file does not exsist or have no datasets"
            
            if dataset_index >= found:    
                dataset_index = 0
            
            stack = (np.single(f[name[dataset_index]]))
        
        finally:
            f.close()

        return stack
    
def get_h5_item_structure(g, name, shape, found) :
        """Extracts the dataset location (and its shape) and it is operated recursively in the h5 file subgroups  """
                
        if   isinstance(g,h5py.File):
            found=found #this and others are unnecessary, but left for future modifications
               
        elif isinstance(g,h5py.Dataset):
           
            found=found+1
            name.append(g.name)
            shape.append(g.shape)
               
        elif isinstance(g,h5py.Group):
            found=found
            
        else :
            found=found
     
        if isinstance(g, h5py.File) or isinstance(g, h5py.Group) :
           
            for key,val in dict(g).items() :
                subg = val
                
                name,shape,found = get_h5_item_structure(subg,name,shape,found)
                 
        return name,shape,found 

           
            
"""The following is only to test the functions.
It will find a dataset and display it
"""     
if __name__ == "__main__" :
    
        import sys
        import pyqtgraph as pg
        import qtpy.QtCore
        from qtpy.QtWidgets import QApplication
        
        # this h5 file must contain a dataset composed by an array or an image
        file_name='D:\\data\\PROCHIP\\temp\\test.h5'
        
        stack = get_dataset(file_name)    
    
            
        pg.image(stack, title="Stack of images")        
               
        #keeps the window open running a QT application
        if sys.flags.interactive != 1 or not hasattr(qtpy.QtCore, 'PYQT_VERSION'):
            QApplication.exec_()
                          
   
        sys.exit ( "End of test")