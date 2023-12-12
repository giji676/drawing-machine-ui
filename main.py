import os
import sys
import math
import json
import time
import dithering
import subprocess
import pathMaker
import toSteps
import numpy as np
from rembg import remove
from PIL import Image, ImageDraw, ImageOps

from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QTabWidget,
        QLineEdit,
        QLabel,
        QHBoxLayout,
        QGridLayout,
        QSpacerItem,
        QSizePolicy,
        QPushButton,
        QFileDialog,
        QTextEdit,
        )

from PyQt5.QtGui import QPainter, QPen, QPixmap, QTransform, QImage, QColor
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal

GENERATED_FILES = "generated_files"

IMAGE_TSP = "image.tsp"
IMAGE_CYC = "image.cyc"
OUTPUT_COORDINATES_TXT = "output_coordinates.txt"
OUTPUT_STEPS_TXT = "output_steps.txt"

tsp_path = f"{GENERATED_FILES}\{IMAGE_TSP}"
cyc_path = f"{GENERATED_FILES}\{IMAGE_CYC}"
output_coordinates_path = f"{GENERATED_FILES}\{OUTPUT_COORDINATES_TXT}"
output_steps_path = f"{GENERATED_FILES}\{OUTPUT_STEPS_TXT}"

SETTINGS = "settings.json"

# Used only for displaying the machine on the canvas, doesn't affect coordinates
IMAGE_OFFSET = (100, 100)

DEFAULT_SETTINGS = {
    "beltToothDistance": 2,
    "toothOngear": 20,
    "stepsPerRev": 3200,
    "motorDir": [1, -1],
    "distanceBetweenMotors": 580,
    "startDistance": [590, 590],
    "paperSize": [190, 270],
    "paperOffset": 35
}

settings = None


class FunctionTypeEnum:
    WAVE = 1
    LINKERN = 2
    DITHER = 3


