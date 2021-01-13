from botaplot.util.util import distance
from .base import BasePost


class GCodePost(BasePost):

    bounds = [(0,0), (230,235)]

    preamble = [
        "G28 X Y",
        "G92 X0 Y0",
        "M280 S5",
        "G4 P150 ; PEN IS UP",
    ]
    penup = [
        "M400 ; PEN UP",
        "M280 S5",
        "G4 P150 ; PEN IS UP",
    ]
    pendown = [
        "M400 ; PEN DOWN",
        "M280 S7",
        "G4 P100 ; Easing",
        "M280 S8",
        "M400",
        "G4 P100 ; Easing",
        "M280 S10",
        "G4 P70 ; PEN IS DOWN",
    ]
    epilog = [
        "M400",
        "M280 S5",
        "G4 P1000",
        "M400",
        "G0X15Y230",
        "G4 P1000",
        "M400",
        "G4 P1000",
        "M400"
    ]

    feedrate = 20*60.0  # MM/Min
    pen_drag_mm = 0.75  # How far we'll drag then pen between lines

    def post_lines_to_file(self, lines, filename):
        with open(filename, "w") as gc:
            self.write_lines_to_fp(lines, gc)

    def write_lines_to_fp(self, lines, gc):
        for stanza in self.lines2gcodes_gen(lines):
            gc.write("%s\n" % stanza)

    def lines2gcodes_gen(self, lines):
        yield from self.preamble
        yield from self.penup
        lastpos = None
        for line in lines:
            if len(line) <= 1:
                # Skip lines that are just a dot
                continue

            # Check if our drag is shorter than our minimum, and skip
            # penup if it is.
            # TODO: Check if the drag is OVER an existing line (or this line)
            # and would result in effectively no line added
            if lastpos is None \
               or distance(lastpos, line[0]) > self.pen_drag_mm:
                # Long drag, so write entire penup/pendown stanza
                yield from self.penup
                yield "G0 X%4.2f Y%4.2f" % (line[0][0], line[0][1])
                yield from self.pendown
            else:
                # Short drag, keep the pen down and save some time.
                yield ("G01 X%4.2f Y%4.2f "
                       "; Skipping PEN UPDOWN for very short drag." %
                       (line[0][0], line[0][1]))

            # Then draw the rest of the line at regular feed rates.
            for (x, y) in line[1:]:
                yield "G01 F%5.2f X%4.2f Y%4.2f" % (self.feedrate, x, y)
            lastpos = line[-1]
        yield from self.epilog
