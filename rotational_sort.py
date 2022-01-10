import numpy as np
import matplotlib.pyplot as plt

from vect_store import Vector

def documented_function(arg):
    """Test function to make sure that the coverage tester is working"""

    return None

def nondocumented(arg):
    return False

def skipdocumented(arg):
    """skip"""
    return True

def rotational_sort(points, ids=None, ccw=False, centre=None):
    """Given a list of x, y points, sort by angle around a midpoint.

    Args:
        points (list[(x,y)]):
            list of (x, y) points to be sorted
        ids (list, optional):
            this list will be sorted identically to `points`
        ccw (bool):
            sort counter-clockwise if True
        centre (tuple(x,y), optional):
            define a set centre to sort around

    Returns:
        list[(x, y)], list:
            sorted list of points, list of IDs sorted identically

    """

    if ids is None:
        ids = list(range(len(points)))

    xpoints = np.array(points).flatten()[0::2]
    ypoints = np.array(points).flatten()[1::2]

    if centre is None:
        avg_x = np.mean(xpoints)
        avg_y = np.mean(ypoints)
    else:
        avg_x = centre[0]
        avg_y = centre[1]

    ref_point = (avg_x, avg_y + max(ypoints))

    ref_vect = Vector.from_points((avg_x, avg_y), ref_point)

    angles = []
    for x, y in zip(xpoints, ypoints):
        angle = ref_vect.angle(Vector.from_points((avg_x, avg_y), (x, y)))
        if x < avg_x:
            angle = 360-angle

        angles.append(angle)

    newpoints = [x for _, x in sorted(zip(angles, points), reverse=ccw)]
    newids = [x for _, x in sorted(zip(angles, ids), reverse=ccw)]

    return newpoints, newids


if __name__ == '__main__':

    #test

    points = [[0, 10],
              [5, 12],
              [4, 6],
              [2, 8],
              [7, 7]]

    idx = 0
    for point in points:
        plt.plot(*point, color='orange',marker='o')
        plt.text(*point, f'{idx}')
        idx += 1

    sort, ids = rotational_sort(points, ccw=True)
    for i in range(len(sort)):
        p = sort[i]

        plt.text(p[0], p[1]-0.5, i)

    print(ids)

    plt.show()