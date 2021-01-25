#!/bin/env python

import unittest
import math
import hjson
from botaplot.models.sketch_graph import *
from botaplot.models.controls import *
from botaplot.models.svg_node import SVGSource, SVGSink, SVGNode, SVGPreviewNode

class TestNodeTypes(unittest.TestCase):

    def test_node_registry(self):
        @register_type
        class TestNode(BaseNode):
            name="Fake Test Node"
        # self.assertEquals(len(lookup_types), 2)
        self.assertEqual(lookup_types["Fake Test Node"], TestNode)


class TestSerialization(unittest.TestCase):

    def test_basenode_both_ways(self):
        basenode = BaseNode()
        hj = hjson.dumps(basenode.to_dict())
        #print(f"HJ IS {hj}")
        data = hjson.loads(hjson.dumps(basenode.to_dict()))
        self.assertEquals(data['_type'], basenode.hname)
        newnode = from_dict(data=data)
        self.assertEquals(type(newnode), type(basenode))

    def test_serialize_graph(self):
        # Create 3 basenodes
        nodes = [SVGNode.create(), SVGPreviewNode.create()]
        graph = SketchGraph(nodes)  #, edges)
        dumpable = graph.to_dict()
        hj = hjson.dumps(dumpable)
        print("HJ FOR SG IS", hj)

        undump = hjson.loads(hj)
        newgraph = from_dict(data=undump)
        self.maxDiff=65535
        self.assertDictEqual(newgraph.to_dict(), dumpable)




