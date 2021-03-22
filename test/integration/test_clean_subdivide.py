import time
import unittest
import matplotlib.pyplot as plt
from botaplot.resources import resource_path
from botaplot.util.svg_util import subdivide_path, svg2lines, path_clean_subdivide_by_len
from svgelements import (SVG, Path, Move, Shape)
from rdp import rdp

class TestCleanSubdivide(unittest.TestCase):

    def setUp(self):
        self.svg = SVG.parse(resource_path("images", "hearts_cropped_test.svg"))

    def test_clean_matplotlib(self):
        points = [(0,0), (10,10), (20,30), (10,40)]
        xp, yp = zip(*points)
        plt.plot(xp, yp, 2)
        plt.show()

    def test_clean_subdivide(self):
        for element in self.svg.elements():
            print("EL IS", type(element), element)
            if isinstance(element, Path):
                points = path_clean_subdivide_by_len(element)
                #print("Points are:", points)
                print("There are %d points" % len(points))
                xp, yp = zip(*points)
                plt.plot(xp, yp, 2)
        plt.show()

    def test_rdp_lines(self):
        num_segs_old = 0
        num_segs_new = 0
        for line in svg2lines(self.svg, 0.5):
            num_segs_old += len(line)
            xp, yp = zip(*line)
            plt.plot(xp, yp, color="b")
            line = rdp(line, epsilon=0.1)
            num_segs_new += len(line)
            xp, yp = zip(*line)
            plt.plot(xp, yp, color="g")
        print("Old method: %d lines" % num_segs_old)
        print("New method: %d lines" % num_segs_new)
        plt.show()

    def test_rdp_endpoints_match(self):
        num_segs_old = 0
        num_segs_new = 0
        for line in svg2lines(self.svg, 0.5):
            num_segs_old += len(line)
            xp, yp = zip(*line)
            plt.plot(xp, yp, color="b")
            newline = rdp(line, epsilon=0.1)
            num_segs_new += len(newline)
            xp, yp = zip(*line)
            plt.plot(xp, yp, color="g")
            self.assertListEqual(line[0], newline[0])
            self.assertListEqual(line[-1], newline[-1])
        print("Old method: %d lines" % num_segs_old)
        print("New method: %d lines" % num_segs_new)
        plt.show()






if __name__ == '__main__':
    unittest.main()
