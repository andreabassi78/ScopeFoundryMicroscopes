import json
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pyqtgraph as pg
import tifffile as tif

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget, QTableWidgetItem, QHeaderView
    
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file

from HexSimProcessor.SIM_processing.hexSimProcessor import HexSimProcessor
from HexSIM_Analyser.image_decorr import ImageDecorr
from HexSIM_Analyser.get_h5_dataset import get_dataset


def add_timer(function):
    """Function decorator to mesaure the execution time of a method""" 
    def inner(cls, *args, **kwargs):
        start_time = time.time() 
        result = function(cls, *args, **kwargs) 
        end_time = time.time() 
        print(f'Execution time for method "{function.__name__}": {end_time-start_time:.6f} s \n') 
        return result
        
    return inner 
    
def add_update_display(function):
    """Function decorator to to update display at the end of the execution
    It assumes that the class cls has the method .update_display 
    and run it after the function is executes""" 
    def inner(cls, *args, **kwargs):
        result = function(cls)
        cls.update_display()
        return result
        
    return inner   
    

class HexSimAnalysis(Measurement):
    name = 'HexSIM_Analysis'

    def setup(self):

        # load ui file
        self.ui_filename = sibling_path(__file__, "hexsim_analysis.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
       
        self.settings.New('debug', dtype=bool, initial=False, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('cleanup', dtype=bool, initial=False, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('gpu', dtype=bool, initial=False, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('compact', dtype=bool, initial=False, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('axial', dtype=bool, initial=False, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('usemodulation', dtype=bool, initial=True, si = True,
                          hardware_set_func = self.setReconstructor) 
        self.settings.New('magnification', dtype=float, initial=63, si=True, spinbox_decimals=2,
                          hardware_set_func = self.setReconstructor)
        self.settings.New('NA', dtype=float, initial=0.75, si=True, spinbox_decimals=2,
                          hardware_set_func = self.setReconstructor)
        self.settings.New('n', dtype=float, initial=1.0, si=True, spinbox_decimals=2,
                          hardware_set_func = self.setReconstructor)
        self.settings.New('wavelength', dtype=float, initial=0.532, si=True, spinbox_decimals=3,
                          hardware_set_func = self.setReconstructor)
        self.settings.New('pixelsize', dtype=float, initial=5.85, si=True, spinbox_decimals=3, unit = 'um',
                          hardware_set_func = self.setReconstructor)
        self.settings.New('alpha', dtype=float, initial=0.500, si=True, spinbox_decimals=3, description='0th att width',
                          hardware_set_func = self.setReconstructor)
        self.settings.New('beta', dtype=float, initial=0.950, si=True, spinbox_decimals=3,description='0th width',
                          hardware_set_func = self.setReconstructor)
        self.settings.New('w', dtype=float, initial=5.00, si=True, spinbox_decimals=2, description='wiener parameter',
                          hardware_set_func = self.setReconstructor)
        self.settings.New('eta', dtype=float, initial=0.70, si=True, spinbox_decimals=2, 
                          description='must be smaller than the sources radius normalized on the pupil size',
                          hardware_set_func = self.setReconstructor)
        self.settings.New('find_carrier', dtype=bool, initial=True, si = True,
                          hardware_set_func = self.setReconstructor) 
        
        
    def setup_figure(self):
        
        self.display_update_period = 0.5 
        
        self.imvRaw = pg.ImageView()
        self.imvRaw.ui.roiBtn.hide()
        self.imvRaw.ui.menuBtn.hide()

        self.imvSIM = pg.ImageView()
        self.imvSIM.ui.roiBtn.hide()
        self.imvSIM.ui.menuBtn.hide()

        self.imvWF = pg.ImageView()
        self.imvWF.ui.roiBtn.hide()
        self.imvWF.ui.menuBtn.hide()

        self.ui.rawImageLayout.addWidget(self.imvRaw)
        self.ui.simImageLayout.addWidget(self.imvSIM)
        self.ui.wfImageLayout.addWidget(self.imvWF)

        # Image initialization
        self.imageRaw = np.zeros((1, 512, 512), dtype=np.uint16) 
        self.imageSIM = np.zeros((1, 1024,1024), dtype=np.uint16) 
        self.imageWF = np.zeros((1, 512, 512), dtype=np.uint16)

        self.imvRaw.setImage(self.imageRaw, autoRange=False, autoLevels=True, autoHistogramRange=True)
        self.imvWF.setImage(self.imageWF, autoRange=False, autoLevels=True, autoHistogramRange=True)
        self.imvSIM.setImage(self.imageSIM, autoRange=False, autoLevels=True, autoHistogramRange=True)

        # Toolbox
        self.ui.loadFileButton.clicked.connect(self.loadFile)
        self.ui.resetMeasureButton.clicked.connect(self.reset)
        self.ui.calibrationResult.clicked.connect(self.showMessageWindow)

        self.ui.calibrationSave.clicked.connect(self.saveMeasurements) #TODO change UI names
        self.ui.calibrationLoad.clicked.connect(self.loadCalibrationResults)

        self.ui.standardSimuButton.clicked.connect(self.standard_reconstruction)
        self.ui.standardSimuUpdate.clicked.connect(self.calibration)

        self.ui.batchSimuButton.clicked.connect(self.batch_recontruction)
        
        self.ui.resolutionEstimateButton.clicked.connect(self.estimate_resolution)
        
        self.start_sim_processor()


    def update_display(self):
        """
        This function runs repeatedly and automatically during the measurement run,
        its update frequency is defined by self.display_update_period.
        """
        self.settings['progress'] = 0.5

        if hasattr(self, 'showCalibrationResult'):
            if self.showCalibrationResult:
                self.showMessageWindow()
                self.showCalibrationResult = False
                self.isCalibrationSaved = False
    
            if self.isCalibrationSaved:
                msg = QMessageBox()
                
        self.imvRaw.setImage(self.imageRaw,
                                 autoRange=False, autoLevels=True, autoHistogramRange=True)
       
        self.imvWF.setImage(self.imageWF,
                                 autoRange=False, autoLevels=True, autoHistogramRange=True)
        
        self.imvSIM.setImage(self.imageSIM,
                                 autoRange=False, autoLevels=True, autoHistogramRange=True)


    def start_sim_processor(self):
        self.isCalibrated = False
        self.kx_input = np.zeros((3, 1), dtype=np.single)
        self.ky_input = np.zeros((3, 1), dtype=np.single)
        self.p_input = np.zeros((3, 1), dtype=np.single)
        self.ampl_input = np.zeros((3, 1), dtype=np.single)
        
        if not hasattr(self, 'h'):
            self.h = HexSimProcessor()  # create reconstruction object
            self.h.opencv = False
            self.h.wienerfilter = np.zeros(self.imageSIM.shape)
            self.setReconstructor()
            
    def stop_sim_processor(self):
        if hasattr(self, 'h'):
            delattr(self, 'h')
     
    def run(self):
        pass
           
    @add_timer
    def load_h5_file(self,filename):
            imageRaw = get_dataset(filename)
            xmin = 900  # TODO: allow the user to manually select the ROI
            ymin = 200
            self.imageRaw = imageRaw [:,ymin:ymin+512, xmin:xmin+512] 
    
    @add_timer
    def load_tif_file(self,filename):
            self.imageRaw = np.single(tif.imread(filename))
    
    @add_update_display
    def loadFile(self):
        
        try:
            
            filename, _ = QFileDialog.getOpenFileName(directory = self.app.settings['save_dir'])
            
            if filename.endswith('.tif') or filename.endswith('.tiff'):
                self.load_tif_file(filename)
            elif filename.endswith('.h5') or filename.endswith('.hdf5'):
                self.load_h5_file(filename)
            else:
                raise OSError('Invalid file type')
            
            self.imageRawShape = np.shape(self.imageRaw)
            self.imageSIM = np.zeros((self.imageRawShape[0]//7,self.imageRawShape[1],self.imageRawShape[2]))
            self.imageWF = np.zeros((self.imageRawShape[0] // 7, self.imageRawShape[1], self.imageRawShape[2]))

            self.raw2WideFieldImage()

            self.filetitle = Path(filename).stem
            self.filepath = os.path.dirname(filename)
            self.isFileLoad = True

            try:
                # get file name of txt file
                for file in os.listdir(self.filepath):
                    if file.endswith(".txt"):
                        configFileName = os.path.join(self.filepath, file)

                configFile = open(configFileName, 'r')
                configSet = json.loads(configFile.read())

                self.kx_input = np.asarray(configSet["kx"])
                self.ky_input = np.asarray(configSet["ky"])
                self.p_input = np.asarray(configSet["phase"])
                self.ampl_input = np.asarray(configSet["amplitude"])

                # set value
                self.settings['magnification'] = configSet["magnification"]
                self.settings['NA'] = configSet["NA"]
                self.settings['n'] = configSet["refractive index"]
                self.settings['wavelength'] = configSet["wavelength"]
                self.settings['pixelsize']  = configSet["pixelsize"]

                try:
                    self.exposuretime = configSet["camera exposure time"]
                except:
                    self.exposuretime = configSet["exposure time (s)"]

                try:
                    self.laserpower = configSet["laser power (mW)"]
                except:
                    self.laserpower = 0

                txtDisplay = "File name:\t {}\n" \
                             "Array size:\t {}\n" \
                             "Wavelength:\t {} um\n" \
                             "Exposure time:\t {:.3f} s\n" \
                             "Laser power:\t {} mW".format(self.filetitle, self.imageRawShape, \
                                                                    configSet["wavelength"], \
                                                                    self.exposuretime, self.laserpower)
                self.ui.fileInfo.setPlainText(txtDisplay)

            except:
                self.ui.fileInfo.setPlainText("No information about this measurement.")

        except:
            self.isFileLoad = False

        if self.isFileLoad:
            self.isCalibrated = False
            self.setReconstructor()
            self.h._allocate_arrays()
        else:
            print("File is not loaded.")
        

    def raw2WideFieldImage(self):
        self.imageWF = np.mean(self.imageRaw, axis=0)
        # for n_idx in range(self.imageRawShape[0]//7):
        #     self.imageWF[n_idx,:,:] = np.sum(self.imageRaw[n_idx*7:(n_idx+1)*7,:,:],axis=0)/7
    
        
    @add_update_display        
    def reset(self):
        self.isFileLoad = False
        self.isCalibrated = False
        self.stop_sim_processor()
        self.start_sim_processor()
        self.imageSIM = np.zeros(self.imageSIMShape, dtype=np.uint16) 
        self.imageRaw = np.zeros(self.imageRawShape, dtype=np.uint16)
        self.imageWF = np.zeros(self.imageRawShape, dtype=np.uint16)
        
        
    
    #@add_timer  #TODO check decorator variables args kwargs
    def calibration(self):
        print('Start calibrating...')
        self.setReconstructor()
        if self.isGpuenable:
            self.h.calibrate_cupy(self.imageRaw, self.isFindCarrier)
            
        else:
            self.h.calibrate(self.imageRaw,self.isFindCarrier)
        self.isCalibrated = True
        self.find_phaseshifts()
        
        
    @add_update_display
    @add_timer  
    def standard_reconstruction(self):
        print('Start standard processing...')

        self.setReconstructor()
        if self.isCalibrated:
            
            if self.isGpuenable:
                self.imageSIM = self.h.reconstruct_cupy(self.imageRaw)

            elif not self.isGpuenable:
                self.imageSIM = self.h.reconstruct_rfftw(self.imageRaw)
            #self.imageSIM = self.imageSIM[np.newaxis, :, :]
        else:
            self.calibration()
            self.standard_reconstruction() # TODO check if this ricursive call is correct
        self.imageSIMShape = self.imageSIM.shape
        
    @add_update_display
    @add_timer    
    def batch_recontruction(self): # TODO fix this reconstruction with  multiple batches (multiple planes)
        print('Start batch processing...')
        self.setReconstructor()
        if self.isCalibrated:
            # Batch reconstruction
            if self.isGpuenable:
                if self.isCompact:
                    self.imageSIM = self.h.batchreconstructcompact_cupy(self.imageRaw)
                elif not self.isCompact:
                    self.imageSIM = self.h.batchreconstruct_cupy(self.imageRaw)

            elif not self.isGpuenable:
                if self.isCompact:
                    self.imageSIM = self.h.batchreconstructcompact(self.imageRaw)
                elif not self.isCompact:
                    self.imageSIM = self.h.batchreconstruct(self.imageRaw)
            
        elif not self.isCalibrated:
            nStack = len(self.imageRaw)
            # calibrate & reconstruction
            if self.isGpuenable:
                self.h.calibrate_cupy(self.imageRaw[int(nStack // 2):int(nStack // 2 + 7), :, :], self.isFindCarrier)
                self.isCalibrated = True
                
                if self.isCompact:
                    self.imageSIM = self.h.batchreconstructcompact_cupy(self.imageRaw)
                elif not self.isCompact:
                    self.imageSIM = self.h.batchreconstruct_cupy(self.imageRaw)
                

            elif not self.isGpuenable:
                self.h.calibrate(self.imageRaw[int(nStack // 2):int(nStack // 2 + 7), :, :], self.isFindCarrier)
                self.isCalibrated = True
                
                if self.isCompact:
                    self.imageSIM = self.h.batchreconstructcompact(self.imageRaw)
                elif not self.isCompact:
                    self.imageSIM = self.h.batchreconstruct(self.imageRaw)
            self.imageSIMShape = self.imageSIM.shape

    def setReconstructor(self,*args):
        self.isCompact = self.settings['compact']
        self.isGpuenable = self.settings['gpu']
        self.isFindCarrier = self.settings['find_carrier']
        self.h.debug = self.settings['debug']
        self.h.cleanup = self.settings['cleanup']
        self.h.axial = self.settings['axial']
        self.h.usemodulation = self.settings['usemodulation']
        self.h.magnification = self.settings['magnification']
        self.h.NA = self.settings['NA']
        self.h.n = self.settings['n']
        self.h.wavelength = self.settings['wavelength']
        self.h.pixelsize = self.settings['pixelsize']
        self.h.alpha = self.settings['alpha']
        self.h.beta = self.settings['beta']
        self.h.w = self.settings['w']
        self.h.eta = self.settings['eta']
        if not self.isFindCarrier:
            self.h.kx = self.kx_input
            self.h.ky = self.ky_input
            

    def saveMeasurements(self):
        t0 = time.time()
        timestamp = datetime.fromtimestamp(t0)
        timestamp = timestamp.strftime("%Y%m%d%H%M")
        pathname = self.filepath + '/reprocess'
        Path(pathname).mkdir(parents=True,exist_ok=True)
        simimagename = pathname + '/' + self.filetitle + timestamp + f'_reprocessed' + '.tif'
        wfimagename = pathname + '/' + self.filetitle + timestamp + f'_widefield' + '.tif'
        txtname =      pathname + '/' + self.filetitle + timestamp + f'_reprocessed' + '.txt'
        tif.imwrite(simimagename, np.single(self.imageSIM))
        tif.imwrite(wfimagename,np.uint16(self.imageWF))
        print(type(self.imageSIM))

        savedictionary = {
            #"exposure time (s)":self.exposuretime,
            #"laser power (mW)": self.laserpower,
            # "z stepsize (um)":  self.
            # System setup:
            "magnification" :   self.h.magnification,
            "NA":               self.h.NA,
            "refractive index": self.h.n,
            "wavelength":       self.h.wavelength,
            "pixelsize":        self.h.pixelsize,
            # Calibration parameters:
            "alpha":            self.h.alpha,
            "beta":             self.h.beta,
            "Wiener filter":    self.h.w,
            "eta":              self.h.eta,
            "cleanup":          self.h.cleanup,
            "axial":            self.h.axial,
            "modulation":       self.h.usemodulation,
            "kx":               self.h.kx,
            "ky":               self.h.ky,
            "phase":            self.h.p,
            "amplitude":        self.h.ampl
            }
        f = open(txtname, 'w+')
        f.write(json.dumps(savedictionary, cls=NumpyEncoder,indent=2))
        self.isCalibrationSaved = True


    @add_update_display
    @add_timer   
    def estimate_resolution(self): #TODO : consider to add QT timers
            pixelsizeWF = self.h.pixelsize / self.h.magnification
            ciWF = ImageDecorr(self.imageWF[:,:], square_crop=True,pixel_size=pixelsizeWF)
            optimWF, resWF = ciWF.compute_resolution()
            ciSIM = ImageDecorr(self.imageSIM[:,:], square_crop=True,pixel_size=pixelsizeWF/2)
            optimSIM, resSIM = ciSIM.compute_resolution()
            txtDisplay = f"Wide field image resolution:\t {ciWF.resolution:.3f} um \
                  \nSIM image resolution:\t {ciSIM.resolution:.3f} um\n"
            self.ui.resolutionEstimation.setPlainText(txtDisplay)
        
        

    def loadCalibrationResults(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(caption="Open file", directory=self.app.settings['save_dir'], filter="Text files (*.txt)")
            file = open(filename,'r')
            loadResults = json.loads(file.read())
            self.kx_input = np.asarray(loadResults["kx"])
            self.ky_input = np.asarray(loadResults["ky"])
            print("Calibration results are loaded.")
        except:
            print("Calibration results are not loaded.")
            
    
    def find_phaseshifts(self):
        self.h.phaseshift = np.zeros((4,7))
        self.h.expected_phase = np.zeros((4,7))
    
        for i in range (3):
            phase, _ = self.h.find_phase(self.h.kx[i],self.h.ky[i],self.imageRaw)
            self.h.expected_phase[i,:] = np.arange(7) * 2*(i+1) * np.pi / 7
            self.h.phaseshift[i,:] = np.unwrap(phase - self.h.expected_phase[i,:]) + self.h.expected_phase[i,:] - phase[0]
    
        self.h.phaseshift[3] = self.h.phaseshift[2]-self.h.phaseshift[1]-self.h.phaseshift[0]
            
    def showMessageWindow(self):
        self.messageWindow = MessageWindow(self.h, self.kx_input, self.ky_input)
        self.messageWindow.show()


class MessageWindow(QWidget):

    """
    This window display the Winier filter and other debug data
    """

    def __init__(self, h, kx, ky):
        super().__init__()
        self.ui = uic.loadUi('calibration_results.ui',self)
        self.h = h
        self.kx = kx
        self.ky = ky
        self.setWindowTitle('Calibration results')
        self.showCurrentTable()
        self.show_images()
        
    def show_images(self):   
        widgets =[pg.ImageView(),
                  pg.PlotWidget(),
                  pg.ImageView()]
        layouts = ['wienerLayout',
                   'phaseLayout',
                   'otfLayout']
        data_to_show = [self.h.wienerfilter,
                        [self.h.phaseshift, self.h.expected_phase],
                        self.h.wienerfilter]
        for widget, layout_name, data in zip(widgets,layouts,data_to_show):
            print(widget)
            layout = getattr(self.ui, layout_name)
            layout.addWidget(widget)
            if isinstance(widget, pg.ImageView):
                    self.show_image_data(widget,data)
            if isinstance(widget, pg.PlotWidget):
                    self.show_plot_data(widget,data)
    

    def showCurrentTable(self):

        self.ui.currentTable.setItem(0, 0, QTableWidgetItem(str(self.kx[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(0, 1, QTableWidgetItem(str(self.kx[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(0, 2, QTableWidgetItem(str(self.kx[2]).lstrip('[').rstrip(']')))
        #
        self.ui.currentTable.setItem(1, 0, QTableWidgetItem(str(self.ky[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(1, 1, QTableWidgetItem(str(self.ky[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(1, 2, QTableWidgetItem(str(self.ky[2]).lstrip('[').rstrip(']')))

        self.ui.currentTable.setItem(2, 0, QTableWidgetItem(str(self.h.kx[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(2, 1, QTableWidgetItem(str(self.h.kx[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(2, 2, QTableWidgetItem(str(self.h.kx[2]).lstrip('[').rstrip(']')))
        #
        self.ui.currentTable.setItem(3, 0, QTableWidgetItem(str(self.h.ky[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(3, 1, QTableWidgetItem(str(self.h.ky[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(3, 2, QTableWidgetItem(str(self.h.ky[2]).lstrip('[').rstrip(']')))
        #
        self.ui.currentTable.setItem(4, 0, QTableWidgetItem(str(self.h.p[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(4, 1, QTableWidgetItem(str(self.h.p[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(4, 2, QTableWidgetItem(str(self.h.p[2]).lstrip('[').rstrip(']')))
        #
        self.ui.currentTable.setItem(5, 0, QTableWidgetItem(str(self.h.ampl[0]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(5, 1, QTableWidgetItem(str(self.h.ampl[1]).lstrip('[').rstrip(']')))
        self.ui.currentTable.setItem(5, 2, QTableWidgetItem(str(self.h.ampl[2]).lstrip('[').rstrip(']')))

        # Table will fit the screen horizontally
        self.currentTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def show_image_data(self, widget, image_to_show):
        widget.aspectRatioMode = Qt.KeepAspectRatio
        widget.ui.roiBtn.hide()
        widget.ui.menuBtn.hide()
        widget.ui.histogram.hide()
        widget.setImage(image_to_show, autoRange=True, autoLevels=True)
        widget.adjustSize()
    
    def show_plot_data(self, widget, plot_to_show):
        
        print(f'{plot_to_show[0]} ')
        print(f'{plot_to_show[1]} ')
        widget.aspectRatioMode = Qt.KeepAspectRatio
        
        for idx in range(4):
            widget.plot(plot_to_show[0][idx], symbol = '+')
            widget.plot(plot_to_show[1][idx])
        widget.adjustSize()


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


    

    
if __name__ == "__main__" :
    from ScopeFoundry import BaseMicroscopeApp
    import sys
    class testApp(BaseMicroscopeApp):
        def setup(self):
            self.add_measurement(HexSimAnalysis)
            self.ui.show()
            self.ui.activateWindow()

    app = testApp(sys.argv)
    
    app.settings_load_ini(".\\Settings\\HexSIM_Analysis.ini")
    sys.exit(app.exec_())