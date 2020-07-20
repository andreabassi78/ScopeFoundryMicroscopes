
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import os
import time
import cv2


class HamamatsuMeasurement(Measurement):
    
    name = "hamamatsu_image"
        
    def setup(self):
        
        "..."

        self.ui_filename = sibling_path(__file__, "form.ui")
        
    
        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('record', dtype=bool, initial=False, hardware_set_func=self.setRecord, hardware_read_func=self.getRecord, reread_from_hardware_after_write=True)
        self.settings.New('save_h5', dtype=bool, initial=False, hardware_set_func=self.setSaveH5, hardware_read_func=self.getSaveH5)
        self.settings.New('refresh_period', dtype=float, unit='s', spinbox_decimals = 4, initial=0.02 , hardware_set_func=self.setRefresh, vmin = 0)
        self.settings.New('autoRange', dtype=bool, initial=True, hardware_set_func=self.setautoRange)
        self.settings.New('autoLevels', dtype=bool, initial=True, hardware_set_func=self.setautoLevels)
        self.settings.New('level_min', dtype=int, initial=60, hardware_set_func=self.setminLevel, hardware_read_func = self.getminLevel)
        self.settings.New('level_max', dtype=int, initial=150, hardware_set_func=self.setmaxLevel, hardware_read_func = self.getmaxLevel)
        self.settings.New('threshold', dtype=int, initial=500, hardware_set_func=self.setThreshold)
        
        self.settings.New('extractRoi', dtype=bool, initial=False, hardware_set_func=self.setExtractRoi, hardware_read_func=self.getExtractRoi)
        self.settings.New('dimRoi', dtype=int, initial=150, hardware_set_func=self.setDimRoi, hardware_read_func = self.getDimRoi)
        self.settings.New('minCellSize', dtype=int, initial=1600, hardware_set_func=self.setMinCellSize, hardware_read_func = self.getMinCellSize)
        
        self.camera = self.app.hardware['HamamatsuHardware']
        
        self.autoRange = self.settings.autoRange.val
        self.display_update_period = self.settings.refresh_period.val
        self.autoLevels = self.settings.autoLevels.val
        self.level_min = self.settings.level_min.val
        self.level_max = self.settings.level_max.val
        
        self.dimRoi = self.settings.dimRoi.val
        self.minCellSize = self.settings.minCellSize.val

        #self.img = pg.gaussianFilter(np.random.normal(size=(400, 600)), (5, 5)) * 20 + 100
        
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
        
        # connect ui widgets of live settings
        self.settings.autoLevels.connect_to_widget(self.ui.autoLevels_checkBox)
        self.settings.autoRange.connect_to_widget(self.ui.autoRange_checkBox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        self.settings.extractRoi.connect_to_widget(self.ui.extractRoi_checkBox)
        self.settings.dimRoi.connect_to_widget(self.ui.dimRoi_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.minCellSize.connect_to_widget(self.ui.minCellSize_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.plot_groupBox.layout().addWidget(self.imv)
        
        # Image initialization
        self.image = np.zeros((int(self.camera.subarrayv.val),int(self.camera.subarrayh.val)),dtype=np.uint16)
        # Create PlotItem object (a set of axes)  
        
    def update_display(self):
        """
        Displays the numpy array called self.image.  
        This function runs repeatedly and automatically during the measurement run,
        its update frequency is defined by self.display_update_period.
        """
        #self.optimize_plot_line.setData(self.buffer) 

        #self.imv.setImage(np.reshape(self.np_data,(self.camera.subarrayh.val, self.camera.subarrayv.val)).T)
        #self.imv.setImage(self.image, autoLevels=False, levels=(100,340))
        if self.autoLevels == False:  
            self.imv.setImage((self.display), autoLevels=self.settings.autoLevels.val, autoRange=self.settings.autoRange.val, levels=(self.level_min, self.level_max))
        else: #levels should not be sent when autoLevels is True, otherwise the image is displayed with them
            self.imv.setImage((self.display), autoLevels=self.settings.autoLevels.val, autoRange=self.settings.autoRange.val)
            self.settings.level_min.read_from_hardware()
            self.settings.level_max.read_from_hardware()
             
    def run(self):
        
        self.eff_subarrayh = int(self.camera.subarrayh.val/self.camera.binning.val)
        self.eff_subarrayv = int(self.camera.subarrayv.val/self.camera.binning.val)
        
        self.image = np.zeros((self.eff_subarrayv,self.eff_subarrayh),dtype=np.uint16)
        self.image[0,0] = 1 #Otherwise we get the "all zero pixels" error (we should modify pyqtgraph...)
        
        self.display=self.image

        try:
            
            self.camera.read_from_hardware()
            print(self.camera.hamamatsu.number_frames)
            
            path = 'C:\\Users\\Andrea Bassi\\OneDrive - Politecnico di Milano\\Data\\PROCHIP\\Throughput_video\\'
    
            filename = 'dual_color_stack'
    
            
    #        path = 'C:\\Users\Mattia Cattaneo\Desktop\Polimi\Magistrale\Tesi\Python\Codes\\'
    #        filename = 'selected_stack'
            np_data = self.camera.hamamatsu.read_image(path, filename)
            
            
            index = 0
            
            if self.camera.acquisition_mode.val == "fixed_length":
                '''
                if self.settings['save_h5']:
                    self.initH5()
                    print("\n \n ******* \n \n Saving :D !\n \n *******")
                '''  
                while index < self.camera.hamamatsu.number_frames:
        
                    # Get frames.
                    #The camera stops acquiring once the buffer is terminated (in snapshot mode)
                    #[frames, dims] = self.camera.hamamatsu.getFrames()
                    im = self.camera.hamamatsu.get_image(np_data, index)
                    im=im*self.camera.hamamatsu.exposure_time*10
                    self.image = np.reshape(im,(self.eff_subarrayh, self.eff_subarrayv))
                    self.display=self.image
                    self.find_cell()
                    self.create_contours()
                    self.roi_creation()
                    '''
                    # Save frames.
                    for aframe in frames:
                        
                        self.np_data = aframe.getData()  
                        self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh)) 
                        if self.settings['save_h5']:
                            self.image_h5[index,:,:] = self.image # saving to the h5 dataset
                            self.h5file.flush() # maybe is not necessary
                    '''                        
                    if self.interrupt_measurement_called:
                        break
                    index+=1
                    print(index)
                    
                    if self.interrupt_measurement_called:
                        break    
                    #index = index + len(frames)
                    #np_data.tofile(bin_fp)
                    self.settings['progress'] = index*100./self.camera.hamamatsu.number_frames
                    
                    #time.sleep(1/self.camera.hamamatsu.exposure_time)
                    time.sleep(0.1)
                    
            elif self.camera.acquisition_mode.val == "run_till_abort":
                
                #save = True
                
                while not self.interrupt_measurement_called:
                    
                    im = self.camera.hamamatsu.get_image(np_data, index)
                    im=im*self.camera.hamamatsu.exposure_time*10
                    #self.image = [posh:posh+dimh, posv:posv+dimv]
                    #METTERE A POSTO VISUALIZZAZIONE SUBARRAY
                    self.image = np.reshape(im,(self.eff_subarrayh, self.eff_subarrayv))
                    self.display=self.image
                    self.find_cell()
                    self.create_contours()
                    self.roi_creation()
                    #self.image = im
                    index+=1
                    print(index)
                    
                    '''
                    if self.settings['record']:
                        self.camera.hamamatsu.stopAcquisition()
                        self.camera.hamamatsu.startRecording()
                        self.camera.hamamatsu.stopRecording()
                        self.interrupt()    
                                        
                    if self.settings['save_h5']:
                        
                        if save:
                            self.initH5()
                            save = False #at next cycle, we don't do initH5 again (we have already created the file)
                        
                        mean_value = np.mean(self.np_data)
                        last_frame_index = self.camera.hamamatsu.buffer_index
                        #print(self.camera.hamamatsu.last_frame_number)
                        if self.debug:
                            print("The mean is: ", mean_value)
                    
#===============================================================================
#                         if mean_value > self.settings['threshold']:
#                             print("\n \n ******* \n \n Saving :D !\n \n *******")
#                             j = 0
#                             
#                             #while(len(frames)) < self.camera.number_frames.val: #we want 200 frames
#                             while j < self.camera.number_frames.val: 
#                                 upgraded_last_frame_index, upgraded_frame_number = self.camera.hamamatsu.getTransferInfo() #we upgrade the transfer information
#                                 
#                                 if last_frame_index < upgraded_last_frame_index: #acquisition has not reached yet the end of the buffer    
#                                     j = self.getThresholdH5(last_frame_index,  upgraded_last_frame_index + 1, j)
# #                                     for i in range(last_frame_index, upgraded_last_frame_index + 1):
# #                                         
# #                                         if j < self.camera.number_frames.val:
# #                                             frame = self.camera.hamamatsu.getRequiredFrame(i)[0]
# #                                             self.np_data = frame.getData() #-1 takes the last element
# #                                             self.image = np.reshape(self.np_data,(int(self.camera.subarrayv.val), int(self.camera.subarrayh.val))).T
# #                                             self.image_h5[j,:,:] = self.image # saving to the h5 dataset
# #                                             j+=1
# #                                             self.settings['progress'] = j*100./self.camera.hamamatsu.number_image_buffers
#                                 
#                                 else: #acquisition has reached the end of the buffer
#                                     j = self.getThresholdH5(last_frame_index+1, 3*self.camera.hamamatsu.number_image_buffers + 1, j)
#                                     j = self.getThresholdH5(0, upgraded_last_frame_index, j)
#                                 
#                                 last_frame_index = upgraded_last_frame_index
#                                 
#                                 
#                                 
#                                 
#                             self.interrupt()
#                             print(self.camera.hamamatsu.last_frame_number)
#===============================================================================
                     
                        if mean_value > self.settings['threshold']:
                            
                            print("\n \n ******* \n \n Saving :D !\n \n *******")
                            j = 0
                            #starting_index=last_frame_index
                            stalking_number = 0
                            remaining = False
                            while j < self.camera.number_frames.val: 
                                
                                self.get_and_save_Frame(j,last_frame_index)
                                last_frame_index = self.updateIndex(last_frame_index)
                                
                                if self.debug:
                                    print("The last_frame_index is: ", last_frame_index)
                                    
                                j+=1
                                
                                if not remaining:
                                    upgraded_last_frame_index = self.camera.hamamatsu.getTransferInfo()[0] # upgrades the transfer information
                                    #The stalking_number represents the relative steps the camera has made in acquisition with respect to the saving.
                                    stalking_number = stalking_number + self.camera.hamamatsu.backlog - 1
                                    
                                    if self.debug:
                                        print('upgraded_last_frame_index: ' , upgraded_last_frame_index)
                                        print('stalking_number: ' , stalking_number)
                                        print('The camera is at {} passes from you'.format(self.camera.hamamatsu.number_image_buffers - stalking_number))
                                    
                                    if stalking_number + self.camera.hamamatsu.backlog > self.camera.hamamatsu.number_image_buffers: 
                                        self.camera.hamamatsu.stopAcquisitionNotReleasing() #stop acquisition when we know that at next iteration, some images may be rewritten
                                        remaining = True #if the buffer reach us, we execute the "while" without the "if not remaining" block.
                                   
                            self.interrupt()
                            self.camera.hamamatsu.stopAcquisition()
                            if self.debug:
                                print("The last_frame_number is: ", self.camera.hamamatsu.last_frame_number)
                         '''
                         
                    #time.sleep(1/self.camera.hamamatsu.exposure_time)
                    time.sleep(0.1)
                         
        finally:
            
            
            '''
            if self.settings['save_h5']:
                self.h5file.close() # close h5 file  
            self.settings.save_h5.update_value(new_val = False)
            '''
            
    def setRefresh(self, refresh_period):  
        self.display_update_period = refresh_period
    
    def setautoRange(self, autoRange):
        self.autoRange = autoRange

    def setautoLevels(self, autoLevels):
        self.autoLevels = autoLevels
            
    def setminLevel(self, level_min):
        self.level_min = level_min
        
    def setmaxLevel(self, level_max):
        self.level_max = level_max
    
    def getminLevel(self):
        return self.imv.levelMin
        
    def getmaxLevel(self):
        return self.imv.levelMax
            
    def setThreshold(self, threshold):
        self.threshold = threshold
    
    def setSaveH5(self, save_h5):
        self.settings.save_h5.val = save_h5
        
    def getSaveH5(self):
        if self.settings['record']:
            self.settings.save_h5.val = False
        return self.settings.save_h5.val 
        
    def setRecord(self, record):
        self.settings.record = record
    
        
    def getRecord(self):
        if self.settings['save_h5']:
            self.settings.record = False
        return self.settings.record 
    
    
    def setExtractRoi(self, extractRoi):
        self.settings.extractRoi = extractRoi
        
    def getExtractRoi(self):
        return self.imv.extractRoi
    
    def setDimRoi(self, dimRoi):
        self.dimRoi = dimRoi
        
    def getDimRoi(self):
        return self.imv.dimRoi

    def setMinCellSize(self, minCellSize):
        self.minCellSize = minCellSize
        
    def getMinCellSize(self):
        return self.imv.minCellSize

    
    
    
    
    
    def initH5(self):
        """
        Initialization operations for the h5 file.
        """
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]
        
    def initH5_temp(self):
        """
        Initialization operations for the h5 file.
        """
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            sample=self.app.settings["sample"],
            ext='h5')
        fname = os.path.join(self.app.settings['save_dir'], f)
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c1/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        self.image_h5_2 = self.h5_group.create_dataset( name  = 't0/c2/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]
        
        self.image_h5_2.dims[0].label = "z"
        self.image_h5_2.dims[1].label = "y"
        self.image_h5_2.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5_2.attrs['element_size_um'] =  [1,1,1]
                
    def initH5_temp2(self):
        """
        Initialization operations for the h5 file.
        """
        t0 = time.time()
        f = self.app.settings['data_fname_format'].format(
            app=self.app,
            measurement=self,
            timestamp=datetime.fromtimestamp(t0),
            sample=self.app.settings["sample"],
            ext='h5')
        fname = os.path.join(self.app.settings['save_dir'], f)
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        img_size=self.image.shape
        length=self.camera.hamamatsu.number_image_buffers
        self.image_h5 = self.h5_group.create_dataset( name  = 't0/c0/image', 
                                                      shape = ( length, img_size[0], img_size[1]),
                                                      dtype = self.image.dtype, chunks = (1, self.eff_subarrayv, self.eff_subarrayh)
                                                      )
        """
        THESE NAMES MUST BE CHANGED
        """
        self.image_h5.dims[0].label = "z"
        self.image_h5.dims[1].label = "y"
        self.image_h5.dims[2].label = "x"
        
        #self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'], self.settings['ysampling'], self.settings['xsampling']]
        self.image_h5.attrs['element_size_um'] =  [1,1,1]
        
    #===========================================================================
    # def getThresholdH5(self, start, end, j):
    #     """
    #     Get the data at the i-th frame (from start to end-1), and 
    #     save the reshaped data into an h5 file.
    #     
    #     j is a variable that gets updated every time. It represents
    #     the number of saved images. If this number gets bigger than
    #     the wanted number of frames, the below operation is not
    #     executed (we dont want to save other frames).
    #     
    #     Upload the progress bar.
    #     """
    #     for i in range(start, end):
    #         #put elements in new_frames until the end of buffer
    #         if j < self.camera.number_frames.val:
    #             frame = self.camera.hamamatsu.getRequiredFrame(i)[0]
    #             self.np_data = frame.getData()
    #             self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh)).T
    #             self.image_h5[j,:,:] = self.image # saving to the h5 dataset
    #             j+=1
    #             self.settings['progress'] = j*100./self.camera.hamamatsu.number_image_buffers
    #             
    #     return j
    #===========================================================================
    
    def get_and_save_Frame(self, saveindex, lastframeindex):
        """
        Get the data at the lastframeindex, and 
        save the reshaped data into an h5 file.
        saveindex is an index representing the position of the saved image
        in the h5 file. 
        Update the progress bar.
        """
           
        frame = self.camera.hamamatsu.getRequiredFrame(lastframeindex)[0]
        self.np_data = frame.getData()
        self.image = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh))
        self.image_h5[saveindex,:,:] = self.image # saving to the h5 dataset
        self.h5file.flush() # maybe is not necessary
        self.settings['progress'] = saveindex*100./self.camera.hamamatsu.number_image_buffers
    
    def updateIndex(self, last_frame_index):
        """
        Update the index of the image to fetch from buffer. 
        If we reach the end of the buffer, we reset the index.
        """
        last_frame_index+=1
        
        if last_frame_index > self.camera.hamamatsu.number_image_buffers - 1: #if we reach the end of the buffer
            last_frame_index = 0 #reset
        
        return last_frame_index
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def find_cell(self): 
        """ 
            Input:
        img8bit: monochrome image, previously converted to 8bit (img8bit)
        cell_size: minimum area of the object to be detected.
            Output:
        cx,cy : list of the coordinates of the centroids of the detected objects 
        selected_contours: list of contours of the detected object (no child contours are detected).  
        """        
        self.display = (self.display/256).astype('uint8') 
        _ret,thresh_pre = cv2.threshold(self.display,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # ret is the threshold that was used, thresh is the thresholded image.     
        kernel  = np.ones((3,3),np.uint8)
        self.thresh = cv2.morphologyEx(thresh_pre,cv2.MORPH_OPEN, kernel, iterations = 2)
        # morphological opening (remove noise)
        contours, _hierarchy = cv2.findContours(self.thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        self.cx = []
        self.cy = []            
        self.area = []
        self.contour =[]
        #print(len(contours))
        
        for cnt in contours:
        #   print(len(cnt))           
            M = cv2.moments(cnt)
            #if M['m00'] >  int(self.camera.min_cell_size.val):   # (M['m00'] gives the contour area, also as cv2.contourArea(cnt)     
            if M['m00'] >  int(self.minCellSize):
                #extracts image center
                self.cx.append(int(M['m10']/M['m00']))
                self.cy.append(int(M['m01']/M['m00']))
                self.area.append(M['m00']) 
                self.contour.append(cnt)
            
        return
                    
    
    
    
    def create_contours(self):        
        """ Input: 
        img8bit: monochrome image, previously converted to 8bit
        cx,cy: list of the coordinates of the centroids  
        cnt: list of the contours.
        rect_size: side of the square to be displayed/extracted  
            Output:
        img: RGB image with annotations
        roi: list of the extracted ROIs  
        
        Note: ROIs are not registered and this might be a problem if one wants to save the stack directly  
        """  
        
        self.display = cv2.cvtColor(self.display,cv2.COLOR_GRAY2RGB)      
        
        for indx, val in enumerate(self.cx):
            
        #x,y,w,h = cv2.boundingRect(cnt)
            # x = int(self.cx[indx] - self.camera.dim_roi.val/2) 
            # y = int(self.cy[indx] - self.camera.dim_roi.val/2)
            x = int(self.cx[indx] - self.dimRoi/2) 
            y = int(self.cy[indx] - self.dimRoi/2)
         
            #w = h = int(self.camera.dim_roi.val)
            w = h = int(self.dimRoi)
            
            self.display = cv2.drawContours(self.display, [self.contour[indx]], 0, (0,256,0), 2) 
            
            if indx == 0:
                color = (256,0,0)    #try with 256 at first place
            else: 
                color = (0,0,256)
                
            cv2.rectangle(self.display,(x,y),(x+w,y+h),color,1)    
            
        return
    
    
    
    def roi_creation(self):
        l = self.image.shape
        self.roi = []
        for indx, val in enumerate(self.cx):
            x = int(self.cx[indx] - self.dimRoi/2) 
            y = int(self.cy[indx] - self.dimRoi/2)
            w = h = int(self.dimRoi)
            if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:
                    detail = self.image [y:y+w, x:x+h]    # we want to save the original 16bit version 
                    if self.settings.extractRoi==True:
                        self.roi.append(detail)
    
