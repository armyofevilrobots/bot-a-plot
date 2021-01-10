# Misc utils
import numpy as np
from math import sqrt
from collections import namedtuple

MAX_LENGTH = 2**24

NextLine = namedtuple("NextLine", ["index", "reverse", "distance", "valid"])


def split_lines_at_discontinuities(coords):
    lines = []
    line = []
    for x, y  in coords:
        if not valid_point((x,y)):
            if line:
                lines.append(line)
                line = []
            continue
        line.append((x, y))
    return lines


def plot_to_lines(proj, size=230, margin=10):
    coords = clamp_coords([(x, y) for (x,y) in zip(*proj)],
                          size, margin)
    lines = optimize_lines(split_lines_at_discontinuities(coords))
    return lines

def valid_point(point):
    if np.isnan(point[0]) or np.isnan(point[1]):
        return False
    return True

def clamp_coords(points, graphsize, margin):
    xmin = min([p[0] for p in points if valid_point(p)])
    xmax = max([p[0] for p in points if valid_point(p)])
    ymin = min([p[1] for p in points if valid_point(p)])
    ymax = max([p[1] for p in points if valid_point(p)])
    scale = (graphsize-(margin*2.0))/(xmax-xmin)
    # Scale and center
    pout = [(margin + (scale*(p[0]-xmin)), (margin + scale*(p[1]-ymin)))
              for p in points]
    return pout


def distance(p0, p1):
    """How far apart are these points"""
    if not (valid_point(p0) and valid_point(p1)):
        return MAX_LENGTH  # Infinite distance, effectively
    dx = p1[0]-p0[0]
    dy = p1[1]-p0[1]
    return sqrt(dx*dx+dy*dy)


def optimize_lines(lines, limit=30000):
    """
    Find the closest line endpoint at the end of a given drawn line,
    and add _that_ to the output list, correctly ordered. Ensures we
    have the shortest hops between lines.
    Brute-force and totally naive. Limit ensures we only scan the next
    $limit lines for close endpoints, and take the closest, so that we
    don't burn a ton of CPU searching the entire line-space every scan.
    """
    print("Lines is type:", type(lines), lines.__class__)
    out_lines = []
    orig_lines = lines.copy()
    line = orig_lines.pop(0)  # Start us out.
    next_line = NextLine(None, False, MAX_LENGTH, False)  # Which index, how far away
    while orig_lines:
        span = min(limit, len(orig_lines))
        for i in range(span):
            d_e2e = distance(line[-1], orig_lines[i][-1])
            d_e2s = distance(line[-1], orig_lines[i][0])
            if next_line.distance > d_e2e:
                # closest is the end of another line...
                next_line = NextLine(i, True, d_e2e, True)
            elif next_line.distance > d_e2s:
                # Closest is the START of another line
                next_line = NextLine(i, False, d_e2s, True)
        if next_line.valid:
            # We found a closer line
            move_line = orig_lines.pop(next_line.index)
            if next_line.reverse:
                move_line.reverse()
        else:
            move_line = orig_lines.pop(0)
            # Special case. Check if it is a better match forwards or backwards.
            d_e2e = distance(move_line[-1], line[-1])
            d_e2s = distance(line[-1], move_line[0])
            if d_e2s > d_e2e:
                move_line.reverse()

        next_line = NextLine(None, False, MAX_LENGTH, False)  # Which index, how far away
        line = move_line
        out_lines.append(move_line)
    return out_lines


