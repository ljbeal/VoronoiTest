import math
import unittest
import numpy as np

TEST = 'testvalue'

class Vector:
    """Vector container

    Args:
        components (list):
            x, y, z, ... direction components
    """

    def __init__(self, *components, _origin=None):
        self._components = [float(v) for v in components]
        if _origin is None:
            self._origin = [0]*len(self._components)
        else:
            self._origin = _origin
        self._origin = tuple(self._origin)

    def __repr__(self):
        if sum(self._origin) == 0:
            ret = ['Vector(']
            for c in self._components:
                ret.append(str(c) + ', ')
            ret = ''.join(ret)[:-2] + ')'

        else:
            ret = f'Vector.point_and_direction({self._origin}, {tuple(self._components)})'

        return ret

    def __iter__(self):
        return (v for v in self._components)

    def __getitem__(self, item):
        return self._components[item]

    def __add__(self, other):
        return Vector.from_points(other.endpoint, self.origin)

    def __sub__(self, other):
        return Vector(*[a-b for a, b in
                        zip(self, other)])

    def __mul__(self, other):
        if type(other) in [int, float]:
            return Vector(*[other*v for v in self])

    def __hash__(self):
        return hash(tuple(self._components))

    def __eq__(self, other):
        if isinstance(other, Vector):
            return self.__hash__() == other.__hash__()
        else:
            raise NotImplementedError('can only compare Vector to Vector')

    @classmethod
    def from_points(cls, P, Q):
        """Create a vector from point P to point Q"""

        if len(P) != len(Q):
            raise ValueError('input coordinates have a dimension mismatch!')

        vect = []
        for p, q in zip(P, Q):
            vect.append(q-p)

        return cls(*vect, _origin=P)

    @classmethod
    def point_and_direction(cls, point, direction):
        """create a vector from a point, with a direction"""
        return cls(*direction, _origin=point)

    @property
    def magnitude(self):
        return sum([x**2 for x in self])**0.5

    @property
    def components(self):
        return tuple(self._components)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, neworigin):
        self._origin = neworigin

    @property
    def endpoint(self):
        return tuple([o+v for o, v in zip(self.origin, self)])

    @property
    def line_equation(self):
        """print vector line equation

        form [x, y, z] = [x0, y0, z0] + t[a, b, c]
        """

        keys = {'x': 'a',
                'y': 'b',
                'z': 'c'}

        eqn = []
        idx = 0
        for x, a in keys.items():
            eqn.append(f'{x} = {self.origin[idx]} + {self.components[idx]}*t')
            idx += 1
            if idx >= len(self.origin):
                break

        return '\n'.join(eqn)

    def normalise(self):
        """return a normalised vector"""
        return Vector(*[x/self.magnitude for x in self])

    def is_parallel(self, other):
        """return True if self is parallel with other vector

        args:
            other (Vector)

        returns:
            bool: True if parallel
        """
        if other[0] != 0:
            scalar = self[0]/other[0]
        else:
            scalar = self[1]/other[1]

        return other * scalar == self

    def is_orthogonal(self, other):
        """Returns True if vectors are orthogonal
        Args:
            other (Vector):
                other vector to be compared against
        Returns:
              bool
        """
        return self.dot(other) == 0

    def dot(self, other):
        """compute the dot product
        Args:
            other (Vector):
                other vector to be compared against
        Returns:
            float: dot product result
        """
        return sum([a*b for a, b in zip(self, other)])

    def angle(self, other, deg=True):
        """return the angle between this vector and another
        Args:
            other (Vector):
                other vector to be compared against
            deg (bool):
                return result in degrees (radians if false)
        Returns:
            float: angle between the two vectors
        """
        # A.B = |A||B| cos(theta)
        # ==> theta = acos(A.B/|A||B|)

        angle = math.acos(self.dot(other)/(self.magnitude * other.magnitude))

        return angle * 180 / math.pi if deg else angle

    def cross(self, other):
        """compute the cross product of vectors
        Args:
            other (Vector):
                other vector to be compared against
        Returns:
            Vector: Cross product
        """
        return Vector(*np.cross(self.components, other.components))

    def point_along(self, frac):
        """return a point at `frac` along the vector from origin"""
        return tuple([o+d*frac for o, d in zip(self.origin, self)])

    def project(self, other):
        """Project this vector onto another
        Args:
            other (Vector):
                vector to be projected onto
        Returns:
            Vector: projected vector
        """
        if not self.origin == other.origin:
            raise ValueError('vector origins must be identical')

        dot = self.dot(other)
        mag2 = other.magnitude ** 2

        proj = other * (dot/mag2)
        proj._origin = other.origin

        return proj

    def intersect(self, other):
        """set vectors equal to one another to find intersection point"""
        if self.is_parallel(other):
            print(f'parallel vectors {self} and {other}')
            return None
        raise NotImplementedError

    def intersect_boundary(self, axis, val):
        """return a point along this vector where it intersects an orthogonal
        boundary

        Args:
            axis (str, int): representation of the axis
                             x/0, y/1, z/2, 3, 4, ..., n

            val (float, int): value of this axis

        Returns:
            coordinate of the plane intersect
        """
        numerate = {'x': 0,
                    'y': 1}

        if type(axis) == str and axis in numerate:
            axis = numerate[axis]

        if type(axis) is not int:
            raise ValueError('pass axis as x,y,z or x=0 indexed integer')

        # test for parallel, create a unit vector on this axis
        dirn = [1, 1]
        dirn[axis] = 0
        test = Vector(*dirn)

        test = Vector.point_and_direction([(1-v)*val for v in dirn],
                                          [v * m * 1.2 for v, m
                                           in zip(dirn, self.endpoint)])
        # print(test)
        if self.is_parallel(test):
            raise ValueError(f'vector is parallel to axis {axis}={val}')

        components = self.components[:2]

        # create linear equations in the form ax + by = c
        # as we know x or y, np.linalg.solve gives unknown axis and c
        A = np.stack([[v*-1 for v in dirn], components]).T
        B = [(1-v)*val - o for v, o in zip(dirn, self.origin)]

        solve = np.linalg.solve(A, B)[0]

        if axis == 0:
            return [val, solve]
        if axis == 1:
            return [solve, val]

    def distance_to_origin(self, point):

        cumulator = []
        for i in range(len(point)):
            if i < len(self._origin):
                c0 = self._origin[i]
            else:
                c0 = 0
            c1 = point[i]

            d = c0 - c1

            cumulator.append(d**2)

        return sum(cumulator)**0.5

    def plot(self, label=''):
        """plot this vector on a matplotlib plot"""
        # plt.arrow(*self.origin, *self.components,
        #           width=0.01)
        plt.plot([self.origin[0], self.origin[0] + self.components[0]],
                 [self.origin[1], self.origin[1] + self.components[1]],
                 label=label)


