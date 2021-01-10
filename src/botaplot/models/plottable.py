"""
Plottables:

These are objects which represent lines that can be sent to a plotter.
They can be processed by a PostProcessor.
They contain a sequence of lines, each of which has a
pressure value (which can represent width/pressure/strokeweight depending
on the post-processor), and a "tool/pen id".
"""

import numpy as np
from math import sqrt
from collections import namedtuple
from botaplot.util.util import (valid_point, distance, NextLine, MAX_LENGTH)



class Plottable(object):

    class PlotChunk(object):
        """A base plottable"""

    class Line(PlotChunk):
        """Line segment"""
        def __init__(self, points: np.ndarray, weight: float=1.0, pen=1):
            self.points = np.ndarray
            self.weight = weight
            self.pen = pen

        def __iter__(self):
            for x in self.points:
                yield x

        def __getitem__(self, idx):
            return self.points[idx]

        def __repr__(self):
            if len(self.points):
                return "<PlotChunk:Line %s .. %s>" % (self.points[0], self.points[-1])
            return "<PlotChunk:Line empty>"

    def __init__(self, chunks=None):
        if chunks is None:
            chunks = list()
        self.chunks = self.optimize_lines(chunks)

    def optimize_lines(self, chunks=None, limit=30000):
        """
        Find the closest line endpoint at the end of a given drawn line,
        and add _that_ to the output list, correctly ordered. Ensures we
        have the shortest hops between lines.
        Brute-force and totally naive. Limit ensures we only scan the next
        $limit lines for close endpoints, and take the closest, so that we
        don't burn a ton of CPU searching the entire line-space every scan.
        """
        out_chunks = list()
        if chunks is not None:
            orig_chunks = chunks.copy()
        else:
            orig_chunks = self.chunks.copy()
        line = orig_chunks.pop(0)  # Start us out.
        next_chunk = NextLine(None, False, MAX_LENGTH, False)  # Which index, how far away
        while orig_chunks:
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
        self.chunks = out_chunks
        return out_chunks

    def __iter__(self):
        for x in self.chunks:
            yield x

    def __getitem__(self, idx):
        return self.chunks[idx]

    def __repr__(self):
        if len(self.points):
            return "<Plottable: %d Chunks>" % (len(self.chunks))
        return "<Plottable:Empty>"
