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
from rembg import remove

from src.image_processing import dithering, wave_smoother, wave_smoother_standalone
from src.utils import path_maker, to_steps, svg_parser
#from src.utils import gcode_convertor


GENERATED_FILES = "generated_files"
STYLE = os.path.normpath("src\style\style.qss")
PATH_MAKER = os.path.normpath(f"external\\thepathmaker-x64\\linkern.exe")

IMAGE_TSP = "image.tsp"
IMAGE_CYC = "image.cyc"
OUTPUT_COORDINATES_TXT = "output_coordinates.txt"
OUTPUT_STEPS_TXT = "path.txt"

tsp_path = os.path.join(GENERATED_FILES, IMAGE_TSP)
cyc_path = os.path.join(GENERATED_FILES, IMAGE_CYC)
output_coordinates_path = os.path.join(GENERATED_FILES, OUTPUT_COORDINATES_TXT)
output_steps_path = os.path.join(GENERATED_FILES, OUTPUT_STEPS_TXT)

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
    "paperOffset": 35,
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
        self.wave_smooth = None

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

    def wave(self, image: Image) -> Image:
        # Converts the image to waves
        if not image:
            return None

        f = open(output_coordinates_path, "w")

        self.update_signal.emit("Starting conversion to wave")
        start_time = time.time()

        # Range of wave values: 0 = horizontal line, max = dense wave - hight amplitude and frequency
        scaled_colour_range = 10
        pixel_wave_size = 20

        max_amplitude = pixel_wave_size / 2

        pixels = np.array(image)
        height, width = pixels.shape

        if self.wave_smooth:
            wave_function_arr = wave_smoother.genWave(
                pixels
            )

            processed_wave = wave_smoother_standalone.process(wave_function_arr)
            processed_height, processed_width = len(processed_wave) * pixel_wave_size, len(
                processed_wave[0]
            )

            image = Image.new("RGB", (processed_width, processed_height), color="white")
            draw = ImageDraw.Draw(image)

            for y in range(len(processed_wave)):
                for x in range(processed_width-1):
                    self.update_signal.emit(
                        f"{str((y*width)+int(x/pixel_wave_size)+1)}/{str(height*width)}, {str(round(time.time() - start_time, 3))}"
                    )

                    y_offset = y * pixel_wave_size + pixel_wave_size / 2
                    draw.line(((x, y_offset + processed_wave[y][x]), (x+1, y_offset + processed_wave[y][x+1])), fill=(0, 0, 0))

                    f.write(str(x) + " " + str(round(y_offset + processed_wave[y][x])) + "\n")

            f.close()
            self.result = (f"\nTotal run time: {round(time.time() - start_time, 3)} seconds\n")
            self.finish_signal.emit()

            return image

        new_height, new_width = height * pixel_wave_size, width * pixel_wave_size

        image = Image.new("RGB", (new_width, new_height), color="white")
        draw = ImageDraw.Draw(image)

        for y in range(height):
            for x in range(width):
                self.update_signal.emit(
                    f"{str((y*width)+x)}/{str(height*width-1)}, {str(round(time.time() - start_time, 3))}"
                )
                n_x = x
                # Every other y level needs to start from the end so the other of the horizontal lines is: left-right-right-left...
                if y % 2 != 0:
                    n_x = width - 1 - x
                amplitude = 0
                frequency = 0

                pixels[y, n_x] = round(
                    pixels[y, n_x] / ((2**8)/scaled_colour_range))
                # If the pixel value is under half of the <scaled_colour_range> only increase the amplitude
                if pixels[y, n_x] < scaled_colour_range / 2:
                    frequency = 1
                    amplitude = pixels[y, n_x]
                # If the pixel value is over half of the <scaled_colour_range> use max amplitude and increase frequency
                else:
                    frequency = pixels[y, n_x] - scaled_colour_range / 2 + 1
                    amplitude = max_amplitude

                # For each pixel of the processed image, <pixel_wave_size> x <pixel_wave_size> "super pixel" is created, that holds the wave for that pixel
                for i in range(pixel_wave_size):
                    n_i = i
                    n_offset = 1
                    if y % 2 != 0:
                        n_i = 0 - i + pixel_wave_size
                        n_offset = -1

                    # Calculate the current pixel coordinates and the next pixel coordinates, so they can be joined with a line
                    x_pos = n_x * pixel_wave_size + n_i
                    y_pos = (y * pixel_wave_size + pixel_wave_size / 2) + (
                        np.sin((n_i) / (pixel_wave_size / 2)
                               * frequency * np.pi)
                        * amplitude
                    )

                    next_x_pos = n_x * pixel_wave_size + n_i + n_offset
                    next_y_pos = (y * pixel_wave_size + pixel_wave_size / 2) + (
                        np.sin(
                            (n_i + n_offset) /
                            (pixel_wave_size / 2) * frequency * np.pi
                        )
                        * amplitude
                    )
                    f.write(str(x_pos) + " " + str(round(y_pos)) + "\n")

                    draw.line(
                        ((x_pos, y_pos), (next_x_pos, next_y_pos)), fill=(0, 0, 0)
                    )
        f.close()
        self.result = (
            f"\nTotal run time: {round(time.time() - start_time, 3)} seconds\n"
        )

        self.finish_signal.emit()

        return image

    def linkern(self) -> None:
        # Runs the linkern.exe program
        linker_command = f"{PATH_MAKER} -o {cyc_path} {tsp_path}"
        print(linker_command)
        linker_result = subprocess.Popen(
            linker_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

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
        image = dithering.applyDithering(image, tsp_path)
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
            int(self.m1[0] - self.motor_ellipse_dia / 2) + IMAGE_OFFSET[0],
            self.m1[1] + IMAGE_OFFSET[1],
            self.motor_ellipse_dia,
            self.motor_ellipse_dia,
        )
        painter.drawEllipse(
            int(self.m2[0] - self.motor_ellipse_dia / 2) + IMAGE_OFFSET[0],
            self.m2[1] + IMAGE_OFFSET[1],
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
            int(self.m1[0] + self.motor_ellipse_dia / 2 + IMAGE_OFFSET[0]),
            int(self.m1[1] + self.motor_ellipse_dia / 2 + IMAGE_OFFSET[1]),
            pen_pos_calculated[0] + IMAGE_OFFSET[0],
            pen_pos_calculated[1] + IMAGE_OFFSET[1],
        )
        painter.drawLine(
            int(self.m2[0] - self.motor_ellipse_dia / 2 + IMAGE_OFFSET[0]),
            int(self.m2[1] + self.motor_ellipse_dia / 2 + IMAGE_OFFSET[1]),
            pen_pos_calculated[0] + IMAGE_OFFSET[0],
            pen_pos_calculated[1] + IMAGE_OFFSET[1],
        )

        painter.drawEllipse(
            int(pen_pos_calculated[0] -
                self.pen_ellipse_dia / 2) + IMAGE_OFFSET[0],
            pen_pos_calculated[1] + IMAGE_OFFSET[1],
            self.pen_ellipse_dia,
            self.pen_ellipse_dia,
        )

        painter.drawRect(
            paper_offset_calculated[0] + IMAGE_OFFSET[0],
            paper_offset_calculated[1] + IMAGE_OFFSET[1],
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


# Canvas that displays the image being processed
class ProcessCanvas(QWidget):
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

        self.process_image_window = None

        self.image_scale = 1

        self.input_image = None
        self.processed_image = None

    def paintEvent(self, event) -> None:
        # QTs function, updates the canvas
        if self.input_image is None:
            return

        painter = QPainter(self)
        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        transform.translate(self.cur_pos.x(), self.cur_pos.y())
        painter.setTransform(transform)
        painter.drawPixmap(0, 0, QPixmap.fromImage(self.input_image))

    def qimageToPil(self, qimage):
        # Get image dimensions
        width = qimage.width()
        height = qimage.height()

        # Convert QImage to a format suitable for PIL
        qimage = qimage.convertToFormat(QImage.Format_RGBA8888)

        # Get the binary data from QImage
        ptr = qimage.constBits()
        ptr.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)

        # Convert to numpy array and reshape
        arr = np.frombuffer(ptr, np.uint8).reshape(height, width, 4)

        # Convert numpy array to PIL Image
        return Image.fromarray(arr)

    def quantizeGrayscaleImage(self) -> None:
        if self.input_image is None:
            return
        # Sets the grayscale image colour range to <num_colors> - so instead of 255 colour values it only has <num_colors> amount
        num_colors = 10
        scaling_factor = 255 / (num_colors - 1)

        quantized_image = self.input_image.copy()

        for x in range(quantized_image.width()):
            for y in range(quantized_image.height()):
                original_pixel_value = quantized_image.pixelColor(x, y).red()

                scaled_value = int(
                    int(original_pixel_value / scaling_factor) * scaling_factor
                )

                quantized_pixel_color = QColor(
                    scaled_value, scaled_value, scaled_value)
                quantized_image.setPixelColor(x, y, quantized_pixel_color)

        self.input_image = quantized_image
        self.update()

    def loadImage(self, path: str) -> None:
        if not os.path.exists(path):
            return

        self.input_image = QImage(path)
        self.update()

    def makePath(self, linker_result: subprocess.CompletedProcess) -> None:
        # Converts the output of linkern program to usable files for this program
        # linker_result = self.linkern()

        if linker_result.returncode == 0:

            image = path_maker.pathMaker(
                tsp_path, cyc_path, output_coordinates_path)

            image = image.convert("RGBA")
            data = image.tobytes("raw", "RGBA")

            self.input_image = QImage(
                data, image.size[0], image.size[1], QImage.Format_RGBA8888
            )
            self.update()

    def convertToSteps(self) -> None:
        # Converts the coordinates of the points to steps of the stepper motor based on the <settings>
        if not os.path.exists(output_coordinates_path):
            return
        steps_output = to_steps.convertToSteps(
            settings, output_coordinates_path, output_steps_path, fit=True, min_pen_pickup=self.process_image_window.cbx_min_pen_pickup.isChecked()
        )
        if steps_output:
            self.process_image_window.updateOutput(steps_output)

    def removeBg(self) -> None:
        # Removes the background of the image, and replaces it with white background instead of transparent
        if self.input_image is None:
            return

        image = self.qimageToPil(self.input_image)
        #image = Image.fromqpixmap(self.input_image)
        image = remove(image)

        jpg_image = Image.new("RGB", image.size, "white")
        jpg_image.paste(image, (0, 0), image)
        image = jpg_image

        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        self.input_image = QImage(
            data, image.size[0], image.size[1], QImage.Format_RGBA8888
        )
        self.update()

    def rotate90(self) -> None:
        if self.input_image is None:
            return

        self.input_image = self.input_image.transformed(QTransform().rotate(90))
        self.update()

    def grayscale(self) -> None:
        # Converts the image to grayscale
        if self.input_image is None:
            return

        self.input_image = self.input_image.convertToFormat(
            QImage.Format_Grayscale8)
        self.update()

    def scale(self) -> None:
        if self.input_image is None:
            return

        self.input_image = self.input_image.scaled(
            int(self.input_image.width() / self.image_scale),
            int(self.input_image.height() / self.image_scale),
        )
        self.update()

    def saveImage(self) -> None:
        if self.input_image is None:
            return
        self.input_image.save("test.png")

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


