import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

from src.utils import constants
from src.window import ProcessImage, ConfigureMachine

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
