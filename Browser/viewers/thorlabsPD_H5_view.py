"""Written by Andrea Bassi (Politecnico di Milano) 10 August 2018:
viewer compatible with Scopefoundry DataBrowser.
Finds a dataset created by thorlabsPD_measure.py and plots it
"""

from ScopeFoundry.data_browser import DataBrowser, DataBrowserView
from qtpy import QtWidgets
import h5py
import pyqtgraph as pg
import numpy as np
import os
from viewers.find_h5_dataset import find_dataset

class PlotH5(DataBrowserView):

    name = 'plot_h5'
    
    def setup(self):
        
        self.ui = QtWidgets.QWidget()
        self.ui.setLayout(QtWidgets.QVBoxLayout())
        self.ui.layout().addWidget(self.settings.New_UI(), stretch=0)
        self.info_label = QtWidgets.QLabel()
        self.ui.layout().addWidget(self.info_label, stretch=0)
        self.plotview = pg.PlotWidget()
        self.plotview.show()
                
        self.ui.layout().addWidget(self.plotview, stretch=0)     
                
    def on_change_data_filename(self, fname):
                
        try:
            [self.time, self.data] = self.load_h5_dataset(fname)
            
            if hasattr(self,'data'):
                       
                self.plotview.plot(self.time,self.data,clear=True)           
                ## This would display the data and assign each frame a time value from 1.0 to 3.0
                #self.plotview.setImage((self.data),xvals=np.linspace(1., 3., num_images))            
                self.update_display()                 
                            
        except Exception as err:
            self.databrowser.ui.statusbar.showMessage("failed to load %s:\n%s" %(fname, err))
            raise(err)       
              
        
    def is_file_supported(self, fname):
        _, ext = os.path.splitext(fname)
        return ext.lower() in ['.h5']
      
    def update_display(self):
        return []
           

    def load_h5_dataset(self, fname):
        f = h5py.File(fname)
        [dataname, shape, found]=find_dataset(f)
        #read data
        data = f[dataname[1]]
        time = f[dataname[0]]
        return (np.array(data), np.array(time))
      
            
if __name__ == '__main__':
    import sys
    
    app = DataBrowser(sys.argv)
    app.load_view(PlotH5(app))
       
    sys.exit(app.exec_())
