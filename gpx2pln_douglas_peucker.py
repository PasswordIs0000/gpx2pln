import LatLon23
import numpy as np
import skimage.measure

def douglas_peucker(coords, max_leg_length):
    # convert to a numpy array
    np_coords = np.empty((len(coords),2), dtype=np.float32)
    for i in range(len(coords)):
        np_coords[i,0] = float(coords[i].lat)
        np_coords[i,1] = float(coords[i].lon)
    
    # subdivide the polygon
    for _ in range(5):
        np_coords = skimage.measure.subdivide_polygon(np_coords, degree=2, preserve_ends=True)
    
    # approximate the polygon
    np_coords = skimage.measure.approximate_polygon(np_coords, tolerance=0.1)

    # convert back
    coords = list()
    for i in range(np_coords.shape[0]):
        c = LatLon23.LatLon(float(np_coords[i,0]), float(np_coords[i,1]))
        coords.append(c)
    
    # split into legs
    legs = list()
    cur_leg = [coords[0]]
    cur_len = 0.0
    for c in coords[1:]:
        assert type(c) == LatLon23.LatLon
        last_coord = cur_leg[-1]
        last_dist = c.distance(last_coord)
        new_len = cur_len + last_dist
        if new_len > max_leg_length:
            new_over = new_len - max_leg_length
            cur_under = max_leg_length - cur_len
            if new_over < cur_under:
                cur_leg.append(c)
                legs.append(cur_leg)
                cur_leg = [c]
                cur_len = 0.0
            else:
                legs.append(cur_leg)
                cur_leg = [last_coord, c]
                cur_len = last_dist
        else:
            cur_len = new_len
            cur_leg.append(c)
    if len(cur_leg) > 1:
        legs.append(cur_leg)
    
    # finished
    return legs