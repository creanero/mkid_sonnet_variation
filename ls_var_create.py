import argparse
import os
from fileinput import filename

import numpy as np


def file_read(in_filename):
    in_file = open(in_filename, 'r')
    text = in_file.read()
    in_file.close()
    return text

def file_write(text, ls):
    out_path = gen_file_name(ls)
    out_file = open(out_path, 'w')
    out_file.write(text)
    out_file.close()

def check_dir(in_dir):
    if in_dir is None:
        print("defaulting to creating in working directory")
        in_dir = os.getcwd()

    if os.path.isdir(in_dir):
        out_dir: str = in_dir
    else:
        try:
            os.mkdir(in_dir)
            out_dir = in_dir
        except FileNotFoundError:
            print("The directory " + in_dir + " could not be created. Exiting!")
            exit(1)


    return out_dir

def gen_file_name(ls):
    out_dir = check_dir(args.dir)

    ls_text = str(ls).replace('.', '_')

    out_path = os.path.expanduser(out_dir+"/"+args.prefix+ls_text+".son")
    return out_path


def gen_ls_line(ls):
    base_text = 'MET "superconductor" 1 SUP 0 0 0 '
    out_text = '\n' + base_text + str(ls) + '\n'
    return out_text

def set_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Directory to hold output .son files", default=None)
    parser.add_argument("-m", "--min", help="Minimum kinetic inductance (pH/sq)", default=5.0, type=float)
    parser.add_argument("-M", "--max", help="Maximum kinetic inductance (pH/sq)", default=6.0, type=float)
    parser.add_argument("-S", "--step", help="Step count", default=11, type=int)
    parser.add_argument("-e", "--endpoint", help="Whether to remove the maximum value", action='store_false', default=True)
    parser.add_argument("-p", "--prefix", help="Prefix for output filenames", default='ls_var_')
    out_args = parser.parse_args()
    return out_args

def main():
    ls_values = np.linspace(args.min, args.max, args.step, args.endpoint)
    part_1 = file_read(os.path.expanduser('templates/ls_var_p1.son'))
    part_2 = file_read(os.path.expanduser('templates/ls_var_p2.son'))
    for ls in ls_values:
        text = part_1 + gen_ls_line(ls) + part_2
        file_write(text, ls)


    pass

if __name__ == '__main__':
    args = set_args()
    main()