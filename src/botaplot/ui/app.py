import os.path
import sys
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.config import Config
from kivy.properties import ObjectProperty, NumericProperty, StringProperty

from kivymd.app import MDApp
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.tab import MDTabsBase, MDTabsCarousel
from kivymd.material_resources import DEVICE_TYPE
from ..models.sketch_graph import SketchGraph
from ..models import *
from ..resources import resource_path
from .drawer_menu import *
from .theming import DesktopThemeClass
from .sketch_canvas import SketchLayout
from .node import DragCard
from .menu import MENU_ITEMS
Config.set('input', 'mouse', 'mouse,multitouch_on_demand,pos')


class Tab(FloatLayout, MDTabsBase):
    '''Class implementing content for a tab.'''

# Monkeypatch the tab carousel...
def on_touch_move(self, touch):
    self._change_touch_mode()
    self.touch_mode_change = True
    super(MDTabsCarousel, self).on_touch_move(touch)

MDTabsCarousel.on_touch_move = on_touch_move


class BotAPlotApp(MDApp):
    model = ObjectProperty()


    def __init__(self, *args, **kw):
        super(BotAPlotApp, self).__init__(*args, **kw)
        self.theme_cls = DesktopThemeClass()
        # Done without set_model because the layout doesn't exist yet.
        self.model = SketchGraph()

    def set_model(self, model):
        Logger.info("Loading model: %s", model)
        self.model = model
        self.root.ids.sketch_layout.center_on_content()

    def on_model(self, instance, model):
        print("Model change", instance, model)
        if self.root is not None:
            self.root.ids.sketch_layout.update(model)

    def save_model(self, *args):
        self.model.to_file()



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

        # print(self.root.ids.sketch_layout, self.root.ids.sketch_layout.children)
        # for child in self.root.ids.sketch_layout.children[::-1]:
        #     self.root.ids.sketch_layout.remove_widget(
        #         child)
        if len(sys.argv)>1 and os.path.isfile(sys.argv[1]):
            model = SketchGraph.from_file(sys.argv[1])
            self.set_model(model)





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