class WorkerThread(QThread):
    # Runs lengthy functions on a separate "worker thread" so the gui doesn't freeze
    # function_signal is "emited" to set the right function to run (eg. linkern, wave, dithering)
    update_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()
    image_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.result = None
        self.image = None
        self.function_type = None

    def run(self):
        # Called by QThread automatically when WorkerThread.start() is called
        if self.function_type == FunctionTypeEnum.WAVE:
            self.image = self.wave(self.image)
            self.image_signal.emit()
        elif self.function_type == FunctionTypeEnum.LINKERN:
            self.linkern()
        elif self.function_type == FunctionTypeEnum.DITHER:
            self.image = self.dither(self.image)
            self.image_signal.emit()

    def wave(self,image: Image) -> Image:
        # Converts the image to waves
        if not image:
            return None

        # Range of wave values: 0 = horizontal line, max = dense wave - hight amplitude and frequency
        scaled_colour_range = 10
        pixel_wave_size = 20

        max_amplitude = pixel_wave_size/2

        pixels = np.array(image)

        height, width = pixels.shape
        new_height, new_width = height*20, width*20

        image = Image.new("RGB", (new_width,new_height), color="white")
        draw = ImageDraw.Draw(image)

        f = open(output_coordinates_path, "w")

        self.update_signal.emit("Starting conversion to wave")
        start_time = time.time()
        for y in range(height):
            for x in range(width):
                self.update_signal.emit(f"{str((y*width)+x)}/{str(height*width)}, {str(time.time() - start_time)}")
                n_x = x
                # Every other y level needs to start from the end so the other of the horizontal lines is: left-right-right-left...
                if y % 2 != 0:
                    n_x = width - 1 - x
                amplitude = 0
                frequency = 0

                pixels[y, n_x] = round(pixels[y, n_x]/25.5)
                # If the pixel value is under half of the <scaled_colour_range> only increase the amplitude
                if pixels[y, n_x] < scaled_colour_range/2:
                    frequency = 1
                    amplitude = pixels[y, n_x]
                # If the pixel value is over half of the <scaled_colour_range> use max amplitude and increase frequency
                else:
                    frequency = pixels[y, n_x] - scaled_colour_range/2 + 1
                    amplitude = max_amplitude

                # For each pixel of the processed image, <pixel_wave_size> x <pixel_wave_size> "super pixel" is created, that holds the wave for that pixel
                for i in range(pixel_wave_size):
                    n_i = i
                    n_offset = 1
                    if y % 2 != 0:
                        n_i = 0 - i + 20
                        n_offset = -1

                    # Calculate the current pixel coordinates and the next pixel coordinates, so they can be joined with a line
                    x_pos = n_x * pixel_wave_size + n_i
                    y_pos = (y * pixel_wave_size + pixel_wave_size/2) + (np.sin((n_i)/(pixel_wave_size/2)*frequency*np.pi)*amplitude)

                    next_x_pos = n_x * pixel_wave_size + n_i + n_offset
                    next_y_pos = (y * pixel_wave_size + pixel_wave_size/2) + (np.sin((n_i+n_offset)/(pixel_wave_size/2)*frequency*np.pi)*amplitude)
                    f.write(str(x_pos) + " " + str(round(y_pos)) + "\n")

                    draw.line(((x_pos, y_pos), (next_x_pos, next_y_pos)), fill=(0,0,0))
        f.close()
        self.result = f"\nTotal run time: {time.time() - start_time} seconds\n"

        self.finish_signal.emit()

        return image


    def linkern(self) -> None:
        # Runs the linkern.exe program
        linker_command = f"thepathmaker-x64\linkern.exe -o {cyc_path} {tsp_path}"
        linker_result = subprocess.Popen(linker_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

        # Continuous updates are emited through update_signal
        while linker_result.poll() is None:
            line = linker_result.stdout.readline()
            self.update_signal.emit(line)

        # Finished result/output emited through finish_signal
        self.result = linker_result

        # Emit a signal with the output
        self.finish_signal.emit()

    def dither(self, image) -> Image:
        start_time = time.time()
        self.update_signal.emit("Starting dithering")
        image = dithering.apply_jarvis_judice_ninke_dithering(image, tsp_path)
        self.result = f"\nTotal run time: {time.time() - start_time} seconds\n"
        self.finish_signal.emit()
        return image

    def getResult(self) -> subprocess.CompletedProcess:
        return self.result


# Canvas that displays the machine configuration
class ConfigurationCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 400)
        self.scale_factor = 1.0
        self.setMouseTracking(True)
        self.dragging = False
        self.start_pos = QPoint()
        self.cur_pos = QPoint()
        self.last_pos = QPoint()
        self.delta = QPoint()

        self.settings = None

        self.motorEllipseDia = 14
        self.penEllipseDia = 8

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        transform.translate(self.cur_pos.x(), self.cur_pos.y())
        painter.setTransform(transform)

        self.m1 = [0, 0]
        self.m2 = [self.m1[0] + self.settings["distanceBetweenMotors"], 0]

        painter.drawEllipse(int(self.m1[0] - self.motorEllipseDia/2)+IMAGE_OFFSET[0],   self.m1[1]+IMAGE_OFFSET[1],   self.motorEllipseDia,  self.motorEllipseDia)
        painter.drawEllipse(int(self.m2[0] - self.motorEllipseDia/2)+IMAGE_OFFSET[0],   self.m2[1]+IMAGE_OFFSET[1],   self.motorEllipseDia,  self.motorEllipseDia)

        paperOffsetCalculated = [0,0]
        penPosCalculated = [0,0]
        if (self.settings["startDistance"][0]**2) - ((self.settings["distanceBetweenMotors"]/2)**2) > 0:
            paperOffsetCalculated = [round(((self.settings["distanceBetweenMotors"]/2)-(self.settings["paperSize"][0]/2))),
                                     (round(math.sqrt(self.settings["startDistance"][0]**2 - (self.settings["distanceBetweenMotors"]/2)**2) - self.settings["paperOffset"] - self.settings["paperSize"][1]))]
            penPosCalculated = [round(self.settings["distanceBetweenMotors"]/2),
                                round(math.sqrt(self.settings["startDistance"][0]**2 - (self.settings["distanceBetweenMotors"]/2)**2))]

        painter.drawLine(int(self.m1[0]+self.motorEllipseDia/2+IMAGE_OFFSET[0]),    int(self.m1[1]+self.motorEllipseDia/2+IMAGE_OFFSET[1]),    penPosCalculated[0]+IMAGE_OFFSET[0],    penPosCalculated[1]+IMAGE_OFFSET[1])
        painter.drawLine(int(self.m2[0]-self.motorEllipseDia/2+IMAGE_OFFSET[0]),    int(self.m2[1]+self.motorEllipseDia/2+IMAGE_OFFSET[1]),    penPosCalculated[0]+IMAGE_OFFSET[0],    penPosCalculated[1]+IMAGE_OFFSET[1])

        painter.drawEllipse(int(penPosCalculated[0] - self.penEllipseDia/2)+IMAGE_OFFSET[0],   penPosCalculated[1]+IMAGE_OFFSET[1],   self.penEllipseDia, self.penEllipseDia)

        painter.drawRect(paperOffsetCalculated[0]+IMAGE_OFFSET[0], paperOffsetCalculated[1]+IMAGE_OFFSET[1],  self.settings["paperSize"][0],   self.settings["paperSize"][1])

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
            self.start_pos = event.pos() - self.last_pos

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.delta = event.pos()
            self.cur_pos = self.delta - self.start_pos
            self.last_pos = self.cur_pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


