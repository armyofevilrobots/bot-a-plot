"""
Plottables:

These are objects which represent lines that can be sent to a plotter.
They can be processed by a PostProcessor.
They contain a sequence of lines, each of which has a
pressure value (which can represent width/pressure/strokeweight depending
on the post-processor), and a "tool/pen id".
"""

import numpy as np
from math import sqrt, floor
from dataclasses import dataclass
from collections import namedtuple
from weakref import WeakValueDictionary, WeakSet
from botaplot.util.util import (valid_point, distance, NextLine, MAX_LENGTH,
                                clamp_coords)
import sys



class XYHash(object):
    """Geometric localized 2d coordinate cache"""
    gridsize = 10.0  # 1cm squares
    _hash = None


    def __init__(self, lines):
        self._hash = dict()
        for pline in lines:
            self.add(pline)

    def add(self, pline):
        start = pline[0]
        end = pline[-1]
        for point in start, end:
            hash = "%dX%d" % (floor(pline[0] / 10), floor(point[1] / 10))
            if pline in self._hash.get(hash, list()):
                continue
            if self._hash.get(hash) is None:
                self._hash[hash] = WeakValueDictionary((0, pline))
            else:
                self._hash[hash][len(self._hash[hash])].append(pline)

    def remove(self, pline):
        start = pline[0]
        end = pline[-1]
        if start == end:
            end = None
        for point in start, end:
            while point in self._hash.get(hash):
                self._hash.get(hash).remove(pline)

    def closest(self, x, y, radius=3, remove=True):
        """
        Returns the closest line, with 1 or -1 for it's
        direction (is it reversed)?
        Radius sets the maximum distance from the center square to search.
        If remove is set, cleans it out of the cache (because you just drew
        it... duh...)

        Algo:
        assume search center = 55,52, radius is 3
        check each endpoint in box[5,5]
        if match: return match
        for d in 1..radius:
            let start = 5 - d
            let end = 5 + d
            i in 0..d-1:
                check each endpoint in box[start+i, start]
                if match: return match
                check each endpoint in box[end, start+i]
                if match: return match
                check each endpoint in box[end-i, end]
                if match: return match
                check each endpoint in box[end, end-i]
                if match: return match




        """






