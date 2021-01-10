#!/bin/env python

import unittest
import math
from botaplot.models.plottable import Plottable

class TestPlottable(unittest.TestCase):

    def setUp(self):
        radius = math.sqrt(15.0*15.0+15.0*15.0)
        self.plottable = Plottable([
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

    def test_len_plottable(self):
        self.assertEquals(len(self.plottable), len(self.plottable.chunks))

    def test_iterate_plottable(self):
        """Draw a square, post it"""
        i = 0
        for item in self.plottable:
            i += 1
            print("ITEM:", item)
        self.assertEquals(i, 2)

    def test_pop_plottable(self):
        tmp = self.plottable.pop()
        self.assertEquals(len(self.plottable), 1)
        print("Popped chunk:", tmp)
        print("Plottable:", self.plottable, self.plottable[0])