# Image processing windows
class ProcessImage(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self) -> None:
        self.left_input_panel = QWidget()
        self.left_input_panel.setStyleSheet("background-color: #EEE;")
        self.image_canvas = ProcessCanvas()
        self.image_canvas.process_image_window = self

        # Creating the lables and inputs
        self.btn_open_image = QPushButton("Open Image")
        self.btn_clear_all = QPushButton("Clear All")
        self.txt_scale = QLineEdit("2")
        self.btn_rotate_90 = QPushButton("Rotate")
        self.btn_scale = QPushButton("Scale")
        self.btn_grayscale = QPushButton("Grayscale")
        self.btn_colourscale = QPushButton("Colour scale")
        self.btn_dither = QPushButton("Dither")
        self.btn_wave = QPushButton("Wave")
        self.btn_remove_BG = QPushButton("Remove BG")
        self.btn_make_path = QPushButton("Make Path")
        self.btn_convert_to_steps = QPushButton("Convert to steps")
        self.btn_save_image = QPushButton("Save Image")
        self.cbx_wave_smooth = QCheckBox("Use Wave Smoother")
        self.cbx_min_pen_pickup = QCheckBox("Use Minimum Pen Pickup Distance")

        self.lbl_output = QLabel("Output")
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)

        # Connecting the inputs to their functions
        self.btn_open_image.clicked.connect(self.openImage)
        self.btn_clear_all.clicked.connect(self.clearAll)
        self.btn_rotate_90.clicked.connect(self.image_canvas.rotate90)
        self.btn_scale.clicked.connect(self.scaleImage)
        self.btn_grayscale.clicked.connect(self.image_canvas.grayscale)
        self.btn_dither.clicked.connect(self.startDither)
        self.btn_wave.clicked.connect(self.startWave)
        self.btn_remove_BG.clicked.connect(self.image_canvas.removeBg)
        self.btn_colourscale.clicked.connect(
        self.image_canvas.quantizeGrayscaleImage)
        self.btn_make_path.clicked.connect(self.startLinkern)
        self.btn_convert_to_steps.clicked.connect(self.image_canvas.convertToSteps)
        self.btn_convert_to_steps.setObjectName("testBtn")
        self.btn_save_image.clicked.connect(self.image_canvas.saveImage)
        

        self.vertical_spacer = QSpacerItem(
            0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding
        )

        # Adding the lables and inputs to the layout
        self.lyt_inputs = QGridLayout()
        self.lyt_inputs.addWidget(self.btn_open_image, 0, 0)
        self.lyt_inputs.addWidget(self.btn_clear_all, 0, 1)
        self.lyt_inputs.addWidget(self.btn_scale, 1, 0)
        self.lyt_inputs.addWidget(self.txt_scale, 1, 1)
        self.lyt_inputs.addWidget(self.btn_rotate_90, 2, 0)
        self.lyt_inputs.addWidget(self.btn_grayscale, 2, 1)
        self.lyt_inputs.addWidget(self.btn_colourscale, 3, 0)
        self.lyt_inputs.addWidget(self.btn_dither, 3, 1)
        self.lyt_inputs.addWidget(self.btn_wave, 4, 0)
        self.lyt_inputs.addWidget(self.btn_remove_BG, 4, 1)
        self.lyt_inputs.addWidget(self.btn_make_path, 5, 0)
        self.lyt_inputs.addWidget(self.btn_convert_to_steps, 5, 1)
        self.lyt_inputs.addWidget(self.btn_save_image, 6, 0)
        self.lyt_inputs.addWidget(self.cbx_wave_smooth, 6, 1)
        self.lyt_inputs.addWidget(self.cbx_min_pen_pickup, 7, 0)

        self.lyt_inputs.addWidget(self.lbl_output, 9, 0)
        self.lyt_inputs.addWidget(self.output_text_edit, 10, 0, 1, 2)

        self.lyt_inputs.addItem(self.vertical_spacer)

        self.left_input_panel.setLayout(self.lyt_inputs)

        self.lyt_process_image_tab = QHBoxLayout()
        self.lyt_process_image_tab.addWidget(self.left_input_panel)
        self.lyt_process_image_tab.addWidget(self.image_canvas)
        self.lyt_process_image_tab.setStretchFactor(self.left_input_panel, 2)
        self.lyt_process_image_tab.setStretchFactor(self.image_canvas, 7)

        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal.connect(self.updateOutput)
        self.worker_thread.finish_signal.connect(self.finishOutput)
        self.worker_thread.image_signal.connect(self.imageOutput)

        self.setLayout(self.lyt_process_image_tab)

    def startLinkern(self):
        if os.path.exists(tsp_path):
            self.worker_thread.function_type = FunctionTypeEnum.LINKERN
            self.worker_thread.start()


    def startWave(self):
        if self.image_canvas.input_image is None:
            return
        image = self.image_canvas.qimageToPil(self.image_canvas.input_image).convert("L")
        #image = Image.fromqpixmap(self.image_canvas.input_image).convert("L")
        image = ImageOps.invert(image)

        self.worker_thread.function_type = FunctionTypeEnum.WAVE
        self.worker_thread.wave_smooth = self.cbx_wave_smooth.isChecked()
        self.worker_thread.image = image
        self.worker_thread.start()


    def startDither(self):
        if self.image_canvas.input_image is None:
            return

        image = self.image_canvas.qimageToPil(self.image_canvas.input_image).convert("L")
        #image = Image.fromqpixmap(self.image_canvas.input_image).convert("L")
        image = ImageOps.invert(image)

        self.worker_thread.function_type = FunctionTypeEnum.DITHER
        self.worker_thread.image = image
        self.worker_thread.start()

    def updateOutput(self, output):
        self.output_text_edit.append(output)

    def finishOutput(self):
        if self.worker_thread.function_type == FunctionTypeEnum.LINKERN:
            result = self.worker_thread.getResult()
            self.image_canvas.makePath(result)
            return
        result = self.worker_thread.getResult()
        self.output_text_edit.append(result)

    def imageOutput(self):
        image = self.worker_thread.image
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")

        self.image_canvas.input_image = QImage(
            data, image.size[0], image.size[1], QImage.Format_RGBA8888
        )
        self.image_canvas.update()

    def scaleImage(self) -> None:
        if self.image_canvas.input_image is None:
            return

        self.image_canvas.image_scale = float(self.txt_scale.text())
        self.image_canvas.scale()

    def clearAll(self) -> None:
        self.image_canvas.input_image = None
        self.image_canvas.scale_factor = 1.0
        self.image_canvas.update()
        self.output_text_edit.clear()

    def openImage(self) -> None:
        # Opens the windows for opening the image
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "Images (*.png *.jpg *.jpeg *.bmp *.svg)"
        self.input_image, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", file_filter, options=options
        )

        if ".svg" in self.input_image:
            # Program cannot work with normal SVG files,
            # but if it's the path of the image
            # (such as output of the "DrawingBot" program)
            # then it can be turned into GCODE,
            # and then turned into normal coordinate image

            # self.SVGToGCODE(self.input_image)

            """ New custom svg parser """
            self.parseSvg(self.input_image)
            return

        self.image_canvas.loadImage(self.input_image)

    def parseSvg(self, path) -> None:
        image = svg_parser.parseSvg(path, self.updateOutput)
        if image == None:
            return

        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")

        self.image_canvas.input_image = QImage(
            data, image.size[0], image.size[1], QImage.Format_RGBA8888
        )
        self.image_canvas.update()

    def SVGToGCODE(self, path) -> None:
        """
        # Turns SVG path to GCODE
        if gcode_convertor.SVGToGCODE(path, output_coordinates_path) == 1:
            # Turnes the GCODE into normal image
            image = self.gcodePlotter()
            image = image.convert("RGBA")
            data = image.tobytes("raw", "RGBA")

            self.image_canvas.input_image = QImage(
                data, image.size[0], image.size[1], QImage.Format_RGBA8888
            )
            self.image_canvas.update()
            """

    def gcodePlotter(self) -> Image:
        f = open(output_coordinates_path, "r")
        max_x, max_y = 0, 0

        # Find max x and y
        for line in f:
            line = line.strip()

            if line == "PENUP" or line == "PENDOWN":
                continue

            line = line.split()
            x, y = float(line[0]), float(line[1])

            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
        f.close()
        max_x, max_y = int(max_x) + 1, int(max_y) + 1

        image = Image.new("RGB", (max_x, max_y), color="white")
        draw = ImageDraw.Draw(image)

        x, y = 0, 0
        pen_down = False
        flipped_image = []

        f = open(output_coordinates_path, "r")

        # Flip the image horizontaly and draw the image
        for line in f:
            line = line.strip()

            if line == "PENUP":
                pen_down = False
                flipped_image.append(f"{line}\n")
            elif line == "PENDOWN":
                pen_down = True
                flipped_image.append(f"{line}\n")

            else:
                line = line.split()
                n_x, n_y = float(line[0]), float(line[1])
                if pen_down:
                    draw.line(((x, max_y - y), (n_x, max_y - n_y)),
                              fill=(0, 0, 0))
                flipped_image.append(f"{n_x} {max_y - n_y}\n")

                x, y = n_x, n_y

        f.close()
        f = open(output_coordinates_path, "w")
        f.writelines(flipped_image)
        f.close()

        return image


