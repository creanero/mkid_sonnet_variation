import argparse
from email import feedparser
from math import fabs
import os
import decimal
from socket import gaierror
from tkinter import FIRST
import numpy as np
import warnings


# TODO: refactor the use of global variables in this code, ideally removing them and replacing with function
#  arguments or class attributes where needed. This will make the code more modular and easier to test.

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
    geometry_text = "GEO"
    # Writes the properties of the "metals" to be used in the circuit (e.g. kinetic inductance per square)
    geometry_text = geometry_text + gen_met()
    # Writes a line explaining the dimensions and grid size to use (checked for floating point errors)
    geometry_text = geometry_text + gen_scale_line()
    # pulls in the backing parameters from a file
    # TODO: check what needs to be done for this to be parameterised
    geometry_text = geometry_text + gen_dielectric()
    # Generates the polygons that constitute the circuit
    geometry_text = geometry_text + gen_circuit()
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


def gen_dielectric():
    """
    Generates the backing text from a template file. This defines the substrate and some other parameters
    :return:
    """
    # TODO: identify ways to improve on this
    dielectric_text = '\n' + file_read(os.path.expanduser('templates/dielectric.son'))
    return dielectric_text


def gen_circuit():
    """
    Generates the polygons and ports that form the foreground circuit
    :return:
    """
    # Generate the ground plane
    gp_ports_string, gp_polygon_string = gen_ground_plane()

    # Generate the inductor
    inductor_string = gen_inductor()

    # Generates the capacitor 
    capacitor_string = gen_capacitor()

    # Combines the base and fingers strings
    polygon_string = gp_polygon_string + '\n' + inductor_string + '\n' + capacitor_string

    # Counts the polygons in the string using the substring "END"
    num_polygons = count_substring(polygon_string, "END")

    # Combines the polygons with the count
    polygon_text = ('NUM ' + str(num_polygons) + '\n' + polygon_string)

    circuit_text = ('\n' + gp_ports_string + '\n' + polygon_text)
    return circuit_text


def gen_ground_plane():
    """
    Generate the ground plane polygon. This is now procedurally generated based on the arguments and the other
    polygons, rather than being read from a template file.
    :return: ground_plane_string (string containing the .son code for the ground plane)
    """
    gp_left = 0
    gp_right = args.x_size
    gp_top = 0
    # top bar is from the top of the circuit to the top of the resonator, and spans the whole width of the circuit
    gp_top_string = gen_sonnet_rectangle(gp_left, gp_right, gp_top, resonator_top)
    # left and right sidebars are from the top of the resonator to the bottom of the resonator, and are gp_sidebar wide
    gp_sidebar_string_l = gen_sonnet_rectangle(gp_left, resonator_left, resonator_top, resonator_bottom)
    resonator_r = gp_right - gp_sidebar_breadth
    gp_sidebar_string_r = gen_sonnet_rectangle(resonator_r, gp_right, resonator_top, resonator_bottom)

    # near bar is from the bottom of the resonator to the gap before the feedline, and spans the whole width of the
    # circuit. It includes ports on the left and right side of the resonator, which are at the midpoint of the near bar 
    gp_port_num = -1
    gp_near_port_string, gp_near_string, gp_near_bottom = gen_gp_port_bar(resonator_bottom, gp_sidebar_breadth, gp_port_num, gp_port_num)

    # generates the feedline and its ports
    feed_line_top = gp_near_bottom + feed_line_space
    feed_line_port_num_l = 2
    feed_line_port_num_r = 1
    feed_line_port_string, feed_line_string, feed_line_bottom = gen_gp_port_bar(feed_line_top, feed_line_breadth, feed_line_port_num_l, feed_line_port_num_r)
    
    # generates the opposite bar of the ground plane and its ports
    gp_opp_top = feed_line_bottom + feed_line_space
    gp_opp_port_string, gp_opp_string, gp_opp_bottom = gen_gp_port_bar(gp_opp_top, gp_opp_breadth, gp_port_num, gp_port_num)

    # generates the final part of the ground plane
    gp_final_string = gen_sonnet_rectangle(0, args.x_size, gp_split, args.y_size)

    # combines the ports into a single string
    gp_ports_string = (gp_near_port_string + '\n' + feed_line_port_string + '\n' + gp_opp_port_string)

    # combines the polygons into a single string
    gp_polygon_string = (gp_top_string + '\n' + gp_sidebar_string_l + '\n' + gp_sidebar_string_r + '\n' +
                           gp_near_string + '\n' + feed_line_string + '\n' + gp_opp_string + '\n' + gp_final_string)
    return gp_ports_string, gp_polygon_string


