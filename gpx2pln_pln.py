import xml.etree.ElementTree
import LatLon23

# DISCLAIMER: I didn't really study the PLN file format. I've exported from Microsoft Flight Simulator 2020 and did 'learning by doing'.
#             Feel free to improve this! :-) I just kindly request that the export is compatible with Microsoft Flight Simulator 2020.

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
        self.__flightElevation = 10000 # default flight elevation is 10000 feet
        if not elevation is None:
            assert type(elevation) == float or type(elevation) == int
            self.__flightElevation = int(elevation) + 1000
        assert type(self.__flightElevation) == int and self.__flightElevation > 0

    def write(self, fname):
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
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureID").text = "CUSTD"
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureLLA").text = _coord2str(self.__flightCoords[0], self.__flightElevation)
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationID").text = "CUSTA"
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationLLA").text = _coord2str(self.__flightCoords[-1], self.__flightElevation)
        xml.etree.ElementTree.SubElement(flightplan_node, "Descr").text = self.__flightDescription
        xml.etree.ElementTree.SubElement(flightplan_node, "DepartureName").text = "GPX departure"
        xml.etree.ElementTree.SubElement(flightplan_node, "DestinationName").text = "GPX destination"

        # app version
        app_version_node = xml.etree.ElementTree.SubElement(flightplan_node, "AppVersion")
        xml.etree.ElementTree.SubElement(app_version_node, "AppVersionMajor").text = "11"
        xml.etree.ElementTree.SubElement(app_version_node, "AppVersionBuild").text = "282174"

        # write the waypoints
        for i in range(len(self.__flightCoords)):
            coord = self.__flightCoords[i]
            name = "Custom " + str(i)
            if i == 0:
                name = "CUSTD"
            elif i == len(self.__flightCoords)-1:
                name = "CUSTA"
            type = "User"
            if (i == 0) or (i == len(self.__flightCoords)-1):
                type = "Intersection"
            waypoint_node = xml.etree.ElementTree.SubElement(flightplan_node, "ATCWaypoint", {"id": name})
            xml.etree.ElementTree.SubElement(waypoint_node, "ATCWaypointType").text = type
            xml.etree.ElementTree.SubElement(waypoint_node, "WorldPosition").text = _coord2str(coord, self.__flightElevation)
            xml.etree.ElementTree.SubElement(waypoint_node, "SpeedMaxFP").text = "-1"
            if (i == 0) or (i == len(self.__flightCoords)-1):
                icao_node = xml.etree.ElementTree.SubElement(waypoint_node, "ICAO")
                xml.etree.ElementTree.SubElement(icao_node, "ICAOIdent").text = name
        
        # write the xml document to the file
        xml_data.write(fname, encoding="utf-8", xml_declaration=True)
