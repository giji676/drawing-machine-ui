import os

from PIL import Image, ImageDraw, ImageOps
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QTransform
from PyQt5.QtWidgets import (QApplication, QFileDialog, QGridLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
                             QTextEdit, QWidget, QCheckBox)

from src.utils import constants, svg_parser, FunctionTypeEnum, WorkerThread
from .process_canvas import ProcessCanvas

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
        if os.path.exists(constants.TSP_PATH):
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
        if gcode_convertor.SVGToGCODE(path, constants.OUTPUT_COODINATES_PATH) == 1:
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
        f = open(constants.OUTPUT_COODINATES_PATH, "r")
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

        f = open(constants.OUTPUT_COODINATES_PATH, "r")

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
        f = open(constants.OUTPUT_COODINATES_PATH, "w")
        f.writelines(flipped_image)
        f.close()

        return image