def gen_gp_port_bar(top, breadth, port_num_l, port_num_r, reference_plane_l=1, reference_plane_r=3):
    """
    Generate a horizontal ground-plane (or feed-line) bar and its two edge ports.

    Parameters
    ----------
    top : float
        Y coordinate of the top edge of the bar (micrometres).
    breadth : float
        Vertical thickness/height of the bar (micrometres).
    port_num_l : int
        Port number to place on the left edge. 
    port_num_r : int
        Port number to place on the right edge. 
    reference_plane_l : int, optional
        Reference plane index for the left port (default: 1).
    reference_plane_r : int, optional
        Reference plane index for the right port (default: 3).

    Returns
    -------
    tuple
        A 3-tuple (port_string, bar_string, bottom) where:
        - port_string (str): combined .son port definitions (right port then left port, separated by newline).
        - bar_string (str): .son rectangle definition for the bar polygon.
        - bottom (float): Y coordinate of the bottom edge of the bar (equal to top + breadth).

    Notes
    -----
    - The bar spans the full circuit width using the global `args.x_size` for the right X coordinate.
    - Ports are placed at the vertical midpoint of the bar and are generated by `gen_port`.
    - The rectangle polygon is generated by `gen_sonnet_rectangle`.
    """
    # near bar is from the bottom of the resonator and gp_sidebar deep, and spans the whole width of the circuit
    bottom = top + breadth
    left = 0
    right = args.x_size

    # generates the ports 
    midpoint = bottom + (breadth/2)
    port_string_l = gen_port(left, midpoint, port_num_l, reference_plane_l)
    port_string_r = gen_port(right, midpoint, port_num_r, reference_plane_r)
    port_string = port_string_r + '\n' + port_string_l

    # generates the sonnet rectangle for the circuit bar
    bar_string = gen_sonnet_rectangle(left, right, top, bottom)

    return port_string, bar_string, bottom


def gen_port(x, y, port_num, reference_plane, port_type="BOX", resistance=50, reactance=0, inductance=0, capacitance=0): # polygon_name is a global variable, so it doesn't need to be passed in
    """
    Generates the port string for the .son file. This is used to define the ports for the Sonnet simulation.
    :param x: X-coordinate of the port in micrometres
    :param y: Y-coordinate of the port in micrometres
    :param port_num: Port number (integer)
    :param reference_plane: Reference plane for the port (integer)
    :param port_type: Type of port (string, default is "BOX")
    :param resistance: Resistance of the port (float, default is 50)
    :param reactance: Reactance of the port (float, default is 0)
    :param inductance: Inductance of the port (float, default is 0)
    :param capacitance: Capacitance of the port (float, default is 0)
    :return: port_string (string containing the .son code for the port)
    """
    port_string =("POR1 {}\n".format(port_type) +
                  "POLY {} 1\n".format(polygon_name) + 
                  "{}\n".format(reference_plane) + 
                  "{} {} {} {} {} {} {}".format(port_num, resistance, reactance, inductance, capacitance, x, y))
    return port_string



def gen_inductor():
    """
    Generate the polygons for the inductor. This is read from a template file.
    :return: inductor_string (string containing the .son code for the inductor)
    """
    # reads inductor from a template file
    inductor_string = file_read(os.path.expanduser('templates/inductor.son'))
    return inductor_string


def gen_inductor_junction():
    """
    Generate the polygons for the inductor junction. This is read from a template file.
    :return: inductor_junction_string (string containing the .son code for the inductor junction)
    """
    inductor_junction_string = file_read(os.path.expanduser('templates/inductor_junction.son'))
    return inductor_junction_string


def gen_inductor_turn():
    pass


def gen_inductor_end():
    pass


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
    capacitor_string = capacitor_frame_string + fingers_string
    # returns the string containing the code for the capacitor
    return capacitor_string


