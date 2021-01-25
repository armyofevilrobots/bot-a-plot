from uuid import uuid4
from kivymd.uix.card import MDCard
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty

BASE_NODE_KV = """
<BaseNode>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_timeout: 10000000
    drag_distance: 0
    width: 600
    height: component_tools.height+sum([child.height for child in component_list.children])
    BoxLayout:
        id: component_box
        size_hint: [1, 1]
        orientation: 'vertical'
        #adaptive_size: True
        adaptive_height: True
        MDToolbar:
            id: component_tools
            title: root.title
            right_action_items: root.actions
            font_size: "12sp"
        MDList:
            id: component_list
            adaptive_size: True
            size_hint: [1, 1]
"""

class DragCard(DragBehavior, MDCard):
    title = StringProperty()
    id = StringProperty()
    actions = ObjectProperty([["language-python", lambda x:x]])

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)


    def on_touch_down(self,touch):
        if not self.collide_point(*touch.pos):
            return False
        return super().on_touch_down(touch)


class BaseNode(DragCard):
    icon = StringProperty("help")
    title = StringProperty("BaseNode")
    value = ObjectProperty()  # Used by events all over the place...



class BaseSource(MDCard):
    icon = StringProperty("help")
    title = StringProperty("BaseSource")

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = kw.get("icon", "help")
        self.title = kw.get("title", "BaseSource")


class BaseSink(MDCard):
    icon = StringProperty("help")
    title = StringProperty("BaseNode")

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = kw.get("icon", "help")
        self.title = kw.get("title", "BaseSink")

Builder.load_string(BASE_NODE_KV)
Factory.register('DragCard', cls=DragCard)
Factory.register('BaseNode', cls=BaseNode)
Factory.register('BaseSource', cls=BaseSource)
Factory.register('BaseSink', cls=BaseSink)
