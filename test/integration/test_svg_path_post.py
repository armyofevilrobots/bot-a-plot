#!/bin/env python

import unittest
import math
import cmath
from io import StringIO

from svgelements import SVG

from botaplot.models.plottable import Plottable
from botaplot.resources import resource_path
from botaplot.util.svg_util import subdivide_path, svg2lines
from botaplot.post.gcode_base import GCodePost
from svgpathtools import svg2paths, wsvg


class TestSVGLibWithPost(unittest.TestCase):

    def setUp(self):
        # self.paths, self.attributes = svg2paths(resource_path("images", "test_simple.svg"))
        # print("ATTRS", self.attributes)
        self.svg = SVG.parse(resource_path("images", "hearts_cropped_test.svg"))
        self.post = GCodePost()
        

    def test_plot_divided_line(self):
        # for path in self.paths:
        #     print("\tPath:",path)
        # lines = [subdivide_path(path, 1) for path in self.paths]
        lines = svg2lines(self.svg)
        plottable = Plottable([Plottable.Line(line) for line in lines])
        # print("SUBD IS", lines)
        # print("Plottable is", plottable)
        ofp = StringIO()
        plottable.clamp(212.0, 10.0, True)
        self.post.write_lines_to_fp(plottable, ofp)
        # print(ofp.getvalue())

    def test_simple_hearts_post(self):
        lines = svg2lines(self.svg)
        plottable = Plottable([Plottable.Line(line) for line in lines])
        scale = plottable.calculate_dpi_via_svg(self.svg)
        print("BOUNDS", plottable.bounds)
        for b in range(len(plottable.bounds)):
            val = (87.638888, 87.5000, 912.500, 912.500)[b]
            self.assertAlmostEqual(val, plottable.bounds[b], 4)

        self.assertAlmostEqual(scale, 0.36417, 5)
        print("VALUES", self.svg.values)
        height = self.svg.values.get('height', "%fin" % (self.svg.viewbox.height/72.0))
        print("HEIGHT:", height)
        self.assertAlmostEqual(float(height[:5]), 10.0)
        bot_dist = self.post.bounds[1][1]-plottable.convert_svg_units_to_mm(height)
        print("BOT_DIST", bot_dist)
        self.assertAlmostEqual(bot_dist, 0.0, 3)


