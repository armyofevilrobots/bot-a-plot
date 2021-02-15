import sys
import os
from io import StringIO
from collections import deque, OrderedDict

from PyQt5 import QtGui

from botaplot.models import Plottable
from botaplot.resources import resource_path
from svgelements import Group

from PyQt5.QtCore import Qt, QVariant, QPoint
from PyQt5.QtGui import QIcon, QCloseEvent, QKeySequence, QPainter, QStandardItemModel, QStandardItem, QPen
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QAction, qApp, QWidget,
                             QVBoxLayout, QCheckBox, QComboBox, QCheckBox, QFileDialog, QHBoxLayout, QDockWidget,
                             QShortcut, QTextEdit, QMenu, QLabel, QSizePolicy, QListWidget, QListView,
                             )
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from botaplot.util.svg_util import svg2lines, calculate_mm_per_unit, read_svg_in_original_dimensions
from botaplot.post.gcode_base import GCodePost
from botaplot.transports import SerialTransport, TelnetTransport
from botaplot.protocols import SimpleAsciiProtocol

class QPlottableWidget(QWidget):
    """This widget displays just the selected plottables from a dict of plottables.
    Scales to fit, no pan/zoom yet.
    """

    # def plot(self, plottable, machine):
    #     self.plottable = plottable
    #     self.machine = machine
    #     self.drawables = list()
    #     for chunk in self.plottable:
    #         line = list()
    #         if len(chunk) == 1:
    #             print("Skipping zero length line")
    #             continue
    #         line = [QPoint(point[0], point[1]) for point in chunk]
    #         self.drawables.append(line)


    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        # if not hasattr(self, 'plottable'):
        #     return

        if ProjectModel.current is None:
            return
        if getattr(self, "drawables", None) is None:
            self.drawables = list()
            if ProjectModel.current.plottables is None or len(ProjectModel.current.plottables)==0:
                return
            plottable = ProjectModel.current.plottables.get('all', [[], 0])[0]
            print("Plottable bounds are", plottable.bounds)
            inv_transform = ProjectModel.current.get_inv_transform(plottable)
            print("Inv transform is", inv_transform)
            self.pbounds = plottable.bounds
            for chunk in plottable.transform(*inv_transform):
                if len(chunk) == 1:
                    print("Skipping zero length line")
                    continue
                print("Chunk is", chunk)
                line = [QPoint(10.0*point[0], 10.0*point[1]) for point in chunk]
                print("Line is", line)
                self.drawables.append(line)
        wwidth = self.width()
        wheight = self.height()
        # xscale = wwidth / (self.pbounds[2] - self.pbounds[0])
        # yscale = wheight / (self.pbounds[3] - self.pbounds[1])
        xscale = wwidth / abs(ProjectModel.current.machine.limits[1][0]- ProjectModel.current.machine.limits[0][0])
        yscale = wheight / abs(ProjectModel.current.machine.limits[1][1]- ProjectModel.current.machine.limits[0][1])
        wscale = min(xscale, yscale)
        print("PBounds:", self.pbounds)
        print("WW,WH,XS,YX:", wwidth, wheight, xscale, yscale)

        qp = QPainter()
        qp.begin(self)
        qp.scale(wscale/10.0, wscale/10.0)
        #Machine bounds
        pen = QPen(Qt.darkRed, 10.0, Qt.DotLine)
        qp.setPen(pen)
        print("MyRect:", 0.0, 0.0, 10.0*ProjectModel.current.machine.limits[1][0], 10.0*ProjectModel.current.machine.limits[1][1])
        qp.drawRect(0.0, 0.0, 10.0*ProjectModel.current.machine.limits[1][0], 10.0*ProjectModel.current.machine.limits[1][1])
        # All those lines...
        pen = QPen(Qt.green, 10.0, Qt.SolidLine)
        qp.setPen(pen)
        for chunk in self.drawables:
            qp.drawLines(*chunk)



        qp.end()


class Machine(object):
    origin = [0.0, 0.0]
    scale = [1.0, -1.0] # units per svg mm
    limits = [[0.0, 0.0], [100.0, 100.0]]
    machine_catalog = {}
    post = GCodePost()
    transport = None

    def __init__(self, origin=None, scale=None, limits=None, post=None, transport=None):
        self.origin = origin or Machine.origin
        self.scale = scale or Machine.scale
        self.limits = limits or Machine.limits
        self.post = post or Machine.post
        self.transport = transport or SerialTransport("/dev/tty.usbmodem14322201")  # Brutal hack for now.

    def plot(self, commands):
        raise NotImplementedError("Calling plot on base Machine class")

