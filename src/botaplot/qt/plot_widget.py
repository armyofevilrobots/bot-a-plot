from PyQt5.QtCore import Qt, pyqtSlot, QVariant, QPoint
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QAction, qApp, QWidget,
                             QVBoxLayout, QCheckBox, QComboBox, QCheckBox, QFileDialog, QHBoxLayout, QDockWidget,
                             QShortcut, QTextEdit, QMenu, QLabel, QSizePolicy, QListWidget, QListView, QGroupBox,
                             QProgressBar, QPushButton, QErrorMessage,
                             )
from botaplot.models import Plottable
from botaplot.resources import resource_path
from botaplot.models.layer_model import LayerModel
from botaplot.models.machine import Machine
from botaplot.transports import TelnetTransport,SerialTransport
import os
import sys
import os.path
import logging
logger = logging.getLogger(__name__)


def _guess_ttys():
    if sys.platform.startswith("darwin"):
        return ["/dev/%s" % filen for filen in os.listdir('/dev')
                if filen.startswith("tty.usb")]
    else:
        return list()



class QPlotRunWidget(QWidget):
    """Runs the plotter in a background thread."""

    def __init__(self, parent):
        super().__init__()

        # Set my layout...
        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        target_box = QGroupBox("Target Plotter")
        target_box_layout = QVBoxLayout()
        target_box.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.machine_select = QComboBox()
        for name, item in Machine.machine_catalog.items():
            self.machine_select.addItem(name, item)
            if LayerModel.current is not None and LayerModel.current.machine == item:
                logger.info("Selecting machine: %s" % name)
                self.machine_select.setCurrentIndex(self.machine_select.count()-1)
        target_box_layout.addWidget(self.machine_select)
        self.machine_select.currentIndexChanged.connect(self.on_machine_change)

        self.transport_select = QComboBox()
        self.transport_select.addItem(QIcon(resource_path("images", "baseline_usb_black_18dp.png")), "Serial", SerialTransport)
        self.transport_select.addItem(QIcon(resource_path("images", "baseline_settings_ethernet_black_18dp.png")),"Telnet", TelnetTransport)
        if LayerModel.current is not None and LayerModel.current.machine.transport is not None:
            if isinstance(LayerModel.current.machine.transport, TelnetTransport):
                self.transport_select.setCurrentIndex(1)
            else:
                self.transport_select.setCurrentIndex(0)
        target_box_layout.addWidget(self.transport_select)
        self.transport_select.currentIndexChanged.connect(self.on_transport_change)

        # Now for the ports...
        self.device_select = QComboBox()
        if LayerModel.current is not None and LayerModel.current.machine.transport is not None:
            if isinstance(LayerModel.current.machine.transport, SerialTransport):
                self._fill_serial_devices()
            else:
                self._fill_telnet_devices()
        target_box_layout.addWidget(self.device_select)
        self.device_select.currentIndexChanged.connect(self.on_device_change)

        target_box.setLayout(target_box_layout)
        v_layout.addWidget(target_box)

        # Now for the progress stuff:
        controls_group = QGroupBox("Controls")
        controls_group.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        pvlayout = QVBoxLayout()
        pvlayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        controls_group.setLayout(pvlayout)
        #Progressbar
        self.plot_progress = QProgressBar()
        pvlayout.addWidget(self.plot_progress)
        #Rewind, start/pause, Cancel
        ctl_but_group = QGroupBox()
        ctl_but_group.setAlignment(Qt.AlignHCenter)
        self.rewind_button = QPushButton(QIcon(resource_path("images", "baseline_skip_previous_black_18dp.png")),"Rew")
        self.play_button = QPushButton(QIcon(resource_path("images", "baseline_play_arrow_black_18dp.png")),"Run")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.plot_clicked)
        ctl_but_layout = QHBoxLayout()
        ctl_but_layout.addWidget(self.rewind_button)
        ctl_but_layout.addWidget(self.play_button)
        ctl_but_group.setLayout(ctl_but_layout)

        pvlayout.addWidget(ctl_but_group)
        v_layout.addWidget(controls_group)

        self.setLayout(v_layout)


    def plot_clicked(self, value=None):
        logger.info("Plot clicked with value %s", value)
        if value:
            if LayerModel.current.sender is not None and len(LayerModel.current.plottables) > 0:
                if LayerModel.current.sender.runner is None:
                    logger.info("Starting plot")
                    LayerModel.current.run_plot()
                    return True
                elif LayerModel.current.machine.protocol.paused:
                    LayerModel.current.machine.protocol.paused = False
                    return True
            else:
                logger.error("Invalid/Missing plot data.")
                error_dialog = QMessageBox()
                error_dialog.setIcon(QMessageBox.Critical)
                error_dialog.setText("Nothing to plot")
                error_dialog.setInformativeText('No sender configured. Machine not set up or no source data?')
                error_dialog.exec_()
                return False
        else:
            LayerModel.current.machine.protocol.paused = True
            return False

    def progress_callback(self, position, size, cmd):
        logger.info("Callback at %d, %d, '%s'", position, size, cmd)

    def _fill_telnet_devices(self):
        self.device_select.clear()
        self.device_select.addItem("bot-a-plot")

    def _fill_serial_devices(self):
        self.device_select.clear()
        for dev in _guess_ttys():
            logger.info("Adding device: %s", dev)
            self.device_select.addItem(dev)
            if LayerModel.current is not None and LayerModel.current.machine.transport.portname is not None:
                if LayerModel.current.machine.transport.portname == dev:
                    self.device_select.setCurrentIndex(self.device_select.count()-1)

    def on_transport_change(self, new_transport=None):
        logger.info("Changed to transport: %s", new_transport)
        if LayerModel.current:
            LayerModel.current.machine.transport = self.transport_select.currentData()(self.device_select.currentData())
            logger.info("New transport is %s" % LayerModel.current.machine.transport)

    def on_device_change(self, new_device=None):
        logger.info("Selected new target device: %s" % new_device)
        if LayerModel.current:
            LayerModel.current.machine.transport = self.transport_select.currentData()(self.device_select.currentData())
            logger.info("New transport is %s" % LayerModel.current.machine.transport)


    def on_machine_change(self, new_machine=None):
        """Called when the machine changes"""
        logger.info("Selected machine: %s", new_machine)
        logger.info("Selected machine: %s", self.machine_select.currentData())

        if LayerModel.current:
            LayerModel.current.machine = self.machine_select.currentData()
            logger.info("Selected machine has transport: %s", self.machine_select.currentData().transport)
            if isinstance(LayerModel.current.machine.transport, TelnetTransport):
                self.transport_select.setCurrentIndex(1)
            else:
                self.transport_select.setCurrentIndex(0)