# Drawing machine configuration window
class ConfigureMachine(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self) -> None:
        self.left_input_panel = QWidget()
        self.left_input_panel.setStyleSheet("background-color: #EEE;")

        self.right_canvas = ConfigurationCanvas()

        self.settings = DEFAULT_SETTINGS.copy()
        global settings
        settings = self.settings

        # Creating the lables and inputs
        self.lbl_belt_tooth_distance = QLabel("Belt tooth distance")
        self.txt_belt_tooth_distance = QLineEdit()

        self.lbl_tooth_on_gear = QLabel("Tooth on gear")
        self.txt_tooth_on_gear = QLineEdit()

        self.lbl_steps_per_rev = QLabel("Steps per rev")
        self.txt_steps_per_rev = QLineEdit()

        self.lbl_motor_dir = QLabel("Motor direction")
        self.txt_motor_dir_1 = QLineEdit()
        self.txt_motor_dir_2 = QLineEdit()

        self.lbl_motor_dist = QLabel("Motor distance")
        self.txt_motor_dist = QLineEdit()

        self.lbl_start_dist = QLabel("Start distance")
        self.txt_start_dist_1 = QLineEdit()
        self.txt_start_dist_2 = QLineEdit()

        self.lbl_paper_dimenions = QLabel("Paper dimensions")
        self.txt_paper_dimenions_1 = QLineEdit()
        self.txt_paper_dimenions_2 = QLineEdit()

        self.lbl_paper_offset = QLabel("Paper offset")
        self.txt_paper_offset = QLineEdit()

        self.btn_load_defaults = QPushButton("Load default settings")
        self.btn_save = QPushButton("Save", self)

        self.loadSettings()
        self.setValuesInput(self.settings)

        self.vertical_spacer = QSpacerItem(
            0, 20, QSizePolicy.Fixed, QSizePolicy.Expanding
        )

        # Adding the lables and inputs to the layout
        self.lyt_inputs = QGridLayout()
        self.lyt_inputs.addWidget(self.lbl_belt_tooth_distance, 0, 0)
        self.lyt_inputs.addWidget(self.txt_belt_tooth_distance, 0, 1)
        self.lyt_inputs.addWidget(self.lbl_tooth_on_gear, 1, 0)
        self.lyt_inputs.addWidget(self.txt_tooth_on_gear, 1, 1)
        self.lyt_inputs.addWidget(self.lbl_steps_per_rev, 2, 0)
        self.lyt_inputs.addWidget(self.txt_steps_per_rev, 2, 1)
        self.lyt_inputs.addWidget(self.lbl_motor_dir, 3, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dir_1, 4, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dir_2, 4, 1)
        self.lyt_inputs.addWidget(self.lbl_motor_dist, 5, 0)
        self.lyt_inputs.addWidget(self.txt_motor_dist, 5, 1)
        self.lyt_inputs.addWidget(self.lbl_start_dist, 6, 0)
        self.lyt_inputs.addWidget(self.txt_start_dist_1, 7, 0)
        self.lyt_inputs.addWidget(self.txt_start_dist_2, 7, 1)
        self.lyt_inputs.addWidget(self.lbl_paper_dimenions, 8, 0)
        self.lyt_inputs.addWidget(self.txt_paper_dimenions_1, 9, 0)
        self.lyt_inputs.addWidget(self.txt_paper_dimenions_2, 9, 1)
        self.lyt_inputs.addWidget(self.lbl_paper_offset, 10, 0)
        self.lyt_inputs.addWidget(self.txt_paper_offset, 10, 1)
        self.lyt_inputs.addWidget(self.btn_load_defaults, 11, 0)
        self.lyt_inputs.addWidget(self.btn_save, 11, 1)

        self.lyt_inputs.addItem(self.vertical_spacer)

        self.left_input_panel.setLayout(self.lyt_inputs)

        self.lyt_configure_machine_tab = QHBoxLayout()
        self.lyt_configure_machine_tab.addWidget(self.left_input_panel)
        self.lyt_configure_machine_tab.addWidget(self.right_canvas)
        self.lyt_configure_machine_tab.setStretchFactor(self.left_input_panel, 2)
        self.lyt_configure_machine_tab.setStretchFactor(self.right_canvas, 7)

        self.setLayout(self.lyt_configure_machine_tab)

        # Connecting the inputs to their functions
        self.txt_paper_offset.textChanged.connect(self.processSettings)
        self.txt_motor_dist.textChanged.connect(self.processSettings)
        self.txt_paper_dimenions_1.textChanged.connect(self.processSettings)
        self.txt_paper_dimenions_2.textChanged.connect(self.processSettings)
        self.txt_start_dist_1.textChanged.connect(self.processSettings)
        self.txt_start_dist_2.textChanged.connect(self.processSettings)

        self.btn_save.clicked.connect(self.saveSettings)
        self.btn_load_defaults.clicked.connect(self.loadDefaultSettings)

        self.processSettings()

    def processSettings(self) -> None:
        # Sets the settings to the values of the input fields
        self.settings["beltToothDistance"] = int(
            self.txt_belt_tooth_distance.text())
        self.settings["toothOngear"] = int(self.txt_tooth_on_gear.text())
        self.settings["stepsPerRev"] = int(self.txt_steps_per_rev.text())
        self.settings["motorDir"] = [
            int(self.txt_motor_dir_1.text()),
            int(self.txt_motor_dir_2.text()),
        ]
        self.settings["distanceBetweenMotors"] = int(self.txt_motor_dist.text())
        self.settings["startDistance"] = [
            int(self.txt_start_dist_1.text()),
            int(self.txt_start_dist_2.text()),
        ]
        self.settings["paperSize"] = [
            int(self.txt_paper_dimenions_1.text()),
            int(self.txt_paper_dimenions_2.text()),
        ]
        self.settings["paperOffset"] = int(self.txt_paper_offset.text())

        self.right_canvas.setSettings(self.settings)
        self.right_canvas.update()
        global settings
        settings = self.settings

    def setValuesInput(self, vals: dict) -> None:
        # Sets the input fields to the <vals> values
        if vals is None:
            return

        self.txt_belt_tooth_distance.setText(str(vals["beltToothDistance"]))
        self.txt_tooth_on_gear.setText(str(vals["toothOngear"]))
        self.txt_steps_per_rev.setText(str(vals["stepsPerRev"]))
        self.txt_motor_dir_1.setText(str(vals["motorDir"][0]))
        self.txt_motor_dir_2.setText(str(vals["motorDir"][1]))
        self.txt_motor_dist.setText(str(vals["distanceBetweenMotors"]))
        self.txt_start_dist_1.setText(str(vals["startDistance"][0]))
        self.txt_start_dist_2.setText(str(vals["startDistance"][1]))
        self.txt_paper_dimenions_1.setText(str(vals["paperSize"][0]))
        self.txt_paper_dimenions_2.setText(str(vals["paperSize"][1]))
        self.txt_paper_offset.setText(str(vals["paperOffset"]))

    def loadDefaultSettings(self) -> None:

        self.setValuesInput(DEFAULT_SETTINGS.copy())
        self.processSettings()
        self.right_canvas.setSettings(self.settings)
        self.right_canvas.update()
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
            self.saveSettings()

        with open(SETTINGS, "r") as settings_file:
            self.settings = json.load(settings_file)
            global settings
            settings = self.settings


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
    if not os.path.exists(GENERATED_FILES):
        os.makedirs(GENERATED_FILES)

    app = QApplication(sys.argv)
    qss = STYLE
    with open(qss, "r") as ss:
        app.setStyleSheet(ss.read())
    window = MyWindow()
    window.showMaximized()
    sys.exit(app.exec_())
