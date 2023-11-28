import numpy as np
from PIL import Image
from rembg import remove

def apply_jarvis_judice_ninke_dithering(image, tsp_path):
    grayscale_image = image.convert('L')
    
    input_pixels = np.array(grayscale_image)
    
    output_image = Image.new('L', grayscale_image.size)
    output_pixels = np.array(output_image)
    count = 0
    
    f = open(tsp_path, "w")

    # Initialize a list to store lines
    file_lines = []

    file_lines.append("NAME : \n")
    file_lines.append("COMMENT : \n")
    file_lines.append("TYPE : TSP\n")
    file_lines.append("EDGE_WEIGHT_TYPE : EUC_2D\n")
    file_lines.append("NODE_COORD_SECTION\n")

    for y in range(input_pixels.shape[0]):
        for x in range(input_pixels.shape[1]):
            old_pixel = input_pixels[y, x]
            new_pixel = 255 if old_pixel >= 128 else 0
            if new_pixel == 0:
                count += 1
                file_lines.append(f"%s %s %s\n" % (count, x, y))
            output_pixels[y, x] = new_pixel

            quant_error = old_pixel - new_pixel
            
            if x < input_pixels.shape[1] - 1:
                input_pixels[y, x + 1] += quant_error * 7 / 48
                if x < input_pixels.shape[1] - 2:
                    input_pixels[y, x + 2] += quant_error * 5 / 48
            if y < input_pixels.shape[0] - 1:
                if x > 0:
                    input_pixels[y + 1, x - 1] += quant_error * 3 / 48
                input_pixels[y + 1, x] += quant_error * 5 / 48
                if x < input_pixels.shape[1] - 1:
                    input_pixels[y + 1, x + 1] += quant_error * 3 / 48
                if x < input_pixels.shape[1] - 2:
                    input_pixels[y + 1, x + 2] += quant_error * 1 / 48

    file_lines.insert(3, "DIMENSION : {}\n".format(count))  # Include count in DIMENSION line
    # Now, write all lines to the file
    f.writelines(file_lines)
    f.write("EOF\n")
    f.close()

    output_image = Image.fromarray(output_pixels)
    output_image = output_image.convert("RGBA")
    # print(count)
    return output_image

# downscale = 2

# input_image = Image.open('input.png')
# input_image = remove(input_image)
# jpg_image = Image.new("RGB", input_image.size, "white")
# jpg_image.paste(input_image, (0, 0), input_image)
# input_image = jpg_image
# input_image = input_image.resize((int(input_image.width/downscale), int(input_image.height/downscale)))
# output_image = apply_jarvis_judice_ninke_dithering(input_image)
# output_image.save('output_image.png')
