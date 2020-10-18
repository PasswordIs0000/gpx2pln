import xml.etree.ElementTree
import LatLon23
import copy

# DISCLAIMER: I didn't study the GPX file format. I've downloaded a few that are freely available and did 'learning by doing'.
#             Feel free to improve this! :-)

MINIMUM_TRACK_SEGMENT_LENGTH = 10.0 # in kilometers
MAXIMUM_DISTANCE_BETWEEN_SEGMENTS = 50.0 # in kilometers

def _length_of_track_segment(track_point_nodes, xml_namespace):
    # sum up the distance
    distance = 0.0
    for i in range(1, len(track_point_nodes)):
        # current node
        lat = LatLon23.Latitude(float(track_point_nodes[i].attrib["lat"]))
        lon = LatLon23.Longitude(float(track_point_nodes[i].attrib["lon"]))
        cur = LatLon23.LatLon(lat, lon)

        # previous node
        lat = LatLon23.Latitude(float(track_point_nodes[i-1].attrib["lat"]))
        lon = LatLon23.Longitude(float(track_point_nodes[i-1].attrib["lon"]))
        prev = LatLon23.LatLon(lat, lon)

        # add the distance
        distance += cur.distance(prev)
    
    # finished
    return distance

def _heading_of_track_segment(track_point_nodes, xml_namespace):
    # first node
    lat = LatLon23.Latitude(float(track_point_nodes[0].attrib["lat"]))
    lon = LatLon23.Longitude(float(track_point_nodes[0].attrib["lon"]))
    start = LatLon23.LatLon(lat, lon)

    # last node
    lat = LatLon23.Latitude(float(track_point_nodes[-1].attrib["lat"]))
    lon = LatLon23.Longitude(float(track_point_nodes[-1].attrib["lon"]))
    end = LatLon23.LatLon(lat, lon)

    # heading calculation and finish
    return start.heading_initial(end)

def _distance_between_points(track_point_node_A, track_point_node_B):
    # first node
    lat = LatLon23.Latitude(float(track_point_node_A.attrib["lat"]))
    lon = LatLon23.Longitude(float(track_point_node_A.attrib["lon"]))
    coord_A = LatLon23.LatLon(lat, lon)

    # second node
    lat = LatLon23.Latitude(float(track_point_node_B.attrib["lat"]))
    lon = LatLon23.Longitude(float(track_point_node_B.attrib["lon"]))
    coord_B = LatLon23.LatLon(lat, lon)

    # finished
    return coord_A.distance(coord_B)

def _minimal_distance_to_track(new_point, existing_segment):
    # first node
    lat = LatLon23.Latitude(float(new_point.attrib["lat"]))
    lon = LatLon23.Longitude(float(new_point.attrib["lon"]))
    new_coord = LatLon23.LatLon(lat, lon)
    
    # find the minimum distance
    min_dist = 999999.999
    for node in existing_segment:
        # existing node
        lat = LatLon23.Latitude(float(node.attrib["lat"]))
        lon = LatLon23.Longitude(float(node.attrib["lon"]))
        existing_coord = LatLon23.LatLon(lat, lon)

        # distance
        dist = existing_coord.distance(new_coord)
        min_dist = min(min_dist, dist)
    
    # finished
    return min_dist


def _choose_track_point_nodes(track_segment_nodes, xml_namespace):
    # collect possible segments
    segments = list()
    for node in track_segment_nodes:
        # find all track points
        track_point_nodes = node.findall("trkpt", xml_namespace)
        
        # info about the forward track
        cur_len = _length_of_track_segment(track_point_nodes, xml_namespace)
        cur_heading = _heading_of_track_segment(track_point_nodes, xml_namespace)
        
        # info about the reverse track
        rev_nodes = copy.deepcopy(track_point_nodes)
        rev_nodes.reverse()
        rev_heading = _heading_of_track_segment(rev_nodes, xml_namespace)

        # add the track segments that are long enough
        if cur_len > MINIMUM_TRACK_SEGMENT_LENGTH:
            segments.append((track_point_nodes, cur_len, cur_heading))
            segments.append((rev_nodes, cur_len, rev_heading))
    
    # no segments at all?
    if len(segments) == 0:
        return list()
    
    # start with the longest segment
    max_length = 0
    max_idx = None
    for i in range(len(segments)):
        if segments[i][1] > max_length:
            max_length = segments[i][1]
            max_idx = i
    res_nodes = segments[max_idx][0]
    del segments[max_idx]

    # add more segments if they actually add distance
    while True:
        best_add = MINIMUM_TRACK_SEGMENT_LENGTH
        best_idx = None
        best_at_end = True
        for i in range(len(segments)):
            # distance between the new segment and the current end
            dist_end = _distance_between_points(res_nodes[-1], segments[i][0][0])

            # distance between the new segment and the current start
            dist_start = _distance_between_points(segments[i][0][-1], res_nodes[0])

            # is this a candidate?
            if not min(dist_end, dist_start) < MAXIMUM_DISTANCE_BETWEEN_SEGMENTS:
                continue

            # different cases for prepending or appending
            if dist_end < dist_start:
                # how much does it add?
                add_dist = _minimal_distance_to_track(segments[i][0][-1], res_nodes)

                # use if best so far
                if add_dist > best_add:
                    best_add = add_dist
                    best_idx = i
                    best_at_end = True
            else:
                # how much does it add?
                add_dist = _minimal_distance_to_track(segments[i][0][0], res_nodes)

                # use if best so far
                if add_dist > best_add:
                    best_add = add_dist
                    best_idx = i
                    best_at_end = False                    
        
        # nothing more found?
        if best_idx is None:
            break

        # add the segment
        if best_at_end:
            append_nodes = segments[best_idx][0]
            res_nodes = res_nodes + append_nodes
        else:
            prepend_nodes = segments[best_idx][0]
            res_nodes = prepend_nodes + res_nodes
        
        # delete from candidates
        del segments[best_idx]

    # finished
    return res_nodes

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
        
        # choose track point nodes
        track_point_nodes = _choose_track_point_nodes(xml_data.findall("./trk/trkseg", xml_namespace), xml_namespace)
        
        # collect the track coordinates
        if len(track_point_nodes) > 1:
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
    
    def __len__(self):
        return len(self.__trackCoords)
    
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
    
    def reverse(self):
        self.__trackCoords.reverse()

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

        # reverse individual tracks if necessary to get one continuous track
        if len(gpx_files) > 1:
            # reverse the first track if necessary
            start_dist = gpx_files[0].get_track_coords()[0].distance(gpx_files[1].get_track_coords()[0])
            end_dist = gpx_files[0].get_track_coords()[-1].distance(gpx_files[1].get_track_coords()[0])
            if start_dist < end_dist:
                gpx_files[0].reverse()
            
            # reverse all the others if necessary
            for i in range(1, len(gpx_files)):
                start_dist = gpx_files[i].get_track_coords()[0].distance(gpx_files[i-1].get_track_coords()[-1])
                end_dist = gpx_files[i].get_track_coords()[-1].distance(gpx_files[i-1].get_track_coords()[-1])
                if end_dist < start_dist:
                    gpx_files[i].reverse()

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
    
    def __len__(self):
        return len(self.__trackCoords)
    
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
    
    def reverse(self):
        self.__trackCoords.reverse()
