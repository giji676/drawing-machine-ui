import math


def convertToSteps(settings, input_file, output_file, fit=False, min_pen_pickup=False):
    global s_current_distance
    # mm | Distance between each tooth on the belt
    mm_belt_tooth_distance = int(settings["beltToothDistance"])
    tooth_on_gear = int(settings["toothOngear"])
    # 200 full step, 1600 1/8 step
    steps_per_rev = int(settings["stepsPerRev"])
    # Used to correct the direction of the motors
    motor_dir = [int(settings["motorDir"][0]), int(settings["motorDir"][1])]
    mm_distance_between_motors = int(settings["distanceBetweenMotors"])  # mm |
    # mm | Distance between start position and M1, M2 motors | default [590, 590]
    mm_start_distance = [
        int(settings["startDistance"][0]),
        int(settings["startDistance"][1]),
    ]
    # mm | Paper dimensions after padding | default [190, 270]
    mm_paper_dimensions = [int(settings["paperSize"][0]), int(settings["paperSize"][1])]
    # mm | Distance between start position of the pen and the paper bottom above it | default 35
    mm_paper_offset_from_start = int(settings["paperOffset"])

    mm_per_step = mm_belt_tooth_distance * tooth_on_gear / steps_per_rev  # mm |

    s_distance_between_motors = round(mm_distance_between_motors / mm_per_step)
    s_start_distance = [
        round(mm_start_distance[0] / mm_per_step),
        round(mm_start_distance[1] / mm_per_step),
    ]
    s_paper_dimensions = [
        round(mm_paper_dimensions[0] / mm_per_step),
        round(mm_paper_dimensions[1] / mm_per_step),
    ]
    s_paper_offset_from_start = round(mm_paper_offset_from_start / mm_per_step)
    s_paper_offset_calculated = [
        round(((s_distance_between_motors / 2) - (s_paper_dimensions[0] / 2))),
        round(
            math.sqrt(s_start_distance[0] ** 2 - (s_distance_between_motors / 2) ** 2)
            - s_paper_offset_from_start
            - s_paper_dimensions[1]
        ),
    ]

    s_current_distance = s_start_distance

    """
    M1 -------------------------------------------------------------- M2
     \                                                                /
      \                                                              /
       \                                                            /
        \                                                          /
         \                                                        /
          \                                                      /
           \                                                    /
            \     ----------------------------------------     /
             \    |                                      |    /
              \   |                                      |   /
               \  |                                      |  /
                \ |                                      | /
                 \|                                      |/
                  \                                      /
                  |\                                    /|
                  | \                                  / |
                  |  \                                /  |
                  |   \                              /   |
                  |    \                            /    |
                  |     \                          /     |
                  |      \                        /      |
                  |       \                      /       |
                  |        \                    /        |
                  |         \                  /         |
                  -----------\----------------/-----------
                              \              /
                               \            /
                                \          /
                                 \        /
                                  \      /
                                   \    /
                                    \  /
                                     \/
    """

    imgs = []
    f = open(input_file, "r")
    max_x = 0
    max_y = 0

    for line in f:
        line = line.strip()
        if line == "PAUSE":
            imgs.append("PAUSE")
        elif line == "PENUP":
            imgs.append("PENUP")
        elif line == "PENDOWN":
            imgs.append("PENDOWN")
        else:
            line = line.split()
            x, y = int(float(line[0])), int(float(line[1]))
            imgs.append([x, y])
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
    f.close()

    def remap(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

    def calculate(img):
        global s_current_distance

        s_new_distance = [
            (math.sqrt(img[0] ** 2 + img[1] ** 2)),
            (math.sqrt((s_distance_between_motors - img[0]) ** 2 + img[1] ** 2)),
        ]

        s_change = [
            round(s_current_distance[0] - s_new_distance[0]),
            round(s_current_distance[1] - s_new_distance[1]),
        ]

        s_current_distance = [round(s_new_distance[0]), round(s_new_distance[1])]
        return s_change


    image_offset = [0, 0]
    new_max = [s_paper_dimensions[0], s_paper_dimensions[1]]

    # fit=True means fit the image to the canvas while preserving aspect ratio
    # fit=False means stretch the image to fully fit the canvas, but changes the aspect ratio
    # stretch will result in stretched/distorted image

    # Calculate the offsets and new max dimensions based on the best fit
    # Image offsets are used to center the image on the canvas
    if fit:
        image_ar = max_x / max_y
        canvas_ar = s_paper_dimensions[0] / s_paper_dimensions[1]
        if image_ar >= canvas_ar:
            new_max = [s_paper_dimensions[0], max_y * (s_paper_dimensions[0] / max_x)]
            image_offset = [0, (s_paper_dimensions[1] / 2) - (new_max[1] / 2)]
        else:
            new_max = [max_x * (s_paper_dimensions[1] / max_y), s_paper_dimensions[1]]
            image_offset = [(s_paper_dimensions[0] / 2) - (new_max[0] / 2), 0]

    def writePos(pos, f, s_motor_current_offset):
        pos = [
            remap(
                pos[0],
                0,
                max_x,
                s_paper_offset_calculated[0],
                s_paper_offset_calculated[0] + new_max[0],
            )
            + image_offset[0],
            remap(
                pos[1],
                0,
                max_y,
                s_paper_offset_calculated[1],
                s_paper_offset_calculated[1] + new_max[1],
            )
            + image_offset[1],
        ]

        values = calculate(pos)

        s_motor_current_offset = [
            round(s_motor_current_offset[0] + values[0]),
            round(s_motor_current_offset[1] + values[1]),
        ]

        uno_input = (
            str(s_motor_current_offset[0] * motor_dir[0])
            + ","
            + str(s_motor_current_offset[1] * motor_dir[1])
            + "\n"
        )

        f.write(uno_input)
        return s_motor_current_offset

    s_motor_current_offset = [0, 0]
    f = open(output_file, "w")

    min_dist_for_servo = 20
    pen_down = False
    last_pos = [0, 0]
    last_line = None
    first = True
    hit_penup = False

    raw_penup_counter = 0
    processed_penup_counter = 0

    if min_pen_pickup:
        for line in imgs:
            if line == "PAUSE":
                f.write(f"{line}\n")
                continue
            if line == "PENUP" and first:
                raw_penup_counter += 1
                if line == last_line:
                    continue
                # f.write(f"{line}:45\n")
                pen_down = False
                last_line = line
                continue
            if line == "PENDOWN":
                if pen_down:
                    continue
                f.write(f"{line}:0\n")
                pen_down = True
                last_line = line
                continue
            if first:
                s_motor_current_offset = writePos(line, f, s_motor_current_offset)
                last_pos = line
                first = False
                last_line = line
                continue
            if line == "PENUP":
                raw_penup_counter += 1
                if line == last_line:
                    continue
                hit_penup = True
                continue
            if hit_penup:
                hit_penup = False
                dist = math.sqrt((line[0] - last_pos[0])**2 + (line[1] - last_pos[1])**2)
                if dist < min_dist_for_servo:
                    f.write("PENUP:45\n")
                    processed_penup_counter += 1
                    s_motor_current_offset = writePos(line, f, s_motor_current_offset)
                    last_pos = line
                    last_line = line
                    pen_down = False
                    continue
                else:
                    s_motor_current_offset = writePos(line, f, s_motor_current_offset)
                    last_pos = line
                    last_line = line
                    continue
            s_motor_current_offset = writePos(line, f, s_motor_current_offset)
            last_pos = line
            last_line = line
        output_txt = f"Finished-\nRaw penups: {raw_penup_counter} Processed penups: {processed_penup_counter}"

    else:
        for line in imgs:
            if line == "PAUSE":
                f.write(f"{line}\n")
                continue
            if line == "PENUP":
                f.write(f"{line}:45\n")
                continue
            if line == "PENDOWN":
                f.write(f"{line}:0\n")
                continue
            s_motor_current_offset = writePos(line, f, s_motor_current_offset)
        output_txt = "Finished"

    f.write("PENUP:45\n")
    f.close()
    return output_txt
