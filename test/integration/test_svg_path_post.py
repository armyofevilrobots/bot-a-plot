#!/bin/env python

import unittest
import math
import cmath
from io import StringIO
from botaplot.models.plottable import Plottable
from botaplot.resources import resource_path
from botaplot.util.svg_util import subdivide_path
from botaplot.post.gcode_base import GCodePost
from svgpathtools import svg2paths, wsvg


class TestSVGLibWithPost(unittest.TestCase):

    def setUp(self):
        self.paths, self.attributes = svg2paths(resource_path("images", "test_simple.svg"))
        # print("ATTRS", self.attributes)
        self.post = GCodePost()
        

    def test_plot_divided_line(self):
        # for path in self.paths:
        #     print("\tPath:",path)
        lines = [subdivide_path(path, 1) for path in self.paths]
        plottable = Plottable([Plottable.Line(line) for line in lines])
        print("SUBD IS", lines)
        print("Plottable is", plottable)
        ofp = StringIO()
        plottable.clamp(212.0, 10.0, True)
        self.post.write_lines_to_fp(plottable, ofp)
        print(ofp.getvalue())

