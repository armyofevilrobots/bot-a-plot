# This is all the available post processors

from .gcode_base import GCodePost

posts = {"bot-a-plot/smoothie": GCodePost}

__all__=["posts", "GCodePost"]
