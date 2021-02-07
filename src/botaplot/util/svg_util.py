import math
import logging
import cmath
import sys
from svgelements import (CubicBezier, Arc, SimpleLine, Line, QuadraticBezier,
                         Close, Polygon, Circle, Polyline, Move, Shape, Path)


# def subdivide_path(path, max_length=2.0):
#     """Returns VERY naive subdivision of a path.
#     path is an svgpathtools path, and max_length is
#     the maximum length (assuming mm) for any segment
#     """
#     chunk_count = int(math.ceil(path.length()/max_length))
#     points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
#     return [(p.real, p.imag) for p in points]

def subdivide_path(path, distance=0.5):
    logging.debug(f"Path is {path.__class__}:{path}")
    chunk_count = int(math.ceil(path.length() / distance))
    # print("Using %d chunks" % chunk_count)
    # These support Numpy acceleration
    if isinstance(path, (CubicBezier, Arc, QuadraticBezier)):
        npoints = [(i / chunk_count) for i in range(chunk_count + 1)]
        points = path.npoint(npoints)
    # So do these, but it's broken
    elif isinstance(path, (Line, SimpleLine, Close, Polyline)):
        points = [path.point(0.0), path.point(1.0)]
    # elif isinstance(path, Polyline):
    #   TODO: Just duplicate the polyline points. No subdivision required.
    #         Also, we might be able to do the same with a polygon
    #     print("POLYLINE:")
    #     points = [path.point(0.0), path.point(1.0)]
    elif isinstance(path, (Polygon, Circle)):
        points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
    else:
        logging.warning("Unusual component: %s" % path)
        # And this is a catch all.
        points = [path.npoint(i/chunk_count) for i in range(chunk_count + 1)]
    return points


def svg2lines(svg, distance=0.5):
    """Converts an SVG into line segments.
    TODO: Layer/Color to pen stuff."""
    lines = list()
    # for item in svg.objects:
    #     sys.stderr.write(f"Item:{item}")
    for element in svg.elements():
        # print(f"E: {type(element)}.{element.id} -> {element}")
        if isinstance(element, Path):
            for sub in element:
                if isinstance(sub, Move):
                    continue  # Skip all the moves
                else:
                    try:
                        lines.append(
                            [[x, y] for [x, y] in subdivide_path(sub, distance)]
                        )
                    except ZeroDivisionError as exc:
                        sys.stderr.write("Skipping zero len line")
        elif isinstance(element, Shape):
            try:
                lines.append(
                    [[x, y] for [x, y] in subdivide_path(element, distance)]
                )
            except ZeroDivisionError as exc:
                sys.stderr.write("Skipping zero len line")
    return lines

