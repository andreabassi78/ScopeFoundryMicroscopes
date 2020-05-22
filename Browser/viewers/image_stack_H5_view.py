"""Written by Andrea Bassi (Politecnico di Milano) 10 August 2018:
viewer compatible with Scopefoundry DataBrowser.
Finds an imaging dataset (3D stack of images) in the h5 file
If multiple datasets are found by the function find_h5dataset, the browser will show the first dataset found  
"""

from ScopeFoundry.data_browser import DataBrowser, DataBrowserView
from qtpy import QtWidgets
import h5py
import pyqtgraph as pg
import numpy as np
import os
from viewers.find_h5_dataset import find_dataset

class ImageStackH5(DataBrowserView):

    name = 'stack_h5_view'
    
    def setup(self):
        
        self.settings.New('Frame rate', dtype=float, initial=10)
        self.settings.get_lq('Frame rate').add_listener(self.update_display)
        
        self.settings.New('Play', dtype=bool, initial= False)
        self.settings.get_lq('Play').add_listener(self.update_display)
        
        
        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QVBoxLayout())
        self.ui.layout().addWidget(self.settings.New_UI(), stretch=0)
        self.info_label = QtWidgets.QLabel()
        self.ui.layout().addWidget(self.info_label, stretch=0)
        self.imview = pg.ImageView(view=pg.PlotItem())
        self.imview.show()
                
        self.ui.layout().addWidget(self.imview, stretch=0)
        
                
    def on_change_data_filename(self, fname):
                
        try:
            self.stack = self.load_h5_dataset(fname)
            
            if hasattr(self,'stack'): #& self.stack.ndim>=2:
                #print(self.stack.ndim)
                #num_images = self.stack.shape[0]
                #self.settings.index.change_min_max(0, num_images-1)        
                self.imview.setImage(self.stack)            
                ## This would display the data and assign each frame a time value from 1.0 to 3.0
                #self.imview.setImage((self.stack),xvals=np.linspace(1., 3., num_images))            
                self.update_display()
                
                  
                            
        except Exception as err:
            self.imview.setImage(np.zeros((10,10,10)))
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            raise(err)
              
        
    def is_file_supported(self, fname):
        _, ext = os.path.splitext(fname)
        return ext.lower() in ['.h5']
      
    def update_display(self):
        
            if hasattr(self,'imview'):
                fr = self.settings['Frame rate']
                #self.imview.setCurrentIndex(ii)
                
                #Plays the stack at the chosen frame rate
                if self.settings['Play']:
                    self.imview.play(fr)
               
    def load_h5_dataset(self, fname):
        f = h5py.File(fname)
        [dataname,shape,found]=find_dataset(f)
        
        return (np.array(f[dataname[0]]))
      
            
if __name__ == '__main__':
    import sys
    
    app = DataBrowser(sys.argv)
    app.load_view(ImageStackH5(app))
       
    sys.exit(app.exec_())
