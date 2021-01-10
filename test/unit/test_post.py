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
        print("Plottable is", self.chunks)
        post = GCodePost()
        ofp = StringIO()
        post.write_lines_to_fp(self.chunks, ofp)
        print(ofp.getvalue())
