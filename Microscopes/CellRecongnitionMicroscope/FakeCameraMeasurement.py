from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
from functools import partial
import numpy as np
from datetime import datetime
import os
import time
import cv2
import pdb

class FakeCameraMeasurement(Measurement):
    
    name = "fake_camera_image"
        
    def setup(self):
        self.ui_filename = sibling_path(__file__, "form.ui")
    
        self.ui = load_qt_ui_file(self.ui_filename)
        #self.settings.New('save_h5', dtype=bool, initial=False)
        
        self.settings.New('refresh_period', dtype = float, initial=0.08, vmin=0, vmax=10)
        
        self.settings.New('auto_range', dtype=bool, initial=True)
        self.settings.New('auto_levels', dtype=bool, initial=True)
        self.settings.New('level_min', dtype=int, initial=60)
        self.settings.New('level_max', dtype=int, initial=140)
        
        self.settings.New('extract_roi', dtype=bool, initial=False)
        self.settings.New('roi_half_side', dtype=int, initial=75)
        self.settings.New('min_cell_size', dtype=int, initial=1600)
        
        self.camera = self.app.hardware['FakeCameraHardware']
        self.display_update_period = self.settings.refresh_period.val
        
        self.cnt = []
        self.cx = []
        self.cy = []
        
        self.roi_num = 0
        
        
    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
                
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        #self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        
        # connect ui widgets of live settings
        self.settings.auto_levels.connect_to_widget(self.ui.autoLevels_checkBox)
        self.settings.auto_range.connect_to_widget(self.ui.autoRange_checkBox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) #spinBox doesn't work nut it would be better

        self.settings.extract_roi.connect_to_widget(self.ui.extractRoi_checkBox)
        self.settings.roi_half_side.connect_to_widget(self.ui.dimRoi_doubleSpinBox) #spinBox doesn't work nut it would be better
        self.settings.min_cell_size.connect_to_widget(self.ui.minCellSize_doubleSpinBox) #spinBox doesn't work nut it would be better
        
        # Set up pyqtgraph graph_layout in the UI
         
        self.imv = pg.ImageView()
        self.imv.ui.histogram.hide()
        self.imv.ui.roiBtn.hide()
        self.imv.ui.menuBtn.hide()
        self.imv.setPredefinedGradient('thermal')
        
        self.ui.plot_groupBox.layout().addWidget(self.imv)
        
        # Image initialization
        # self.image = np.zeros((int(self.camera.subarrayv.val),int(self.camera.subarrayh.val)),dtype=np.uint16)
        
        
    def update_display(self):    # .T (transposed) delayed to allow the rgb visualization
        """
        Displays the numpy array called self.image.  
        This function runs repeatedly and automatically during the measurement run,
        its update frequency is defined by self.display_update_period.
        """
        
        if hasattr(self, "image"):
              
            
            t0 = time.time()
            if self.settings.auto_levels.val:
                # if autolevel is on, normalize the image to its max and min     
                level_min = np.amin(self.image)
                level_max = np.amax(self.image)
                self.settings['level_min'] = level_min    
                self.settings['level_max'] = level_max
            
            else:
                # if autolevel is on, normalize the image to the choosen  values     
                level_min = self.settings.level_min.val
                level_max = self.settings.level_max.val
            
            # note that these levels are uiint16, but the visulaized image is uint8, for compatibility with opencv processing (contours and rectangles annotations) 
            img_thres = np.clip(self.image, level_min, level_max) # thresolding is required if autolevel is off (could be avoided if autolevel is on)
            
            image8bit_normalized = ( (img_thres-level_min)/(level_max-level_min)*255).astype('uint8') # convert to 8bit is done here for compatibility with opencv    
            
            self.displayed_image = self.draw_contours(image8bit_normalized,self.cnt,self.cx,self.cy)
            
            self.imv.setImage(self.image, autoLevels=True, autoRange=True)
            
            self.imv_external.setImage(self.displayed_image, autoLevels=False, autoRange=self.settings.auto_range.val, levels=(0,255))
            #print('Elapsed time for visualization:', time.time()-t0)
            
            
    

    def pre_run(self):
        
        if not hasattr(self, "imv_external"):
            self.display_update_period = self.settings.refresh_period.val
            plot = pg.PlotItem(title="channel")
            #plot.setLabel(axis='left', text='y-axis')
            #plot.setLabel(axis='bottom', text='x-axis')
            self.imv_external = pg.ImageView(view = plot)
            self.imv_external.show()

             
    def run(self):
        

        try:
            
        
            self.camera.read_from_hardware()
               
            while not self.interrupt_measurement_called:
                
                #pdb.set_trace()
                
                self.image = self.camera.fakecamera.get_image()
                t0 = time.time()
                image8bit = (self.image/256).astype('uint8')
                
                self.cnt,self.cx,self.cy = self.find_cell(image8bit)
                
                if self.settings.extract_roi.val:                    
                    self.roi = self.roi_creation(self.image, self.cx, self.cy)
                           
                #print('Elapsed time for cell recongnition:', time.time()-t0)
                
                time.sleep(0.05)
                
        finally:
            pass            
     
        
    def find_cell(self, image8bit): 
        """ 
            Input:
        image: 16 bit monochrome image
            Output:
        contour: list of contours of the detected object (no child contours are detected) 
        cx,cy: list of the coordinates of the centroids of the detected objects 
        """    
       
        _ret,thresh_pre = cv2.threshold(image8bit,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        # ret is the threshold that was used, thresh is the thresholded image.     
        kernel  = np.ones((3,3),np.uint8)
        thresh = cv2.morphologyEx(thresh_pre,cv2.MORPH_OPEN, kernel, iterations = 2)
        # morphological opening (remove noise)
        contours, _hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cx = []
        cy = []            
        contour =[]
        
        for cnt in contours:
        #   print(len(cnt))           
            M = cv2.moments(cnt)
            if M['m00'] >  int(self.settings.min_cell_size.val):
                #extracts image center
                cx.append(int(M['m10']/M['m00']))
                cy.append(int(M['m01']/M['m00']))
                contour.append(cnt)
        
        self.roi_num = len(contour)
        return contour,cx,cy
                    
    
    
    
    def draw_contours(self, image8bit,contour,cx,cy):        
        """ Input: 
        img8bit: monochrome image, previously converted to 8bit and "autoleveled"
        contour: list of the contours
        cx,cy: list of the coordinates of the centroids  
            Output:
        displayed_image: 8 bit RGB image with annotations to be displayed
        """  
        
        displayed_image = cv2.cvtColor(image8bit,cv2.COLOR_GRAY2RGB)      
        
        for indx in range(self.roi_num):
            
            #x,y,w,h = cv2.boundingRect(cnt)
            x = int(cx[indx] - self.settings.roi_half_side.val) 
            y = int(cy[indx] - self.settings.roi_half_side.val)
            w = h = self.settings.roi_half_side.val*2
            
            displayed_image = cv2.drawContours(displayed_image, [contour[indx]], 0, (0,256,0), 2)   #(0,256,0)
            
            if indx == 0:
                color = (256,0,0)
            else: 
                color = (0,0,256)
                
            cv2.rectangle(displayed_image,(x,y),(x+w,y+h),color,1)    
            
        return displayed_image
    
    
    
    def roi_creation(self,image,cx,cy):
        """ Input: 
        image: 16 bit monochrome image
        cx,cy: list of the coordinates of the centroids  
        
        It creates a list of roi present in the specific image frame analyzed
        """  
        roi_half_side = self.settings.roi_half_side.val
        l = image.shape
        roi = []
        for indx in range(self.roi_num):
            x = int(cx[indx] - roi_half_side) 
            y = int(cy[indx] - roi_half_side)
            w = h = roi_half_side *2
            if x>0 and y>0 and x+w<l[1]-1 and y+h<l[0]-1:
                    detail = image [y:y+w, x:x+h]    # we want to save the original 16bit version 
                    roi.append(detail)
        return roi
                        
    @property
    def roi_num(self):
        return self._roi_num
    
    @roi_num.setter
    def roi_num(self, num):
        self._roi_num = num