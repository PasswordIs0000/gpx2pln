import urllib.request
import json
import os
import gzip
import datetime
import LatLon23

class AirportDatabase:
    def __init__(self, fname):
        # open the database if possible
        db_blob = None
        if os.path.isfile(fname):
            file_dtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(fname))
            cur_dtime = datetime.datetime.utcnow()
            if (cur_dtime-file_dtime) < datetime.timedelta(weeks=2):
                print("Loading the airports database... ", end="", flush=True)
                with gzip.open(fname, "rb") as fd:
                    db_blob = fd.read()
                print("done!", flush=True)
        
        # download the database if necessary
        if db_blob is None:
            print("Downloading the airports database... ", end="", flush=True)
            db_blob = urllib.request.urlopen("https://github.com/mwgg/Airports/raw/master/airports.json").read()
            with gzip.open(fname, "wb") as fd:
                fd.write(db_blob)
            print("done!", flush=True)
        
        # decode the json
        self.__airportDict = json.loads(db_blob.decode("utf-8"))
        assert len(self.__airportDict) > 25000 # there should be a few airports...

        # store the airport codes searchable by their latitude and longitude as integers
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
        nearest_lat = info["lat"]
        nearest_lon = info["lon"]
        nearest_ele = info["elevation"]
        nearest_name = info["name"]

        # finished
        return nearest_icao, nearest_lat, nearest_lon, int(nearest_ele), nearest_name
