from PIL import Image, ImageDraw

# code taken from: https://github.com/ugocapeto/thescribbler/blob/main/tracing_path_write_to_image.c


def pathMaker(tsp, cyc, output_path):
    tsp_arr = []
    cyc_arr = []
    point_arr = []
    trace_path = []

    # load the tsp file and turn it into an array
    with open(tsp) as f:
        found_coords = False
        for line in f:
            if "DIMENSION :" in line:
                point_nbr = int(line.split()[2])

            if "NODE_COORD_SECTION" in line:
                found_coords = True
                continue

            if "EOF" in line:
                break

            if found_coords:
                arr = line.split()
                arr = [int(x) for x in arr]
                tsp_arr.append(arr)

    for point_ind in range(point_nbr):
        index, x, y = tsp_arr[point_ind]
        point_arr.insert((2 * point_ind + 0), x)
        point_arr.insert((2 * point_ind + 1), y)

    # load the cyc file and turn it into an array
    with open(cyc) as f:
        first_line = True
        for line in f:
            if first_line:
                segment_nbr = int(line.split()[0])
                segment_nbr2 = int(line.split()[1])
                first_line = False
                continue
            arr = line.split()
            arr = [int(x) for x in arr]
            cyc_arr.append(arr)

    for segment_ind in range(segment_nbr):
        point_ind0, point_ind1, dist_int = cyc_arr[segment_ind]
        if segment_ind == 0:
            first_point_ind0 = point_ind0
        x = point_arr[2 * point_ind0 + 0]
        y = point_arr[2 * point_ind0 + 1]

        trace_path.append([x, y])

        prev_point_ind1 = point_ind1

    # save the create trace_path array to a file
    with open(output_path, "w") as path_file:
        for row in trace_path:
            path_file.write(" ".join([str(a) for a in row]) + "\n")

    # create empty image
    img = Image.new("RGB", (1500, 1500), color="white")
    img1 = ImageDraw.Draw(img)

    # draw lines from the trace_path
    for x in range(len(trace_path) - 1):
        coord1, coord2 = trace_path[x], trace_path[x + 1]
        img1.line((coord1[0], coord1[1], coord2[0], coord2[1]), fill="black", width=1)

    return img
