import LatLon23

MINIMUM_DISTANCE_BETWEEN_POINTS = 0.1 # in kilometers

def subsample(coords, max_leg_length, num_leg_points):
    # remove points that are too near to each other
    filtered_coords = [coords[0]]
    last_coord = coords[0]
    for c in coords[1:]:
        if last_coord.distance(c) > MINIMUM_DISTANCE_BETWEEN_POINTS:
            filtered_coords.append(c)
            last_coord = c
    if last_coord != coords[-1]:
        filtered_coords.append(coords[-1])
    coords = filtered_coords

    # split the track into legs if requested
    raw_legs = [coords]
    if not max_leg_length is None:
        assert type(coords[0]) == LatLon23.LatLon
        raw_legs = list()
        cur_leg = [coords[0]]
        cur_len = 0.0
        for c in coords[1:]:
            assert type(c) == LatLon23.LatLon
            cur_len += c.distance(cur_leg[-1])
            cur_leg.append(c)
            if cur_len > max_leg_length:
                raw_legs.append(cur_leg)
                cur_leg = [c]
                cur_len = 0.0
        if len(cur_leg) > 1:
            raw_legs.append(cur_leg)
    
    # subsample the legs
    num_intermediate = num_leg_points - 2
    legs = list()
    for raw in raw_legs:
        num_raw = len(raw)
        spacing = int(num_raw / (num_intermediate+1))
        cur_leg = [raw[0]]
        for i in range(num_intermediate):
            idx = (i+1) * spacing
            cur_leg.append(raw[idx])
        cur_leg.append(raw[-1])
        legs.append(cur_leg)
    
    # finished
    return legs
