import argparse
import os

import numpy as np

# global variables as placeholders
cap_x_min = 24.0
cap_y_min = 186.0
cap_x_max = 476.0
cap_y_max = 316.0

def gen_preamble():
    preamble_text = file_read(os.path.expanduser('templates/head_dim_control.son'))
    return preamble_text

def gen_geometry():
    geometry_text = "\nGEO"
    geometry_text = geometry_text + gen_met()
    geometry_text = geometry_text + gen_scale_line()
    geometry_text = geometry_text + gen_backing()
    geometry_text = geometry_text + gen_polygons()
    geometry_text = geometry_text + '\nEND GEO'
    return geometry_text

def gen_met():
    met_text = '\n' + file_read(os.path.expanduser('templates/met_p1.son'))
    met_text = met_text + gen_ls_line()
    met_text = met_text + '\n' + file_read(os.path.expanduser('templates/met_p2.son'))
    return met_text

def gen_ls_line():
    base_text = 'MET "superconductor" 1 SUP 0 0 0 '
    out_text = '\n' + base_text + str(args.ls)
    return out_text

def gen_backing():
    backing_text = '\n' + file_read(os.path.expanduser('templates/backing.son'))
    return backing_text


def gen_scale_line():
    base_text = "BOX 1 "
    # makes sure that the size that's selected is a valid multiple of the boxes selected
    x_size = args.x_size - (args.x_size % args.x_scale)
    y_size = args.y_size - (args.y_size % args.y_scale)

    # calculates the number of boxes needed (doubled for Sonnet reasons
    x_scale_factor = int(x_size*2 / args.x_scale)
    y_scale_factor = int(y_size*2 / args.y_scale)
    trail_text = ' 20 0'
    out_text = ('\n' + base_text +
                str(args.x_size) + ' ' +
                str(args.y_size) + ' ' +
                str(x_scale_factor) + ' ' +
                str(y_scale_factor) +
                trail_text)
    return out_text

def gen_polygons():
    base_polygon_string = gen_base_polygons()
    num_base_polygons = count_substring(base_polygon_string, "END")
    fingers_string = gen_fingers()
    num_full_fingers = count_substring(fingers_string, "END")

    num_polygons = num_full_fingers + num_base_polygons
    polygon_text = ('\nNUM ' + str(num_polygons) +
                    '\n' + base_polygon_string +
                    '\n' + fingers_string )
    return polygon_text

def gen_base_polygons():
    base_polygon_string = file_read(os.path.expanduser('templates/base_polygons.son'))
    return base_polygon_string

def gen_fingers():
    # fingers_string = file_read(os.path.expanduser('templates/fingers_27.son'))
    fingers_string = '\n'
    num_fingers = args.num_fingers
    finger_length = args.length
    finger_thickness = args.thick
    finger_gap = args.gap

    end_fingers = cap_y_max - (finger_gap + finger_thickness) * num_fingers

    # need to leave space for final (partial) finger
    if end_fingers - (finger_gap + finger_thickness) < cap_y_min:
        raise OverflowError

    start_points = np.linspace(cap_y_max, end_fingers, num_fingers, endpoint=False)

    for i in range(num_fingers):
        right = bool(i%2)
        x_min, x_max, y_min, y_max = gen_points(start_points[i], finger_length, right)
        polygon_name = 100+i
        fingers_string = fingers_string + gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name)

    right = bool((i+1)%2)
    fingers_string = fingers_string + gen_part_finger(end_fingers, right)

    return fingers_string

def gen_part_finger(y_start, right=True):
    # part_finger_string = file_read(os.path.expanduser('templates/incomplete_finger_28.son')
    finger_length = args.final

    x_min, x_max, y_min, y_max = gen_points(y_start, finger_length, right)

    polygon_name = 200
    part_finger_string = gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name)
    return part_finger_string

def gen_points(y_start, finger_length, right=True):
    finger_thickness = args.thick
    if right:
        x_min = cap_x_max - finger_length
        x_max = cap_x_max
    else:
        x_min = cap_x_min
        x_max = cap_x_min + finger_length

    # following Sonnet file logic, which is reverse of display logic
    y_min = y_start - finger_thickness
    y_max = y_start

    return x_min, x_max, y_min, y_max

def gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name = 100):
    # header line taken from template
    head = "0 5 0 N {} 1 1 100 100 0 0 0 Y".format(polygon_name)
    # this nomenclature is correct for how sonnet displays the geometry.
    # The indices Sonnet displays in the editor count from bottom left
    # The positions used in the file count from top left
    top_left = "{} {}".format(x_min, y_min)
    top_right = "{} {}".format(x_max, y_min)
    bottom_right = "{} {}".format(x_max, y_max)
    bottom_left = "{} {}".format(x_min, y_max)

    # the representation of a polygon in sonnet is as a loop
    out_text = ('\n' + head +
                '\n' + top_left +
                '\n' + top_right +
                '\n' + bottom_right +
                '\n' + bottom_left +
                '\n' + top_left +
                "\nEND")
    return out_text

def count_substring(in_string, substring):
    counter = 0
    for line in in_string.split('\n'):
        if line == substring:
            counter += 1
    return counter

def gen_tail():
    tail_text = file_read(os.path.expanduser('templates/tail.son'))
    return tail_text

def file_read(in_filename):
    in_file = open(in_filename, 'r')
    text = in_file.read()
    in_file.close()
    return text

def gen_text():
    content = gen_preamble()
    content = content + '\n' + gen_geometry()
    content = content + '\n' + gen_tail()
    return content

def write_son(content):
    out_path = check_path(args.save)
    out_file = open(out_path, 'w')
    out_file.write(content)
    out_file.close()
    pass

def check_path(path):
    # dir_name = os.path.dirname(path)
    # if os.path.isdir(dir_name):
    #     return path + "/mkid.son"
    # elif os.path.isfile(path):
    #     return path
    # elif
    path=os.path.expanduser(path)
    return path

def set_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--ls", help="Kinetic inductance (pH/sq)", default=5.0, type=float)
    parser.add_argument("-x", "--x_scale", help="x-scale factor: minimum cell size in micrometres", default=1.0, type=float)
    parser.add_argument("-y", "--y_scale", help="y-scale factor: minimum cell size in micrometres", default=1.0, type=float)
    parser.add_argument("-X", "--x_size", help="x-size in micrometres", default=500.0, type=float)
    parser.add_argument("-Y", "--y_size", help="y-size in micrometres", default=500.0, type=float)
    parser.add_argument("-N", "--num_fingers", help="Number of fingers", default=27, type=int)
    parser.add_argument("-s", "--save", help="Save the generated son", default="~/mkid.son", type=str)
    parser.add_argument("-t", "--thick", help="Thickness of fingers in micrometres", default=2.0, type=float)
    parser.add_argument("-g", "--gap", help="Gap in micrometres", default=2.0, type=float)
    parser.add_argument("-L", "--length", help="Length of fingers in micrometres", default=450.0, type=float)
    parser.add_argument("-f", "--final", help="length of final finger in micrometers", default=84.0, type=float)
    out_args = parser.parse_args()
    return out_args

def main():
    content = gen_text()
    write_son(content)
    pass

if __name__ == '__main__':
    args = set_args()
    main()

