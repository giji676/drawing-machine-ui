import xml.etree.ElementTree as ET
import re
import sys

from PIL import Image, ImageDraw


def svgToCoordinates(path):
    # Split path data into individual commands
    commands = re.findall(
        r"([MmLlHhVvCcSsQqTtAaZz])\s*([^MmLlHhVvCcSsQqTtAaZz]*)", path
    )

    coordinates = []
    current_point = [0, 0]
    for command, values in commands:
        # Split values and convert to floats
        values = re.split(r"[ ,]+", values.strip())
        values = [float(v) for v in values if v.strip()]

        if command in ("M", "m"):
            # Move to command
            current_point = values[:2]
            coordinates.append(command)
            coordinates.append(current_point)
        elif command in ("L", "l"):
            # Line to command
            coordinates.append(command)
            for i in range(0, len(values), 2):
                x, y = values[i: i + 2]
                current_point = [x, y]
                coordinates.append(current_point)
        elif command in ("H", "h"):
            # Horizontal line to command
            coordinates.append(command)
            for x in values:
                current_point[0] = x
                coordinates.append(current_point.copy())
        elif command in ("V", "v"):
            # Vertical line to command
            coordinates.append(command)
            for y in values:
                current_point[1] = y
                coordinates.append(current_point.copy())
        elif command in ("C", "c"):
            # Cubic Bézier curve command
            coordinates.append(command)
            for i in range(0, len(values), 6):
                x1, y1, x2, y2, x, y = values[i: i + 6]
                # Cubic Bézier curve has two control points (x1, y1) and (x2, y2), and an endpoint (x, y)
                coordinates.append([x1, y1])
                coordinates.append([x2, y2])
                coordinates.append([x, y])

    return coordinates


def extractIdsStyles(svg_file, callback):
    ids = []
    tree = ET.parse(svg_file)
    root = tree.getroot()

    max_x, max_y = 0, 0

    g_ids = root.findall('.//{http://www.w3.org/2000/svg}g[@id]')
    if len(g_ids) == 0:
        g_ids = root

    # Finds all the <g> tags with "id"
    for group_with_id in g_ids:
        # callback(f"Processing {g_ids.index(group_with_id)+1}/{len(g_ids)}")
        # Gets the "id" which should be the name of the colour pen used
        id_value = group_with_id.get('id')
        coordinates = []
        # Finds all the <g> tags with "style" that are children of previous <g> tag
        g_styles = group_with_id.findall(
            './/{http://www.w3.org/2000/svg}g[@style]')
        if len(g_styles) == 0:
            g_styles = g_ids

        for child_group in g_styles:
            # Gets the "style" which should contain information about the pen used
            # E.g fill, fill opacity
            style_value = child_group.get('style')
            fill = ""
            fill_opacity = 1.0
            if style_value:
                style_parts = style_value.split(";")
                for part in style_parts:
                    if "fill:" in part:
                        fill = part.split(":")[1].strip()
                        fill = tuple(int(x) for x in re.search(
                            r'rgb\((.*?)\)', fill).group(1).split(','))
                    elif "fill-opacity:" in part:
                        fill_opacity = float(part.split(":")[1].strip())
            else:
                fill = (0, 0, 0)
                fill_opacity = 1.0

            # Finds all the <path> tags that are children of the previous <g> tag with "style"
            if g_styles == g_ids:
                path_parent = g_styles
            else:
                path_parent = child_group

            paths = path_parent.findall('.//{http://www.w3.org/2000/svg}path')
            for path in paths:
                d_value = path.get('d')
                path_coordinates = svgToCoordinates(d_value)
                coordinates.extend(path_coordinates)

        local_max_x, local_max_y = getMaxWidthHeight(coordinates)

        if local_max_x > max_x:
            max_x = local_max_x
        if local_max_y > max_y:
            max_y = local_max_y

        ids.append(
            {
                "id": id_value,
                "fill": fill,
                "fill_opacity": fill_opacity,
                "coordinates": coordinates,
            }
        )

    return ids, max_x, max_y


