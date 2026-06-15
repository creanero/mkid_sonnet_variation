import pandas as pd
import sys
import os
import glob
from matplotlib import pyplot as plt
from matplotlib import rc
import numpy as np
import argparse
import warnings

from pygments.lexer import default


def read_one(filename):
    """
    Read one CSV file into a data frame
    :param filename: a string containing one file
    :return: a dataframe containing the contents of filename
    """
    # uses pandas to read the CSV file specified in filename into a dataframe, and specifies that it has a header line.
    out_df = pd.read_csv(filename, header=[1])
    return out_df


def extract_f_s21_df(in_df):
    # tries to read the x column from the dataframe
    try:
        x = in_df[args.x_column]
    # if it fails, sets x to empty list
    except KeyError:
        print("Warning: column '" + args.x_column + "' not found in the dataframe")
        x = []

    # tries to read the y column from the dataframe
    try:
        y = in_df[args.y_column]
    # if it fails, sets y to empty list
    except KeyError:
        print("Warning: column '" + args.y_column + "' not found in the dataframe")
        y = []

    # if either x or y are empty, set them both to empty
    if len(x) == 0 or len(y) == 0:
        x = []
        y = []
    # returns the columns or empty list
    return x, y


def get_csv_dir(in_dir):
    """
    Gets a sorted list of all of the CSV files in the input directory
    :param in_dir:
    :return: a (possibly empty) list of all CSV files in the specified directory
    """
    # gets the paths to all CSV files in in_dir and sorts it alphabetically
    csvs = sorted(glob.glob(in_dir + '*.csv'))
    return csvs


def check_dir(in_dir):
    """
    Checks if the input directory exists, and raises an error if it does not
    :param in_dir: a string that should specify a directory containing CSV files
    :return:
    """
    # checks if in_dir is a currently existing directory
    if os.path.isdir(in_dir):
        out_dir: str = in_dir
    # if it isn't, exit with an informative message
    else:
        exit_message = "Input directory:\n\t{}\n does not exist".format(in_dir)
        sys.exit(exit_message)
    return out_dir


def get_dir_args():
    """
    Gets and checks the directory specified in the arguments
    :return:
    """
    # Gets the input directory specified in the arguments
    in_dir = args.dir
    # sets the current working directory as a default value to return if the input directory isn't specified
    out_dir = os.getcwd()

    # if the input directory isn't specified
    if in_dir is None:
        # raise a warning
        warning_text = "No directory specified, using current working directory:\n{}".format(out_dir)
        warnings.warn(warning_text)

    # Checks the input directory
    out_dir = check_dir(in_dir)

    return out_dir


def get_dfs():
    """
    Gets the dataframes from the CSV files in the directories specified in the arguments
    :return: a list of data frames containing the data from the CSV files
    """
    # gets the input directory specified in the arguments
    in_dir = get_dir_args()
    # gets a list of the CSV files specified in the input directory
    csvs = get_csv_dir(in_dir)
    # creates an empty list of dataframes
    dfs = []

    # for each CSV file in the list of CSV files from the input directory
    for csv in csvs:
        # read the contents of the CSV file, and append it to the list of dataframes
        dfs.append(read_one(csv))

    # return the list of dataframes
    return dfs


def gen_labels(n_files):
    points = np.linspace(args.min, args.max, n_files, args.endpoint)
    labels = []
    for point in points:
        labels.append(str(point) + ' pH/sq')  # +str(args.unit))

    return labels


