from PIL import Image, ImageDraw
import numpy as np
import math

class EdgeDetector:
    sobel_output = None
    gaussian_output = None
    path = None
    image = None

    # Sobel filters (Gx and Gy)
    Gx = [[-1, 0, 1],
          [-2, 0, 2],
          [-1, 0, 1]]

    Gy = [[-1, -2, -1],
          [0, 0, 0],
          [1, 2, 1]]

    def __init__(self, path):
        self.loadImage(path)

    def remap(self, val, in_min, in_max, out_min, out_max):
        return max(out_min, min((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, out_max))

    def loadImage(self, path):
        self.path = path
        self.image = Image.open(self.path)

    def sobel(self, image):
        image = image.convert("L")
        input_pixels = np.array(image)

        output_pixels = np.zeros_like(input_pixels, dtype=np.uint8)
        Gx_out = np.zeros_like(input_pixels, dtype=np.int32)
        Gy_out = np.zeros_like(input_pixels, dtype=np.int32)

        for y in range(1, input_pixels.shape[0] - 1):
            for x in range(1, input_pixels.shape[1] - 1):
                Gx_sum = 0
                Gy_sum = 0
                for j in range(-1, 2):
                    for i in range(-1, 2):
                        Gx_sum += input_pixels[y + j, x + i] * self.Gx[j + 1][i + 1]
                        Gy_sum += input_pixels[y + j, x + i] * self.Gy[j + 1][i + 1]

                Gx_out[y, x] = Gx_sum
                Gy_out[y, x] = Gy_sum
                G = math.sqrt(Gx_sum**2 + Gy_sum**2)
                # Remap the gradient magnitude
                G = self.remap(G, 0, math.sqrt(255**2 + 255**2), 0, 255)

                output_pixels[y, x] = np.uint8(G)  # Ensure it's an 8-bit value

        output_image = Image.fromarray(output_pixels, mode="L")
        self.sobel_output = output_image
        return self.sobel_output

    def gaussianKernelGenerator(self, x, y, sigma):
        return (1 / (2 * np.pi * sigma**2)) * np.exp(-(x**2 + y**2) / (2 * sigma**2))

    def gaussian(self, image, radius):
        diam = radius * 2 + 1
        kernel = []
        sigma = max(radius / 2, 1)

        # Generate Gaussian kernel
        for i in range(-radius, radius + 1):
            temp = []
            for j in range(-radius, radius + 1):
                temp.append(self.gaussianKernelGenerator(i, j, sigma))
            kernel.append(temp)

        # Normalize the kernel
        kernel_sum = sum(sum(row) for row in kernel)
        kernel = [[value / kernel_sum for value in row] for row in kernel]

        image = image.convert("L")
        input_pixels = np.array(image)

        output_pixels = np.zeros_like(input_pixels, dtype=np.uint8)

        # Apply convolution
        for y in range(radius, input_pixels.shape[0] - radius):
            for x in range(radius, input_pixels.shape[1] - radius):
                sum_val = 0
                for j in range(-radius, radius + 1):
                    for i in range(-radius, radius + 1):
                        sum_val += input_pixels[y + j, x + i] * kernel[j + radius][i + radius]
                output_pixels[y, x] = np.clip(sum_val, 0, 255)  # Ensure pixel values are within valid range

        output_image = Image.fromarray(output_pixels, mode="L")
        self.gaussian_output = output_image
        return self.gaussian_output

# Usage example:
edgeDetector = EdgeDetector("test.jpg")
edgeDetector.gaussian(edgeDetector.image, 3).save("gausia.jpg")
edgeDetector.sobel(edgeDetector.gaussian_output).save("sobel.jpg")
