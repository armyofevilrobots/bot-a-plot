import math
import logging
import cmath
import sys
from svgelements import (CubicBezier, Arc, SimpleLine, Line, QuadraticBezier,
                         Close, Polygon, Circle, Polyline, Move, Shape, Path,
                         Rect, SVG)
import os

def read_svg_in_original_dimensions(path):
    """Clean parse of the SVG in it's native dimensions"""
    path = os.path.normpath(path)
    tsvg = SVG.parse(path, reify=True, ppi=25.4)  # Why inches for FSM's sake?!
    if tsvg.values.get("width") is not None:
        svg = tsvg
    else:
        svg = SVG.parse(path,
                        width=tsvg.viewbox.width,
                        height=tsvg.viewbox.height,
                        reify=True)  # Why inches for FSM's sake?!
    return svg

# def subdivide_path(path, max_length=2.0):
#     """Returns VERY naive subdivision of a path.
#     path is an svgpathtools path, and max_length is
#     the maximum length (assuming mm) for any segment
#     """
#     chunk_count = int(math.ceil(path.length()/max_length))
#     points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
#     return [(p.real, p.imag) for p in points]
def calculate_mm_per_unit(svg):
    """Inspect an SVG and determine it's scale factor so that we can
    convert it to MM"""
    # TODO: Actually calculate if there is a width and height unit value
    return 25.4/72.0

def subdivide_path(path, distance=0.5):
    logging.debug(f"Path is {path.__class__}:{path}")
    chunk_count = int(math.ceil(path.length() / distance))
    # print("Using %d chunks" % chunk_count)
    # These support Numpy acceleration
    if isinstance(path, (CubicBezier, Arc, QuadraticBezier)):
        npoints = [(i / chunk_count) for i in range(chunk_count + 1)]
        points = path.npoint(npoints)
    # So do these, but it's broken
    elif isinstance(path, (Line, SimpleLine, Close)):
        points = [path.point(0.0), path.point(1.0)]
    # elif isinstance(path, Polyline):
    #   TODO: Just duplicate the polyline points. No subdivision required.
    #         Also, we might be able to do the same with a polygon
    #     print("POLYLINE:")
    #     points = [path.point(0.0), path.point(1.0)]
    elif isinstance(path, (Polygon, Circle)):
        points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
    elif isinstance(path, (Polyline, Rect)):
        points = subdivide_path(path.segments())
    else:
        logging.warning("Unusual component: %s" % path)
        # And this is a catch all.
        # points = [path.npoint(i/chunk_count) for i in range(chunk_count + 1)]
        points = list()
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
                        if sub:  # Skip empty subsections
                            lines.append(
                                [[x, y] for [x, y] in subdivide_path(sub, distance)]
                            )
                    except ZeroDivisionError as exc:
                        sys.stderr.write("Skipping zero len line\n")
                    except ValueError as exc:
                        sys.stderr.write("Invalid/Empty segment: %s\n" % exc)
        elif isinstance(element, Shape):
            try:
                tmpsub = [[x, y] for [x, y] in subdivide_path(element, distance)]
                if tmpsub:
                    lines.append(tmpsub)
            except ZeroDivisionError as exc:
                sys.stderr.write("Skipping zero len line")
    return lines

