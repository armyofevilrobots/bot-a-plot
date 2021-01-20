from uuid import uuid4
from kivymd.uix.card import MDCard
from kivy.factory import Factory
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty


class DragCard(DragBehavior, MDCard):
    title = StringProperty()
    id = StringProperty()
    actions = [["language-python", lambda x:x]]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)


    def on_touch_down(self,touch):
        if not self.collide_point(*touch.pos):
            return False
        return super().on_touch_down(touch)


class BaseNode(DragCard):
    icon="language-python"
    name="Base Node"

Factory.register('DragCard', cls=DragCard)
Factory.register('BaseNode', cls=BaseNode)