# Canvas that displays the image being processed
class ProcessCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 400, 400)
        self.zoomScale = 1.0
        self.setMouseTracking(True)
        self.dragging = False
        self.start_pos = QPoint()
        self.cur_pos = QPoint()
        self.last_pos = QPoint()
        self.delta = QPoint()

        self.imageScale = 1

        self.inputImage = None
        self.processedImage = None

    def paintEvent(self, event) -> None:
        # QTs function, updates the canvas
        if self.inputImage == None: return

        painter = QPainter(self)
        transform = QTransform()
        transform.scale(self.zoomScale, self.zoomScale)
        transform.translate(self.cur_pos.x(), self.cur_pos.y())
        painter.setTransform(transform)
        painter.drawPixmap(0, 0, QPixmap.fromImage(self.inputImage))

    def quantize_grayscale_image(self) -> None:
        if self.inputImage == None: return
        # Sets the grayscale image colour range to <num_colors> - so instead of 255 colour values it only has <num_colors> amount
        num_colors = 10
        scaling_factor = 255 / (num_colors-1)

        quantized_image = self.inputImage.copy()

        for x in range(quantized_image.width()):
            for y in range(quantized_image.height()):
                original_pixel_value = quantized_image.pixelColor(x, y).red()

                scaled_value = int(int(original_pixel_value / scaling_factor) * scaling_factor)

                quantized_pixel_color = QColor(scaled_value, scaled_value, scaled_value)
                quantized_image.setPixelColor(x, y, quantized_pixel_color)

        self.inputImage = quantized_image
        self.update()

    def loadImage(self, path: str) -> None:
        if not os.path.exists(path): return

        self.inputImage = QImage(path)
        self.update()

    def makePath(self, linker_result: subprocess.CompletedProcess) -> None:
        # Converts the output of linkern program to usable files for this program
        # linker_result = self.linkern()

        if linker_result.returncode == 0:

            image = pathMaker.pathMaker(tsp_path, cyc_path, output_coordinates_path)

            image = image.convert("RGBA")
            data = image.tobytes("raw","RGBA")

            self.inputImage = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)
            self.update()

    def convertToSteps(self) -> None:
        # Converts the coordinates of the points to steps of the stepper motor based on the <settings>
        if not os.path.exists(output_coordinates_path): return
        toSteps.convertToSteps(settings, output_coordinates_path, output_steps_path)

    def removeBg(self) -> None:
        # Removes the background of the image, and replaces it with white background instead of transparent
        if self.inputImage == None: return

        image = Image.fromqpixmap(self.inputImage)
        image = remove(image)

        jpg_image = Image.new("RGB", image.size, "white")
        jpg_image.paste(image, (0, 0), image)
        image = jpg_image

        image = image.convert("RGBA")
        data = image.tobytes("raw","RGBA")
        self.inputImage = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)
        self.update()

    def rotate90(self) -> None:
        if self.inputImage == None: return

        self.inputImage = self.inputImage.transformed(QTransform().rotate(90))
        self.update()

    def grayscale(self) -> None:
        # Converts the image to grayscale
        if self.inputImage == None: return

        self.inputImage = self.inputImage.convertToFormat(QImage.Format_Grayscale8)
        self.update()

    def scale(self) -> None:
        if self.inputImage == None: return

        self.inputImage = self.inputImage.scaled(int(self.inputImage.width()/self.imageScale), int(self.inputImage.height()/self.imageScale))
        self.update()

    # Mouse events for moving the image around and zooming in
    def wheelEvent(self, event):
        # Zoom in/out with the mouse wheel
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1
        self.zoomScale *= zoom_factor
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.pos() - self.last_pos

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.delta = event.pos()
            self.cur_pos = self.delta - self.start_pos
            self.last_pos = self.cur_pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


