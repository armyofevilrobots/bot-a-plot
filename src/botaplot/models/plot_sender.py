import logging
import threading
from io import StringIO
from PyQt5.QtCore import QObject, QThread, pyqtSignal

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





class PlotSender(QObject):
    """slices and sends the plottables"""

    done = pyqtSignal()



    def __init__(self):
        self.runner = None




    def plot(self, plottables=list(), callback=None):
        from .layer_model import LayerModel  # Runtime import because of circular dependency.
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
        from .layer_model import LayerModel  # Runtime import because of circular dependency.
        LayerModel.current.machine.protocol.paused = paused

    def plot_monitor(self, callback):
        from .layer_model import LayerModel  # Runtime import because of circular dependency.
        """Background thread that watches stuff and sends plot commands"""
        sem = threading.Semaphore()

        def _safe_callback(*args, **kw):
            logger.debug("Callback: %s", args)
            with sem:
                callback(*args, **kw)

        logger.debug("The LM machine callback is %s", callback)
        LayerModel.current.machine.plot(self.gcode, callback)