def gen_capacitor_frame():
    """
    Generate the outline of the capacitor. This is generated procedurally based on the arguments and the other polygons, rather than being read from a template file.
    :return: capacitor_frame_string (string containing the .son code for the capacitor outline)
    """
    # generates the coordinates for the capacitor frame based on the arguments and the other polygons
    # calculates the space between the transfer bar and the capacitor fingers
    cap_finger_space = args.pitch - args.thick
    # calculates the bottom of the capacitor frame based on the transfer bar and the space between the transfer bar
    # and the capacitor fingers
    cap_left_bottom = transfer_bar_in - cap_finger_space
    # generates the polygons for the capacitor frame using the coordinates calculated above
    capacitor_frame_l_string = gen_sonnet_rectangle(cap_left_out, cap_left_in, cap_top_out, cap_left_bottom)
    capacitor_frame_r_string = gen_sonnet_rectangle(cap_right_in, cap_right_out, cap_top_out, transfer_bar_out)
    capacitor_top_l_string = gen_sonnet_rectangle(cap_left_in, inductor_junction_start, cap_top_out, cap_top_in)
    capacitor_top_r_string = gen_sonnet_rectangle(inductor_junction_end, cap_right_in, cap_top_out, cap_top_in)
    transfer_bar_string = gen_sonnet_rectangle(transfer_bar_end, cap_right_in, transfer_bar_in, transfer_bar_out)
    
    # combines these into a single string
    capacitor_frame_string = (capacitor_frame_l_string + '\n' + capacitor_frame_r_string + '\n' + capacitor_top_l_string
                              + '\n' + capacitor_top_r_string + '\n' + transfer_bar_string)
    return capacitor_frame_string


def gen_fingers():
    """
    Generate the capacitor finger polygons
    :return:
    """
    # TODO: refactor this function, it's messy and uses deprecated terminology
    fingers_string = ''

    # gets the finger properties from the arguments
    num_fingers = int(args.num_fingers)
    finger_length = args.length
    finger_thickness = args.thick
    finger_pitch = args.pitch 
    
    # calculates the space between the fingers based on the pitch and thickness
    finger_space = finger_pitch - finger_thickness
    # calculates the starting point for the first finger based on the transfer bar and the space between the fingers
    first_finger = transfer_bar_in - finger_space
    # calculates the end point for the last finger based on the first finger, the pitch and the number of fingers
    end_fingers = first_finger - (finger_pitch * num_fingers)

    # need to leave space for final (partial) finger
    if (end_fingers - finger_pitch) < cap_top_in:
        raise OverflowError

    # generates the starting points for each finger based on the first finger, the pitch and the number of fingers
    start_points = np.linspace(first_finger, end_fingers, num_fingers, endpoint=False)

    # generates an index variable to keep track of which finger is being generated, and whether it is on the right or
    # left side of the capacitor
    i = 0
    # iterates through the starting points, generating the polygons for each finger and adding them to the
    # fingers_string
    for i in range(num_fingers):
        right = bool(i % 2)
        x_min, x_max, y_min, y_max = gen_points(start_points[i], finger_length, right)
        fingers_string = fingers_string + '\n' + gen_sonnet_rectangle(x_min, x_max, y_min, y_max)

    # gets the right/left status of the final finger based on the number of fingers, and generates the partial finger
    # at the end of the capacitor
    right = bool(num_fingers % 2)
    fingers_string = fingers_string + '\n' + gen_part_finger(end_fingers, right)

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

    # Generates a rectangle (polygon) with those coordinates.
    part_finger_string = gen_sonnet_rectangle(x_min, x_max, y_min, y_max)
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
        x_min = cap_right_in - finger_length
        # and maximum is at the maximum edge of the capacitor
        x_max = cap_right_in
    # otherwise, it's coming from the left
    else:
        # minimum is at the minimum edge of the capacitor
        x_min = cap_left_in
        # maximum is the length onto the minimum edge of the capacitor
        x_max = cap_left_in + finger_length

    # Y minimum is subtracted from the start point
    # following Sonnet file logic, which is reverse of display logic
    y_min = y_start - finger_thickness
    # Y maximum is equal to the start point
    y_max = y_start

    return x_min, x_max, y_min, y_max