# Image processing windows
class ProcessImage(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self) -> None:
        leftInputs = QWidget()
        leftInputs.setStyleSheet("background-color: #EEE;")
        self.imageCanvas = ProcessCanvas()

        # Creating the lables and inputs
        self.btnOpenImage = QPushButton("Open Image")
        self.txtScale = QLineEdit("2")
        self.btnRotate90 = QPushButton("Rotate")
        self.btnScale = QPushButton("Scale")
        self.btnGrayscale = QPushButton("Grayscale")
        self.btnColourScale = QPushButton("Colour scale")
        self.btnDither = QPushButton("Dither")
        self.btnWave = QPushButton("Wave")
        self.btnRemoveBG = QPushButton("Remove BG")
        self.btnMakePath = QPushButton("Make Path")
        self.btnConvertToSteps = QPushButton("Convert to steps")

        self.lblOutput = QLabel("Output")
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        # Connecting the inputs to their functions
        self.btnOpenImage.clicked.connect(self.openImage)
        self.btnRotate90.clicked.connect(self.imageCanvas.rotate90)
        self.btnScale.clicked.connect(self.scaleImage)
        self.btnGrayscale.clicked.connect(self.imageCanvas.grayscale)
        self.btnDither.clicked.connect(self.start_dither)
        self.btnWave.clicked.connect(self.start_wave)
        self.btnRemoveBG.clicked.connect(self.imageCanvas.removeBg)
        self.btnColourScale.clicked.connect(self.imageCanvas.quantize_grayscale_image)
        self.btnMakePath.clicked.connect(self.start_linkern)
        self.btnConvertToSteps.clicked.connect(self.imageCanvas.convertToSteps)
        self.btnConvertToSteps.setObjectName("testBtn")

        self.vertical_spacer = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Adding the lables and inputs to the layout
        lytInputs = QGridLayout()
        lytInputs.addWidget(self.btnOpenImage, 0, 0, 1, 2)
        lytInputs.addWidget(self.btnScale, 1, 0)
        lytInputs.addWidget(self.txtScale, 1, 1)
        lytInputs.addWidget(self.btnRotate90, 2, 0)
        lytInputs.addWidget(self.btnGrayscale, 2, 1)
        lytInputs.addWidget(self.btnColourScale, 3, 0)
        lytInputs.addWidget(self.btnDither, 3, 1)
        lytInputs.addWidget(self.btnWave, 4, 0)
        lytInputs.addWidget(self.btnRemoveBG, 4, 1)
        lytInputs.addWidget(self.btnMakePath, 5, 0)
        lytInputs.addWidget(self.btnConvertToSteps, 5, 1)

        lytInputs.addWidget(self.lblOutput, 6, 0)
        lytInputs.addWidget(self.output_text_edit, 7, 0, 1, 2)

        lytInputs.addItem(self.vertical_spacer)

        leftInputs.setLayout(lytInputs)

        lytTabProcessImage = QHBoxLayout()
        lytTabProcessImage.addWidget(leftInputs)
        lytTabProcessImage.addWidget(self.imageCanvas)
        lytTabProcessImage.setStretchFactor(leftInputs, 2)
        lytTabProcessImage.setStretchFactor(self.imageCanvas, 7)

        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal.connect(self.update_output)
        self.worker_thread.finish_signal.connect(self.finish_output)
        self.worker_thread.image_signal.connect(self.image_output)

        self.setLayout(lytTabProcessImage)

    def start_linkern(self):
        self.worker_thread.function_type = FunctionTypeEnum.LINKERN
        self.worker_thread.start()

    def start_wave(self):
        image = Image.fromqpixmap(self.imageCanvas.inputImage).convert('L')
        image = ImageOps.invert(image)

        self.worker_thread.function_type = FunctionTypeEnum.WAVE
        self.worker_thread.image = image
        self.worker_thread.start()

    def start_dither(self):
        image = Image.fromqpixmap(self.imageCanvas.inputImage).convert('L')
        image = ImageOps.invert(image)

        self.worker_thread.function_type = FunctionTypeEnum.DITHER
        self.worker_thread.image = image
        self.worker_thread.start()

    def update_output(self, output):
        self.output_text_edit.append(output)

    def finish_output(self):
        if self.worker_thread.function_type == FunctionTypeEnum.LINKERN:
            result = self.worker_thread.getResult()
            self.imageCanvas.makePath(result)
            return
        result = self.worker_thread.getResult()
        self.output_text_edit.append(result)

    def image_output(self):
        image = self.worker_thread.image
        image = image.convert("RGBA")
        data = image.tobytes("raw","RGBA")

        self.imageCanvas.inputImage = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)
        self.imageCanvas.update()

    def scaleImage(self) -> None:
        if self.inputImage == None: return

        self.imageCanvas.imageScale = float(self.txtScale.text())
        self.imageCanvas.scale()

    def openImage(self) -> None:
        # Opens the windows for opening the image
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileFilter = "Images (*.png *.jpg *.jpeg *.bmp)"
        self.inputImage, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", fileFilter, options=options)
        self.imageCanvas.loadImage(self.inputImage)


