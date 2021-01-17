#!/bin/env python

import unittest
import math
import hjson
from botaplot.models.sketch_graph import *
from botaplot.models.controls import *


class TestControls(unittest.TestCase):

    def setUp(self):
        self.foo = BoundedNumericControl(3, "test", "2<x<4")

    def test_bounded_range(self):
        self.assertTrue(self.foo.in_range(3))
        self.assertFalse(self.foo.in_range(8))
        self.assertFalse(self.foo.in_range(1))

    def test_set_range_ok(self):
        self.foo.value = 3.5

    def test_set_range_bad(self):
        def _set(x):
            self.foo.value=x
        self.assertRaises(ValueError, _set, 4.01)