def getMaxWidthHeight(coordinates):
    if coordinates == []:
        return 0, 0
    max_x = float('-inf')
    max_y = float('-inf')

    for coord in coordinates:
        try:
            x, y = coord
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        except (TypeError, ValueError):
            pass

    return int(max_x), int(max_y)


def drawImage(ids_styles_coordinates, width=800, height=800):
    if width <= 0 or height <= 0:
        return
    image = Image.new("RGBA", (width+1, height+1), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    command_string = "MmLlVvHhCc"

    cubic_bezier_curve_res = 5

    GENERATED_FILES = "generated_files"
    OUTPUT_COORDINATES_TXT = "output_coordinates.txt"
    output_coordinates_path = f"{GENERATED_FILES}\{OUTPUT_COORDINATES_TXT}"

    f = open(output_coordinates_path, "w")

    # data will represent each pen group - pen id/name, colour desc, coordinates
    for data in ids_styles_coordinates:
        fill = data["fill"]
        fill_opacity = data["fill_opacity"]
        coordinates = data["coordinates"]
        if coordinates == []:
            return image

        fill_rgba = fill + (int(255 * fill_opacity),)

        command = ""
        last_command = ""
        offset_index = 0
        prev_coords = (0, 0)
        for i in range(len(coordinates) - 1):
            if offset_index > 0:
                offset_index -= 1
                continue
            if coordinates[i] in (list(command_string)):
                command = coordinates[i]
                if command in ("M", "m"):
                    f.write("PENUP\n")
                    prev_coords = coordinates[i+1]
                    last_command = command
                    offset_index = 1
                    continue
                if command in ("C", "c"):
                    start_point = prev_coords
                    if last_command in ("M", "m"):
                        f.write(f"{str(start_point[0])} {str(start_point[1])}\n")
                        f.write("PENDOWN\n")
                    for t in range(cubic_bezier_curve_res+1):
                        end_point = cubicBezier(
                            t/cubic_bezier_curve_res, start_point, coordinates[i+1], coordinates[i+2], coordinates[i+3])
                        draw.line(
                            (start_point[0], start_point[1], end_point[0], end_point[1]), fill=fill_rgba, width=1)
                        start_point = end_point
                        f.write(f"{str(start_point[0])} {str(start_point[1])}\n")
                    prev_coords = end_point
                    last_command = command
                    offset_index = 3
                    continue
                if command in ("L", "l", "H", "h", "V", "v"):
                    start_point = prev_coords
                    if last_command in ("M", "m"):
                        f.write(f"{str(start_point[0])} {str(start_point[1])}\n")
                        f.write("PENDOWN\n")
                    end_point = coordinates[i + 1]
                    draw.line(
                        (start_point[0], start_point[1], end_point[0], end_point[1]), fill=fill_rgba, width=1)
                    f.write(f"{str(end_point[0])} {str(end_point[1])}\n")
                    last_command = command
                    offset_index = 1
        f.write("PENUP\n")
        f.write("PAUSE\n")
        image.show()
    f.close()
    return image


def cubicBezier(t, p0, p1, p2, p3):
    x = (1-t)**3*p0[0]+3*(1-t)**2*t*p1[0]+3*(1-t)*t**2*p2[0]+t**3*p3[0]
    y = (1-t)**3*p0[1]+3*(1-t)**2*t*p1[1]+3*(1-t)*t**2*p2[1]+t**3*p3[1]
    return (x, y)


def parseSvg(path, callback=None):
    ids_styles_coordinates, max_x, max_y = extractIdsStyles(path, callback)
    return drawImage(ids_styles_coordinates, width=max_x, height=max_y)


if __name__ == '__main__':
    globals()[sys.argv[1]](sys.argv[2])
