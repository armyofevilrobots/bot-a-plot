import logging
import coloredlogs
coloredlogs.install(level=logging.DEBUG)
logger = logging.getLogger(__name__)
import sys
import os
from io import StringIO

from PyQt5 import QtGui

from botaplot.resources import resource_path
from svgelements import Group

from PyQt5.QtCore import Qt, QVariant, QPoint
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QAction, qApp, QWidget,
                             QVBoxLayout, QCheckBox, QComboBox, QCheckBox, QFileDialog, QHBoxLayout, QDockWidget,
                             QShortcut, QTextEdit, QMenu, QLabel, QSizePolicy, QListWidget, QListView,
                             )
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from botaplot.models.layer_model import LayerModel
from botaplot.models.machine import Machine, BotAPlot
from botaplot.qt.plot_widget import QPlotRunWidget
from botaplot.qt.plot_preview import QPlotPreviewWidget


class BAPMainWindow(QMainWindow):

    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent, flags)
        appicon = QIcon(resource_path("images", "aoer_logo_min.png"))
        self.setWindowTitle("Bot-à-Plot")
        qApp.setWindowIcon(appicon)
        self.setWindowIcon(appicon)
        self.statusBar()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        layout = QHBoxLayout()

        # Layer Dock Setup
        self.layer_dock = self.setup_layer_dock()
        self.layer_list = QListView()
        self.layer_model = QStandardItemModel()
        self.layer_list.setModel(self.layer_model)
        self.layer_dock.setWidget(self.layer_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_dock)

        # Pen Dock Setup
        # self.pen_dock = QDockWidget("Pens", self)
        # self.layer_list = QListView()
        # self.layer_model = QStandardItemModel()
        # self.layer_list.setModel(self.layer_model)
        # self.pen_dock.setWidget(self.layer_list)
        # self.addDockWidget(Qt.RightDockWidgetArea, self.pen_dock)

        # Plotter Dock Setup
        self.plotter_dock = QDockWidget("Plotter", self)
        self.plotter_dock.setWidget(QPlotRunWidget(self))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plotter_dock)


        self.drawing = QPlotPreviewWidget()
        layout.addWidget(self.drawing)
        self.central_widget.setLayout(layout)

        self.menu_bar = self.setup_menu()

        LayerModel.watch(self.model_change)

    def setup_layer_dock(self):
        return QDockWidget("Layers/Groups", self)

    def model_change(self, evname, value=None):
        """Called by the model class when we change shit."""
        logger.info("Loaded new svg: %s", value)
        if evname == "load_from_svg":
            self.drawing.drawables = None
            self.statusBar().showMessage(f"Loaded {os.path.basename(value)}")
            # for group in ProjectModel.current.svg.elements(conditional=lambda x: isinstance(x, Group)):
            #     print("Found group: ", group.values)
            self.layer_model.clear()

            logger.info("Current plottables are %s", LayerModel.current.plottables.keys())
            for layername, (el, length) in LayerModel.current.plottables.items():
                item = QStandardItem(f"{layername}:{el.__class__.__name__} - {length} chunks")
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
                self.layer_model.appendRow(item)





    def filedialog_open_svg(self):
        options = QFileDialog.Options() | QFileDialog.DontUseNativeDialog  # noqa
        filename, _ = QFileDialog.getOpenFileName(self, "Open SVG File",
                                                  LayerModel.default_path,
                                                  "SVG files (*.svg)",
                                                  "*.svg",
                                                  options=options)
        LayerModel.load_from_svg(filename)


    def show_layers(self, *args):
        if self.layer_dock.isHidden():
            self.layer_dock.show()
        else:
            self.layer_dock.hide()

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


    def setup_menu(self):
        menubar = self.menuBar()
        try:
            from PyQt5.QtGui import qt_set_sequence_auto_mnemonic
            qt_set_sequence_auto_mnemonic(True)
        except ImportError:
            logger.error("Couldn't load auto mnemonic")
        menu_items = {
            "&File": [
                ["&New Project", 'Ctrl-N', 'Create new project', qApp.aboutQt],
                ["&Save Project", 'Command-S', 'Save project', qApp.aboutQt],
                None,
                ["&Open SVG", None, 'Open SVG File', self.filedialog_open_svg],
                None,
                [" &Exit",
                 'Ctrl-Q',
                 'Exit Application',
                 qApp.quit],
            ],
            "&Edit": [
                ["&Undo", None, 'Undo', qApp.aboutQt],
                None, ],
            "&View": [None,
                      ["[]&Layer drawer", None, 'Toggle Layer Drawer', self.show_layers],
                      ],
            "&Help": [None, ],
        }


        for title, submenu_items in menu_items.items():
            submenu = menubar.addMenu(title)
            for act in submenu_items:
                logger.info("Adding: %s" % act)
                if act is None:
                    submenu.addSeparator()
                else:
                    if act[0].startswith("[]"):
                        _act = QAction(QIcon(), act[0][2:], self, checkable=True, checked=(not self.layer_dock.isHidden()))
                    else:
                        _act = QAction(QIcon(), act[0], self)
                    if act[1] is not None:
                        _act.setShortcut(act[1])
                        if sys.platform.startswith('darwin') and act[3] is not None:
                            _sc = QShortcut(QKeySequence(act[1]), self)
                            _sc.activated.connect(act[3])
                    if act[2] is not None:
                        _act.setStatusTip(act[2])
                    _act.triggered.connect(act[3])
                    submenu.addAction(_act)

        menubar.show()
        return menubar


    def closeEvent(self, event: QCloseEvent) -> None:
        # reply = QMessageBox.question(self, 'Message',
        #                              "Are you sure? Changes are not saved.", QMessageBox.Yes |
        #                              QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()
        event.accept()

def run_app():
    if LayerModel.current is None:
        LayerModel.current = LayerModel()
    appctxt = ApplicationContext()
    window = BAPMainWindow()

    window.resize(900, 600)
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
