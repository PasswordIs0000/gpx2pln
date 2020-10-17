import xml.etree.ElementTree
import LatLon23

# DISCLAIMER: I didn't study the GPX file format. I've downloaded a few that are freely available and did 'learning by doing'.
#             Feel free to improve this! :-)

# representation of a single .gpx file
class GpxFile:
    def __init__(self, fname):
        # to be filled now...
        self.__authorName = "Unknown author"
        self.__authorLinks = set() # all links associated with the author
        self.__trackName = "Unnamed track"
        self.__trackLinks = set() # all links associated with the track in general
        self.__trackCoords = list()
        self.__maxElevation = None # maximum elevation in feet. none if unknown.

        # read and parse the xml file
        xml_data = xml.etree.ElementTree.parse(fname)
        xml_root = xml_data.getroot()
        xml_namespace = xml_root.tag.split("}")[0].strip("{}")
        xml_namespace = {
            "": xml_namespace
        }
        
        # collect the metadata
        track_name_node = xml_data.find("./metadata/name", xml_namespace)
        if not track_name_node is None:
            self.__trackName = track_name_node.text
        track_link_nodes = xml_data.findall("./metadata/link", xml_namespace)
        for node in track_link_nodes:
            self.__trackLinks.add(node.attrib["href"])
        author_name_node = xml_data.find("./metadata/author/name", xml_namespace)
        if not author_name_node is None:
            self.__authorName = author_name_node.text
        author_link_nodes = xml_data.findall("./metadata/author/link", xml_namespace)
        for node in author_link_nodes:
            self.__authorLinks.add(node.attrib["href"])
        
        # collect the track coordinates
        # TODO: currently we're using the first track segment in assumption that this is the main track
        # and other segments are e.g. alternative trail head. we should actually choose the longest segment
        # or let the user decide.
        track_segment_node = xml_data.find("./trk/trkseg", xml_namespace)
        if not track_segment_node is None:
            track_point_nodes = track_segment_node.findall("trkpt", xml_namespace)
            assert len(track_point_nodes) > 1 # at least two to actually be a track
            for node in track_point_nodes:
                # raw coordinates as strings
                lat = node.attrib["lat"]
                lon = node.attrib["lon"]

                # parse the coordinates
                lat = LatLon23.Latitude(float(lat))
                lon = LatLon23.Longitude(float(lon))
                coord = LatLon23.LatLon(lat, lon)

                # append the coordinates
                self.__trackCoords.append(coord)

                # elevation in this point?
                elevation_node = node.find("ele", xml_namespace)
                if not elevation_node is None:
                    if self.__maxElevation is None:
                        self.__maxElevation = 0.0
                    elevation = float(elevation_node.text)
                    self.__maxElevation = max(self.__maxElevation, elevation)
    
    def get_author_name(self):
        return self.__authorName
    
    def get_author_links(self):
        return self.__authorLinks
    
    def get_track_name(self):
        return self.__trackName
    
    def get_track_links(self):
        return self.__trackLinks
    
    def get_track_coords(self):
        return self.__trackCoords
    
    def get_max_elevation(self):
        return self.__maxElevation

# concatenation of multiple .gpx files
class GpxConcat:
    def __init__(self, gpx_files):
        # to be filled now...
        self.__authorName = set() # will be converted to a string later
        self.__authorLinks = set() # all links associated with the author
        self.__trackName = None # we will use the first one
        self.__trackLinks = set() # all links associated with the track in general
        self.__trackCoords = list()
        self.__maxElevation = None # maximum elevation in feet. none if unknown.

        # collect the values
        for gpx in gpx_files:
            self.__authorName.add(gpx.get_author_name())
            self.__authorLinks.update(gpx.get_author_links())
            if self.__trackName is None:
                self.__trackName = gpx.get_track_name()
            self.__trackLinks.update(gpx.get_track_links())
            self.__trackCoords.extend(gpx.get_track_coords())
            max_ele = gpx.get_max_elevation()
            if not max_ele is None:
                if self.__maxElevation is None:
                    self.__maxElevation = 0.0
                self.__maxElevation = max(self.__maxElevation, max_ele)
        
        # convert the author names
        self.__authorName = ", ".join(self.__authorName)
    
    def get_author_name(self):
        return self.__authorName
    
    def get_author_links(self):
        return self.__authorLinks
    
    def get_track_name(self):
        return self.__trackName
    
    def get_track_links(self):
        return self.__trackLinks
    
    def get_track_coords(self):
        return self.__trackCoords
    
    def get_max_elevation(self):
        return self.__maxElevation
