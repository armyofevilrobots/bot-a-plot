
#!/bin/env python

import unittest
import math
import cmath
from io import StringIO
from botaplot.models.plottable import Plottable
from botaplot.resources import resource_path
from botaplot.util.svg_util import subdivide_path, svg2lines
from svgelements import (SVG, Path, Move, Shape)
import json



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
        #self.paths, self.attributes = svg2paths(resource_path("images", "test_simple.svg"))
        # print("ATTRS", self.attributes)
        self.svg = SVG.parse(resource_path("images", "test_simple.svg"))

    def test_naive_subdivision(self):
        # for path in self.paths:
        #     print("\tPath:",path)
        # subd = subdivide_path(self.svg, 50)
        subd = svg2lines(self.svg)
        print("There are %d" % len(subd), "lines")
        print("SUBD:", json.dumps(subd, indent=2))
        self.assertEqual(len(subd), 9)

    def test_minimal_lines(self):
        svg = SVG.parse(resource_path("images", "hearts_cropped_test.svg"))
        print("SVG:", svg)
        print("VALUES:", svg.values)
        print("DIR:", dir(svg))
        print("VIEWBOX:", svg.viewbox.__dict__)
        self.assertAlmostEqual(svg.viewbox.width, 666.0, 3)
        self.assertAlmostEqual(svg.viewbox.height, 720.0, 3)
        lines = svg2lines(svg)
        print("LEN:", len(lines))
        print("LINES:", json.dumps(lines))
        self.assertEqual(len(lines), 44)