def plot_dfs(dfs):
    """
    Plots the X and Y variables of each of the dataframes as overlaid plots
    :param dfs: a list containing zero or more dataframes
    :return:
    """
    # gets the number of dataframes in the list
    n_files = len(dfs)
    # creates a set of colours using the jet colourmap
    colors = plt.cm.jet(np.linspace(0, 1, n_files))
    # generates the labels for each of the files
    labels = gen_labels(n_files)

    # creates the plot
    plt.figure()

    # iterates over the number of files
    for i in range(n_files):
        # gets the x and y coordinates from the dataframe
        x, y = extract_f_s21_df(dfs[i])
        # tries to plot them
        try:
            # plots the datapoints joined with a line and using a label and colour as specified
            plt.plot(x, y, label=labels[i], linestyle="-", color=colors[i])
        # if there is a problem with plotting
        except ValueError:  # x and y are incompatible with plotting
            # issue a warning
            warning_message = "\nUnable to plot dataframe {}" \
                              "\n\t{}" \
                              "\n\t{} and {} columns are incompatible." \
                              "".format(str(i), labels[i], args.x_column, args.y_column)
            warnings.warn(warning_message)
        except RuntimeError:  # probably latex not available
            # issue a warning
            warning_message = "\nUnable to plot dataframe {}" \
                              "\n\t{}" \
                              "\n\tFailed to process string with tex because latex could not be found!" \
                              "".format(str(i), labels[i])
            warnings.warn(warning_message)

    # Set the font size on the x and y labels and tickmarks
    plt.xlabel(args.x_column, fontsize=16)
    plt.ylabel(args.y_column, fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # make the Y-axis logarithmic in scale this was a recommendation from the paper referee
    # TODO: make this an option in the arguments
    plt.yscale('log')

    # Put a title and legend on the plot
    plt.title("Plot of " + args.x_column + " vs. " + args.y_column + " for " + str(n_files) + " values of " + args.unit)
    plt.legend()

    # if the user has requested that the plot be saved to disk
    if args.save:
        # save the figure using a generated filename
        plt.savefig(get_out_filename("curves"))
        # close the plot gracefully
        plt.close()
    else:  # no output directory is specified
        # show the plot in the interactive interface
        plt.show()


def get_out_filename(suffix, file_type=None):
    if file_type is None:
        file_type = args.type
    out_path = os.path.expanduser(args.save) + ('var_' + args.unit + '_' +
                                                str(args.min) + '-' +
                                                str(args.max) + '_' +
                                                suffix + '.' + file_type)
    return out_path


def plot_mins(dfs):
    n_files = len(dfs)
    x = np.linspace(args.min, args.max, n_files, args.endpoint)
    y = get_mins(dfs)

    plt.figure()
    plt.plot(x, y)
    plt.xlabel(args.unit)
    plt.ylabel(args.x_column)
    plt.title("Plot of the minima in " + args.x_column + " against " + args.unit)
    if args.save:
        plt.savefig(get_out_filename("mins"))
        plt.close()
        out_dict = {args.unit: x, args.x_column: y}
        out_df = pd.DataFrame(out_dict)
        out_df.to_csv(get_out_filename("mins", file_type="csv"))
    else:
        plt.show()


def get_mins(dfs):
    mins = []
    for df in dfs:
        # gets the index of the local minimum of the y column
        min_y = df[args.y_column].idxmin()
        # gets the value of the x variable that corresponds to the minimum in y
        x_at_y_min = df[args.x_column][min_y]
        # adds that x value to the collection
        mins.append(x_at_y_min)
    return mins


def set_args():
    """
    Sets the arguments using argparse
    :return:
    """
    parser = argparse.ArgumentParser()
    # LISTS OF OPTIONS
    # sets up the lists of possible options for variable
    unit_varied = ["ph_sq", "um_R", "um_L", "um_B"]
    # sets up the options of what to plot
    plot_options = ["curves", "both", "mins"]
    # sets up the options for file type to save the output plots as
    file_types = ["png", "jpg", "jpeg", "pdf"]

    # INPUTS
    # adds the option for the directory containing input files
    parser.add_argument("dir", help="Directory containing csv files")
    # sets the units that are varied in the input files
    parser.add_argument("-u", "--unit", help="Units varied in the directory", choices=unit_varied, default="ph_sq")
    # specifies the minimum and maximum values of that variable
    parser.add_argument("-m", "--min", help="Minimum value of variable", default=1.0, type=float)
    parser.add_argument("-M", "--max", help="Maximum value of variable", default=4.0, type=float)
    # specifies whether the max value is included or not
    parser.add_argument("-e", "--endpoint", help="Whether to remove the maximum value", action='store_false',
                        default=True)

    # PLOTS
    # adds the option for the user to select the variable to plot on the x-axis
    parser.add_argument("-x", "--x_column", help="Sonnet output column containing the x coordinates",
                        default="Frequency (GHz)")
    # adds the option for the user to select the variable to plot on the y-axis
    parser.add_argument("-y", "--y_column", help="Sonnet output column containing the y coordinates",
                        default="MAG[S21]")
    # adds the option for the user to select between various options to plot
    parser.add_argument("-N", "--n_plots", help="Select which plots to show", default="both", choices=plot_options)

    # OUTPUTS
    # sets the path to save the output plot(s) in.
    parser.add_argument("-s", "--save", help="Path to save the plots", default=None)
    # sets the file type for the output plots
    parser.add_argument("-T", "--type", help="Select file type to save output files", default="png", choices=file_types)

    # actually parses the arguments
    out_args = parser.parse_args()
    return out_args


def main():
    """
    main function for reading and plotting Sonnet CSV outputs
    :return:
    """
    # gets the dataframes from the files
    dfs = get_dfs()
    # if the user has selected to plot the data curves directly
    if args.n_plots in ["both", "curves"]:
        # plots the contents of the dataframes
        plot_dfs(dfs)
    # if the user has selected to plot the minima
    if args.n_plots in ["both", "mins"]:
        # plots the trends in the minima
        plot_mins(dfs)
    pass


if __name__ == '__main__':
    # Gets the arguments using argparse
    # args becomes a global variable
    args = set_args()
    # runs the main function
    main()
