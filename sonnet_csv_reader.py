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

def gen_labels(steps):
    points = np.linspace(args.min, args.max, steps, args.endpoint)
    labels = []
    for point in points:
        labels.append(str(point)+'_'+str(args.unit))

    return labels



def plot_dfs(dfs):
    n = len(dfs)
    colors = plt.cm.jet(np.linspace(0, 1, n))
    labels = gen_labels(n)

    for i in range(n):
        x, y = extract_f_s21_df(dfs[i])

        plt.plot(x, y, label=labels[i], linestyle="-", color=colors[i])
    plt.xlabel(args.x_column)
    plt.ylabel(args.y_column)
    plt.title(args.title)
    plt.legend()
    if args.save:
        plt.savefig(os.path.expanduser(args.save))
        plt.close()
    else:
        plt.show()

def set_args():
    parser = argparse.ArgumentParser()
    unit_varied = ["ph_sq", "um_R", "um_L", "um_B"]
    parser.add_argument("dir", help="Directory containing csv files")
    parser.add_argument("-x", "--x_column", help="Sonnet output column containing the x coordinates", default="Frequency (GHz)")
    parser.add_argument("-y", "--y_column", help="Sonnet output column containing the y coordinates", default="MAG[S21]")
    parser.add_argument("-s", "--save", help="Path to save the plot", default=None)
    parser.add_argument("-t", "--title", help="Title of the plot", default="Plot of S21 against Frequency")
    parser.add_argument("-u", "--unit", help="Units varied in the directory", choices=unit_varied)
    parser.add_argument("-m", "--min", help="Minimum value of variable", default=1.0, type=float)
    parser.add_argument("-M", "--max", help="Maximum value of variable", default=6.0, type=float)
    parser.add_argument("-e", "--endpoint", help="Whether to remove the maximum value", action='store_false', default=True)

    out_args = parser.parse_args()
    return out_args

def main():
    dfs = get_dfs()
    plot_dfs(dfs)
    pass

if __name__ == '__main__':
    args = set_args()
    main()
