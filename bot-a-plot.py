from collections import OrderedDict
from importlib import resources
from kivy.uix.screenmanager import Screen
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty, StringProperty
from kivy.logger import Logger

from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.tab import MDTabsBase
from botaplot.resources import resource_path
from botaplot.ui.drawer_menu import *
from botaplot.ui.filechooser import LoadDialog
import os.path

# from kivy.core.window import Window
# Window.size = (1920, 1080)

class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''


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

class FileOpener(EventDispatcher):
    valid = BooleanProperty(False)
    path = StringProperty("")

    def __init__(self,
                 success=None,
                 fail=None,
                 rootpath=os.path.expanduser("~"),
                 extensions=False):

        self.filemanager = MDFileManager(
            ext=extensions or list(),
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            sort_by="name",
            preview=False
        )
        self.success = success
        self.fail = fail
        self.rootpath = rootpath

    def show(self, rootpath=None):
        self.valid = False
        self.path = ""
        self.filemanager.show(self.rootpath)

    def exit_manager(self, state=None):
        Logger.info("Exiting file manager")
        self.filemanager.close()
        if self.fail is not None and not self.valid:
            self.fail(self)

    def select_path(self, path=None):
        Logger.info("Selecting path in file manager")
        self.path = path
        self.valid = (path is not None)
        self.filemanager.close()
        if self.success is not None:
            self.success(self, path)
        elif self.fail is not None:
            self.fail(self)



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


# Later on, these should really get built up from some kind of plugin system
MENU_ITEMS = [
    MenuAndCallback("New Project", "folder-plus"),
    MenuAndCallback("Open Project", "folder-open"),
    MenuAndCallback("Import SVG", "drawing", load_svg),
    MenuAndCallback("Settings", "database-settings"),
    MenuAndCallback("Plot", "printer"),
    MenuAndCallback("Quit", "exit-run", lambda: MDApp.get_running_app().stop())
]



class BotAPlotApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Red"
        #self.theme_cls.theme_style = "Dark"
        return Builder.load_file(resource_path("kv", "botaplot.kv"))

    def on_start(self):
        Logger.info("On start")
        for item in MENU_ITEMS:
            widget = ItemDrawer(icon=item.icon, text=item.name)
            if callable(item.action):
                widget.on_release = item.action
            self.root.ids.content_nav_drawer.ids.md_list.add_widget(
                widget
            )
        Logger.info("Done creating menu items.")


    def on_tab_switch(
            self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        '''Called when switching tabs.

        :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
        :param instance_tab: <__main__.Tab object>;
        :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
        :param tab_text: text or name icon of tab;
        '''
        #count_icon = [k for k, v in md_icons.items() if v == tab_text]
        #instance_tab.ids.icon.icon = count_icon[0]
        Logger.info("Switching to tab %s with label %s -> %s",
                    instance_tab.__dict__,
                    instance_tab_label.__dict__,
                    tab_text)
        # if tab_text == "Canvas":
        #     self.root.ids.app_pages.page=0
        # elif tab_text == "Layers":
        #     self.root.ids.app_pages.page=1
        # elif tab_text == "Plotter":
        #     self.root.ids.app_pages.page=2



if __name__ == "__main__":
    BotAPlotApp().run()
