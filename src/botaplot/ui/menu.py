from kivy.factory import Factory
from kivy.logger import Logger
from kivymd.app import MDApp
from kivymd.toast import toast

from kivymd.uix.menu import MDDropdownMenu

from .filechooser import FileOpener, FileSaver
from .util import load_svg
#from ..models.sketch_graph import SketchGraph
#from ..models import *  # Make sure we've got all the models loaded
import botaplot.models as models


class MenuAndCallback(object):
    # If it's NONE it's a mistake, dict is submenu, callable is menu action
    action = None
    name = "Unknown"
    icon = "alien"

    def __init__(self, name="Unknown", icon="alien", action=None):
        if action is None:
            action = lambda: Logger.error("No action defined for %s" % name)
        self.action = action
        self.name = name
        self.icon = icon


def new_sketch():
    new_model = models.SketchGraph()
    MDApp.get_running_app().root.ids.nav_drawer.set_state("close")
    MDApp.get_running_app().set_model(new_model)


def load_sketch():
    def success(self, filename):
        Logger.warn("OPENING BAP: %s" % filename)
        root = MDApp.get_running_app().root
        new_sketch()
        root.ids.nav_drawer.set_state("close")
        model = models.SketchGraph.from_file(filename)
        MDApp.get_running_app().set_model(model)

    def fail(self):
        Logger.warn("Not opening due to cancel/fail")
        toast("No file, or invalid file selected.")
        root = MDApp.get_running_app().root
        root.ids.nav_drawer.set_state("close")

    opener = FileOpener(success, fail, extensions=['.bap', '.botaplot'])
    opener.show()

def save_sketch():
    app = MDApp.get_running_app()
    def success(self, filename):
        Logger.warn("Saving BAP: %s" % filename)
        app.root.ids.nav_drawer.set_state("close")
        if app.model is not None:
            app.model.filename = filename
            app.save_model()
        else:
            Logger.warn("Not actually saving empty file yet.")

    if app.model and app.model.filename:
        app.save_model()
    else:
        saver = FileSaver(success, extensions=['.bap', '.botaplot'])
        saver.show()
        # raise RuntimeError("Cannot save a file with no name")
        # Figure out a path.


def create_widget_menu(caller):
    menu_items = [
        {"icon": "plus", "text":"Add Node"},
        {}
    ]
    print(f"Base Node is: {models.BaseNode}")
    for name, ltype in models.lookup_types.items():
        print(f"{name}:{ltype}")
        if not issubclass(ltype, models.BaseNode):
            Logger.info(f"Skipping model {ltype}")
            continue
        print(Factory.get(name))
        widget = Factory.get(name)
        print(f"\tAdding: {name}:{ltype}")
        menu_items.append({"icon": widget.icon,
                           "text": name})

    widget = MDDropdownMenu(caller=caller,
                            items=menu_items,
                            width_mult=4)


    return widget


# Later on, these should really get built up from some kind of plugin system
MENU_DRAWER_ITEMS = [
    MenuAndCallback("New Project", "folder-plus", new_sketch),
    MenuAndCallback("Open Project", "folder-open", load_sketch),
    MenuAndCallback("Save Project", "content-save", save_sketch),
    MenuAndCallback("Import SVG", "drawing", load_svg),
    MenuAndCallback("Settings", "database-settings"),
    MenuAndCallback("Plot", "printer"),
    MenuAndCallback("Theme", "theme-light-dark", lambda: MDApp.get_running_app().toggle_dark()),
    MenuAndCallback("Quit", "exit-run", lambda: MDApp.get_running_app().stop())
]
