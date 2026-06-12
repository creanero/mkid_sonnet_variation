import argparse
import os
import decimal
import numpy as np

# global variables as placeholders
# These are the corners of the capacitor.
# TODO: Parameterise these using arg or otherwise
cap_x_min = 24.0
cap_y_min = 186.0
cap_x_max = 476.0
cap_y_max = 316.0


def gen_preamble():
    """
    Generate the preamble (Header, dimensions and control) for the .son file from a template
    :return:
    """
    # TODO: separately implement the header, dimensions, and control parameters
    preamble_text = file_read(os.path.expanduser('templates/head_dim_control.son'))
    return preamble_text


def gen_geometry():
    """
    Generate the Sonnet geometry: the metals, the scale parameters, the backing material and
    the polygons that make up the circuit.
    :return: string containing the text for the geometry (circuit)
    """
    # Writes the "open" for the geometry
    geometry_text = "\nGEO"
    # Writes the properties of the "metals" to be used in the circuit (e.g. kinetic inductance per square)
    geometry_text = geometry_text + gen_met()
    # Writes a line explaining the dimensions and grid size to use (checked for floating point errors)
    geometry_text = geometry_text + gen_scale_line()
    # pulls in the backing parameters from a file
    # TODO: check what needs to be done for this to be parameterised
    geometry_text = geometry_text + gen_backing()
    # Generates the polygons that constitute the circuit
    geometry_text = geometry_text + gen_polygons()
    # End the geometry section
    geometry_text = geometry_text + '\nEND GEO'
    return geometry_text


def gen_met():
    """
    Generates the "metals" to be used in the circuit. Most of these come from template files
    The kinetic inductance parameter is set based on the arguments
    :return: string containing the "metals" used in the Sonnet simulation
    """
    # Extracts the TMET and BMET parameters from a template
    met_text = '\n' + file_read(os.path.expanduser('templates/met_p1.son'))
    # Generates the line for the "metal" used in the circuit
    met_text = met_text + gen_ls_line()
    # Extracts the "TiN multi" and "thick Ta" parameters from a template
    # TODO: experiment to see/how if these can be replaced
    met_text = met_text + '\n' + file_read(os.path.expanduser('templates/met_p2.son'))
    return met_text


def gen_ls_line():
    """
    Generates the line controlling the kinetic inductance per square of the circuit
    :return: string containing the line for "metal" MET 1, used in the rest of the circuit
    """
    # Creates the base text used to define metal 1 as a superconductor
    base_text = 'MET "superconductor" 1 SUP 0 0 0 '
    # adds the kinetic inductance in picoHenry per square to the line
    out_text = '\n' + base_text + str(args.ls)
    return out_text


def gen_scale_line():
    """
    Generates the line that defines the size of the circuit in micrometres
    and the number of boxes in the grid in each dimension
    :return:
    """
    base_text = "BOX 1 "
    # makes sure that the size that's selected is a valid multiple of the boxes selected
    x_size, x_boxes = gen_safe_scale(args.x_size, args.x_scale)
    y_size, y_boxes = gen_safe_scale(args.y_size, args.y_scale)
    # y_size = args.y_size - (decimal.Decimal(str(args.y_size)) % decimal.Decimal(str(args.y_scale)))
    # x_boxes = int(decimal.Decimal(x_size*2) / decimal.Decimal(args.x_scale))
    # y_boxes = int(decimal.Decimal(y_size*2) / decimal.Decimal(args.y_scale))

    # Generates the required trailing text
    trail_text = ' 20 0'

    # combines the size and grid variables into a single string
    out_text = ('\n' + base_text +
                str(args.x_size) + ' ' +
                str(args.y_size) + ' ' +
                str(x_boxes) + ' ' +
                str(y_boxes) +
                trail_text)
    return out_text


def gen_safe_scale(size, scale_factor):
    """
    Generates the size and number of boxes along a single dimension based in the arguments
    :param size: Size of the axis in micrometres
    :param scale_factor: desired maximum box size in micrometres
    :return: safe_size (Decimal with desired size) safe_boxes (integer with the number of boxes)
    """
    # Extracts size and scale factor from the arguments
    # Decimal and string logic are needed to minimise floating point errors
    dec_size = decimal.Decimal(str(size))
    dec_scale_factor = decimal.Decimal(str(scale_factor))
    # removes any remainder from the size dimension
    safe_size = dec_size - (dec_size % dec_scale_factor)
    # calculates the number of boxes needed (doubled for Sonnet reasons
    safe_boxes = (2 * dec_size) // dec_scale_factor
    return safe_size, safe_boxes


def gen_backing():
    """
    Generates the backing text from a template file. This defines the substrate and some other parameters
    :return:
    """
    # TODO: identify ways to improve on this
    backing_text = '\n' + file_read(os.path.expanduser('templates/backing.son'))
    return backing_text


def gen_polygons():
    """
    Generates the polygons that form the foreground circuit
    :return:
    """
    # Generate the base circuit (this includes the ground plane and inductor)
    base_polygon_string = gen_base_polygons()

    # Generates the capacitor fingers
    fingers_string = gen_fingers()

    # Combines the base and fingers strings
    polygon_string = base_polygon_string + '\n' + fingers_string
    # Counts the polygons in the string using the substring "END"
    num_polygons = count_substring(base_polygon_string, "END")
    # num_base_polygons = count_substring(base_polygon_string, "END")
    # num_fingers = count_substring(fingers_string, "END")
    # num_polygons = num_fingers + num_base_polygons

    # Combines the polygons with the count
    polygon_text = ('\nNUM ' + str(num_polygons) + '\n' + polygon_string)
    return polygon_text


