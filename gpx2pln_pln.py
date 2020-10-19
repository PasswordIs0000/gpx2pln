import xml.etree.ElementTree
import LatLon23
import copy

# DISCLAIMER: I didn't really study the PLN file format. I've exported from Microsoft Flight Simulator 2020 and did 'learning by doing'.
#             Feel free to improve this! :-) I just kindly request that the export is compatible with Microsoft Flight Simulator 2020.

# add a slight offset to the last waypoint when ending in flight just to see two different points on the map
DEGREE_OFFSET_END_IN_FLIGHT = 0.1 # in degree

# format geo-coordinates and elevation for the .pln format
def _coord2str(coord, elevation):
    assert type(coord) == LatLon23.LatLon
    assert type(elevation) == int
    coord = coord.to_string("%H%d%° %m%' %S%\"")
    coord = ",".join(coord)
    elevation = str(float(elevation))
    return coord + ",+" + elevation

# representation of a .pln file
class PlnFile:
    def __init__(self, title, description, coords, elevation=None):
        # save the title
        self.__flightTitle = title
        assert type(self.__flightTitle) == str and len(self.__flightTitle) > 0

        # save the description
        self.__flightDescription = description
        assert type(self.__flightDescription) == str and len(self.__flightDescription) > 0
        
        # save the coordinates
        assert type(coords) == list and len(coords) > 1
        self.__flightCoords = list()
        for val in coords:
            assert type(val) == LatLon23.LatLon
            self.__flightCoords.append(val)
        
        # save the elevation
        self.__flightElevation = 10000 # default flight elevation
        if not elevation is None:
            assert type(elevation) == float or type(elevation) == int
            self.__flightElevation = max(self.__flightElevation, int(elevation) + 3500)
        assert type(self.__flightElevation) == int and self.__flightElevation > 0

    def write(self, fname, airport_db):
        # sanity checks
        assert not airport_db is None

        # select waypoints to write
        coords = copy.deepcopy(self.__flightCoords)

        # HINT: microsoft flight simulator seems to loose the last waypoint when finishing in the air.
        # this is why we add the last waypoint twice when not using the airport database.
        # the destination airport will sometimes not be consistent and then the same behaviour occurs and we
        # will finish in the air.
        # this looks strange on the world map when planning a flight, but the vfr map seems to be okay.

        # nearest departure airport
        lat = float(coords[0].lat)
        lon = float(coords[0].lon)
        departure_id, departure_lat, departure_lon, departure_ele, departure_name = airport_db.find_nearest(lat, lon)
        departure_type = "Airport"
        departure_coord = _coord2str(LatLon23.LatLon(departure_lat, departure_lon), departure_ele)

        # nearest destination airport
        lat = float(coords[-1].lat)
        lon = float(coords[-1].lon)
        destination_id, destination_lat, destination_lon, destination_ele, destination_name = airport_db.find_nearest(lat, lon)
        destination_type = "Airport"
        destination_coord = _coord2str(LatLon23.LatLon(destination_lat, destination_lon), destination_ele)

        # are the two airports the same?
        if departure_id == destination_id:
            # distances to the departure and destination
            departure_dist = coords[0].distance(LatLon23.LatLon(departure_lat, departure_lon))
            destination_dist = coords[-1].distance(LatLon23.LatLon(destination_lat, destination_lon))
            
            # use the airport to the nearest waypoint
            if departure_dist < destination_dist:
                # destination info
                destination_id = "CUSTA"
                destination_type = "Intersection"
                lat = float(coords[-1].lat) + DEGREE_OFFSET_END_IN_FLIGHT
                lon = float(coords[-1].lon) + DEGREE_OFFSET_END_IN_FLIGHT
                destination_coord = _coord2str(LatLon23.LatLon(lat, lon), self.__flightElevation)
                destination_name = "GPX destination"
            else:
                # departure info
                departure_id = "CUSTD"
                departure_type = "Intersection"
                departure_coord = _coord2str(coords[0], self.__flightElevation)
                departure_name = "GPX departure"

                # trim the coordinates
                coords = coords[1:]

        # empty xml document
        xml_root = xml.etree.ElementTree.Element("SimBase.Document", {"Type": "AceXML", "version": "1,0"})
        xml_data = xml.etree.ElementTree.ElementTree(xml_root)

        # general information
        xml.etree.ElementTree.SubElement(xml_root, "Descr").text = "AceXML Document"

        # flight plan
        flightplan_node = xml.etree.ElementTree.SubElement(xml_root, "FlightPlan.FlightPlan")
        xml.etree.ElementTree.SubElement(flightplan_node, "Title").text = self.__flightTitle
        xml.etree.ElementTree.SubElement(flightplan_node, "FPType").text = "VFR"
        xml.etree.ElementTree.SubElement(flightplan_node, "CruisingAlt").text = str(self.__flightElevation)
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureID").text = departure_id
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureLLA").text = departure_coord
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationID").text = destination_id
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationLLA").text = destination_coord
        xml.etree.ElementTree.SubElement(flightplan_node, "Descr").text = self.__flightDescription
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureName").text = departure_name
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationName").text = destination_name

        # app version
        app_version_node = xml.etree.ElementTree.SubElement(flightplan_node, "AppVersion")
        xml.etree.ElementTree.SubElement(app_version_node, "AppVersionMajor").text = "11"
        xml.etree.ElementTree.SubElement(app_version_node, "AppVersionBuild").text = "282174"

        # write the departure
        departure_node = xml.etree.ElementTree.SubElement(flightplan_node, "ATCWaypoint", {"id": departure_id})
        xml.etree.ElementTree.SubElement(departure_node, "ATCWaypointType").text = departure_type
        xml.etree.ElementTree.SubElement(departure_node, "WorldPosition").text = departure_coord
        xml.etree.ElementTree.SubElement(departure_node, "SpeedMaxFP").text = "-1"
        icao_node = xml.etree.ElementTree.SubElement(departure_node, "ICAO")
        xml.etree.ElementTree.SubElement(icao_node, "ICAOIdent").text = departure_id

        # write the waypoints
        for i in range(len(coords)):
            coord = coords[i]
            name = "Cust" + str(i+1)
            type = "User"
            waypoint_node = xml.etree.ElementTree.SubElement(flightplan_node, "ATCWaypoint", {"id": name})
            xml.etree.ElementTree.SubElement(waypoint_node, "ATCWaypointType").text = type
            xml.etree.ElementTree.SubElement(waypoint_node, "WorldPosition").text = _coord2str(coord, self.__flightElevation)
            xml.etree.ElementTree.SubElement(waypoint_node, "SpeedMaxFP").text = "-1"
        
        # write the destination
        destination_node = xml.etree.ElementTree.SubElement(flightplan_node, "ATCWaypoint", {"id": destination_id})
        xml.etree.ElementTree.SubElement(destination_node, "ATCWaypointType").text = destination_type
        xml.etree.ElementTree.SubElement(destination_node, "WorldPosition").text = destination_coord
        xml.etree.ElementTree.SubElement(destination_node, "SpeedMaxFP").text = "-1"
        icao_node = xml.etree.ElementTree.SubElement(destination_node, "ICAO")
        xml.etree.ElementTree.SubElement(icao_node, "ICAOIdent").text = destination_id
        
        # write the xml document to the file
        xml_data.write(fname, encoding="utf-8", xml_declaration=True)
