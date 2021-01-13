
#!/bin/env python

import unittest
import math
import cmath
from io import StringIO
from botaplot.models.plottable import Plottable
from botaplot.resources import resource_path
from botaplot.util.svg_util import subdivide_path
from svgpathtools import svg2paths, wsvg




def subdivide_path_fancy(path, aspect=0.99):
    """Returns less naive subdivision of a path.
    path is an svgpathtools path, and aspect is
    the maximum linear length vs actual length
    of the lines. We do a binary search through
    the segment length space until we get a good result.
    """
    chunk_count = int(math.ceil(path.length()/max_length))
    points = [path.point((i+1.0)/chunk_count) for i in range(chunk_count)]
    return [(p.real, p.imag) for p in points]

class TestSVGLib(unittest.TestCase):


    def setUp(self):
        self.paths, self.attributes = svg2paths(resource_path("images", "test_simple.svg"))
        # print("ATTRS", self.attributes)

    def test_naive_subdivision(self):
        # for path in self.paths:
        #     print("\tPath:",path)
        subd = subdivide_path(self.paths[0], 50)
        merged = zip(subd,
            #          [
            # (10.5, 80.0),
            # (38.882277139029085, 33.30759797433691),
            # (66.37603751030969, 33.38497473599764),
            # (95.09913752005491, 80.2311084322917),
            # (123.76490824106628, 126.71796745162936),
            # (151.32690058650726, 126.64093130753213),
            # (180.0, 80.0)]
                     [(10.095285, 56.293531),
                      (38.085334003323055, 21.39561777284851),
                      (66.3302758289649, 56.44715604941179),
                      (94.54531225862775, 91.19144538945112),
                      (122.76582999999991, 56.29353100000003)]
                     )
        print([x[0] for x in merged])
        for pair in merged:
            self.assertAlmostEqual(pair[0][0], pair[1][0])
            self.assertAlmostEqual(pair[0][1], pair[1][1])

