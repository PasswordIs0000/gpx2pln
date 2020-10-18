import argparse
import os
import glob

from gpx2pln_gpx import GpxFile, GpxConcat
from gpx2pln_pln import PlnFile
from gpx2pln_airports import AirportDatabase

import gpx2pln_subsample

# only for debugging. coordinates can be copy-pasted into microsoft flight simulator.
def _debug_print_leg(coords):
    for c in coords:
        print("%s,%s" % (c.lat,c.lon))

def main():
    # parse command line arguments
    parser = argparse.ArgumentParser(description="Convert a GPX file to one or multiple PLN files for import in a flight simulator.")
    parser.add_argument("--pln_stem", type=str, default="gpx2pln", help="Stem for generating paths to the PLN files to write.")
    parser.add_argument("--max_leg_length", type=int, default=None, help="Maximum length of one leg in miles.")
    parser.add_argument("--num_leg_points", type=int, default=5, help="Number of waypoints per leg, departure and arrival inclusive.")
    parser.add_argument("--algorithm", type=str, default="subsample", help="Algorithm for choosing waypoints. Values: 'subsample'.")
    parser.add_argument("--use_airports", type=str, default=None, help="Download airport database to this file. Use nearest airports to departure and destination.")
    parser.add_argument("--reverse", action="store_true", help="Reverse the flight plan.")
    parser.add_argument("--no_local_airports", action="store_true", help="Do not use local airports in flight plans.")
    parser.add_argument("gpx_fnames", type=str, nargs="+", help="Paths to the GPX files to read.")
    args = parser.parse_args()

    # sanity checks
    assert args.max_leg_length is None or args.max_leg_length > 0
    assert args.num_leg_points >= 2
    assert args.algorithm in ["subsample"]

    # warn the user if not using the airport database
    if args.use_airports is None:
        print("WARNING: Using the option '--use_airports' is highly recommended! E.g.: --use_airports airports.json")

    # create the airport database if requested
    airport_db = None
    if not args.use_airports is None:
        airport_db = AirportDatabase(args.use_airports, args.no_local_airports)

    # convert the maximum leg length from miles to kilometres
    max_leg_length = None if args.max_leg_length is None else args.max_leg_length * 1.609344

    # read the gpx files
    print("Processing the GPX file(s)... ", end="", flush=True)
    gpx = list()
    for val in args.gpx_fnames:
        for fname in sorted(glob.glob(val)):
            gpx_part = GpxFile(fname)
            if len(gpx_part) > 0:
                gpx.append(gpx_part)
    gpx = GpxConcat(gpx)
    print("done!", flush=True)

    # reverse if requested
    if args.reverse:
        gpx.reverse()

    # choose waypoints for the flight plan
    print("Choosing waypoints... ", end="", flush=True)
    legs = None
    if args.algorithm == "subsample":
        legs = gpx2pln_subsample.subsample(gpx.get_track_coords(), max_leg_length, args.num_leg_points)
    else:
        raise NotImplementedError
    assert type(legs) == list and len(legs) > 0
    print("done!", flush=True)

    # save the legs as pln files
    print("Writing the PLN file(s)... ", end="", flush=True)
    for i in range(len(legs)):
        counter = str(i+1)
        title = gpx.get_track_name()
        if len(title) == 0:
            title = "Unnamed flight plan"
        elif len(title) > 30:
            title = title[:30] + "..."
        title += " (" + counter + ")"
        description = gpx.get_track_name() + " by " + gpx.get_author_name()
        pln = PlnFile(title, description, legs[i], elevation=gpx.get_max_elevation())
        pln.write(args.pln_stem + "_" + counter + ".pln", airport_db=airport_db)
    print("done!", flush=True)

if __name__ == "__main__":
    main()
