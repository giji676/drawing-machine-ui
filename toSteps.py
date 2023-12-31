import math


def convertToSteps(settings, input_file, output_file):
    global s_current_distance
    mm_belt_tooth_distance = int(settings["beltToothDistance"])                                     # mm | Distance between each tooth on the belt
    tooth_on_gear = int(settings["toothOngear"])                    
    steps_per_rev = int(settings["stepsPerRev"])                                                    # 200 full step, 1600 1/8 step
    motor_dir = [int(settings["motorDir"][0]), int(settings["motorDir"][1])]                        # Used to correct the direction of the motors
    mm_distance_between_motors = int(settings["distanceBetweenMotors"])                             # mm |
    mm_start_distance = [int(settings["startDistance"][0]), int(settings["startDistance"][1])]      # mm | Distance between start position and M1, M2 motors | default [590, 590]
    mm_paper_dimensions = [int(settings["paperSize"][0]), int(settings["paperSize"][1])]            # mm | Paper dimensions after padding | default [190, 270]
    mm_paper_offset_from_start = int(settings["paperOffset"])                                       # mm | Distance between start position of the pen and the paper bottom above it | default 35

    mm_per_step = mm_belt_tooth_distance * tooth_on_gear / steps_per_rev # mm | 

    s_distance_between_motors = round(mm_distance_between_motors / mm_per_step)
    s_start_distance = [round(mm_start_distance[0] / mm_per_step), round(mm_start_distance[1] / mm_per_step)]
    s_paper_dimensions = [round(mm_paper_dimensions[0] / mm_per_step), round(mm_paper_dimensions[1] / mm_per_step)]
    s_paper_offset_from_start = round(mm_paper_offset_from_start / mm_per_step)
    s_paper_offset_calculated = [round(((s_distance_between_motors / 2) - (s_paper_dimensions[0] / 2))), 
                                round(math.sqrt(s_start_distance[0] ** 2 - (s_distance_between_motors / 2) ** 2) - s_paper_offset_from_start - s_paper_dimensions[1])]

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
    sample_array = []
    for line in f.readlines():
        temp = line.split(" ")
        temp[1] = temp[1].strip("\n")
        sample_array.append([temp[0], temp[1]])
    f.close()

    for arr in sample_array:
        arr = [int(numeric_string) for numeric_string in arr]
        imgs.append(arr)

    def remap(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
        
    def calculate(img):
        global s_current_distance

        s_new_distance = [(math.sqrt(img[0] ** 2 + img[1] ** 2)), 
                        (math.sqrt((s_distance_between_motors - img[0]) ** 2 + img[1] ** 2))]
        
        s_change = [round(s_current_distance[0] - s_new_distance[0]), round(s_current_distance[1] - s_new_distance[1])]
        
        s_current_distance = [round(s_new_distance[0]), round(s_new_distance[1])]
        return s_change

    max_x = max(row[0] for row in imgs)
    max_y = max(row[1] for row in imgs)

    s_motor_current_offset = [0, 0]

    f = open(output_file, "w")

    for img in imgs:
        img = [remap(img[0], 0, max_x, s_paper_offset_calculated[0], s_paper_offset_calculated[0] + s_paper_dimensions[0]), 
            remap(img[1], 0, max_y, s_paper_offset_calculated[1], s_paper_offset_calculated[1] + s_paper_dimensions[1])]
        
        values = calculate(img)
        
        s_motor_current_offset = [round(s_motor_current_offset[0] + values[0]),
                                round(s_motor_current_offset[1] + values[1])]
        
        uno_input = str(s_motor_current_offset[0]*motor_dir[0]) + "," + str(s_motor_current_offset[1]*motor_dir[1]) + "\n"

        f.write(uno_input)
    f.close()