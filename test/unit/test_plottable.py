#!/bin/env python

import unittest
import math
from botaplot.models.plottable import Plottable, XYHash
from weakref import WeakSet
from scipy.sparse import dok_matrix

class TestXYHash(unittest.TestCase):

    def test_base_xyhash(self):
        tline = Plottable.Line([
            (20, 20), (20, 40),
            (35, 50), (50, 40),
            (50, 20), (20, 20)]
        ),


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
        self.assertEqual(len(self.plottable), len(self.plottable.chunks))

    def test_iterate_plottable(self):
        """Draw a square, post it"""
        i = 0
        for item in self.plottable:
            i += 1
        self.assertEqual(i, 2)

    def test_pop_plottable(self):
        tmp = self.plottable.pop()
        self.assertEqual(len(self.plottable), 1)

    def _disabled_test_optimize(self):
        """Optimization is currently disabled"""
        tp = Plottable(
            [
                Plottable.Line([(20,20), (120,20), (20,30)]),
                Plottable.Line([(20,30.5), (120,32)]),
                Plottable.Line([(20,40), (120,42)])
            ])

        # It should reverse that last line
        self.assertEqual(tp[2][0], (120,32))
