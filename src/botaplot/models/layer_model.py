import logging
import os
from collections import deque, OrderedDict

from PyQt5.QtCore import pyqtSignal, QThread

from botaplot.util.svg_util import svg2lines, calculate_mm_per_unit, read_svg_in_original_dimensions
from .machine import Machine
from .plottable import Plottable
import threading
from io import StringIO

logger = logging.getLogger(__name__)

#
# class PlotThread(QThread):
#     """
#     Runs a counter thread.
#     """
#     countChanged = pyqtSignal(int, int, str)
#
#     def run(self):
#         count = 0
#         while count < TIME_LIMIT:
#             count +=1
#             time.sleep(1)
#             self.countChanged.emit(count)

class PlotSender(object):
    """slices and sends the plottables"""
    # def send_to_machine(self):
    #     gcode = ()
    #     ofp = StringIO()
    #     plottable = LayerModel.current.plottables["all"][0]
    #     plottable = plottable.transform(*LayerModel.current.get_transform(plottable))
    #     LayerModel.current.machine.post.write_lines_to_fp(
    #         plottable, ofp)
    #     gcode = ofp.getvalue()
    #     logger.debug("GCode is %s", gcode)
    #     LayerModel.current.machine.plot(gcode)
    def __init__(self):
        self.runner = None


    def plot(self, plottables=list(), callback=None):
        """Create the stuff we'll actually send"""
        ofp = StringIO()
        # plottable = LayerModel.current.plottables["all"][0]
        plottable = plottables[0]
        plottable = plottable.transform(*LayerModel.current.get_transform(plottable))
        LayerModel.current.machine.post.write_lines_to_fp(
            plottable, ofp)
        self.gcode = ofp.getvalue()
        logger.debug("GCode is %s", len(self.gcode))
        logger.debug("Callback is %s", callback)
        # TODO: Switch to https://riptutorial.com/pyqt5/example/29500/basic-pyqt-progress-bar
        # TODO: See the PlotThread class I've started above.
        self.runner = threading.Thread(target=self.plot_monitor, args=[callback, ], daemon=True)
        self.runner.start()

    def pause(self, paused=True):
        LayerModel.current.machine.protocol.paused = paused

    def plot_monitor(self, callback):
        """Background thread that watches stuff and sends plot commands"""
        sem = threading.Semaphore()

        def _safe_callback(*args, **kw):
            logger.debug("Callback: %s", args)
            with sem:
                callback(*args, **kw)

        logger.debug("The LM machine callback is %s", callback)
        LayerModel.current.machine.plot(self.gcode, callback)


class LayerModel(object):
    """The main app model"""

    current = None
    # Used for undo, up to 32 layers
    history = deque(maxlen=32)
    callbacks = list()
    default_path = "X/Users/derek/Downloads/Beep Logo Pack 2020-06-24/"
    sender = None

    def __init__(self, svg=None, svg_path=None, enabled_groups=None, post=None, machine=None):
        self.svg = svg
        self.svg_path = svg_path
        self.enabled_groups = enabled_groups or list()
        self.machine = machine or Machine.machine_catalog.get("botaplot_v1")
        self.dirty = False
        self.plottables = dict()
        self.scale = 1.0
        self.sender = PlotSender()

    @classmethod
    def watch(cls, fun):
        """Call fun whenever we change the content."""
        cls.callbacks.append(fun)

    @classmethod
    def load_from_svg(cls, path, callback=None):
        if callback is None:
            callback = lambda x: x
        svg = read_svg_in_original_dimensions(os.path.normpath(path))
        cls.current = cls(svg, path, None, None, None)
        lines = svg2lines(svg, 0.5)
        plottable = Plottable([Plottable.Line(line) for line in lines], callback=callback)
        cls.current.plottables = OrderedDict(all=(plottable, len(plottable)))
        scale = calculate_mm_per_unit(svg)  # 25.4/72.0 #plottable.calculate_dpi_via_svg(svg)
        cls.current.scale = scale

        for callback in cls.callbacks:
            callback("load_from_svg", path)

    def get_transform(self, plottable):
        bot_dist = self.machine.limits[1][1] + (self.machine.scale[1] * plottable.convert_svg_units_to_mm(
            self.svg.values.get('height', "%fin" % (self.svg.viewbox.height / 72.0))))
        # This gets passed to a plottable.transform_self instance via *args
        transform = (self.machine.scale[0] * self.scale * self.svg.viewbox.x+self.machine.limits[0][0],
                     (self.machine.scale[1]*self.scale * self.svg.viewbox.y)+self.machine.limits[1][1] - bot_dist,
                     self.machine.scale[0]* self.scale, self.machine.scale[1] * self.scale)
        return transform

    def get_inv_transform(self, plottable):
        """Used to position the drawing in screen coords correctly"""
        logger.info("machine lims: %s", self.machine.limits)
        logger.info("machine scale: %s", self.machine.scale)
        bot_dist = self.machine.limits[1][1] + \
                   (self.machine.scale[1] * plottable.convert_svg_units_to_mm(
                       self.svg.values.get('height', "%fin" % (self.svg.viewbox.height / 72.0))))
        return [0, bot_dist,
                self.scale, self.scale]

    def run_plot(self, callback=None):
        if self.sender is not None:
            self.sender.plot([self.plottables["all"][0], ], callback)  # TODO: Make this send all enabled plottables
