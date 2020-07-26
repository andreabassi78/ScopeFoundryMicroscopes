from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
from datetime import datetime
import os
import time
import cv2

class FakeCameraMeasurement(Measurement):
    
    name = "fake_camera_image"
        
    def setup(self):
    
        self.ui_filename = sibling_path(__file__, "form.ui")
    
        self.ui = load_qt_ui_file(self.ui_filename)
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('refresh_period', dtype=float, unit='s', spinbox_decimals = 4, initial=0.02 , hardware_set_func=self.setRefresh, vmin = 0)
        self.settings.New('autoRange', dtype=bool, initial=True, hardware_set_func=self.setautoRange)
        self.settings.New('autoLevels', dtype=bool, initial=True, hardware_set_func=self.setautoLevels)
        self.settings.New('level_min', dtype=int, initial=60, hardware_set_func=self.setminLevel, hardware_read_func = self.getminLevel)
        self.settings.New('level_max', dtype=int, initial=150, hardware_set_func=self.setmaxLevel, hardware_read_func = self.getmaxLevel)
        
        self.settings.New('extractRoi', dtype=bool, initial=False, hardware_set_func=self.setExtractRoi, hardware_read_func=self.getExtractRoi)
        self.settings.New('dimRoi', dtype=int, initial=150, hardware_set_func=self.setDimRoi, hardware_read_func = self.getDimRoi)
        self.settings.New('minCellSize', dtype=int, initial=1600, hardware_set_func=self.setMinCellSize, hardware_read_func = self.getMinCellSize)
        
        self.camera = self.app.hardware['FakeCameraHardware']
        
        self.autoRange = self.settings.autoRange.val
        self.display_update_period = self.settings.refresh_period.val
        self.autoLevels = self.settings.autoLevels.val
        self.level_min = self.settings.level_min.val
        self.level_max = self.settings.level_max.val
        
        self.dimRoi = self.settings.dimRoi.val
        self.minCellSize = self.settings.minCellSize.val

        
        
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
            self.imv.setImage((self.displayed_image), 
                              autoLevels=self.settings.autoLevels.val,
                              autoRange=self.settings.autoRange.val,
                              levels=(self.level_min, self.level_max))
        else: #levels should not be sent when autoLevels is True, otherwise the image is displayed with them
            self.imv.setImage((self.displayed_image), 
                              autoLevels=self.settings.autoLevels.val, 
                              autoRange=self.settings.autoRange.val)
            self.settings.level_min.read_from_hardware()
            self.settings.level_max.read_from_hardware()
             
    def run(self):
        
        self.image = np.zeros((int(self.camera.subarrayv.val),int(self.camera.subarrayh.val)),dtype=np.uint16)
        self.image[0,0] = 1 #Otherwise we get the "all zero pixels" error (we should modify pyqtgraph...)
        
        self.displayed_image=self.image

        try:
            
            self.camera.read_from_hardware()
                        
               
            while not self.interrupt_measurement_called:
                    
                im = self.camera.fakecamera.get_image()
                self.image = im
                #self.image = np.reshape(im,(self.eff_subarrayh, self.eff_subarrayv))
                
                image8bit, cnt,cx,cy = self.find_cell(self.image)
                self.displayed_image = self.draw_contours(image8bit,cnt,cx,cy)
                self.roi = self.roi_creation(self.image, cx, cy)
                           
                time.sleep(0.1)
        
        finally:
            pass            
                                
    
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
    
    def find_cell(self, image): 
        """ 
            Input:
        img8bit: monochrome image, previously converted to 8bit (img8bit)
        cell_size: minimum area of the object to be detected.
            Output:
        cx,cy : list of the coordinates of the centroids of the detected objects 
        selected_contours: list of contours of the detected object (no child contours are detected).  
        """        
        image8bit = (image/256).astype('uint8') 
        _ret,thresh_pre = cv2.threshold(image8bit,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # ret is the threshold that was used, thresh is the thresholded image.     
        kernel  = np.ones((3,3),np.uint8)
        thresh = cv2.morphologyEx(thresh_pre,cv2.MORPH_OPEN, kernel, iterations = 2)
        # morphological opening (remove noise)
        contours, _hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cx = []
        cy = []            
        #area = []
        contour =[]
        #print(len(contours))
        
        for cnt in contours:
        #   print(len(cnt))           
            M = cv2.moments(cnt)
            #if M['m00'] >  int(self.camera.min_cell_size.val):   # (M['m00'] gives the contour area, also as cv2.contourArea(cnt)     
            if M['m00'] >  int(self.minCellSize):
                #extracts image center
                cx.append(int(M['m10']/M['m00']))
                cy.append(int(M['m01']/M['m00']))
                contour.append(cnt)
            
        return image8bit,contour,cx,cy
                    
    
    
    
    def draw_contours(self, image8bit,contour,cx,cy):        
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
        
        displayed_image = cv2.cvtColor(image8bit,cv2.COLOR_GRAY2RGB)      
        
        for indx, val in enumerate(cx):
            
            #x,y,w,h = cv2.boundingRect(cnt)
            # x = int(self.cx[indx] - self.camera.dim_roi.val/2) 
            # y = int(self.cy[indx] - self.camera.dim_roi.val/2)
            x = int(cx[indx] - self.dimRoi/2) 
            y = int(cy[indx] - self.dimRoi/2)
         
            #w = h = int(self.camera.dim_roi.val)
            w = h = int(self.dimRoi)
            
            displayed_image = cv2.drawContours(displayed_image, [contour[indx]], 0, (0,256,0), 2) 
            
            if indx == 0:
                color = (256,0,0)    #try with 256 at first place
            else: 
                color = (0,0,256)
                
            cv2.rectangle(displayed_image,(x,y),(x+w,y+h),color,1)    
            
        return displayed_image
    
    
    
    def roi_creation(self,image,cx,cy):
        l = image.shape
        self.roi = []
        for indx, val in enumerate(cx):
            x = int(cx[indx] - self.dimRoi/2) 
            y = int(cy[indx] - self.dimRoi/2)
            w = h = int(self.dimRoi)
            if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:
                    detail = image [y:y+w, x:x+h]    # we want to save the original 16bit version 
                    if self.settings.extractRoi==True:
                        self.roi.append(detail)
    
