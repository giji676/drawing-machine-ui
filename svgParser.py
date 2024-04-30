import xml.etree.ElementTree as ET
import re

from PIL import Image, ImageDraw


def svg_to_coordinates(path):
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

        """ =============== TODO ============= """
        """
        Currently the pen is always down and drawing,
        need to add pen lift
        """
        if command in ("M", "m"):
            # Move to command
            current_point = values[:2]
            #coordinates.append(command)
            coordinates.append(current_point)
        elif command in ("L", "l"):
            # Line to command
            #coordinates.append(command)
            for i in range(0, len(values), 2):
                x, y = values[i: i + 2]
                current_point = [x, y]
                coordinates.append(current_point)
        elif command in ("H", "h"):
            # Horizontal line to command
            #coordinates.append(command)
            for x in values:
                current_point[0] = x
                coordinates.append(current_point.copy())
        elif command in ("V", "v"):
            # Vertical line to command
            #coordinates.append(command)
            for y in values:
                current_point[1] = y
                coordinates.append(current_point.copy())
        elif command in ("C", "c"):
            # Cubic Bézier curve command
            #coordinates.append(command)
            """ =============== TODO ============= """
            """
            currently the raw coordinates of control points and end points are added to the coordinates list,
            instead the curve should be approximated at regular intervals,
            and their coordinates should be used
            """
            for i in range(0, len(values), 6):
                x1, y1, x2, y2, x, y = values[i: i + 6]
                # Cubic Bézier curve has two control points (x1, y1) and (x2, y2), and an endpoint (x, y)
                coordinates.append([x1, y1])
                coordinates.append([x2, y2])
                coordinates.append([x, y])

    return coordinates


def extract_ids_styles(svg_file, callback):
    ids = []
    tree = ET.parse(svg_file)
    root = tree.getroot()

    max_x, max_y = 0, 0

    g_ids = root.findall('.//{http://www.w3.org/2000/svg}g[@id]')

    # Finds all the <g> tags with "id"
    for group_with_id in g_ids:
        callback(f"Processing {g_ids.index(group_with_id)+1}/{len(g_ids)}")
        # Gets the "id" which should be the name of the colour pen used
        id_value = group_with_id.get('id')
        coordinates = []
        # Finds all the <g> tags with "style" that are children of previous <g> tag
        for child_group in group_with_id.findall('.//{http://www.w3.org/2000/svg}g[@style]'):
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
                        fill = tuple(int(x) for x in re.search(r'rgb\((.*?)\)', fill).group(1).split(','))
                    elif "fill-opacity:" in part:
                        fill_opacity = float(part.split(":")[1].strip())

            # Finds all the <path> tags that are children of the previous <g> tag with "style"
            for path in child_group.findall('.//{http://www.w3.org/2000/svg}path'):
                d_value = path.get('d')
                path_coordinates = svg_to_coordinates(d_value)
                coordinates.extend(path_coordinates)

        local_max_x, local_max_y = get_max_width_height(coordinates)

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


def get_max_width_height(coordinates):
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


def draw_image(ids_styles_coordinates, width=800, height=800):
    image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)

    # data will represent each pen group - pen id/name, colour desc, coordinates
    for data in ids_styles_coordinates:
        fill = data["fill"]
        fill_opacity = data["fill_opacity"]
        coordinates = data["coordinates"]

        fill_rgba = fill + (int(255 * fill_opacity),)

        for i in range(len(coordinates) - 1):
            start_point = coordinates[i]
            end_point = coordinates[i + 1]
            draw.line((start_point[0], start_point[1], end_point[0], end_point[1]), fill=fill_rgba, width=1)
        image.show()
    return image


def parseSvg(path, callback):
    ids_styles_coordinates, max_x, max_y = extract_ids_styles(path, callback)
    return draw_image(ids_styles_coordinates, width=max_x, height=max_y)
