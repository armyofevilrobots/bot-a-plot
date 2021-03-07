from PyQt5.QtCore import (Qt, pyqtSlot, QVariant, QPoint,
                          QObject, pyqtSignal, QThread, QRunnable,)
import logging
import time
from io import StringIO
logger = logging.getLogger(__name__)
from botaplot.models.plot_sender import PlotWorker, PlotWorkerState
from botaplot.models.project_model import ProjectModel


class QPlotMonitor(QObject):
    """Just watches progress and machine state, and updates the UI."""
    progress_signal = pyqtSignal(int, int, str)
    done_signal = pyqtSignal(bool)

    def __init__(self, event_id:str, plot_worker:PlotWorker):
        super().__init__()
        self.plot_worker = plot_worker
        self.event_id = event_id
        self.die = False
        # self.notifier = plot_worker.progress_notify
        # self.queue = plot_worker.progress_q

    def run(self):
        logger.info("Plot monitor started.")
        self.plot_worker.progress_q.put([1,1,"Ready"])
        logger.info("PROGRESS QUEUE: %s", self.plot_worker.progress_q)
        while not self.die:
            while not self.plot_worker.progress_q.empty():
                logger.info("Got an update...")
                progress = self.plot_worker.progress_q.get()
                logger.info("WAS: %s", progress)
                # DO SOME NOTIFY MAGIC...
                logger.info("Emitting: %s" % progress)
                self.progress_signal.emit(*progress)
                logger.info("Emitted")
            time.sleep(0.1)  # TODO: Fix this with a better method
            if self.plot_worker.dead:
                break
            if (not self.plot_worker.outq.empty()
                    and self.plot_worker.state is not PlotWorkerState.PAUSED):
                logger.info("Got a state in the result loop.")
                result = PlotWorker.parse_result(self.plot_worker.recv(True))
                logger.info("Got a final response of: %s", result)
                if result['id'] == self.event_id:
                    # logger.info("That's a match for my expected id: %s", self.event_id)
                    self.die = True
                    if result['status'] == "ERR":
                        self.progress_signal.emit(99, 100, "ERROR")
                    if result['status'] == 'FATAL':
                        self.progress_signal.emit(99, 100, "FATAL: RESTART PLOTTER")
                    else:
                        self.progress_signal.emit(100, 100, "DONE")
                    self.done_signal.emit(True)
                    return
                else:
                    self.done_signal.emit(True)
                    logger.error("Mismatched IDs. Got %s expected %s", result['id'], self.event_id)
                    return




class QPostProcessComplete(QObject):
    finished = pyqtSignal(bool)

class QPostProcessRunnable(QRunnable):
    """Slices up a single thing for plotting"""
    def __init__(self, plottables=None):
        super(QPostProcessRunnable, self).__init__()
        self.finished = QPostProcessComplete()
        self.plottables = plottables or list()

    def run(self):
        ofp = StringIO()
        # plottable = LayerModel.current.plottables["all"][0]
        plottable = self.plottables[0]  # TODO: This should plot EVERYTHING
        plottable = plottable.transform(*ProjectModel.current.get_transform(plottable))
        ProjectModel.current.machine.post.write_lines_to_fp(
            plottable, ofp)
        self.gcode = ofp.getvalue()
        self.finished.finished.emit(True)