class BotAPlot(Machine):
    """
    This is the basic botaplot machine, with M280/281 height control and
    works best at mm scale after a G28 X0 Y0.
    It's also gonna change over time.
    """

    def __init__(self, origin=None, scale=None, limits=None, post=None, transport=None):
        """Given a transport (either a serial or telnet transport), create
        a botaplot that can plot lines over serial/telnet. Expects gcode
        """
        super().__init__(origin, scale, limits, post, transport)
        self.protocol = SimpleAsciiProtocol()

    def plot(self, commands):
        """Lines just needs to be a generator that contains a list of commands.
        If you want to convert line segments to commands, you'll need to POST first
        """
        self.protocol.plot(commands.split("\n"), self.transport)
    #
    # def post(self, lines: Plottable, fp=None):
    #     if fp is None:
    #         ofp = StringIO()
    #     else:
    #         ofp = fp
    #     self.post.post_lines_to_fp(lines.transform(*transform), ofp)
    #     if fp is None:
    #         return ofp.getvalue()


Machine.machine_catalog["botaplot_v1"] = BotAPlot(limits=[[0.0, 0.0], [235.0, 254.0]])


class ProjectModel(object):
    """The main app model"""

    current = None
    # Used for undo, up to 32 layers
    history = deque(maxlen=32)
    callbacks = list()
    default_path = "/Users/derek/Downloads/Beep Logo Pack 2020-06-24/"

    def __init__(self, svg=None, svg_path=None, enabled_groups=None, post=None, machine=None):
        self.svg = svg
        self.svg_path = svg_path
        self.enabled_groups = enabled_groups or list()
        self.machine = machine or Machine.machine_catalog.get("botaplot_v1")
        self.dirty = False
        self.plottables = dict()
        self.scale = 1.0

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
        print("machine lims: ", self.machine.limits)
        print("machine scale: ", self.machine.scale)
        bot_dist = self.machine.limits[1][1] + \
                   (self.machine.scale[1] * plottable.convert_svg_units_to_mm(
                       self.svg.values.get('height', "%fin" % (self.svg.viewbox.height / 72.0))))
        return [0, bot_dist,
                self.scale, self.scale]


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
        self.layer_dock = self.setup_layer_dock()
        # self.layer_dock.setWidget(QWidget())
        # self.layer_dock.setLayout(QVBoxLayout())
        self.layer_list = QListView()
        self.layer_model = QStandardItemModel()
        self.layer_list.setModel(self.layer_model)
        self.layer_dock.setWidget(self.layer_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_dock)

        self.drawing = QPlottableWidget()
        layout.addWidget(self.drawing)
        self.central_widget.setLayout(layout)

        self.menu_bar = self.setup_menu()

        ProjectModel.watch(self.model_change)

    def setup_layer_dock(self):
        return QDockWidget("Layers/Groups", self)

    def model_change(self, evname, value=None):
        """Called by the model class when we change shit."""
        if evname == "load_from_svg":
            self.statusBar().showMessage(f"Loaded {os.path.basename(value)}")
            # for group in ProjectModel.current.svg.elements(conditional=lambda x: isinstance(x, Group)):
            #     print("Found group: ", group.values)
            self.layer_model.clear()

            print("Current plottables are", ProjectModel.current.plottables.keys())
            for layername, (el, length) in ProjectModel.current.plottables.items():
                item = QStandardItem(f"{layername}:{el.__class__.__name__} - {length} chunks")
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
                self.layer_model.appendRow(item)

            # self.drawing.plot(ProjectModel.current.plottables.get('all')[0], ProjectModel.current.machine)





    def filedialog_open_svg(self):
        options = QFileDialog.Options() | QFileDialog.DontUseNativeDialog  # noqa
        filename, _ = QFileDialog.getOpenFileName(self, "Open SVG File",
                                                  ProjectModel.default_path,
                                                  "SVG files (*.svg)",
                                                  "*.svg",
                                                  options=options)
        ProjectModel.load_from_svg(filename)


    def show_layers(self, *args):
        if self.layer_dock.isHidden():
            self.layer_dock.show()
        else:
            self.layer_dock.hide()

    def send_to_machine(self):
        gcode = ()
        ofp = StringIO()
        plottable = ProjectModel.current.plottables["all"][0]
        plottable = plottable.transform(*ProjectModel.current.get_transform(plottable))
        ProjectModel.current.machine.post.write_lines_to_fp(
            plottable, ofp)
        gcode =  ofp.getvalue()
        print("GCodce is", gcode)
        ProjectModel.current.machine.plot(gcode)


    def setup_menu(self):
        menubar = self.menuBar()
        try:
            from PyQt5.QtGui import qt_set_sequence_auto_mnemonic
            qt_set_sequence_auto_mnemonic(True)
        except ImportError:
            print("Couldn't load auto mnemonic")
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
            "&Plot": [
                ["&Plot", None, "Plot this drawing", self.send_to_machine],
                None, ],
            "&Help": [None, ],
        }


        for title, submenu_items in menu_items.items():
            submenu = menubar.addMenu(title)
            for act in submenu_items:
                print("Adding:", act)
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
    appctxt = ApplicationContext()
    window = BAPMainWindow()

    window.resize(900, 600)
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
