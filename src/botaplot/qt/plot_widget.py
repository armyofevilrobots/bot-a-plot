from queue import Queue

from PyQt5.QtCore import Qt, pyqtSlot, QVariant, QPoint, QObject, pyqtSignal, QThread, QRunnable, QThreadPool
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QAction, qApp, QWidget,
                             QVBoxLayout, QCheckBox, QComboBox, QCheckBox, QFileDialog, QHBoxLayout, QDockWidget,
                             QShortcut, QTextEdit, QMenu, QLabel, QSizePolicy, QListWidget, QListView, QGroupBox,
                             QProgressBar, QPushButton, QErrorMessage, QGridLayout,
                             QLineEdit, QSpinBox)
from botaplot.models import Plottable
from botaplot.models.plot_sender import PlotWorker, PlotWorkerState
from botaplot.qt.plot_monitor import QPostProcessRunnable, QPlotMonitor
from botaplot.resources import resource_path
from botaplot.models.project_model import ProjectModel
from botaplot.models.machine import Machine
from botaplot.transports import TelnetTransport, SerialTransport
import json
import os
import sys
import os.path
import logging
import time
import uuid
from io import StringIO
from serial.tools import list_ports
logger = logging.getLogger(__name__)


def _guess_ttys():
    results = list()
    for port in list_ports.comports():
        device = port.device
        name = port.name
        if port.description and port.description.lower() not in ['n/a', ]:
            name = port.description  # Better
        results.append((device, name))

    results.sort(key=lambda x: "smoothie" in x[1].lower(), reverse=True)
    return results







