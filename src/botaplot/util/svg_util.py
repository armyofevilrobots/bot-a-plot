import math
import logging
import cmath
from math import sqrt
import sys
from svgelements import (CubicBezier, Arc, SimpleLine, Line, QuadraticBezier,
                         Close, Polygon, Circle, Polyline, Move, Shape, Path,
                         Rect, SVG)
import os
try:
    from dataclasses import dataclass
except ImportError:
    def dataclass(cls=None, /, **kw):
        def wrap(cls):
            return cls
        if cls is None:
            return wrap
        else:
            return wrap(cls)


logger = logging.getLogger(__name__)

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


@dataclass
class PChunk:
    """
    pchunks are representations of a path chunk, and are (startval, endval, start_xy, end_xy, children)
    - startval : Where on the top level path it starts, is 0.5 is the dead center
    - endval   : Where on the top level path it ends. See above
    - start_xy : x,y position of the start of this chunk, if it were a line
    - end_xy   : x,y position of the end ^^^
    - children : A maximum of TWO children, in order of path direction, which define the same segment,
                 but with 2x more detail than this line. If children is None, then we don't have any,
                 and this is the path segment that will be drawn, otherwise, this path segment is
                 hidden and the children are drawn instead.
    """
    startval: float
    endval: float
    startxy: tuple
    endxy: tuple
    children: tuple or None



def path_clean_subdivide_by_len(path: Path, err=0.001, min_len=0.05, diverge=0.1):
    """Subdivides a curved path into successively smaller chunks until the sum
    of the lengths of the chunks is within $error of the length of the path
    overall.
    """
    pathlen = path.length(error=0.1, min_depth=10)
    def _recur_split_pchunk(pchunk: PChunk, err=0.1) -> PChunk:
        """Takes a pchunk, and splits or not depending on error value"""

        # ie: if it's from 0.0 to 0.5, it's 0.5 * total path length
        _want_len = pathlen * (pchunk.endval - pchunk.startval)
        print("Want len is", _want_len)
        _got_len = sqrt(
            ((pchunk.endxy[0] - pchunk.startxy[0]) ** 2.0) +
            ((pchunk.endxy[1] - pchunk.startxy[1]) ** 2.0)
        )
        print("Len is", _got_len)
        # Calculate difference from 1.0
        _err = 1.0 - (_got_len / _want_len)
        print("Error is", _err)
        if _err < 0.0 or _err < err or _got_len > _want_len or _want_len < min_len:
            return pchunk
        else:
            child_a_mid = (pchunk.endval+pchunk.startval)/2.0
            child_midpoint = path.point(child_a_mid)
            child_a = _recur_split_pchunk(
                PChunk(pchunk.startval, child_a_mid,
                       pchunk.startxy, child_midpoint,
                       None),
                err
            )
            child_b = _recur_split_pchunk(
                PChunk(child_a_mid, pchunk.endval,
                       child_midpoint, pchunk.endxy,
                       None),
                err
            )
            new_pchunk = PChunk(
                pchunk.startval, pchunk.endval,
                pchunk.startxy, pchunk.endxy,
                [child_a, child_b]
            )
            # print("New pchunk is", new_pchunk)
            return new_pchunk

    def _flatten_pchunk(pchunk: PChunk):
        """Flattens the segments of a pchunk, in order"""
        if pchunk.children is None:
            return [pchunk.startxy, pchunk.endxy]
        else:
            return _flatten_pchunk(pchunk.children[0]) + _flatten_pchunk(pchunk.children[1])

    initial_pchunk = PChunk(0.0, 1.0, path.point(0.0), path.point(1.0), None)
    return _flatten_pchunk(_recur_split_pchunk(initial_pchunk, err))






def subdivide_path(path, distance=0.5):
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
        # points = subdivide_path(path.segments())
        # TODO: Break this down cleaner
        points = [path.point(i / chunk_count) for i in range(chunk_count + 1)]
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

                logger.info("Splitting element: %s", element)
                tmpsub = [[x, y] for [x, y] in subdivide_path(element, distance)]
                if tmpsub:
                    lines.append(tmpsub)
            except ZeroDivisionError as exc:
                sys.stderr.write("Skipping zero len line")
    return lines

