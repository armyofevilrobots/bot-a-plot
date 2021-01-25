#!/bin/env python

import unittest
import math
import hjson
from botaplot.models.sketch_graph import *
from botaplot.models.controls import *
from botaplot.models.svg_node import SVGSource, SVGSink, SVGNode, SVGPreviewNode
from botaplot.resources import resource_path



class TestBasicEvents(unittest.TestCase):

    def test_svg_file_change_value(self):
        # Create 3 basenodes
        svg_node, svg_preview = SVGNode.create(), SVGPreviewNode.create()
        graph = SketchGraph([svg_node, svg_preview])
        svg_node.controls[0].value = resource_path("images", "test_simple.svg")
        self.assertEqual(svg_node.value, svg_node.controls[0].value)

    def test_svg_file_change_callback(self):
        # Create 3 basenodes
        was_called = False

        svg_node, svg_preview = SVGNode.create(), SVGPreviewNode.create()
        def _callback(obj, value):
            self.assertEqual(obj, svg_node)
            was_called = True
        svg_node.watch(_callback)
        graph = SketchGraph([svg_node, svg_preview])
        svg_node.controls[0].value = resource_path("images", "test_simple.svg")





