#import PyDAQmx as mx
#import numpy as np
import nidaqmx
import pyqtgraph as pg
import qtpy.QtCore
from qtpy.QtWidgets import QApplication

task= nidaqmx.Task()

task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
data=task.read(number_of_samples_per_channel=1000)
pg.plot(data, title="Analog Input signal")
task.close()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if sys.flags.interactive != 1 or not hasattr(qtpy.QtCore, 'PYQT_VERSION'):
        QApplication.exec_()
