from sqlite3.dbapi2 import connect
import urllib.request
import json
import os
import datetime
import LatLon23
import csv
import io
import sqlite3

def _add_mwgg_to_database(db):
    mwgg_blob = urllib.request.urlopen("https://github.com/mwgg/Airports/raw/master/airports.json").read()
    mwgg_dict = json.loads(mwgg_blob.decode("utf-8"))
    for icao, info in mwgg_dict.items():
        icao = str(icao).upper()
        iata = info["iata"]
        if type(iata) == str and len(iata) == 0:
            iata = None
        if type(iata) == str:
            iata = iata.upper()
        db[icao] = {
            "lat": float(info["lat"]),
            "lon": float(info["lon"]),
            "elevation": int(info["elevation"]),
            "name": str(info["name"]),
            "local_code": None,
            "iata": iata
        }

def _add_ourairports_com_to_database(db):
    ourairports_blob = urllib.request.urlopen("https://ourairports.com/data/airports.csv").read()
    ourairports_fd = io.StringIO(ourairports_blob.decode("utf-8"))
    ourairports_reader = csv.DictReader(ourairports_fd, dialect="excel")
    for info in ourairports_reader:
        type = info["type"]
        if type in ("closed", "heliport", "seaplane_base"):
            continue
        icao = str(info["ident"]).upper()
        local_code = str(info["local_code"]).upper()
        iata = info["iata_code"]
        if len(iata) == 0:
            iata = None
        else:
            iata = iata.upper()
        if iata is None and icao in db:
            iata = db[icao]["iata"]
        if len(local_code) == 0 or local_code == icao:
            local_code = None
        ele = str(info["elevation_ft"])
        if len(ele) == 0:
            if icao in db:
                ele = db[icao]["elevation"]
            else:
                continue
        db[icao] = {
            "lat": float(info["latitude_deg"]),
            "lon": float(info["longitude_deg"]),
            "elevation": int(ele),
            "name": str(info["name"]),
            "local_code": local_code,
            "iata": iata
        }

def _add_lnv_to_database(db, fname):
    # connect to the database
    connection = sqlite3.connect(fname)
    cursor = connection.cursor()

    # select the required values
    cursor.execute("SELECT ident,name,icao,iata,lonx,laty,altitude FROM airport")

    # add the values to the database
    for val in cursor:
        ident = str(val[0]).upper()
        db[ident] = {
            "lat": float(val[5]),
            "lon": float(val[4]),
            "elevation": int(val[6]),
            "name": str(val[1]),
            "local_code": None,
            "iata": str(val[3])
        }

class AirportDatabase:
    def __init__(self, fname, no_local_airports):
        # airports dictionary
        self.__airportDict = dict()

        # path to the little navmap database
        lnv_db_fname = os.environ["APPDATA"] + "\\ABarthel\little_navmap_db\\little_navmap_msfs.sqlite"

        # load from file if possible
        if os.path.isfile(fname):
            file_dtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(fname))
            cur_dtime = datetime.datetime.utcnow()
            if (cur_dtime-file_dtime) < datetime.timedelta(weeks=2):
                print("Loading the airports database... ", end="", flush=True)
                with open(fname, "r") as fd:
                    self.__airportDict = json.load(fd)
                print("done!", flush=True)
        
        # download and fill necessary
        save_database = False
        if len(self.__airportDict) == 0:
            save_database = True
            if os.path.isfile(lnv_db_fname):
                print("Importing the Little Navmap database... ", end="", flush=True)
                _add_lnv_to_database(self.__airportDict, lnv_db_fname)
                print("done!", flush=True)
            else:
                print("Downloading the airports database... ", end="", flush=True)
                _add_mwgg_to_database(self.__airportDict)
                _add_ourairports_com_to_database(self.__airportDict)
                print("done!", flush=True)
        
        # save the database if necessary
        if save_database:
            print("Saving the airports database... ", end="", flush=True)
            with open(fname, "w") as fd:
                json.dump(self.__airportDict, fd)
            print("done!", flush=True)
        
        # filter the airports if requested
        if no_local_airports:
            filtered_dict = dict()
            for icao, info in self.__airportDict.items():
                if not info["iata"] is None:
                    filtered_dict[icao] = info
            self.__airportDict = filtered_dict
        
        # print the number of airports in the database
        print("Using a total of %i airports!" % (len(self.__airportDict)))

        # store the airport codes searchable by their latitude and longitude as integers
        assert len(self.__airportDict) > 0
        self.__idxLat = [None] * 360
        self.__idxLon = [None] * 360
        for icao, info in self.__airportDict.items():
            lat = int(info["lat"] + 180.0)
            lon = int(info["lon"] + 180.0)
            assert lat >= 0 and lon >= 0
            if self.__idxLat[lat] is None:
                self.__idxLat[lat] = set()
            self.__idxLat[lat].add(icao)
            if self.__idxLon[lon] is None:
                self.__idxLon[lon] = set()
            self.__idxLon[lon].add(icao)
    
    def find_nearest(self, lat, lon):
        # convert to integers
        lat_idx = int(lat + 180.0)
        lon_idx = int(lon + 180.0)
        assert lat_idx >= 0 and lon_idx >= 0

        # find candidate airports
        lat_cands = set()
        lon_cands = set()
        for offset in range(-3, +4):
            # find candidates with latitude offset
            cand_idx = (lat_idx + offset) % 360
            if not self.__idxLat[cand_idx] is None:
                lat_cands.update(self.__idxLat[cand_idx])

            # find candidates with longitude offset
            cand_idx = (lon_idx + offset) % 360
            if not self.__idxLon[cand_idx] is None:
                lon_cands.update(self.__idxLon[cand_idx])
        cands = lat_cands.intersection(lon_cands)
        
        # target coordiate
        target_coord = LatLon23.LatLon(lat, lon)
        nearest_icao = None
        nearest_dist = 999999999.999
        
        # check all the candidates
        for icao in cands:
            # candidate coordinate
            info = self.__airportDict[icao]
            cand_coord = LatLon23.LatLon(info["lat"], info["lon"])

            # distance to the candidate
            dist = target_coord.distance(cand_coord)
            
            # smaller distance?
            if dist < nearest_dist:
                nearest_icao = icao
                nearest_dist = dist
        
        # retrieve information about the nearest airport
        info = self.__airportDict[nearest_icao]
        if not info["local_code"] is None:
            # TODO: need to figure out when to use the local code and when not
            nearest_icao = info["local_code"]
        nearest_lat = info["lat"]
        nearest_lon = info["lon"]
        nearest_ele = info["elevation"]
        nearest_name = info["name"]

        # finished
        return nearest_icao, nearest_lat, nearest_lon, int(nearest_ele), nearest_name
