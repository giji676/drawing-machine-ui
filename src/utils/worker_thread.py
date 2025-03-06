import time
import subprocess
import numpy as np

from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image, ImageDraw

from src.image_processing import dithering, wave_smoother, wave_smoother_standalone
from . import FunctionTypeEnum, constants


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

        f = open(constants.OUTPUT_COODINATES_PATH, "w")

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
        linker_command = f"{constants.PATH_MAKER} -o {constants.CYC_PATH} {constants.TSP_PATH}"
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
        image = dithering.applyDithering(image, constants.TSP_PATH)
        self.result = f"\nTotal run time: {time.time() - start_time} seconds\n"
        self.finish_signal.emit()
        return image

    def getResult(self) -> subprocess.CompletedProcess:
        return self.result

