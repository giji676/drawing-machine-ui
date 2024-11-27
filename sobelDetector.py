from PIL import Image, ImageDraw
import numpy as np
import math
import colorsys

Gx = [[-1, 0, 1],
      [-2, 0, 2],
      [-1, 0, 1]]

Gy = [[-1, -2, -1],
      [0, 0, 0],
      [1, 2, 1]]

def remap(val, in_min, in_max, out_min, out_max):
    return max(out_min, min((val - in_min) * (out_max - out_min) // (in_max - in_min) + out_min, out_max))

def sobelDetector(image):
    image = image.convert("L")  # Convert to grayscale
    input_pixels = np.array(image)

    output_pixels = np.zeros((input_pixels.shape[0], input_pixels.shape[1], 3), dtype=np.uint8)  # RGB output
    GxOut = np.zeros_like(input_pixels, dtype=np.int32)  # Store Gx as integers
    GyOut = np.zeros_like(input_pixels, dtype=np.int32)  # Same for Gy

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

            # Avoid division by zero for angle calculation
            if sum_Gx == 0:
                angle = math.pi / 2 if sum_Gy != 0 else 0
            else:
                angle = math.atan2(sum_Gy, sum_Gx)  # atan2 handles all quadrants

            # Normalize angle to [0, 1] for hue
            hue = (angle + math.pi) / (2 * math.pi)

            # Gradient magnitude
            G = math.sqrt(sum_Gx**2 + sum_Gy**2)
            G = remap(G, 0, math.sqrt(255**2 + 255**2), 0, 255)  # Remap gradient to [0, 255]
            brightness = G / 255  # Normalize brightness to [0, 1]

            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, 1, brightness)
            output_pixels[y, x] = (int(r * 255), int(g * 255), int(b * 255))

    # Convert the result back to an image
    output_image = Image.fromarray(output_pixels, mode="RGB")
    output_image.show()

    return output_image

def generate_gradient_wheel(size, filename="gradient_wheel.png"):
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)

    center = size // 2
    radius = center - 1  # Leave a 1-pixel margin

    # Draw the gradient wheel
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            distance = math.sqrt(dx**2 + dy**2)

            # Only draw within the circle
            if distance <= radius:
                angle = math.atan2(dy, dx)  # Angle in radians
                hue = (angle + math.pi) / (2 * math.pi)  # Normalize to [0, 1]
                brightness = distance / radius  # Normalize to [0, 1] (intensity)
                r, g, b = colorsys.hsv_to_rgb(hue, 1, brightness)
                color = (int(r * 255), int(g * 255), int(b * 255))
                draw.point((x, y), fill=color)

    # Save the image
    image.save(filename)
    print(f"Gradient wheel saved as {filename}")
    return image

sobelDetector(Image.open("test.jpg"))
