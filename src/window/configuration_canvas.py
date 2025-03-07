import math

from PyQt5.QtCore import QPoint, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QTransform
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
                             QTextEdit, QWidget, QCheckBox)

from src.utils import constants

# TODO: change the global settings usage

# Canvas that displays the machine configuration
class ConfigurationCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 400)
        self.setMouseTracking(True)
        self.scale_factor = 1.0
        self.dragging = False
        self.start_pos = QPoint()
        self.cur_pos = QPoint()
        self.last_pos = QPoint()
        self.delta = QPoint()

        self.settings = None

        self.motor_ellipse_dia = 14
        self.pen_ellipse_dia = 8

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        transform.translate(self.cur_pos.x(), self.cur_pos.y())
        painter.setTransform(transform)

        self.m1 = [0, 0]
        self.m2 = [self.m1[0] + self.settings["distanceBetweenMotors"], 0]

        painter.drawEllipse(
            int(self.m1[0] - self.motor_ellipse_dia / 2) + constants.IMAGE_OFFSET[0],
            self.m1[1] + constants.IMAGE_OFFSET[1],
            self.motor_ellipse_dia,
            self.motor_ellipse_dia,
        )
        painter.drawEllipse(
            int(self.m2[0] - self.motor_ellipse_dia / 2) + constants.IMAGE_OFFSET[0],
            self.m2[1] + constants.IMAGE_OFFSET[1],
            self.motor_ellipse_dia,
            self.motor_ellipse_dia,
        )

        paper_offset_calculated = [0, 0]
        pen_pos_calculated = [0, 0]
        if (self.settings["startDistance"][0] ** 2) - (
            (self.settings["distanceBetweenMotors"] / 2) ** 2
        ) > 0:
            paper_offset_calculated = [
                round(
                    (
                        (self.settings["distanceBetweenMotors"] / 2)
                        - (self.settings["paperSize"][0] / 2)
                    )
                ),
                (
                    round(
                        math.sqrt(
                            self.settings["startDistance"][0] ** 2
                            - (self.settings["distanceBetweenMotors"] / 2) ** 2
                        )
                        - self.settings["paperOffset"]
                        - self.settings["paperSize"][1]
                    )
                ),
            ]
            pen_pos_calculated = [
                round(self.settings["distanceBetweenMotors"] / 2),
                round(
                    math.sqrt(
                        self.settings["startDistance"][0] ** 2
                        - (self.settings["distanceBetweenMotors"] / 2) ** 2
                    )
                ),
            ]

        painter.drawLine(
            int(self.m1[0] + self.motor_ellipse_dia / 2 + constants.IMAGE_OFFSET[0]),
            int(self.m1[1] + self.motor_ellipse_dia / 2 + constants.IMAGE_OFFSET[1]),
            pen_pos_calculated[0] + constants.IMAGE_OFFSET[0],
            pen_pos_calculated[1] + constants.IMAGE_OFFSET[1],
        )
        painter.drawLine(
            int(self.m2[0] - self.motor_ellipse_dia / 2 + constants.IMAGE_OFFSET[0]),
            int(self.m2[1] + self.motor_ellipse_dia / 2 + constants.IMAGE_OFFSET[1]),
            pen_pos_calculated[0] + constants.IMAGE_OFFSET[0],
            pen_pos_calculated[1] + constants.IMAGE_OFFSET[1],
        )

        painter.drawEllipse(
            int(pen_pos_calculated[0] -
                self.pen_ellipse_dia / 2) + constants.IMAGE_OFFSET[0],
            pen_pos_calculated[1] + constants.IMAGE_OFFSET[1],
            self.pen_ellipse_dia,
            self.pen_ellipse_dia,
        )

        painter.drawRect(
            paper_offset_calculated[0] + constants.IMAGE_OFFSET[0],
            paper_offset_calculated[1] + constants.IMAGE_OFFSET[1],
            self.settings["paperSize"][0],
            self.settings["paperSize"][1],
        )

    def setSettings(self, settings_: dict):
        self.settings = settings_
        global settings
        settings = self.settings

    # Mouse events for moving the image around and zooming in
    def wheelEvent(self, event):
        # Zoom in/out with the mouse wheel
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.scale_factor *= zoom_factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.pos() - self.last_pos * self.scale_factor

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.delta = event.pos()
            self.cur_pos = (self.delta - self.start_pos) / self.scale_factor
            self.last_pos = self.cur_pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

