import urllib.request
import json
import os
import gzip
import datetime

class AirportDatabase:
    def __init__(self, fname):
        # open the database if possible
        db_blob = None
        if os.path.isfile(fname):
            file_dtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(fname))
            cur_dtime = datetime.datetime.utcnow()
            if (cur_dtime-file_dtime) < datetime.timedelta(weeks=2):
                with gzip.open(fname, "rb") as fd:
                    db_blob = fd.read()
        
        # download the database if necessary
        if db_blob is None:
            db_blob = urllib.request.urlopen("https://github.com/mwgg/Airports/raw/master/airports.json").read()
            with gzip.open(fname, "wb") as fd:
                fd.write(db_blob)
        
        # decode the json
        self.__airportDict = json.loads(db_blob.decode("utf-8"))
        assert len(self.__airportDict) > 25000 # there should be a few airports...

        # store the airport codes searchable by their latitude and longitude as integers
        self.__idxLat = [list()] * 360
        self.__idxLon = [list()] * 360
        for icao, info in self.__airportDict.items():
            lat = int(info["lat"] + 180.0)
            lon = int(info["lon"] + 180.0)
            assert lat >= 0 and lon >= 0
            self.__idxLat[lat].append(icao)
            self.__idxLon[lon].append(icao)