from uuid import uuid4
from kivy.logger import Logger
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast

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
            
<-BaseSink>:
    orientation: "horizontal"
    size_hint: [1,1]

    MDIconButton:
        id: sink_connect
        icon: "arrow-right-bold-circle-outline"
        halign: "left"
        #padding: ["8dp","8dp"]
        size_hint: [None,1]
        on_press: root.do_sink_button_menu()
    MDLabel:
        text: root.title
        halign: "left"
        padding: ["12dp","12dp"]
        size_hint: [1,1]
    MDIcon:
        icon: root.icon
        halign: "right"
        padding: ["12dp","12dp"]
        size_hint: [None,1]
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

# class LongPressIconButton(MDIconButton):
#     """Special icon button that handles long press (3 second) events.
#     Used for deleting the sink connection edges that have already
#     been established.
#       NOTE: THIS DOESN'T SEEM TO WORK IN A SCATTER LAYOUT!!!
#     """
#     def __init__(self, *args, **kw):
#         super().__init__(*args, **kw)
#         self.register_event_type('on_long_press')
#
#
#     long_press_time = NumericProperty(3)
#
#     def on_state(self, instance, value):
#         if value == 'down':
#             Logger.info("Starting long press")
#             lpt = self.long_press_time
#             self._long_clicked_ev = Clock.schedule_once(self._do_long_press, lpt)
#         else:
#             Logger.info("Cancelling long press")
#             self._long_clicked_ev.cancel()
#
#     def _do_long_press(self, dt):
#         self.dispatch('on_long_press')
#
#     def on_long_press(self, dt):
#         Logger.info("Dispatching long press")
#         self.dispatch('on_long_press')




class BaseNode(DragCard):
    icon = StringProperty("help")
    title = StringProperty("BaseNode")
    value = ObjectProperty()  # Used by events all over the place...



class BaseSource(MDCard):
    icon = StringProperty("help")
    title = StringProperty("BaseSource")
    model = ObjectProperty(None)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = kw.get("icon", "help")
        self.title = kw.get("title", "BaseSource")


class BaseSink(MDCard):
    icon = StringProperty("help")
    title = StringProperty("BaseNode")
    model = ObjectProperty(None)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = kw.get("icon", "help")
        self.title = kw.get("title", "BaseSink")
        menu_items = [
            {
                "icon": "close",
                "text": "Break Connection",
            }
        ]
        self.menu_disconnect = MDDropdownMenu(
            caller=self.ids.sink_connect,
            items=menu_items,
            width_mult=4,
        )
        self.menu_disconnect.bind(on_release=self.handle_sink_menu)

    def handle_sink_menu(self, menu, item):
        Logger.info(f"Menu was clicked with {menu},{item}")
        self.menu_disconnect.dismiss()
        if menu == self.menu_disconnect and item.text == 'Break Connection':
            self.model.source = None

    def do_sink_button_menu(self, *args, **kw):
        if self.model.source is None:
            Logger.info("Disabling menu because we're already disconnected")
            toast("Nothing to disconnect!")
        else:
            self.menu_disconnect.open()




Builder.load_string(BASE_NODE_KV)
Factory.register('DragCard', cls=DragCard)
Factory.register('BaseNode', cls=BaseNode)
Factory.register('BaseSource', cls=BaseSource)
Factory.register('BaseSink', cls=BaseSink)
