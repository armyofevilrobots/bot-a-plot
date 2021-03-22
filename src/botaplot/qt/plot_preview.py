from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget
from botaplot.models.project_model import ProjectModel
from botaplot.models.machine import Machine, BotAPlot
from PyQt5.QtCore import Qt, QVariant, QPoint
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen, \
    QPainterPath
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

        if ProjectModel.current is None:
            return
        if getattr(self, "startpoints", None) is None:
            self.startpoints = list()
        if getattr(self, "endpoints", None) is None:
            self.endpoints = list()
        if getattr(self, "drawables", None) is None:
            self.drawables = list()
            self.startpoints = list()
            self.endpoints = list()
            if ProjectModel.current.plottables is None or len(ProjectModel.current.plottables)==0:
                return
            plottable = ProjectModel.current.plottables.get('all', [[], 0])[0]
            logger.info("We now have %d SOURCE lines" % len(plottable))
            logger.info("Plottable bounds are %s", plottable.bounds)
            inv_transform = ProjectModel.current.get_inv_transform(plottable)
            logger.info("Inv transform is %s",  inv_transform)
            self.pbounds = plottable.bounds
            self.endpoints = list()
            for chunk in plottable.transform(*inv_transform):
                if len(chunk) == 1:
                    logger.warning("Skipping zero length line")
                    continue
                # logger.debug("Chunk is %s", chunk)
                points = [QPoint(10.0*point[0], 10.0*point[1]) for point in chunk]

                # assert len(line) == len(chunk)
                # logger.debug("Line is %s", line)
                self.drawables.append(points)
                self.startpoints.append((QPoint(10.0 * chunk[0][0], 10.0 * chunk[0][1])))
                self.endpoints.append((QPoint(10.0 * chunk[-1][0], 10.0 * chunk[-1][1])))
            self.paths = list()
            for chunk in self.drawables:
                path = QPainterPath()
                path.moveTo(chunk[0])
                for point in chunk:
                    path.lineTo(point)
                # qp.drawPath(path)
                self.paths.append(path)

            logger.info("We now have %d drawable lines" % len(self.drawables))
        wwidth = self.width()
        wheight = self.height()
        xscale = wwidth / abs(ProjectModel.current.machine.limits[1][0] - ProjectModel.current.machine.limits[0][0])
        yscale = wheight / abs(ProjectModel.current.machine.limits[1][1] - ProjectModel.current.machine.limits[0][1])
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
        qp.drawRect(0.0, 0.0, 10.0 * ProjectModel.current.machine.limits[1][0], 10.0 * ProjectModel.current.machine.limits[1][1])
        pen = QPen(Qt.blue, 10.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        qp.setPen(pen)
        # All those lines...
        if getattr(self, "paths", None) is not None:
            for path in self.paths:
                qp.drawPath(path)
        # Start Points
        pen = QPen(Qt.green, 3, Qt.SolidLine)
        qp.setPen(pen)
        for point in self.startpoints:
            qp.drawPoint(point)
        # Ends
        pen = QPen(Qt.red, 2, Qt.SolidLine)
        qp.setPen(pen)
        for point in self.endpoints:
            qp.drawPoint(point)
        qp.end()



