"""Written by Andrea Bassi (Politecnico di Milano) 15-August-2018
to measure the signal received by a Thorlabs DET10A photodiode using a National Intruments  NI USB-6212 board.
It is compatible with Scope Foundry and modified by the Virtual Signal Generation measurement 
"""

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time

class ThorlabsPD_Measure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "thorlabsPD_plot"
    
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
        self.ui_filename = sibling_path(__file__, "thorlabsPD_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('refresh_period', dtype=float, unit='s', initial=0.1)      
        
        # Convenient reference to the hardware used in the measurement
        self.NIboard=self.app.hardware['NI_DAQ_AI_HW']
        
        # Initialize a  buffer where the acquired data will be stored: the buffer is a ampty list
        self.buffer = []    
        # in alternative it could be initialized as:
        # self.buffer = self.NIboard.data
        # or, other alternative as a list of 0s:
        # self.buffer = [0]*self.NIboard.samples_size.val 
        
        #Initialize a variable for the time to show in the plot
        self.t=[]
        self.t0=0
        
        # Define how often to update display during a run
        self.display_update_period = self.settings.refresh_period.val 
        #self.display_update_period = self.settings['refresh_period'] # other way to get the same value
        
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
        
        # Set up pyqtgraph graph_layout in the UI
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)

        # Create PlotItem object (a set of axes)  
        self.plotgraph = self.graph_layout.addPlot(title="Photodiode readout")  
        self.plotgraph.setLabel('bottom','time',units='s')
        self.plotgraph.setLabel('left','readout',units='V')
    
    def update_display(self):
        """
        Displays (plots) the np.array(self.buffer). 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        #convert the data and show them in plot
        shown_data = np.array(self.buffer, dtype=float)
        shown_time = np.array(self.t, dtype=float)
        self.plotgraph.plot(shown_time,shown_data,clear=True) # clear will remove the previously shown data from the plot

        
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """     
       
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        try:
            i = 0
           
            #
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:                
                samples_num=self.NIboard.samples_size.val 
                #acq_time=1/self.NIboard.sampling_freq.val*samples_num
                
                #if self.NIboard.AI_device.task.is_task_done() == False:
                #    print('waiting')
                #    print(self.NIboard.AI_device.task.in_stream)
               
                samples_num=self.NIboard.samples_size.val            
                
                # read the voltage from the NIboard
                # multiples samples means that samples_size samples are acquired  
                if self.NIboard.settings['multiple_samples']:  #Note: an alternative form is: if self.NIboard.multiple.val    
                        #stops the task in case it is still acquiring
                        self.NIboard.AI_device.stop_NI_DAQ_AI()
                        # acquires a full array of samples 
                        self.buffer = self.NIboard.AI_device.read_NI_DAQ_AI(samples_num)
                        
                        self.settings['progress'] = 100
                        #creates a time-scale for the plot
                        tmin=0
                        num=len(self.buffer)
                        tmax=1/self.NIboard.settings.sampling_freq.val*num
                        self.t=(np.linspace(tmin,tmax,num)).tolist()
                        # during multiple acquisition the time delay is set to 0
                        self.t0=0
            
                #this is non-multiple acquisition, showing the single data as they are captured        
                else:   
                        #if the measurement is just started or was on multiple acquisition, 
                        #the time delay is 0
                        if self.t0 == 0:
                            self.t0 = time.time()-1/self.NIboard.settings.sampling_freq.val*len(self.buffer)
                        #stops the task in case it is still acquiring
                        self.NIboard.AI_device.stop_NI_DAQ_AI()
                        # acquires a single value and add it to the buffer
                        list_data = (self.NIboard.AI_device.read_NI_DAQ_AI(1))
                        self.buffer.append(list_data[0]) 
                        self.t.append(time.time()-self.t0)                  
                        #if the buffer is bigger than setting['sample_size'], remove the excess elements from the buffer 
                        excess_elements= len(self.buffer)-samples_num
                        if excess_elements > 0:
                            for x in range(0, excess_elements):
                                self.buffer.pop(0) #removes the first element of the buffer
                                self.t.pop(0)
                        #updates the progress bar
                        i %= samples_num # means: i = i % samples_num                
                        self.settings['progress'] = i * 100./samples_num
                        i += 1
                                         
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    break
                
                # wait between readings.
                # We will use our refresh_period settings to define time
                # wait between readings.
                time.sleep(self.settings['refresh_period'])                
                        
            #data are saved only at the end of the measurement (interrupt button pressed)    
            if self.settings['save_h5']:
                    # if enabled will create an HDF5 file with the plotted data
                    # first we create an H5 file (by default autosaved to app.settings['save_dir']
                    # This stores all the hardware and app meta-data in the H5 file
                    self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
                    # create a measurement H5 group (folder) within self.h5file
                    # This stores all the measurement meta-data in this group
                    self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
                    #convert the data to float
                    h5_dataset = np.array(self.buffer, dtype=float) 
                    h5_timeset = np.array(self.t, dtype=float)         
                    # create an h5 dataset to store the data
                    self.data_h5 = self.h5_group.create_dataset(name  = 'data', shape = h5_dataset.shape, dtype = h5_dataset.dtype)
                    self.time_h5 = self.h5_group.create_dataset(name  = 'time', shape = h5_dataset.shape, dtype = h5_dataset.dtype)
                    # copy data to H5 dataset
                    self.data_h5[:] = h5_dataset
                    self.time_h5[:] = h5_timeset
                    #Note: when writing the dataset the use of [:] is required.
                    # Not specifying the location within the destination buffer would result in no data writing
                    
                    # flush H5
                    self.h5file.flush()
                                                                                        

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
