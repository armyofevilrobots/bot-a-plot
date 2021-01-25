from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc
from svgpathtools import svg2paths, wsvg
import math
import cmath


def subdivide_path(path, max_length=2.0):
    """Returns VERY naive subdivision of a path.
    path is an svgpathtools path, and max_length is
    the maximum length (assuming mm) for any segment
    """
    chunk_count = int(math.ceil(path.length()/max_length))
    points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
    return [(p.real, p.imag) for p in points]
