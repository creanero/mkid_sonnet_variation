import argparse
import os
import decimal
from socket import gaierror
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
    # Generate the ground plane
    ground_plane_string = gen_ground_plane()

    # Generate the inductor
    inductor_string = gen_inductor()

    # Generates the capacitor 
    capacitor_string = gen_capacitor()

    # Combines the base and fingers strings
    polygon_string = ground_plane_string + '\n' + inductor_string + '\n' + capacitor_string

    # Counts the polygons in the string using the substring "END"
    num_polygons = count_substring(polygon_string, "END")

    # Combines the polygons with the count
    polygon_text = ('\nNUM ' + str(num_polygons) + '\n' + polygon_string)
    return polygon_text


def gen_ground_plane():
    """
    Generate the ground plane polygon. This is read from a template file.
    :return: ground_plane_string (string containing the .son code for the ground plane)
    """
    # reads ground plane from a template file
    ground_plane_string = file_read(os.path.expanduser('templates/ground_plane.son'))
    return ground_plane_string


def gen_inductor():
    """
    Generate the polygons for the inductor. This is read from a template file.
    :return: inductor_string (string containing the .son code for the inductor)
    """
    # reads inductor from a template file
    inductor_string = file_read(os.path.expanduser('templates/inductor.son'))
    return inductor_string


def gen_capacitor():
    """
    Generate the polygons for the capacitor. This includes the outline of the capacitor and the fingers.
    :return: capacitor_string (string containing the .son code for the capacitor)
    """
    # Generates the outline of the capacitor
    capacitor_frame_string = gen_capacitor_frame()
    # Generates the capacitor fingers
    fingers_string = gen_fingers()
    # combines these into a single string
    capacitor_string = capacitor_frame_string + '\n' + fingers_string
    # returns the string containing the code for the capacitor
    return capacitor_string


def gen_capacitor_frame():
    """
    Generate the outline of the capacitor. This is read from a template file.
    :return: capacitor_frame_string (string containing the .son code for the capacitor outline)
    """
    capacitor_frame_string = file_read(os.path.expanduser('templates/capacitor_frame.son'))
    return capacitor_frame_string


def gen_fingers():
    """
    Generate the capacitor finger polygons
    :return:
    """
    # TODO: refactor this function, it's messy and uses deprecated terminology
    # TODO: Implement pitch, separation and breadth terminology
    # starts the string with a newline
    fingers_string = '\n'

    # gets the finger properties from the arguments
    num_fingers = int(args.num_fingers)
    finger_length = args.length
    finger_thickness = args.thick
    finger_space = args.space  # this should be pitch in the new terminology

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
    """
    Generates the partial finger at the end of the capacitor.
    :param y_start: Starting point in the Y direction in micrometres
    :param right: Whether this finger is starting from the right side of the capacitor walls
    :return: A string containing the .son code for the partial finger
    """
    # part_finger_string = file_read(os.path.expanduser('templates/incomplete_finger_28.son')
    finger_length = args.final

    # generates the X and Y coordinates for the polygon
    x_min, x_max, y_min, y_max = gen_points(y_start, finger_length, right)

    # sets the polygon name to 200
    # TODO: merge this number to the sequence with the whole fingers
    polygon_name = 200
    # Generates a rectangle (polygon) with those coordinates.
    part_finger_string = gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name)
    return part_finger_string


def gen_points(y_start, finger_length, right=True):
    """
    Generates the maximum and minimum X- and Y-coordinates in micrometres
    :param y_start: Starting point in the Y-direction
    :param finger_length: length of the capacitor finger
    :param right: whether it is starting from the right or left of the capacitor
    :return: (x_min, x_max, y_min, y_max) tuple containing floats with those coordinates
    """

    # gets the finger thickness from the arguments
    # TODO: Make this consistent in terms of sourcing data (program arguments vs function arguments)
    finger_thickness = args.thick

    # if it's coming from the right:
    if right:
        # minimum is the length away from the maximum edge of the capacitor
        x_min = cap_x_max - finger_length
        # and maximum is at the maximum edge of the capacitor
        x_max = cap_x_max
    # otherwise, it's coming from the left
    else:
        # minumum is at the minimum edge of the capacitor
        x_min = cap_x_min
        # maximum is the length onto the minimum edge of the capacitor
        x_max = cap_x_min + finger_length

    # Y minimum is subtracted from the start point
    # following Sonnet file logic, which is reverse of display logic
    y_min = y_start - finger_thickness
    # Y maximum is equal to the start point
    y_max = y_start

    return x_min, x_max, y_min, y_max


