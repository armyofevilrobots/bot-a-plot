#!/bin/env python

import unittest
import math
from io import StringIO
from botaplot.models.plottable import Plottable
from botaplot.post.gcode_base import GCodePost

class TestPosts(unittest.TestCase):

    def setUp(self):
        radius = math.sqrt(15.0*15.0+15.0*15.0)
        self.chunks = Plottable([
            Plottable.Line([
                (20,20), (20, 40),
                (35, 50), (50, 40),
                (50, 20), (20, 20)]
            ),
            Plottable.Line([
                (35+(radius*math.cos(math.pi*angle*22.5/180.0)),
                 35+(radius*math.sin(math.pi*angle*22.5/180.0)))
                for angle in range(0, 16)]
            )
        ])


    def test_basic_post(self):
        """Draw a square, post it"""
        post = GCodePost()
        lines = post.lines2gcodes_gen(self.chunks)


    def test_stringio_post(self):
        """Draw a square, post it"""
        post = GCodePost()
        ofp = StringIO()
        post.write_lines_to_fp(self.chunks, ofp)

        checks = [line for line in ofp.getvalue().split("\n") if line.startswith("G01")]
        print("Check is:", checks)
        self.assertListEqual(checks, [
            'G01 F1200.00 X20.00 Y40.00', 'G01 F1200.00 X35.00 Y50.00',
            'G01 F1200.00 X50.00 Y40.00', 'G01 F1200.00 X50.00 Y20.00',
            'G01 F1200.00 X20.00 Y20.00', 'G01 F1200.00 X54.60 Y43.12',
            'G01 F1200.00 X50.00 Y50.00', 'G01 F1200.00 X43.12 Y54.60',
            'G01 F1200.00 X35.00 Y56.21', 'G01 F1200.00 X26.88 Y54.60',
            'G01 F1200.00 X20.00 Y50.00', 'G01 F1200.00 X15.40 Y43.12',
            'G01 F1200.00 X13.79 Y35.00', 'G01 F1200.00 X15.40 Y26.88',
            'G01 F1200.00 X20.00 Y20.00', 'G01 F1200.00 X26.88 Y15.40',
            'G01 F1200.00 X35.00 Y13.79', 'G01 F1200.00 X43.12 Y15.40',
            'G01 F1200.00 X50.00 Y20.00', 'G01 F1200.00 X54.60 Y26.88'
        ])



