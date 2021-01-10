from botaplot.post.gcode_base import GCodePost
from ..transports import *
from ..protocols import *
from ..models.plottable import Plottable
from io import StringIO


class BotAPlot(object):
    """
    This is the basic botaplot machine, with M280/281 height control and
    works best at mm scale after a G28 X0 Y0.
    It's also gonna change over time.
    """

    def __init__(self, transport, post=None):
        """Given a transport (either a serial or telnet transport), create
        a botaplot that can plot lines over serial/telnet. Expects gcode
        """
        if post is None:
            post = GCodePost()
        self.post = post
        self.transport = transport
        self.protocol = SimpleAsciiProtocol()

    def plot(self, commands):
        """Lines just needs to be a generator that contains a list of commands.
        If you want to convert line segments to commands, you'll need to POST first
        """
        self.protocol.plot(commands, self.transport)

    def post(self, lines: Plottable, fp=None):
        if fp is None:
            ofp = StringIO()
        else:
            ofp = fp
        self.post.post_lines_to_fp(lines, ofp)
        if fp is None:
            return ofp.getvalue()
