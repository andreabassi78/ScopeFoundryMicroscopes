from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time

class VirtualImageGenMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "virtual_image_measure"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "random_images.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('number_of_images_to_save', dtype=int, initial=10)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        self.settings.New('xsampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('ysampling', dtype=float, unit='um', initial=0.5)
        self.settings.New('zsampling', dtype=float, unit='um', initial=3.0)
              
        # Define how often to update display during a run
        self.display_update_period = 0.05 
        
        # Convenient reference to the hardware used in the measurement
        self.image_gen = self.app.hardware['virtual_image_gen']
        
        # Create an empty image with the size defined by the hardware
        #self.img = np.empty([self.image_gen.settings['size'],self.image_gen.settings['size']], dtype = float)
        self.img = self.image_gen.image_data
        
        
        print ('SETTINGS:', dir(self.settings))
        
        print ('SETTINGS.number_of_images_to_save:', dir(self.settings.number_of_images_to_save))
        print ('SETTINGS.number_of_images_to_save.val:', dir(self.settings.number_of_images_to_save.val))
        print ('SETTINGS[number_of_images_to_save]:', dir(self.settings['number_of_images_to_save']))



    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        self.image_gen.settings.amplitude.connect_to_widget(self.ui.amp_doubleSpinBox)
        
                
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.image_groupBox.layout().addWidget(self.imv)
        colors = [(0, 0, 0),
                  (45, 5, 61),
                  (84, 42, 55),
                  (150, 87, 60),
                  (208, 171, 141),
                  (255, 255, 255)
                  ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        self.imv.setColorMap(cmap)
       
    
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        
        self.imv.setImage(self.img)
        
    
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        # first, create a data file
        if self.settings['save_h5']:
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
            
            # create an h5 dataset to store the data
            img_size=self.img.shape
            length=self.settings['number_of_images_to_save']
            self.image_h5 = self.h5_group.create_dataset(name  = 't0/c0/image', 
                                                          shape = [ length, img_size[0], img_size[1]],
                                                          dtype = self.img.dtype)
            self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        try:
            i = 0
            
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                # defines a number of acquisitions to be done, then measurement will be repeated until interrupt is pressed
                
                length=self.settings['number_of_images_to_save']
                
                i %= length
                
                # Set progress bar percentage complete
                self.settings['progress'] = i * 100./length
                
                # Fills the buffer with sine wave readings from func_gen Hardware
                
                #data=self.image_gen.settings.data.read_from_hardware()
                data=self.image_gen.vimage_gen_dev.read_image()
                
                self.img = data
                                
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.image_h5[i,:,:] = self.img
                    # flush H5
                    self.h5file.flush()
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                time.sleep(self.settings['sampling_period'])
                
                i += 1

                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
