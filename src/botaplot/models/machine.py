from botaplot.transports import SerialTransport, TelnetTransport
from botaplot.protocols import SimpleAsciiProtocol
from botaplot.post.gcode_base import GCodePost
import logging
logger = logging.getLogger(__name__)

class Machine(object):
    origin = [0.0, 0.0]
    scale = [1.0, -1.0] # units per svg mm
    limits = [[0.0, 0.0], [100.0, 100.0]]
    machine_catalog = {}
    post = GCodePost()
    transport = None

    def __init__(self, origin=None, scale=None, limits=None, post=None, transport=None, protocol=None):
        self.origin = origin or Machine.origin
        self.scale = scale or Machine.scale
        self.limits = limits or Machine.limits
        self.post = post or Machine.post
        self.transport = transport or SerialTransport("/dev/tty.usbmodem14322201")  # Brutal hack for now.
        self.protocol = protocol or SimpleAsciiProtocol()

    def plot(self, commands):
        raise NotImplementedError("Calling plot on base Machine class")

class BotAPlot(Machine):
    """
    This is the basic botaplot machine, with M280/281 height control and
    works best at mm scale after a G28 X0 Y0.
    It's also gonna change over time.
    """

    def __init__(self, origin=None, scale=None, limits=None, post=None, transport=None, protocol=None):
        """Given a transport (either a serial or telnet transport), create
        a botaplot that can plot lines over serial/telnet. Expects gcode
        """
        super().__init__(origin, scale, limits, post, transport, protocol)

    def plot(self, commands, callback=None):
        """Lines just needs to be a generator that contains a list of commands.
        If you want to convert line segments to commands, you'll need to POST first
        """
        logger.info("Sending commands [%d items] with callback: %s", len(commands), callback)
        self.protocol.plot(commands.split("\n"), self.transport, callback=callback)


Machine.machine_catalog["generic_gcode"] = Machine()
Machine.machine_catalog["botaplot_v1"] = BotAPlot(limits=[[0.0, 0.0], [235.0, 254.0]])

