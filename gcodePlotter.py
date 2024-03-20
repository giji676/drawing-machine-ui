from PIL import Image, ImageDraw, ImageOps

f = open("drawing.gcode", "r")

image = Image.new("RGB", (1200, 1200), color="white")
draw = ImageDraw.Draw(image)

x, y = 0, 0
pen_down = False

for line in f:
    line = line.strip()

    if line == "PENUP":
        pen_down = False
    elif line == "PENDOWN":
        pen_down = True

    else:
        line = line.split()
        n_x, n_y = float(line[0]), float(line[1])

        draw.line(((x, 1200-y), (n_x, 1200-n_y)), fill=(0, 0, 0))
        x, y = n_x, n_y
image.show()
