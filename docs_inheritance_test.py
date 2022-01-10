from vect_store import Vector

class cross_file_vector(Vector):
    """subclass of Vector that goes across files (and therefore modules)"""

    def __init__(self):
        pass

    def undocumented_crossfile_func(self):

        pass

class subVector:
    """secondary subVector class to test the subclass with name clashing"""

    def __init__(self):
        pass

    def nondocumented(self):
        pass