# Drawing machine configuration window
class ConfigureMachine(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        leftInputs = QWidget()
        leftInputs.setStyleSheet("background-color: #EEE;")

        self.rightCanvas = ConfigurationCanvas()

        self.settings = DEFAULT_SETTINGS.copy()
        global settings
        settings = self.settings

        # Creating the lables and inputs
        self.lblBeltToothDistance = QLabel("Belt tooth distance")
        self.txtBeltToothDistance = QLineEdit()

        self.lblToothOnGear = QLabel("Tooth on gear")
        self.txtToothOnGear = QLineEdit()

        self.lblStepsPerRev = QLabel("Steps per rev")
        self.txtStepsPerRev = QLineEdit()

        self.lblMotorDir = QLabel("Motor direction")
        self.txtMotorDir1 = QLineEdit()
        self.txtMotorDir2 = QLineEdit()

        self.lblMotorDist = QLabel("Motor distance")
        self.txtMotorDist = QLineEdit()

        self.lblStartDist = QLabel("Start distance")
        self.txtStartDist1 = QLineEdit()
        self.txtStartDist2 = QLineEdit()

        self.lblPaperDimenions = QLabel("Paper dimensions")
        self.txtPaperDimenions1 = QLineEdit()
        self.txtPaperDimenions2 = QLineEdit()

        self.lblPaperOffset = QLabel("Paper offset")
        self.txtPaperOffset = QLineEdit()

        self.btnLoadDefaults = QPushButton("Load default settings")
        self.btnSave = QPushButton("Save", self)

        self.loadSettings()
        self.setValuesInput(self.settings)

        self.vertical_spacer = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Adding the lables and inputs to the layout
        lytInputs = QGridLayout()
        lytInputs.addWidget(self.lblBeltToothDistance, 0, 0)
        lytInputs.addWidget(self.txtBeltToothDistance, 0, 1)
        lytInputs.addWidget(self.lblToothOnGear, 1, 0)
        lytInputs.addWidget(self.txtToothOnGear, 1, 1)
        lytInputs.addWidget(self.lblStepsPerRev, 2, 0)
        lytInputs.addWidget(self.txtStepsPerRev, 2, 1)
        lytInputs.addWidget(self.lblMotorDir, 3, 0)
        lytInputs.addWidget(self.txtMotorDir1, 4, 0)
        lytInputs.addWidget(self.txtMotorDir2, 4, 1)
        lytInputs.addWidget(self.lblMotorDist, 5, 0)
        lytInputs.addWidget(self.txtMotorDist, 5, 1)
        lytInputs.addWidget(self.lblStartDist, 6, 0)
        lytInputs.addWidget(self.txtStartDist1, 7, 0)
        lytInputs.addWidget(self.txtStartDist2, 7, 1)
        lytInputs.addWidget(self.lblPaperDimenions, 8, 0)
        lytInputs.addWidget(self.txtPaperDimenions1, 9, 0)
        lytInputs.addWidget(self.txtPaperDimenions2, 9, 1)
        lytInputs.addWidget(self.lblPaperOffset, 10, 0)
        lytInputs.addWidget(self.txtPaperOffset, 10, 1)
        lytInputs.addWidget(self.btnLoadDefaults, 11, 0)
        lytInputs.addWidget(self.btnSave, 11, 1)

        lytInputs.addItem(self.vertical_spacer)

        leftInputs.setLayout(lytInputs)

        lytTabConfigureMachine = QHBoxLayout()
        lytTabConfigureMachine.addWidget(leftInputs)
        lytTabConfigureMachine.addWidget(self.rightCanvas)
        lytTabConfigureMachine.setStretchFactor(leftInputs, 2)
        lytTabConfigureMachine.setStretchFactor(self.rightCanvas, 7)

        self.setLayout(lytTabConfigureMachine)

        # Connecting the inputs to their functions
        self.txtPaperOffset.textChanged.connect(self.processSettings)
        self.txtMotorDist.textChanged.connect(self.processSettings)
        self.txtPaperDimenions1.textChanged.connect(self.processSettings)
        self.txtPaperDimenions2.textChanged.connect(self.processSettings)
        self.txtStartDist1.textChanged.connect(self.processSettings)
        self.txtStartDist2.textChanged.connect(self.processSettings)

        self.btnSave.clicked.connect(self.saveSettings)
        self.btnLoadDefaults.clicked.connect(self.loadDefaultSettings)

        self.processSettings()

    def processSettings(self) -> None:
        # Sets the settings to the values of the input fields
        self.settings["beltToothDistance"] = int(self.txtBeltToothDistance.text())
        self.settings["toothOngear"] = int(self.txtToothOnGear.text())
        self.settings["stepsPerRev"] = int(self.txtStepsPerRev.text())
        self.settings["motorDir"] = [int(self.txtMotorDir1.text()), int(self.txtMotorDir2.text())]
        self.settings["distanceBetweenMotors"] = int(self.txtMotorDist.text())
        self.settings["startDistance"] = [int(self.txtStartDist1.text()), int(self.txtStartDist2.text())]
        self.settings["paperSize"] = [int(self.txtPaperDimenions1.text()), int(self.txtPaperDimenions2.text())]
        self.settings["paperOffset"] = int(self.txtPaperOffset.text())

        self.rightCanvas.setSettings(self.settings)
        self.rightCanvas.update()
        global settings
        settings = self.settings

    def setValuesInput(self, vals: dict) -> None:
        # Sets the input fields to the <vals> values
        if vals == None: return

        self.txtBeltToothDistance.setText(str(vals["beltToothDistance"]))
        self.txtToothOnGear.setText(str(vals["toothOngear"]))
        self.txtStepsPerRev.setText(str(vals["stepsPerRev"]))
        self.txtMotorDir1.setText(str(vals["motorDir"][0]))
        self.txtMotorDir2.setText(str(vals["motorDir"][1]))
        self.txtMotorDist.setText(str(vals["distanceBetweenMotors"]))
        self.txtStartDist1.setText(str(vals["startDistance"][0]))
        self.txtStartDist2.setText(str(vals["startDistance"][1]))
        self.txtPaperDimenions1.setText(str(vals["paperSize"][0]))
        self.txtPaperDimenions2.setText(str(vals["paperSize"][1]))
        self.txtPaperOffset.setText(str(vals["paperOffset"]))

    def loadDefaultSettings(self) -> None:

        self.setValuesInput(DEFAULT_SETTINGS.copy())
        self.processSettings()
        self.rightCanvas.setSettings(self.settings)
        self.rightCanvas.update()
        global settings
        settings = self.settings

    def saveSettings(self) -> None:
        # Saves settings to <SETTINGS> file
        with open(SETTINGS, "w") as settings_file:
            json.dump(self.settings, settings_file)

    def loadSettings(self) -> None:
        # Loads settings if the <SETTINGS> file exists
        # Otherwise loads default settings
        if not os.path.exists(SETTINGS):
            self.loadDefaultSettings()

        with open(SETTINGS, "r") as settings_file:
            self.settings = json.load(settings_file)
            global settings
            settings = self.settings


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        tab_widget = QTabWidget(self)

        self.tabConfigureMachine = ConfigureMachine()
        self.tabProcessImage = ProcessImage()

        tab_widget.addTab(self.tabProcessImage, "Process Image")
        tab_widget.addTab(self.tabConfigureMachine, "Configure Machine")

        self.setCentralWidget(tab_widget)


if __name__ == '__main__':
    if not os.path.exists(GENERATED_FILES):
        os.makedirs(GENERATED_FILES)

    app = QApplication(sys.argv)
    qss = "style.qss"
    with open(qss, "r") as ss:
        app.setStyleSheet(ss.read())
    window = MyWindow()
    window.showMaximized()
    sys.exit(app.exec_())
