import scipy.spatial
import random

import numpy as np

from PIL import Image

from rotational_sort import rotational_sort
from vect_store import Vector

from random import randint


class Regions(list):
    """Subclass list to store regions

    Allows for more powerful data access than a base list
    """

    @property
    def centroids(self):
        """Return a generator yielding the centroid of each region stored"""
        for region in self:
            yield region.centroid

    def display(self):
        """Generate a plot of each region, similar to the voronoi_plot_2d"""
        raise NotImplementedError


class Region:
    """Container for a Voronoi region

    Args:
        origin (x,y tuple): origin point of this region

        points (list): list of x,y points defining this region

        edge (bool): True if this region has some form of unbound edge
    """

    _edge = False

    def __init__(self, origin, points, id=-1):

        self._origin = origin
        self._set_points(points)
        self._id = id

    def _set_points(self, points):
        self._points = [list(x) for x in points]

    @property
    def origin(self):
        """Origin point of this region"""
        return self._origin

    @property
    def points(self):
        """Bounding points of this region"""
        return self._points

    @property
    def id(self):
        """Region ID within Regions"""
        return self._id

    @property
    def area(self):
        """area of the region"""
        if not hasattr(self, '_area'):
            self.centroid()
        return self._area

    @property
    def centroid(self):
        """Generate the centroid (centre of mass) of the region

        Centroid can be used for lloyds relaxation algorithm

        Regions marked as Edge will return their origin to prevent boundary
        escape.

        Returns:
            tuple(x,y):
                x, y coordinate of the centroid of this region

        """

        # https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
        # http://paulbourke.net/geometry/polygonmesh/
        # we're assuming here that the points are sorted either CCW or CW

        if len(self._points) == 0:
            return None

        points = self._points
        points.append(points[0])  # shoelace method needs a wraparound

        Cx = 0
        Cy = 0
        A = 0
        for p in range(len(points) - 1):
            x0 = points[p][0]
            y0 = points[p][1]

            x1 = points[p + 1][0]
            y1 = points[p + 1][1]

            shoelace = x0 * y1 - x1 * y0

            A += shoelace
            Cx += (x0 + x1) * shoelace
            Cy += (y0 + y1) * shoelace
        A /= 2
        if A == 0:
            xpoints = np.array(self._points).flatten()[0::2]
            ypoints = np.array(self._points).flatten()[1::2]
            return (np.mean(xpoints), np.mean(ypoints))

        Cx *= 1 / (6 * A)
        Cy *= 1 / (6 * A)

        self._area = abs(A)

        return ((Cx,Cy))

    @property
    def outside_point(self):
        """Generate a point _outside_ the polygon, for raycast tests

        Pick a point on the edge of the poly and move it away from the centroid
        This works assuming Region describes a convex polygon

        Also NEEDS a centroid, so doesn't work for edge regions atm
        """

        cent_point = self.centroid
        edge_point = self._points[0]

        # generate unit vector from centre to outer point
        vect = Vector.from_points(cent_point, edge_point).normalise()

        # add the vector to the edge point to move outside
        return [e+v for e,v in zip(edge_point, vect)]

    def plot(self, title=None):
        """Plot this individual region on a matplotlib figure"""
        fig = plt.figure()

        plt.plot(*self.origin, 'bo')

        plotpoints, _ = rotational_sort(list(self.points), self.centroid)
        plotpoints.append(plotpoints[0])

        for i in range(len(plotpoints) - 1):

            p0 = plotpoints[i]
            p1 = plotpoints[i+1]

            plt.plot(*p0,color='orange',marker='o')
            plt.plot([p0[0],p1[0]], [p0[1],p1[1]], color = 'black')

        if self.centroid != (-1,-1):
            plt.plot(*self.centroid, 'b+')
            plt.text(*self.centroid, f'centre {self.centroid}')

        # plt.plot([0,0],[0,10], color = 'red')
        # plt.plot([0,10],[10,10], color = 'red')
        # plt.plot([10,10],[10,0], color = 'red')
        # plt.plot([10,0],[0,0], color = 'red')

        plt.xlim(0,10)
        plt.ylim(0,10)

        if title is not None:
            plt.title(str(title))

        return fig


