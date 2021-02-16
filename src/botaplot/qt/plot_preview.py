from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget
from botaplot.models.layer_model import LayerModel
from botaplot.models.machine import Machine, BotAPlot
from PyQt5.QtCore import Qt, QVariant, QPoint
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QAction, qApp, QWidget,
                             QVBoxLayout, QCheckBox, QComboBox, QCheckBox, QFileDialog, QHBoxLayout, QDockWidget,
                             QShortcut, QTextEdit, QMenu, QLabel, QSizePolicy, QListWidget, QListView,
                             )
import logging
logger = logging.getLogger(__name__)


class QPlotPreviewWidget(QWidget):
    """This widget displays just the selected plottables from a dict of plottables.
    Scales to fit, no pan/zoom yet.
    """

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        # if not hasattr(self, 'plottable'):
        #     return

        if LayerModel.current is None:
            return
        if getattr(self, "drawables", None) is None:
            self.drawables = list()
            if LayerModel.current.plottables is None or len(LayerModel.current.plottables)==0:
                return
            plottable = LayerModel.current.plottables.get('all', [[], 0])[0]
            logger.info("Plottable bounds are %s", plottable.bounds)
            inv_transform = LayerModel.current.get_inv_transform(plottable)
            logger.info("Inv transform is %s",  inv_transform)
            self.pbounds = plottable.bounds
            for chunk in plottable.transform(*inv_transform):
                if len(chunk) == 1:
                    logger.warning("Skipping zero length line")
                    continue
                # logger.debug("Chunk is %s", chunk)
                line = [QPoint(10.0*point[0], 10.0*point[1]) for point in chunk]
                # logger.debug("Line is %s", line)
                self.drawables.append(line)
        wwidth = self.width()
        wheight = self.height()
        xscale = wwidth / abs(LayerModel.current.machine.limits[1][0] - LayerModel.current.machine.limits[0][0])
        yscale = wheight / abs(LayerModel.current.machine.limits[1][1] - LayerModel.current.machine.limits[0][1])
        wscale = min(xscale, yscale)
        # logger.info("PBounds: %s", self.pbounds)
        # logger.info("WW,WH,XS,YX: (%5.2f, %5.2f) (%5.2f, %5.2f)", wwidth, wheight, xscale, yscale)

        qp = QPainter()
        qp.begin(self)
        qp.scale(wscale/10.0, wscale/10.0)
        #Machine bounds
        pen = QPen(Qt.darkRed, 10.0, Qt.DotLine)
        qp.setPen(pen)
        # logger.info("MyRect: (%5.2f, %5.2f) - (%5.2f, %5.2f)", 0.0, 0.0, 10.0 * LayerModel.current.machine.limits[1][0], 10.0 * LayerModel.current.machine.limits[1][1])
        qp.drawRect(0.0, 0.0, 10.0 * LayerModel.current.machine.limits[1][0], 10.0 * LayerModel.current.machine.limits[1][1])
        # All those lines...
        pen = QPen(Qt.green, 10.0, Qt.SolidLine)
        qp.setPen(pen)
        for chunk in self.drawables:
            qp.drawLines(*chunk)
        qp.end()


