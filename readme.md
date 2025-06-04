# MKID Sonnet Variation
This is a project to create automated variations of MKID designs using Python to create Sonnet Geometries.

![Schematic of an MKID resonator. Shown in green is the interdigitated capacitor and shown in red is the meandering inductor.](schematic.svg)
*Schematic of an MKID resonator. Shown in green is the interdigitated capacitor and shown in red is the meandering inductor. The software presented here generates Sonnet geometries with specificied values or variations in the identified parameters.*

## How to use
This tool generates MKID geometries based on command line inputs.  It is currently in active development. Due to this, the internal documentation is the best route to read how to use it. To access the internal help, enter

`python3 gen_mkids.py -h` or `python3 sonnet_csv_reader.py -h`

## Acknowledgements
A template by Cathal McAleer is used as the base geometry.

This project relies on the `os`, `numpy`, `decimal`, `pandas` and `argparse` libraries.

Outputs from this software require the use of Sonnet software to process.