class EdgeRegion(Region):
    """Region, but on the edge"""

    _edge = True

    def add_boundary_point(self, point):
        """add a new point, on the region boundary"""
        oldpoints = [list(x) for x in self._points]

        newpoints = oldpoints + [point]

        self._set_points(newpoints)

    def remove_outside_points(self, xbounds, ybounds):
        """remove any points outside the boundaries"""

        x0 = xbounds[0]
        x1 = xbounds[1]
        y0 = ybounds[0]
        y1 = ybounds[1]

        newpoints = []
        for point in self._points:
            if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
                newpoints.append(point)

        self._set_points(newpoints)


class Voronoi:
    """Container for a flexible 2D voronoi plot

    Args:
        points (list[x, y]):
            list of origin points to generate from
        xlim (list[x0, x1]):
            limit of the plot in the x direction
        ylim (list[y0, y1]):
            limit of the plot in the y direction

    """

    def __init__(self, points, xlim, ylim):

        self._points = points
        self._limit = {'x':xlim,
                       'y':ylim}

        self._generate_voronoi()
        self._centred = False
        self._wrapped = False

    @staticmethod
    def staticmethod_docstest(arg):
        """empty staticmethod to make sure the callable section is behaving"""
        return arg

    @classmethod
    def random(cls, xlim, ylim, npoints, decimals=1):
        """Generate random voronoi diagram within the limits

        Args:
            xlim (int):
                Limit in the x direction
            ylim (int):
                Limit in the y direction
            npoints (int):
                Number of points to generate
            decimals (int):
                Decimal places to use (essentially grid spacing)

        Returns:
            class (Voronoi):
                self type class with randomly generated points

        Raises:
            ValueError:
                if decmials < 0
        """

        if decimals < 0:
            raise ValueError(f"Decimcal places must be >= 0 ({decimals})")

        mult = 10**decimals

        points = []
        for p in range(npoints):
            x = randint(0, xlim * mult)/mult
            y = randint(0, ylim * mult)/mult

            points.append([x,y])

        return cls(points, xlim, ylim)

    @property
    def points(self):
        """List of origin points

        Returns:
            list[x, y]: origin points used for the current diagram
        """
        return self._points

    @property
    def limits(self):
        """x, y limits of the plot

            Returns:
                dict: minmax limits
        """
        return self._limit

    @property
    def vertices(self):
        """Hook for voronoi vertices"""
        return self._voronoi.vertices

    @property
    def regions(self):
        """Region list of each region present"""
        return self._regions

    @property
    def ridge_vertices(self):
        """Hook for voronoi ridge_vertices"""
        return self._voronoi.ridge_vertices

    @property
    def ridge_points(self):
        """Hook for voronoi ridge_points"""
        return self._voronoi.ridge_points

    def _generate_voronoi(self):
        """Generate the voronoi plot using scipy.spatial.Voronoi"""
        self._voronoi = scipy.spatial.Voronoi(self._points)

        # store regions for further computation
        regions = Regions()
        for idx in range(len(self._points)):
            points = self._voronoi.points[idx]
            region_id = self._voronoi.point_region[idx]
            bounds = np.array([self._voronoi.vertices[r] for r in
                      self._voronoi.regions[region_id] if r != -1])

            xpoints = bounds.flatten()[0::2]
            ypoints = bounds.flatten()[1::2]

            edge = False
            if min(xpoints) < 0 or \
                    min(ypoints) < 0 or \
                    max(xpoints) > self.limits['x'] or \
                    max(ypoints) > self.limits['y'] or \
                    -1 in self._voronoi.regions[region_id]:
                regions.append(EdgeRegion(points, bounds, region_id))
            else:
                regions.append(Region(points, bounds, region_id))
            # if -1 in self._voronoi.regions[region_id]:
            #     regions[-1].plot(title=region_id)

        # create "outer loop" for edge binding
        region_pts = []
        region_ids = []
        idx=0
        for region in regions:
            if region._edge:
                region_pts.append(region.origin)
                region_ids.append(idx)
            idx+=1
        # sort ids by origin point

        region_pts, mapping = rotational_sort(region_pts)

        circle = [region_ids[idx] for idx in mapping]
        circle.append(circle[0])

        for i in range(len(circle) - 1):
            u = regions[circle[i]]
            v = regions[circle[i+1]]

            UV = Vector.from_points(u.origin, v.origin)
            mid = UV.point_along(0.5) # midpoint along line in question

            outer = UV.cross(Vector(0,0,-1)).normalise()*10 # vector pointing outward
            outer.origin = mid  # shift vector to it's actual location

            bounds = (('x', 0),
                      ('x', self._limit['x']),
                      ('y', 0),
                      ('y', self._limit['y']))

            # generate all possible intersects and take the one closest to origin
            intersects = []
            for b in bounds:
                bound = b[0]
                val = b[1]
                try:
                    intersects.append(outer.intersect_boundary(bound, val))
                except np.linalg.LinAlgError:
                    pass

            distances = [outer.distance_to_origin(p) for p in intersects]
            min_id = distances.index(min(distances))
            intersect = intersects[min_id]

            # plt.plot(*intersect, color='red', marker='o')
            # print(f'plotting boundary intersect at {intersect}')

            u.add_boundary_point(intersect)
            v.add_boundary_point(intersect)

            u.remove_outside_points((0, self._limit['x']), (0, self._limit['y']))
            v.remove_outside_points((0, self._limit['x']), (0, self._limit['y']))

            tmp = [m+p for m, p in zip(mid, outer.components)]
            # plt.plot([u.origin[0], v.origin[0]],[u.origin[1], v.origin[1]])
            # plt.plot([mid[0], tmp[0]],[mid[1], tmp[1]], color = 'black')
            # plt.plot(*u.origin,color='orange',marker='o')
            # plt.text(*u.origin,f'{u.id}: {i}')
            # plt.xlim(0,10)
            # plt.ylim(0,10)

        self._regions = regions

    def lloyds_relax(self):
        """Relax voronoi regions using Lloyd's algorithm

        Move each voronoi origin point to the centroid of the region and
        recalculate the plot
        """
        # TODO (lbeal):
        #   add option regarding boundary region
        #   unbounded: points are free to move beyond bound
        #   hard fixed: edge points are locked in place
        #   soft fixed: edge points consider boundary as part of region

        pt = []
        for region in self._regions:
            cent = region.centroid
            if cent is not None:
                pt.append(cent)
            else:
                print('removing region',region)
                self._regions.remove(region)
        
        self._points = pt
        self._generate_voronoi()

    def plot(self):
        """Plot matplotlib diagram and return the figure

        scipy.spatial.voronoi_plot_2d covers the plotting
        """
        fig = scipy.spatial.voronoi_plot_2d(self._voronoi)
        plt.xlim(0, self.limits['x'])
        plt.ylim(0, self.limits['y'])

        for region in self._regions:
            cent = region.centroid
            orig = region.origin

            plt.text(*orig, region.id)
            if cent is not None:
                plt.plot(*cent, color='blue', marker='+')
                plt.text(*cent, region.id)

        return fig


if __name__ == '__main__':

    import matplotlib.pyplot as plt


    xlim = 10
    ylim = 10
    npoints = 50

    P = [2,-7,0]
    Q = [1,-3,-5]

    test_voronoi = Voronoi.random(xlim,ylim,npoints)

    # test_voronoi = Voronoi(points_test, xlim, ylim)



    # vplot = test_voronoi.plot()

    # for c in test_voronoi.regions.centroids:
    #     plt.plot(*c,'b+')

    # for region in test_voronoi.regions:
    #     if region._edge:
    #         plt.plot(*region.origin,'rx')

    # n = 10
    #
    # for r in test_voronoi.regions:
    #     plt.text(*r.origin,f'{r.id}')
    # plt.text(*test_voronoi.regions[n].origin, 'test')

    test_voronoi.plot()
    plt.title('voronoi 0')

    stages = 5
    for idx in range(stages):
        print(f'relaxation stage {idx}')
        print(f'\t{len(test_voronoi.regions)} regions')
        test_voronoi.lloyds_relax()
        test_voronoi.plot()
        plt.title(f'voronoi {idx + 1}')

    plt.show()