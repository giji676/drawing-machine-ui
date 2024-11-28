from PIL import Image, ImageDraw
import numpy as np
import math

class EdgeDetector:
    image = None
    sobel_output = None

    Gx = [[-1, 0, 1],
          [-2, 0, 2],
          [-1, 0, 1]]

    Gy = [[-1, -2, -1],
          [0, 0, 0],
          [1, 2, 1]]

    def __init__(self, image):
        self.image = image

    def remap(self, val, in_min, in_max, out_min, out_max):
        return max(out_min, min((val - in_min) * (out_max - out_min) // (in_max - in_min) + out_min, out_max))


    def sobel(self):
        image = self.image.convert("L")
        input_pixels = np.array(image)

        output_pixels = np.zeros((input_pixels.shape[0],
                                input_pixels.shape[1]),
                                dtype=np.uint8)
        Gx_out = np.zeros_like(input_pixels, dtype=np.int32)
        Gy_out = np.zeros_like(input_pixels, dtype=np.int32)

        for y in range(1, input_pixels.shape[0] - 1):
            for x in range(1, input_pixels.shape[1] - 1):
                Gx_sum = 0
                Gy_sum = 0
                for j in range(-1, 2):
                    for i in range(-1, 2):
                        Gx_sum += input_pixels[y+j, x+i] * self.Gx[j+1][i+1]
                        Gy_sum += input_pixels[y+j, x+i] * self.Gy[j+1][i+1]

                Gx_out[y, x] = Gx_sum
                Gy_out[y, x] = Gy_sum
                G = math.sqrt(Gx_sum**2 + Gy_sum**2)
                G = self.remap(G, 0, math.sqrt(255**2 + 255**2), 0, 255)

                output_pixels[y, x] = G
        output_image = Image.fromarray(output_pixels, mode="L")
        output_image.show()

        self.sobel_output = output_image
        return self.sobel_output

EdgeDetector(Image.open("test.jpg")).sobel()