def gen_sonnet_rectangle(x_min, x_max, y_min, y_max, polygon_name=100):
    """
    Generates a sonnet rectangle based on the coordinates provided
    :param x_min:float Minimum x-coordinate in micrometres
    :param x_max:float Maximum x-coordinate in micrometres
    :param y_min:float Minimum y-coordinate in micrometres
    :param y_max:float Maximum y-coordinate in micrometres
    :param polygon_name:int A unique identifier for each polygon
    :return:str Containing the sonnet formtted code for the rectangle
    """
    # header line taken from template
    # TODO: (Low priority) parameterise this line - find out function of each element.
    head = "0 5 0 N {} 1 1 100 100 0 0 0 Y".format(polygon_name)
    # this nomenclature is correct for how sonnet displays the geometry.
    # The indices Sonnet displays in the editor count from bottom left
    # The positions used in the file count from top left
    top_left = "{} {}".format(x_min, y_min)
    top_right = "{} {}".format(x_max, y_min)
    bottom_right = "{} {}".format(x_max, y_max)
    bottom_left = "{} {}".format(x_min, y_max)

    # the representation of a polygon in sonnet is as a loop, so the start point is repeated
    out_text = ('\n' + head +
                '\n' + top_left +
                '\n' + top_right +
                '\n' + bottom_right +
                '\n' + bottom_left +
                '\n' + top_left +
                "\nEND")
    return out_text


def count_substring(in_string, substring):
    """
    Count the instances of substring on a unique line in in_string
    :param in_string: a string to search through
    :param substring: a string to search for
    :return:int the count of substrings
    """
    # TODO: (low priority) test if the builtin in_string.count(substring) would work here
    #       see if there are any efficiency gains to be made.
    #       Possible implementation in_string.count('\n' + substring + '\n')?
    #       Query: how would the count builtin handle consecutive lines with substring?

    # starts a counter
    counter = 0

    # splits in_string into lines using '\n'
    for line in in_string.split('\n'):
        # checks each line to see if it matches the substring
        if line == substring:
            # increments the counter
            counter += 1

    # returns the count of substrings
    return counter


def gen_tail():
    """
    Adds the tail content (OPT, VarSweep, Sonnet output file, and Translator for GDS Export) to the string
    :return:
    """
    # reads the tail content from the template
    # TODO: sepatate out the OPT, VarSweep, Sonnet output file, and Translator components and make these variable
    tail_text = file_read(os.path.expanduser('templates/tail.son'))
    return tail_text


def file_read(in_filename):
    """
    Reads in the contents of in_filename and returns the contents as a string
    :param in_filename:
    :return:
    """
    # TODO: Add try/Except blocks to handle exceptions here.
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
    """
    This function expands the input path to something that can be used for file I/O.
    It does not check if the path exists.
    :param path:
    :return:
    """
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
        # expands the provided path with ~ replaced with environment-specific values
        path = os.path.expanduser(path)
        # gets the base of the path provided, removing any extension
        base_path = os.path.splitext(path)[0]
        # string for the sonnet extension
        ext = '.son'
        # HACK: this still isn't very extensible, but it's better than it was
        # gets the parameter being iterated over
        varying_parameter = str(args.iter)
        # gets the current value of that parameter and replaces '.' with '_' to avoid issues with extensions
        current_value = str(getattr(args, args.iter)).replace('.', '_')
        # creates a path suffix consisting of the parameter and its value
        suffix = '_' + varying_parameter + '_' + current_value
        # combines these into a path
        path = base_path + suffix + ext

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