def gen_base_polygons():
    """
    Generate the base circuit (this includes the ground plane and inductor)
    :return:
    """
    # reads ground plane and inductor from a template file
    # TODO separate out the ground plane and inductor, and parameterise them
    base_polygon_string = file_read(os.path.expanduser('templates/base_polygons.son'))
    return base_polygon_string


def gen_fingers():
    # fingers_string = file_read(os.path.expanduser('templates/fingers_27.son'))
    fingers_string = '\n'
    # TODO: ensure this is an integer - quickfix, put into check_arguments() when developed
    num_fingers = int(args.num_fingers)
    finger_length = args.length
    finger_thickness = args.thick
    finger_space = args.space

    end_fingers = cap_y_max - (finger_space * num_fingers)

    # need to leave space for final (partial) finger
    if (end_fingers - finger_space) < cap_y_min:
        raise OverflowError

    start_points = np.linspace(cap_y_max, end_fingers, num_fingers, endpoint=False)

    i = 0
    for i in range(num_fingers):
        right = bool(i % 2)
        x_min, x_max, y_min, y_max = gen_points(start_points[i], finger_length, right)
        polygon_name = 100 + i
        fingers_string = fingers_string + gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name)

    # python ranges end at final value. If ever translating this to C-like code, replace i+1 with i
    right = bool((i + 1) % 2)
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


def gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name=100):
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
    """
    Generate the text for the .son file in several parts.
    :return: content (string containing the .son file content)
    """
    # generate the preamble (Header, dimensions and control)
    content = gen_preamble()
    # generate the geometry (metals, scale, backing and polygons)
    content = content + '\n' + gen_geometry()
    # generate the tail text (opt, var sweep, output file from sonnet, and translator)
    content = content + '\n' + gen_tail()
    return content


def write_son(content):
    """
    Writes the content to a file
    :param content: A string containing all of the content for a Sonnet Geometry file (.son)
    :return:
    """
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
    # TODO: Make this check if the path is valid, separate out path generation functionality
    if args.iter == "None":
        path = os.path.expanduser(path)
    else:
        path = os.path.expanduser(path)
        base_path = os.path.splitext(path)[0]
        ext = '.son'
        suffix = '_' + str(args.iter) + '_' + str(getattr(args, args.iter)).replace('.', '_')
        path = base_path + suffix + ext
        print(path)
    return path


def gen_iter():
    """
    Uses the start point, end point and count of steps to generate a range to iterate over
    Then iterates through that range, generating content and writing it to a .son file.
    :return:
    """
    start_iter = getattr(args, args.iter)
    end_iter = args.end
    iter_range = np.linspace(start_iter, end_iter, args.count)
    for iter_value in iter_range:
        setattr(args, args.iter, iter_value)
        content = gen_text()
        write_son(content)


def set_args():
    """
    Sets the arguments for the rest of the program using argparse.
    :return: out_args (a dictionary of the values of the arguments)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--ls", help="Kinetic inductance (pH/sq)", default=5.0, type=float)
    parser.add_argument("-x", "--x_scale", help="x-scale factor: minimum cell size in micrometres", default=1.0,
                        type=float)
    parser.add_argument("-y", "--y_scale", help="y-scale factor: minimum cell size in micrometres", default=1.0,
                        type=float)
    parser.add_argument("-X", "--x_size", help="x-size in micrometres", default=500.0, type=float)
    parser.add_argument("-Y", "--y_size", help="y-size in micrometres", default=500.0, type=float)
    parser.add_argument("-N", "--num_fingers", help="Number of fingers", default=27, type=int)
    parser.add_argument("-s", "--save", help="Save the generated file", default="~/mkid.son", type=str)
    parser.add_argument("-t", "--thick", help="Thickness of fingers in micrometres", default=2.0, type=float)
    parser.add_argument("-S", "--space", help="Finger Spacing (start to start) in micrometres", default=4.0, type=float)
    parser.add_argument("-L", "--length", help="Length of fingers in micrometres", default=450.0, type=float)
    parser.add_argument("-f", "--final", help="length of final finger in micrometers", default=84.0, type=float)
    iter_options = ["None", "length", "thick", "space", "final", "num_fingers"]
    parser.add_argument("-i", "--iter", help="Property to iterate over", default="None", choices=iter_options, type=str)
    parser.add_argument("-e", "--end", help="Endpoint for iteration", default=None, type=float)
    parser.add_argument("-c", "--count", help="Count of steps in iteration", default=10, type=int)
    out_args = parser.parse_args()
    return out_args


def main():
    """
    Checks if the user has selected to iteratively generate MKIDs, and calls the function to generate
    one or many based on that choice
    :return:
    """
    # no iterations selected
    if args.iter == "None":
        # generate the contents of an MKID geometry
        content = gen_text()
        # writes it to an output file
        write_son(content)
    # some non-zero number of iterations selected
    else:
        # generates multiple MKID geometries.
        gen_iter()


if __name__ == '__main__':
    # Gets the arguments from the command line and stores them globally.
    args = set_args()
    # Executes the main function.
    main()
