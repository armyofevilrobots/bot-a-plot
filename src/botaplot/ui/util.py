from kivy.logger import Logger
from kivymd.app import MDApp
from .filechooser import FileOpener


def load_svg():
    """Loads an SVG via dialog"""
    def success(self, filename):
        Logger.warn("OPENING SVG: %s" % filename)
        root = MDApp.get_running_app().root
        root.ids.nav_drawer.set_state("close")

    def fail(self):
        Logger.warn("Not opening due to cancel/fail")
        root = MDApp.get_running_app().root
        root.ids.nav_drawer.set_state("close")


    opener = FileOpener(success, extensions=['.svg', ])
    opener.show()
