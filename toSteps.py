import math


def convertToSteps(settings, input_file, output_file):
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

    for line in f:
        line = line.strip()
        if line == "PENUP":
            pen_down = False
            imgs.append("PENUP")
        elif line == "PENDOWN":
            pen_down = True
            imgs.append("PENDOWN")
        else:
            line = line.split()
            x, y = int(float(line[0])), int(float(line[1]))
            imgs.append([x, y])
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

    max_x = 0
    max_y = 0
    for row in imgs:
        if row == "PENUP" or row == "PENDOWN":
            continue
        if row[0] > max_x:
            max_x = row[0]
        if row[1] > max_y:
            max_y = row[1]

    s_motor_current_offset = [0, 0]

    f = open(output_file, "w")

    for img in imgs:
        if img == "PENUP":
            f.write(f"{img}:45\n")
            continue
        if img == "PENDOWN":
            f.write(f"{img}:0\n")
            continue

        img = [
            remap(
                img[0],
                0,
                max_x,
                s_paper_offset_calculated[0],
                s_paper_offset_calculated[0] + s_paper_dimensions[0],
            ),
            remap(
                img[1],
                0,
                max_y,
                s_paper_offset_calculated[1],
                s_paper_offset_calculated[1] + s_paper_dimensions[1],
            ),
        ]

        values = calculate(img)

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
    f.close()
    print("done")
