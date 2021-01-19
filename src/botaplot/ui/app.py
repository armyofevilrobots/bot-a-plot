from kivy.lang import Builder
from kivy.logger import Logger

from kivymd.app import MDApp
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.tab import MDTabsBase, MDTabsCarousel
from kivymd.material_resources import DEVICE_TYPE
from ..resources import resource_path
from .drawer_menu import *
from .filechooser import FileOpener
from .theming import DesktopThemeClass
from .sketch_canvas import SketchLayout
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''

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
    MenuAndCallback("Theme", "theme-light-dark", lambda: MDApp.get_running_app().toggle_dark()),
    MenuAndCallback("Quit", "exit-run", lambda: MDApp.get_running_app().stop())
]

class BotAPlotApp(MDApp):

    

    def __init__(self, *args, **kw):
        super(BotAPlotApp, self).__init__(*args, **kw)
        self.theme_cls = DesktopThemeClass()
        # self.theme_cls.

    def build_config(self, config):
        config.setdefaults(
            'foo', {
                'key1': 'value1',
                'key2': '42'
            })

    def toggle_dark(self):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.theme_style = "Dark"


    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.primary_hue = "700"

        if DEVICE_TYPE != "mobile":
            for key, val in {
                    "H1": ["RobotoLight", 76, False, -1.5],
                    "H2": ["RobotoLight", 50, False, -0.5],
                    "H3": ["Roboto", 40, False, 0],
                    "H4": ["Roboto", 30, False, 0.25],
                    "H5": ["Roboto", 20, False, 0],
                    "H6": ["RobotoMedium", 16, False, 0.15],
                    "Subtitle1": ["Roboto", 12, False, 0.15],
                    "Subtitle2": ["RobotoMedium", 11, False, 0.1],
                    "Body1": ["Roboto", 12, False, 0.5],
                    "Body2": ["Roboto", 11, False, 0.25],
                    "Button": ["RobotoMedium", 11, True, 1.25],
                    "Caption": ["Roboto", 10, False, 0.4],
                    "Overline": ["Roboto", 9, True, 1.5],
                    "Icon": ["Icons", 20, False, 0],
            }.items():
                self.theme_cls.font_styles[key] = val
            # Hammering standard increment is _gross_, but straightforward:


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
