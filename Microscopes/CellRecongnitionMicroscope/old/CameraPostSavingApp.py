from ScopeFoundry import BaseMicroscopeApp
from ScopeFoundry.logged_quantity import LoggedQuantity, FileLQ
import os
from qtpy import QtCore, QtGui, QtWidgets
from ScopeFoundry.helper_funcs import confirm_on_close, ignore_on_close, load_qt_ui_file, \
    OrderedAttrDict, sibling_path, get_logger_from_class, str2bool
from PyQt5.Qt import QMessageBox
    
class FakeCameraApp(BaseMicroscopeApp):
    
    name = 'HamamatsuApp'
    
    
    def setup(self):
        
        from FakeCameraHardware import FakeCameraHardware
        self.add_hardware(FakeCameraHardware(self))
        print("Adding Hardware Components")
        
        from FakeCameraMeasurement import FakeCameraMeasurement
        self.add_measurement(FakeCameraMeasurement(self))
        print("Adding measurement components")
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
            
    import sys
    app = FakeCameraApp(sys.argv)
    sys.exit(app.exec_())