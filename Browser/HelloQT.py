import sys
#import PySide2
from qtpy.QtWidgets import QApplication, QLabel
                                                     
if __name__ == "__main__":
    app = QApplication(sys.argv)
    label = QLabel("Hello World")
    label.show()
    sys.exit(app.exec_())