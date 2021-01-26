from kivy.logger import Logger
from kivymd.app import MDApp
from .filechooser import FileOpener
from .util import load_svg
from ..models.sketch_graph import SketchGraph

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
    model = SketchGraph()
    MDApp.get_running_app().root.ids.nav_drawer.set_state("close")
    MDApp.get_running_app().set_model(model)

def load_sketch():
    def success(self, filename):
        Logger.warn("OPENING BAP: %s" % filename)
        root = MDApp.get_running_app().root
        new_sketch()
        root.ids.nav_drawer.set_state("close")
        model = SketchGraph.from_file(filename)
        MDApp.get_running_app().set_model(model)

    def fail(self):
        Logger.warn("Not opening due to cancel/fail")
        root = MDApp.get_running_app().root
        root.ids.nav_drawer.set_state("close")

    opener = FileOpener(success, extensions=['.bap', '.botaplot'])
    opener.show()
    


# Later on, these should really get built up from some kind of plugin system
MENU_ITEMS = [
    MenuAndCallback("New Project", "folder-plus", new_sketch),
    MenuAndCallback("Open Project", "folder-open", load_sketch),
    MenuAndCallback("Import SVG", "drawing", load_svg),
    MenuAndCallback("Settings", "database-settings"),
    MenuAndCallback("Plot", "printer"),
    MenuAndCallback("Theme", "theme-light-dark", lambda: MDApp.get_running_app().toggle_dark()),
    MenuAndCallback("Quit", "exit-run", lambda: MDApp.get_running_app().stop())
]
