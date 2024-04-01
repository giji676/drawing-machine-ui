import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

fEnd, gStart = (
    1 * 20,
    20,
)  # fEnd = where the function f will end, gStart = where the function g will start

pixel_size = 20
minX, maxX = 0, 40  # min and max values of the x axis


def wave(x, frequency, amplitude):
    return np.sin(x / (pixel_size / 2) * frequency * np.pi) * amplitude


def psi(x):  # Ψ or "psi" function
    result = np.zeros_like(x)
    result[x > 0] = np.exp(-1 / x[x > 0])
    return result


def phi(x):  # Φ or "phi" function
    condition_1 = x <= 0
    condition_2 = (x > 0) & (x < 1)
    condition_3 = x >= 1

    result = np.zeros_like(x)
    result[condition_1] = 0
    result[condition_2] = psi(x[condition_2]) / (
        psi(x[condition_2]) + psi(1 - x[condition_2])
    )
    result[condition_3] = 1

    return result


def phiab(x, a, b):  # phi function with a and b as input for domain control
    return phi((x - a) / (b - a))


def smooth(x_smoothed, a, b, x1, x2, f1, a1, f2, a2):
    return (1 - phiab(x_smoothed, a, b)) * wave(x_smoothed, f1, a1) + phiab(
        x_smoothed, a, b
    ) * wave(x_smoothed, f2, a2)


smoothing_start, smoothing_finish = pixel_size - 10, pixel_size + 10


def process(arr):
    processed_wave = []
    for j in range(len(arr)):
        processed_wave_row = []
        for i in range(len(arr[j]) - 1):
            f1, a1 = arr[j][i]
            f2, a2 = arr[j][i + 1]
            x1 = np.linspace(minX, fEnd - 1, pixel_size)
            x2 = np.linspace(gStart, maxX - 1, pixel_size)

            x_smoothed = np.linspace(minX, maxX - 1, pixel_size * 2)
            y_smoothed = smooth(
                x_smoothed, smoothing_start, smoothing_finish, x1, x2, f1, a1, f2, a2
            )
            for val in y_smoothed:
                processed_wave_row.append(val)
        processed_wave.append(processed_wave_row)
    return processed_wave
