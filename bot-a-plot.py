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
from kivy.uix.behaviors import DragBehavior
from kivymd.uix.tab import MDTabsBase, MDTabsCarousel
from kivymd.uix.card import MDCard
from kivy.core.window import Window
from botaplot.resources import resource_path
from botaplot.ui.drawer_menu import *
from botaplot.ui.filechooser import LoadDialog, FileOpener
from botaplot.ui.sketch_canvas import SketchLayout
import os.path
from kivy.config import Config



class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass

# Monkeypatch the tab carousel...
def on_touch_move(self, touch):
    self._change_touch_mode()
    self.touch_mode_change = True
    super(MDTabsCarousel, self).on_touch_move(touch)

MDTabsCarousel.on_touch_move = on_touch_move

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


    def build_config(self, config):
        config.setdefaults(
            'foo', {
                'key1': 'value1',
                'key2': '42'
            })

    def build(self):
        #self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.primary_palette = "Red"
        #self.theme_cls.theme_style = "Dark"
        self.theme_cls.theme_style = "Light"
        return Builder.load_file(resource_path("kv", "botaplot.kv"))

    def on_start(self):
        Logger.info("On start")
        for item in MENU_ITEMS:
            widget = ItemDrawer(icon=item.icon, text=item.name)
            if callable(item.action):
                widget.on_release = item.action
                widget.ids.icon.on_release = item.action
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
        Logger.info("Switching to tab %s with label %s -> %s",
                    instance_tab.__dict__,
                    instance_tab_label.__dict__,
                    tab_text)



if __name__ == "__main__":
    BotAPlotApp().run()