class Plottable(object):

    class PlotChunk(object):
        """A base plottable"""

        def transform(self, x, y, scalex, scaley):
            raise NotImplementedError()


    class Line(PlotChunk):
        """Line segment"""
        def __init__(self, points: list, weight: float=1.0, pen=1):
            self.points = points
            self.weight = weight
            self.pen = pen

        def __len__(self):
            return len(self.points)

        def __iter__(self):
            for x in self.points:
                yield x

        def __getitem__(self, idx):
            return self.points[idx]

        def __repr__(self):
            if len(self.points):
                return "<PlotChunk:Line %s .. %s>" % (self.points[0], self.points[-1])
            return "<PlotChunk:Line empty>"

        def transform(self, x, y, scalex, scaley):
            return [(x+p[0]*scalex, y+p[1]*scaley) for p in self.points]

        @property
        def bounds(self):
            xmin = min([p[0] for p in self.points])
            xmax = max([p[0] for p in self.points])
            ymin = min([p[1] for p in self.points])
            ymax = max([p[1] for p in self.points])
            return xmin, ymin, xmax, ymax


    def __init__(self, chunks=None, callback=None):
        if chunks is None:
            chunks = list()
        #self.chunks = chunks
        self.chunks = chunks #self.optimize_lines(chunks, callback=callback)

    def clamp(self, graphsize=230.0, margins=10, invert=True):
        xmin = MAX_LENGTH
        xmax = -MAX_LENGTH
        ymin = MAX_LENGTH
        ymax = -MAX_LENGTH
        for chunk in self.chunks:
            # First we measure
            xmin = min(xmin, min([p[0] for p in chunk.points]))
            xmax = max(xmax, max([p[0] for p in chunk.points]))
            ymin = min(ymin, min([p[1] for p in chunk.points]))
            ymax = max(ymax, max([p[1] for p in chunk.points]))
        scale = min((graphsize-(margins*2.0))/(ymax-ymin),
                    (graphsize-(margins*2.0))/(xmax-xmin))
        for chunk in self.chunks:
            # Now we scale
            if invert:
                chunk.points = [(margins + (scale*(p[0]-xmin)),
                                 ((graphsize-margins) - scale*(p[1]-ymin)))
                                for p in chunk.points]
            else:
                chunk.points = [(margins + (scale*(p[0]-xmin)),
                                 (margins + scale*(p[1]-ymin)))
                                for p in chunk.points]

    def scale(self, scale=1.0, margins=0.0):
        xmin = ymin = 0.0
        if isinstance(margins, (tuple, list)):
            xmargin = margins[0]
            ymargin = margins[1]
        else:
            xmargin = ymargin = margins
        for chunk in self.chunks:
            # Now we scale
            chunk.points = [(xmargin + (scale*(p[0]-xmin)),
                             (ymargin + scale*(p[1]-ymin)))
                            for p in chunk.points]


    @property
    def bounds(self):
        bounds = [chunk.bounds for chunk in self.chunks]
        xmin = min(bound[0] for bound in bounds)
        ymin = min(bound[1] for bound in bounds)
        xmax = max(bound[2] for bound in bounds)
        ymax = max(bound[3] for bound in bounds)
        return xmin, ymin, xmax, ymax


    @staticmethod
    def convert_svg_units_to_mm(value):
        """Parse in/mm to mm units normalized"""
        if isinstance(value, float):
            return value  # Assume MM
        if value.endswith("mm"):
            return 1.0*float(value[:-2])
        elif value.endswith("in"):
            return 25.4*float(value[:-2])

    def calculate_dpi_via_svg(self, svg):
        """Figure out what our point size is relative to MM"""
        return 72.0
        # if svg.values.get('width') is not None:
        #     sys.stderr.write("Calculating DPI via Width/Viewport")
        #     return svg.viewbox.width / self.convert_svg_units_to_mm(svg.values.get('width'))
        # else:
        #     sys.stderr.write("Calculating DPI via Width/Viewport")
        #     return svg.viewbox.width/(25.4*72.0)

    def transform_self(self, x=0.0, y=0.0, scalex=1.0, scaley=1.0):
        """Transform all internal coords by scale, moved by x,y"""
        self.chunks = self.transform(x, y, scalex, scaley)
        # for chunk in self.chunks:
        #     chunk.transform(x, y, scalex, scaley)

    def transform(self, x=0.0, y=0.0, scalex=1.0, scaley=1.0):
        return [chunk.transform(x, y, scalex, scaley) for chunk in self.chunks]

    def optimize_lines(self, chunks=None, limit=100, callback=None):
        """
        Find the closest line endpoint at the end of a given drawn line,
        and add _that_ to the output list, correctly ordered. Ensures we
        have the shortest hops between lines.
        Brute-force and totally naive. Limit ensures we only scan the next
        $limit lines for close endpoints, and take the closest, so that we
        don't burn a ton of CPU searching the entire line-space every scan.
        """

        # The XYHash is a grid of squares. We bin the endpoints for various lines
        # into it so that we can more easily find their endpoints. It's a weakref
        # dict, so when we pull the lines _out_ of orig_chunks, they disappear
        # from the hash too.
        if callback is not None and not callable(callback):
            raise TypeError("Callback is not a callable")
        out_chunks = list()
        if chunks is not None:
            orig_chunks = chunks.copy()
        else:
            orig_chunks = self.chunks.copy()
        line = orig_chunks.pop(0)  # Start us out.
        out_chunks.append(line)
        next_chunk = NextLine(None, False, MAX_LENGTH, False)  # Which index, how far away
        while len(orig_chunks) > 0:
            if len(orig_chunks) % 10 == 0:
                if callback is not None:
                    callback("optimizing", len(orig_chunks), chunks and len(chunks) or len(self.chunks))

                # sys.stderr.write("%d chunks left.\n" % len(orig_chunks))
                # sys.stderr.flush()
            span = min(limit, len(orig_chunks))
            for i in range(span):
                d_e2e = distance(line.points[-1], orig_chunks[i].points[-1])
                d_e2s = distance(line.points[-1], orig_chunks[i].points[0])
                if next_chunk.distance > d_e2e:
                    # closest is the end of another line...
                    next_chunk = NextLine(i, True, d_e2e, True)
                elif next_chunk.distance > d_e2s:
                    # Closest is the START of another line
                    next_chunk = NextLine(i, False, d_e2s, True)
            if next_chunk.valid:
                # We found a closer line
                move_chunk = orig_chunks.pop(next_chunk.index)
                if next_chunk.reverse:
                    move_chunk.points.reverse()
                    #move_chunk.points = np.flip(move_chunk.points)
                    # if isinstance(move_chunk.points, np.ndarray):
                    #     move_chunk.points.flip()
                    # else:
                    # #     move_chunk.points.reverse()
            else:
                move_chunk = orig_chunks.pop(0)
                # Special case. Check if it is a better match forwards or backwards.
                d_e2e = distance(move_chunk[-1], line[-1])
                d_e2s = distance(line[-1], move_chunk[0])
                if d_e2s > d_e2e:
                    move_chunk.points.reverse()

            next_chunk = NextLine(None, False, MAX_LENGTH, False)  # Which index, how far away
            line = move_chunk
            out_chunks.append(move_chunk)
        callback("optimizing", len(orig_chunks), chunks and len(chunks) or len(self.chunks))

        self.chunks = out_chunks
        return out_chunks

    def __len__(self):
        return len(self.chunks)

    def __iter__(self):
        for x in self.chunks:
            yield x

    def __getitem__(self, idx):
        return self.chunks[idx]

    def __repr__(self):
        if len(self.chunks):
            return "<Plottable: %d Chunks>" % (len(self.chunks))
        return "<Plottable:Empty>"

    def pop(self, *args, **kw):
        return self.chunks.pop(*args, **kw)

    def reverse(self):
        self.chunks.reverse()

    def append(self, *args, **kw):
        self.chunks.append(*args, **kw)
