import numpy as np
from PIL import Image, ImageOps
import math

Gx = [[-1, 0, 1],
      [-2, 0, 2],
      [-1, 0, 1]]

Gy = [[-1, -2, -1],
      [0, 0, 0],
      [1, 2, 1]]

def remap(val, in_min, in_max, out_min, out_max):
    return max(out_min, min((val - in_min) * (out_max - out_min) // (in_max - in_min) + out_min, out_max))

def sobelDetector(image):
    image = image.convert("L")
    input_pixels = np.array(image)

    # Initialize the output arrays with zeros
    output_pixels = np.zeros_like(input_pixels, dtype=np.uint8)
    GxOut = np.zeros_like(input_pixels, dtype=np.int32)  # Store Gx as integers to avoid overflow
    GyOut = np.zeros_like(input_pixels, dtype=np.int32)  # Same for Gy

    # Apply Sobel operator
    for y in range(1, input_pixels.shape[0] - 1):
        for x in range(1, input_pixels.shape[1] - 1):
            sum_Gx = 0
            sum_Gy = 0
            for j in range(-1, 2):
                for i in range(-1, 2):
                    sum_Gx += input_pixels[y + j, x + i] * Gx[j + 1][i + 1]
                    sum_Gy += input_pixels[y + j, x + i] * Gy[j + 1][i + 1]
            GxOut[y, x] = sum_Gx
            GyOut[y, x] = sum_Gy
            G = math.sqrt(GyOut[y, x]**2 + GxOut[y, x]**2)
            G = remap(G, 0, math.sqrt(255**2 + 255**2), 0, 255)  # Remap gradient to [0, 255]
            output_pixels[y, x] = int(G)

    # Convert the result back to an image
    output_image = Image.fromarray(output_pixels)
    output_image = output_image.convert("RGBA")  # Convert to RGBA if needed
    output_image.show()

    return output_image

# Example usage:
sobelDetector(Image.open("test.jpg"))
