import argparse
import os
import glob

from gpx2pln_gpx import GpxFile, GpxConcat
from gpx2pln_pln import PlnFile

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Convert a GPX file to one or multiple PLN files for import in a flight simulator.")
    parser.add_argument("--pln_stem", type=str, default="gpx2pln", help="Stem for generating paths to the PLN files to write.")
    parser.add_argument("gpx_fnames", type=str, nargs="+", help="Paths to the GPX files to read.")
    args = parser.parse_args()

    # read the gpx files
    print("Reading the GPX files... ", end="", flush=True)
    gpx = list()
    for val in args.gpx_fnames:
        for fname in sorted(glob.glob(val)):
            gpx.append(GpxFile(fname))
    gpx = GpxConcat(gpx)
    print("done!", flush=True)

if __name__ == "__main__":
    main()
