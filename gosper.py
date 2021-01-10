# Gosper plot for bot-a-plot testing
from math import pi, sin, cos
from lib_botaplot.mpl_util import plot_coords
from lib_botaplot import clamp_coords

ANGLE=60
AXIOM="A"
REPLACEMENTS={
    "A": "A-B--B+A++AA+B-",
    "B": "+A-BB--B-A++A+B"
}
ORDER=5
LENGTH=10

DTR = pi / 180

GRAPHSIZE = 170.0  # this is size in MM
MARGIN = 5
FEED = 20*60.0  # MM/Min
PREAMBLE = "G92 X0 Y0 Z0"
PENUP = "M280 S5\nG4 P1350"
PENDOWN = "M280 S11\nG4 P1350"
EPILOG = "G0X0Y0\nG4 P2000"


def replace_l_system(axiom, replacements, order=3):
    # Create the initial system
    system = axiom
    for iteration in range(order):
        system = "".join([replacements.get(x, x) for x in system])
    return system


def l_to_gosper(system, turn_angle=60, length=10):
    x, y, angle = 0.0, 0.0, 90
    for item in system:
        if item == "-":
            angle = (360 + angle + turn_angle) % 360
        elif item == "+":
            angle = (360 + angle - turn_angle) % 360
        if item in "AB":
            x, y = (x - cos(angle * DTR),
                    y + sin(angle * DTR))
            yield x, y


system = replace_l_system(AXIOM, REPLACEMENTS, ORDER)
points = [p for p in l_to_gosper(system)]

points = clamp_coords(points, GRAPHSIZE, MARGIN)
plt = plot_coords(points)
plt.show()

gc = [PREAMBLE, PENUP]
gc.append("G0 X%4.2f Y%4.2f" % (points[0][0], points[0][1]))
gc.append(PENDOWN)
for point in points[1:]:
    gc.append("G01 F%6.2f X%4.2f Y%4.2f" % (FEED, point[0], point[1]))
gc.append(PENUP)
gc.append(EPILOG)


# print("(GCODE:)\n")
print("\n".join(gc))