class subVector(Vector):

    def this_is_just_a_test(self):
        pass

    def this_is_just_a_test_but_with_doc(self):
        "this is just a test"
        pass


class test_Vector(unittest.TestCase):

    def test_creation(self):
        vect = Vector(0, 10)

        self.assertEqual(vect.components, (0, 10))
        self.assertEqual(vect.origin, (0, 0))

    def create_from_points(self):
        vect = Vector.from_points((2, -7, 0), (1, -3, -5))

        self.assertEqual(vect.components, (-1, 4, 5))
        self.assertEqual(vect.origin, (2, -7, 0))

    def length_test(self):
        vect = Vector(3, -5, 10)

        self.assertEqual(vect.magnitude, 134**0.5)

    def vector_addition(self):
        A = Vector(1, 2, 0)
        B = Vector(2, 5, 6)

        C = A + B

        self.assertEqual(C.components, (3, 7, 6))

    def vector_subtraction(self):
        A = Vector(1, 2, 0)
        B = Vector(2, 5, 6)

        C = A - B

        self.assertEqual(C.components, (-1, -3, -6))

    def scalar_multiply_int(self):
        A = Vector(2, 5, 6)
        B = A * 5

        self.assertEqual(B.components, (10, 25, 30))

    def scalar_multiply_float(self):
        A = Vector(1, 2, 9)
        B = A * 2.2

        self.assertEqual(B.components, (2.2, 4.4, 19.8))

    def test_parallel(self):
        A = Vector(2, -4, 1)
        B = Vector(-6, 12, -3)
        C = Vector(7, -4, 1)

        self.assertTrue(A.is_parallel(B))
        self.assertTrue(B.is_parallel(A))
        self.assertFalse(A.is_parallel(C))

    def dot_product(self):
        A = Vector(0, 3, -7)
        B = Vector(2, 3, 1)

        self.assertEqual(A.dot(B), 2.0)

    def angle(self):
        A = Vector(3, -4, -1)
        B = Vector(0, 5, 2)

        self.assertEqual(A.angle(B, deg=False),
                         math.acos(-22/(26**0.5 * 29**0.5)))

    def test_point_along_length(self):
        A = Vector.from_points((0, 6), (0, 16))

        self.assertEqual(A.point_along(0.5), (0, 11))

    def shift_origin(self):
        test = Vector(5, 5)
        test.origin = (2, 2)

        self.assertEqual(test.endpoint, (7, 7))


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    # TODO:
    #   normal vector isn't considered parallel thanks to rounding issues
    #   2.0 != 1.9999999999999998
    #   also need to align origins on vector operations

    A = Vector.from_points((1, 2), (7, 12))
    A = Vector.point_and_direction((8.45, 2.2), (5.931990380498499, -8.050558373533681, 0.0))
    print(A.distance_to_origin((8.45, 2.2, 1)))
    A.plot()

    val = 10
    axis = 'y'

    intersect = A.intersect_boundary(axis, val)
    if axis == 'x':
        plt.axvline(val, color='r')
    else:
        plt.axhline(val, color='r')
    plt.plot(*intersect, color='orange', marker='o')

    plt.xlim(0,10)
    plt.ylim(0,10)

    plt.show()