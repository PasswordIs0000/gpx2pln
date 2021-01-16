# gpx2pln

## Overview

Tool to load a bunch of .gpx files and the tracks contained in them. Write the combined track as one or multiple .pln files for Microsoft Flight Simulator 2020. The intended use is to e.g. fly along long distance hiking trails, bicycle routes or really any other track in GPX format. The basic task that this tool should solve is that a GPX track consists of many thousands of waypoints and that way too much for a useable flight plan. We want to actually choose a suitable subset of the waypoints (or generate new artificial ones) that break down the GPX track to a reasonable flight plan.

General features are:
- Load one or more GPX files and concatenate them in order to retrieve a full track. For example the GPX track for the PCT is split into sections.
- Find a reasonable small amount of waypoints to use in a flight plan that still follow along the original track.
- If requested, split down the total flight plan into legs of a specific maximum length.
- Find nearest airports to the start and end of each leg to use as departure and destination.
- Export the generated flight plan in one or multiple PLN files that can be loaded into Microsoft Flight Simulator 2020.

## A Word on Airports

I really recommend to download the MSFS-compatible version of [Little Navmap](https://albar965.github.io/littlenavmap.html) and start it at least once. It will parse the Microsoft Flight Simulator 2020 packages and generate a database of airports in the simulation. This database will again be detected and used by gpx2pln in order to find the nearest airports to the legs that are created. This is really nice if you want to start and land on an actual airport in the simulation.

Not using [Little Navmap](https://albar965.github.io/littlenavmap.html) will result in gpx2pln using other airport databases (see below), which may work but there is also a chance that the airport is not in the simulation or uses a different ICAO code and thus you will start or end your flight in the air above the not existing airport.

## Disclaimer

Uses data from [GitHub/mwgg](https://github.com/mwgg/Airports) and [OurAirports](https://ourairports.com/data/) to find the nearest airports to the departure and destination. Imports airport database from [Little Navmap](https://albar965.github.io/littlenavmap.html) if found on the machine.

Uses [LatLon23](https://github.com/hickeroar/LatLon23) for calculations with geo-coordinates. Used [Scikit-Image](https://scikit-image.org/) for polygon subdivision and approximation algorithms.

Cheers and much thanks to the authors!

## Usage

This is a command line tool, written in Python 3.8. An example call would be:
    
    python gpx2pln.py Kungsleden.gpx

Which would write one file *Kungsleden_1.pln* describing the flight plan. We can also split it into legs of a maximum length in miles:

    python gpx2pln.py --max_leg_length 5 Kungsleden.gpx

Which would generate multiple flight plans *Kungsleden_1.pln*, *Kungsleden_2.pln* and so on, each with a length of approximate 5 miles. Not really usable, but a nice example. The utility can also load several GPX files in order and process them in order to retrieve one or multiple flight plans:

    python gpx2pln.py --pln_stem pct PCT\s_ca_halfmile_gpx\*.gpx PCT\n_ca_halfmile_gpx\*.gpx PCT\or_halfmile_gpx\*.gpx PCT\wa_halfmile_gpx\*.gpx

## Command Line Parameters

Currently supported parameters are:
- **pln_stem** to choose how to name the resulting PLN files. They will be named *pln_stem_1.pln*, *pln_stem_2.pln* and so on.
- **max_leg_length** to limit the maximum length of one leg in miles. The flight plan will be split into multiple parts if necessary.
- **num_leg_points** the number of waypoints per leg. More will result in a flight plan that better follows the GPX track but has more curves to fly.
- **algorithm** selects the algorithm applied to choose a subset of waypoints for each leg or generate new waypoints alltogether.
- **reverse** does indeed reverse the direction of the flight.
- **reset_airports** regenerates the airports database from scratch.