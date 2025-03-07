import json
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from PyQt5.QtCore import QPoint, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QTransform
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
                             QTextEdit, QWidget, QCheckBox)

from src.image_processing import dithering, wave_smoother, wave_smoother_standalone
from src.utils import constants, path_maker, to_steps, svg_parser, FunctionTypeEnum, WorkerThread
from src.window import ConfigurationCanvas, ProcessCanvas, ProcessImage, ConfigureMachine
#from src.utils import gcode_convertor

settings = None


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        tab_widget = QTabWidget(self)

        self.tab_configure_machine = ConfigureMachine()
        self.tab_process_image = ProcessImage()

        tab_widget.addTab(self.tab_process_image, "Process Image")
        tab_widget.addTab(self.tab_configure_machine, "Configure Machine")

        self.setCentralWidget(tab_widget)


if __name__ == "__main__":
    if not os.path.exists(constants.GENERATED_FILES):
        os.makedirs(constants.GENERATED_FILES)

    app = QApplication(sys.argv)
    qss = constants.STYLE
    with open(qss, "r") as ss:
        app.setStyleSheet(ss.read())
    window = MyWindow()
    window.showMaximized()
    sys.exit(app.exec_())
