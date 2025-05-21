import pandas as pd
import sys
import os
import glob
from matplotlib import pyplot as plt
import numpy as np
import argparse

from pygments.lexer import default


def read_one(filename):
    out_df = pd.read_csv(filename, header=[1])
    return out_df

def extract_f_s21_df(in_df):

    # tries to read the x column from the dataframe
    try:
        x=in_df[args.x_column]
    # if it fails, sets x to empty list
    except KeyError:
        print("Warning: column '" + args.x_column + "' not found in the dataframe")
        x=[]

    # tries to read the y column from the dataframe
    try:
        y=in_df[args.y_column]
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
    csvs = glob.glob(in_dir + '*.csv')
    return csvs

def check_dir(in_dir):
    if os.path.isdir(in_dir):
        out_dir: str = in_dir
    else:
        raise IOError
    return out_dir

def get_dir_args():
    in_dir = args.dir
    out_dir = os.getcwd()
    if in_dir is None:
        print("No directory specified, using current working directory.")
    else:
        out_dir = check_dir(in_dir)
    # else:
    #     print("Invalid number of arguments. Defaulting to current working directory.")
    return out_dir

def get_dfs():
    in_dir = get_dir_args()
    csvs = get_csv_dir(in_dir)
    dfs = []
    for csv in csvs:
        dfs.append(read_one(csv))
    return dfs

def gen_labels(n_files):
    points = np.linspace(args.min, args.max, n_files, args.endpoint)
    labels = []
    for point in points:
        labels.append(str(point)+'_'+str(args.unit))

    return labels



def plot_dfs(dfs):
    n_files = len(dfs)
    colors = plt.cm.jet(np.linspace(0, 1, n_files))
    labels = gen_labels(n_files)
    plt.figure()

    for i in range(n_files):
        x, y = extract_f_s21_df(dfs[i])

        plt.plot(x, y, label=labels[i], linestyle="-", color=colors[i])
    plt.xlabel(args.x_column)
    plt.ylabel(args.y_column)
    plt.title("Plot of "+args.x_column+" vs. "+args.y_column+" for "+str(n_files)+" values of "+args.unit)
    plt.legend()
    if args.save:
        plt.savefig(get_out_filename("curves"))
        plt.close()
    else:
        plt.show()

def get_out_filename(suffix):
    out_path = os.path.expanduser(args.save) + 'var_' + args.unit + '_' + args.min + '-' + args.max + '_' + suffix + '.' + args.type
    return out_path

def plot_mins(dfs):
    n_files = len(dfs)
    x = np.linspace(args.min, args.max, n_files, args.endpoint)
    y = get_mins(dfs)

    plt.figure()
    plt.plot(x, y)
    plt.xlabel(args.unit)
    plt.ylabel(args.x_column)
    plt.title("Plot of the minima in "+args.x_column+" against "+args.unit)
    if args.save:
        plt.savefig(get_out_filename("mins"))
        plt.close()
    else:
        plt.show()

def get_mins(dfs):
    mins=[]
    for df in dfs:
        # gets the index of the local minimum of the y column
        min_y=df[args.y_column].idxmin()
        # gets the value of the x variable that corresponds to the minimum in y
        x_at_y_min = df[args.x_column][min_y]
        # adds that x value to the collection
        mins.append(x_at_y_min)
    return mins

def set_args():
    parser = argparse.ArgumentParser()
    unit_varied = ["ph_sq", "um_R", "um_L", "um_B"]
    plot_options = ["curves", "both", "mins"]
    file_types = ["png", "jpg", "jpeg", "pdf"]
    parser.add_argument("dir", help="Directory containing csv files")
    parser.add_argument("-x", "--x_column", help="Sonnet output column containing the x coordinates", default="Frequency (GHz)")
    parser.add_argument("-y", "--y_column", help="Sonnet output column containing the y coordinates", default="MAG[S21]")
    parser.add_argument("-s", "--save", help="Path to save the plots", default=None)
    parser.add_argument("-u", "--unit", help="Units varied in the directory", choices=unit_varied)
    parser.add_argument("-m", "--min", help="Minimum value of variable", default=1.0, type=float)
    parser.add_argument("-M", "--max", help="Maximum value of variable", default=6.0, type=float)
    parser.add_argument("-e", "--endpoint", help="Whether to remove the maximum value", action='store_false', default=True)
    parser.add_argument("-N", "--n_plots", help="Select which plots to show", default="both", choices=plot_options)
    parser.add_argument("-T", "--type", help="Select file type to save output files", default="png", choices=file_types)

    out_args = parser.parse_args()
    return out_args

def main():
    dfs = get_dfs()
    if args.n_plots in ["both", "curves"]:
        plot_dfs(dfs)
    if args.n_plots in ["both", "mins"]:
        plot_mins(dfs)
    pass

if __name__ == '__main__':
    args = set_args()
    main()
