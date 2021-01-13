import numpy as np
import matplotlib
matplotlib.use('macOSX')
import json
from penkit.fractal import hilbert_curve, flowsnake
from penkit.textures import make_lines_texture, make_grid_texture, make_spiral_texture
from penkit.textures.util import fit_texture, rotate_texture
from penkit.surfaces import make_noise_surface
from penkit.projection import project_and_occlude_texture, project_texture_on_surface
from penkit.write import write_plot
from botaplot.util.util import (clamp_coords, valid_point, optimize_lines, distance,
                                split_lines_at_discontinuities, plot_to_lines)
from botaplot.util.gcode import GCodePost


# create a texture
# texture = hilbert_curve(7)
# texture  = make_spiral_texture(spirals=15)
# texture = flowsnake(4, 3)
texture = make_lines_texture(30, 250)
# texture = make_grid_texture(60, 60, 100)

# rotate the texture
texture = rotate_texture(texture, 10)
texture = fit_texture(texture)

# create the surface
surface = make_noise_surface(dims=(2048, 2048),
                             blur=90,
                             seed=1336) * 10 + 15.0

# project the texture onto the surface
proj = project_and_occlude_texture(texture, surface, 50)
write_plot([proj], 'project_lines.svg')

lines = plot_to_lines(proj)

post = GCodePost()
post.feedrate = 40*60
post.post_lines_to_file(lines, "project_lines.gcode")