class QPlotRunWidget(QWidget):
    """Runs the plotter in a background thread."""

    def __init__(self, parent):
        super().__init__()

        # Set my layout...
        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.target_box = QGroupBox("Target Plotter")
        target_box_layout = QVBoxLayout()
        self.target_box.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.machine_select = QComboBox()
        for name, item in Machine.machine_catalog.items():
            self.machine_select.addItem(name, item)
            if ProjectModel.current is not None and ProjectModel.current.machine == item:
                logger.info("Selecting machine: %s" % name)
                self.machine_select.setCurrentIndex(self.machine_select.count()-1)
        target_box_layout.addWidget(self.machine_select)
        self.machine_select.currentIndexChanged.connect(self.on_machine_change)

        self.transport_select = QComboBox()
        self.transport_select.addItem(QIcon(resource_path("images", "baseline_usb_black_18dp.png")), "Serial", SerialTransport)
        self.transport_select.addItem(QIcon(resource_path("images", "baseline_settings_ethernet_black_18dp.png")),"Telnet", TelnetTransport)
        if ProjectModel.current is not None and ProjectModel.current.machine.transport is not None:
            if isinstance(ProjectModel.current.machine.transport, TelnetTransport):
                self.transport_select.setCurrentIndex(1)
            else:
                self.transport_select.setCurrentIndex(0)
        target_box_layout.addWidget(self.transport_select)
        self.transport_select.currentIndexChanged.connect(self.on_transport_change)

        # Now for the ports...
        self.device_select = QComboBox()
        self.transport_combo_changed()
        self.device_select.setEditable(True)
        target_box_layout.addWidget(self.device_select)
        self.device_select.currentIndexChanged.connect(self.on_device_change)

        self.target_box.setLayout(target_box_layout)
        v_layout.addWidget(self.target_box)

        # Now for the progress stuff:
        controls_group = QGroupBox("Controls")
        controls_group.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        pvlayout = QVBoxLayout()
        pvlayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        controls_group.setLayout(pvlayout)

        #Progressbar
        self.plot_progress = QProgressBar()
        self.plot_progress.setRange(0, 100)
        pvlayout.addWidget(self.plot_progress)
        # Message/last GCode|HPGL command
        self.plot_msg = QLineEdit(self)
        self.plot_msg.setText("Messages...")
        self.plot_msg.setEnabled(False)
        pvlayout.addWidget(self.plot_msg)

        #Rewind, start/pause, Cancel
        ctl_but_group = QGroupBox()
        ctl_but_group.setAlignment(Qt.AlignHCenter)
        self.rewind_button = QPushButton(QIcon(resource_path("images", "baseline_skip_previous_black_18dp.png")),"Reset")
        self.rewind_button.clicked.connect(self.cancel_clicked)
        self.play_button = QPushButton(QIcon(resource_path("images", "baseline_play_arrow_black_18dp.png")),"Run")
        self.play_button.setCheckable(True)
        self.play_button.clicked.connect(self.plot_clicked)
        ctl_but_layout = QHBoxLayout()
        ctl_but_layout.addWidget(self.rewind_button)
        ctl_but_layout.addWidget(self.play_button)
        ctl_but_group.setLayout(ctl_but_layout)

        #UpUpDownDownLeftRightLeftRight_B_A_START
        self.mv_but_group = QGroupBox("Manual Control")
        mv_but_layout = QGridLayout()
        self.mv_but_group.setAlignment(Qt.AlignHCenter)
        self.move_size_box = QComboBox()
        self.move_size_box.addItem("1mm", 1)
        self.move_size_box.addItem("5mm", 5)
        self.move_size_box.addItem("10mm", 10)
        self.move_size_box.addItem("25mm", 25)
        self.move_size_box.addItem("100mm", 100)
        self.mv_home_button = QPushButton(
            QIcon(resource_path("images", "baseline_home_black_18dp.png")), "Home")
        self.mv_home_button.clicked.connect(self._home)
        self.mv_back_button = QPushButton(
            QIcon(resource_path("images", "baseline_north_west_black_18dp.png")), "Back")
        self.mv_pen_up_button = QPushButton(
            QIcon(resource_path("images", "pen_up_black_18dp.png")), "Pen Up")
        self.mv_pen_up_button.clicked.connect(self._penup)
        self.mv_pen_down_button = QPushButton(
            QIcon(resource_path("images", "pen_down_black_18dp.png")), "Pen Down")
        self.mv_pen_down_button.clicked.connect(self._pendown)
        self.mv_up_button = QPushButton(
            QIcon(resource_path("images", "baseline_keyboard_arrow_up_black_18dp.png")), "Up")
        self.mv_up_button.clicked.connect(lambda: self._move(0, 1))
        self.mv_down_button = QPushButton(
            QIcon(resource_path("images", "baseline_keyboard_arrow_down_black_18dp.png")), "Down")
        self.mv_down_button.clicked.connect(lambda: self._move(0, -1))
        self.mv_left_button = QPushButton(
            QIcon(resource_path("images", "baseline_keyboard_arrow_left_black_18dp.png")), "Left")
        self.mv_left_button.clicked.connect(lambda: self._move(-1, 0))
        self.mv_right_button = QPushButton(
            QIcon(resource_path("images", "baseline_keyboard_arrow_right_black_18dp.png")), "Right")
        self.mv_right_button.clicked.connect(lambda: self._move(1, 0))
        self.mv_set_origin_button = QPushButton(
            QIcon(resource_path("images", "baseline_center_focus_strong_black_18dp.png")), "Set Origin")
        mv_but_layout.addWidget(self.move_size_box, 0, 0)
        mv_but_layout.addWidget(self.mv_up_button, 0, 1)
        mv_but_layout.addWidget(self.mv_down_button, 2, 1)
        mv_but_layout.addWidget(self.mv_pen_up_button, 0, 2)
        mv_but_layout.addWidget(self.mv_pen_down_button, 2, 2)
        mv_but_layout.addWidget(self.mv_left_button, 1, 0)
        mv_but_layout.addWidget(self.mv_right_button, 1, 2)
        mv_but_layout.addWidget(self.mv_home_button, 2, 0)
        mv_but_layout.addWidget(self.mv_set_origin_button, 1, 1)
        self.mv_but_group.setLayout(mv_but_layout)

        pvlayout.addWidget(ctl_but_group)
        v_layout.addWidget(controls_group)
        v_layout.addWidget(self.mv_but_group)

        self.setLayout(v_layout)

    def _send_cmd(self, cmd):
        id = str(uuid.uuid1())
        cmd_out = f"CMD[{id}]:{cmd}"
        ProjectModel.current.plot_worker.send(cmd_out)
        result = ProjectModel.current.plot_worker.parse_result(
            ProjectModel.current.plot_worker.recv(True))
        if result['status'].upper() != 'OK' or result['id'] != id:
            logger.error("Got result '%s' for home command(s)", result)
            # raise RuntimeError(f"Invalid result: {str(result)} for home command.")
            self.plot_msg.setText(
                json.loads(
                    result.get('content', {})).get('error', "Unknown error"))

    def _cancel(self):
        if not hasattr(self, 'monitor'):
            return False
        id = self.monitor.event_id
        cmd_out = f"CANCEL[{id}]"
        ProjectModel.current.plot_worker.cancel_job=True  # Tell it to die
        ProjectModel.current.machine.protocol.paused=False  # Needs to be awake to die
        # ProjectModel.current.plot_worker.send(cmd_out)

    def _home(self):
        cmd = json.dumps(ProjectModel.current.machine.post.util_home())
        self._send_cmd(cmd)

    def _penup(self):
        cmd = json.dumps(ProjectModel.current.machine.post.util_pen(True))
        self._send_cmd(cmd)

    def _pendown(self):
        cmd = json.dumps(ProjectModel.current.machine.post.util_pen(False))
        self._send_cmd(cmd)

    def _move(self, x, y):
        distance = int(self.move_size_box.currentText()[:-2])  # remove mm suffix
        cmd = json.dumps(ProjectModel.current.machine.post.util_move(
            x * distance, y * distance))
        logger.info("Move command is %s", cmd)
        self._send_cmd(cmd)

    def _plot(self):
        logger.info("Starting plot")
        self.target_box.setDisabled(True)
        self.mv_but_group.setDisabled(True)
        self.plot_msg.setText("Post Processor dispatching.")
        # First we slice it up/post it
        post = QPostProcessRunnable([ProjectModel.current.plottables["all"][0], ])
        pool = QThreadPool.globalInstance()

        def run_plot(finished):
            load_id = str(uuid.uuid1())
            logger.info("Finished: %s", finished)
            ProjectModel.current.plot_worker.send(
                f"LOAD[{load_id}]:{post.gcode}")
            result = PlotWorker.parse_result(ProjectModel.current.plot_worker.recv(True))
            logger.info("Result is: %s", result)
            if result['id'] != load_id:
                raise RuntimeError("Mismatched command IDs on GCODE LOAD")
            plot_id = str(uuid.uuid1())
            ProjectModel.current.plot_worker.send(
                f"START[{plot_id}]")
            # This would block, actually, if we waited for a response.

            self.monitor = QPlotMonitor(plot_id, ProjectModel.current.plot_worker)
            self.monitor_thread = QThread()
            self.monitor.moveToThread(self.monitor_thread)
            self.monitor_thread.started.connect(self.monitor.run)
            self.monitor_thread.finished.connect(self.plot_complete)
            self.monitor.progress_signal.connect(self.progress_callback)
            self.monitor.done_signal.connect(lambda x: self.monitor_thread.quit())
            logger.info("Starting monitor thread.")
            self.monitor_thread.start()

        post.finished.finished.connect(run_plot)
        pool.start(post)
        return True

    def plot_clicked(self, value=None):
        logger.info("Plot clicked with value %s", value)
        if self.play_button.isChecked():  # It JUST got checked when it was clicked.
            logger.info("The button is DOWN")
            if (ProjectModel.current.plot_worker is not None
                    and len(ProjectModel.current.plottables) > 0):
                logger.info("We have a project with valid plottables")
                logger.info("Current state: %s:%s",
                            type(ProjectModel.current.plot_worker.state),
                            ProjectModel.current.plot_worker.state)
                # if ProjectModel.current.plot_worker.runner is None:
                if ProjectModel.current.plot_worker.state is PlotWorkerState.READY:
                    return self._plot()
                elif ProjectModel.current.machine.protocol.paused:
                    logger.info("Paused?!")
                    ProjectModel.current.machine.protocol.paused = False
                    # self.play_button.setChecked(True)
                    return True
                else:
                    logger.info("Not plotting. Current state: %s", ProjectModel.current.plot_worker.state)
            else:
                logger.error("Invalid/Missing plot data.")
                error_dialog = QMessageBox()
                error_dialog.setIcon(QMessageBox.Critical)
                error_dialog.setText("Nothing to plot")
                error_dialog.setInformativeText('No sender configured. Machine not set up or no source data?')
                error_dialog.exec_()
                self.play_button.setChecked(False)
                return False
        else:
            ProjectModel.current.machine.protocol.paused = True
            self.play_button.setChecked(False)
            return True

    def cancel_clicked(self, *args, **kw):
        logger.info("Cancel clicked")
        if self.play_button.isChecked():
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText("Cannot Cancel")
            error_dialog.setInformativeText('Cannot cancel unless paused.')
            error_dialog.exec_()
            return False
        logger.info("Checking if we can cancel.")
        if ProjectModel.current.plot_worker is not None:
            logger.info("Cancel sending")
            self._cancel()

    def plot_complete(self, *args, **kw):
        """Called when the plot monitor is done."""
        logger.info("Plot monitor is done.")
        self.target_box.setDisabled(False)
        self.mv_but_group.setDisabled(False)
        self.play_button.setChecked(False)
        # self.plot_msg.setText("Plot complete")

    def progress_callback(self, position, size, cmd):
        # logger.info("Callback at %d, %d, '%s'", position, size, cmd)
        self.plot_progress.setValue(round(100*(position/size)))
        self.plot_msg.setText(cmd)

    def transport_combo_changed(self):
        # if ProjectModel.current is not None and ProjectModel.current.machine.transport is not None:
        if self.transport_select.currentData() == SerialTransport:
            self._fill_serial_devices()
        elif self.transport_select.currentData() == TelnetTransport:
            self._fill_telnet_devices()
        else:
            logger.error("Unexpected transport named: %s", self.transport_select.currentData())



    def _fill_telnet_devices(self):
        self.device_select.clear()
        self.device_select.addItem("bot-a-plot", "bot-a-plot")

    def _fill_serial_devices(self):
        self.device_select.clear()
        for dev, name in _guess_ttys():
            logger.info("Adding device: %s", dev)
            self.device_select.addItem(name, dev)
            if ProjectModel.current is not None \
                    and ProjectModel.current.machine.transport is not None \
                    and ProjectModel.current.machine.transport.portname is not None:
                if ProjectModel.current.machine.transport.portname == dev:
                    self.device_select.setCurrentIndex(self.device_select.count()-1)

    def on_transport_change(self, new_transport=None):
        logger.info("Changed to transport: %s", new_transport)
        self.transport_combo_changed()
        if ProjectModel.current:
            logger.info("switching to transport type: %s", self.transport_select.currentData())
            ProjectModel.current.machine.transport = self.transport_select.currentData()(self.device_select.currentData())
            logger.info("Current transport now: %s" % ProjectModel.current.machine.transport)
            logger.info("New transport is %s" % ProjectModel.current.machine.transport)

    def on_device_change(self, new_device=None):
        logger.info("Selected new target device: %s" % new_device)
        if ProjectModel.current:
            if self.device_select.currentData() is not None:
                logger.info("CurrentData is %s of type %s",
                            self.device_select.currentData(),
                            type(self.device_select.currentData()))
                device = self.device_select.currentData()
            elif self.device_select.currentText():
                # Try to determine the device via the manually entered text.
                logger.info("Getting device from currentText %s", self.device_select.currentText())
                device = self.device_select.currentText()
                logger.info("Falling back to the manually entered device: %s", device)
            else:
                logger.error("No valid device descriptor available. Current text is: %s",
                             self.device_select.currentText())
                device = None

            ProjectModel.current.machine.transport = self.transport_select.currentData()(device)
            logger.info("New transport is %s" % ProjectModel.current.machine.transport)
        else:
            logger.error("No current model?! This should never happen.")


    def on_machine_change(self, new_machine=None):
        """Called when the machine changes"""
        logger.info("Selected machine: %s", new_machine)
        logger.info("Selected machine: %s", self.machine_select.currentData())

        if ProjectModel.current:
            ProjectModel.current.machine = self.machine_select.currentData()
            logger.info("Selected machine has transport: %s", self.machine_select.currentData().transport)
            if isinstance(ProjectModel.current.machine.transport, TelnetTransport):
                self.transport_select.setCurrentIndex(1)
            else:
                self.transport_select.setCurrentIndex(0)