def gen_sonnet_rectangle(x_min, x_max, y_min, y_max):
    """
    Generates a sonnet rectangle based on the coordinates provided
    :param x_min:float Minimum x-coordinate in micrometres
    :param x_max:float Maximum x-coordinate in micrometres
    :param y_min:float Minimum y-coordinate in micrometres
    :param y_max:float Maximum y-coordinate in micrometres
    :return:str Containing the sonnet formatted code for the rectangle
    """
    # header line taken from template
    # TODO: (Low priority) parameterise this line - find out function of each element.
    global polygon_name
    head = "0 5 0 N {} 1 1 100 100 0 0 0 Y".format(polygon_name)
    # this nomenclature is correct for how sonnet displays the geometry.
    # The indices Sonnet displays in the editor count from bottom left
    # The positions used in the file count from top left
    top_left = "{} {}".format(x_min, y_min)
    top_right = "{} {}".format(x_max, y_min)
    bottom_right = "{} {}".format(x_max, y_max)
    bottom_left = "{} {}".format(x_min, y_max)

    # the representation of a polygon in sonnet is as a loop, so the start point is repeated
    out_text = (head +
                '\n' + top_left +
                '\n' + top_right +
                '\n' + bottom_right +
                '\n' + bottom_left +
                '\n' + top_left +
                "\nEND")
    
    # increments the polygon name for the next polygon
    # TODO: this is a bit hacky, ideally the polygon name would be
    #  generated in a more modular way, perhaps by a class that keeps track of the count of polygons and generates
    #  unique names as needed.
    polygon_name = polygon_name + 1  

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
    :return: tail_text (string containing the tail content for the .son file)
    """
    # reads the tail content from the template
    # TODO: separate out the OPT, VarSweep, Sonnet output file, and Translator components and make these variable
    tail_text = file_read(os.path.expanduser('templates/tail.son'))
    return tail_text


def file_read(in_filename):
    """
    Reads in the contents of in_filename and returns the contents as a string.
    :param in_filename: string containing the path to the file to be read
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
        if os.path.isdir(path):
            warnings.warn("The path provided is a directory. The file will be saved as mkid.son in that directory.")
            path = os.path.join(path, "mkid.son")
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
    parser.add_argument("-p", "--pitch", help="Finger Pitch (start to start) in micrometres", default=4.0, type=float)
    parser.add_argument("-L", "--length", help="Length of fingers in micrometres", default=450.0, type=float)
    parser.add_argument("-f", "--final", help="length of final finger in micrometers", default=84.0, type=float)
    iter_options = ["None", "length", "thick", "pitch", "final", "num_fingers"]
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
    # global variables as placeholders
    # TODO: Parameterise these using arg or otherwise

    # These relate to the edges of the ground plane.
    gp_split = 409.0
    gp_opp_breadth = 25.0
    gp_sidebar_breadth = 12.0

    # these relate to the edges of the feed line
    feed_line_space = 5.0 
    feed_line_breadth = 35.0

    # these relate to the edges of the resonator
    resonator_top = 152.0
    resonator_bottom = resonator_top + 175.0
    resonator_left = gp_sidebar_breadth

    # polygon name counter, used to give each polygon a unique name
    polygon_name = 100

    # these relate to the edges of the inductor 
    inductor_junction_start = 240.0
    inductor_space = 1.0
    inductor_breadth = 1.0
    inductor_width = 20.0
    inductor_junction_end = inductor_junction_start + (2 * inductor_breadth) + inductor_space
    inductor_turns = 5
    inductor_height = inductor_turns * 2 * (inductor_breadth  + inductor_space)

    # These are the edges of the capacitor.
    cap_side_space = 5.0
    cap_side_breadth = 7.0
    cap_left_out = gp_sidebar_breadth + cap_side_space
    cap_left_in = cap_left_out + cap_side_breadth
    cap_right_out = args.x_size - gp_sidebar_breadth - cap_side_space
    cap_right_in = cap_right_out - cap_side_breadth
    cap_vert_space = 4.0
    cap_top_breadth = 10.0
    cap_top_out = resonator_top + cap_vert_space + inductor_height
    cap_top_in = cap_top_out + cap_top_breadth
    transfer_bar_breadth = 5.0
    transfer_bar_end = 250.0
    transfer_bar_out = resonator_bottom - cap_vert_space
    transfer_bar_in = transfer_bar_out - transfer_bar_breadth
    # Executes the main function.
    main()
