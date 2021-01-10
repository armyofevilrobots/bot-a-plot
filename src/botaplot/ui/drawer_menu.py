from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.navigationdrawer import (
    MDNavigationDrawer,
)
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.theming import ThemableBehavior
from kivy.properties import StringProperty

class ItemDrawer(OneLineIconListItem):
    icon = StringProperty()

class ContentNavigationDrawer(BoxLayout):
    pass

class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        '''Called when tap on a menu item.'''
        pass

        # Set the color of the icon and text for the menu item.
        # for item in self.children:
        #     if item.text_color == self.theme_cls.primary_color:
        #         item.text_color = self.theme_cls.text_color
        #         break
        # instance_item.text_color = self.theme_cls.primary_color

__all__ = ["ItemDrawer", "ContentNavigationDrawer", "DrawerList"]
