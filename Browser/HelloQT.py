import sys
#import PySide2
from qtpy.QtWidgets import QApplication, QLabel
   
#import pdb
                                                  
if __name__ == "__main__":
    #pdb.set_trace()
    app = QApplication(sys.argv)
    label = QLabel("Hello World")
    label.show()
    
    app = app.exec_()
    
    sys.exit(app)