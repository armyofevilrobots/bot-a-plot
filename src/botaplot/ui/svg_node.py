from kivy.logger import Logger
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.factory import Factory

from . import BaseControl
from .node import BaseNode, BaseSource, BaseSink

from cairosvg import svg2png

SVG_NODE_KV = '''

<--SVGNode>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_timeout: 10000000
    drag_distance: 0
    width: 600
    height: component_tools.height+sum([child.height for child in component_list.children])
    BoxLayout:
        id: component_box
        size_hint: [1, 1]
        orientation: 'vertical'
        adaptive_size: True
        Image:
            id: preview_widget
            size_hint: [1,1]
            keep_ratio: True
            
        MDToolbar:
            id: component_tools
            title: root.title
            right_action_items: root.actions
            font_size: "12sp"
        MDList:
            adaptive_size: True
            id: component_list
            size_hint: [1, 1]

<-SVGSource>:
    orientation: "horizontal"
    size_hint: [1,1]

    MDIcon:
        icon: root.icon
        halign: "left"
        padding: ["12dp","12dp"]
        size_hint: [None,1]
    MDLabel:
        text: root.title
        halign: "left"
        padding: ["12dp","12dp"]
        size_hint: [1,1]
    MDIconButton:
        id: source_connect
        icon: "arrow-right-bold-circle-outline"
        halign: "right"
        #padding: ["8dp","8dp"]
        size_hint: [None,1]


<-SVGSink>:
    orientation: "horizontal"
    size_hint: [1,1]

    MDIconButton:
        id: sink_connect
        icon: "arrow-right-bold-circle-outline"
        halign: "left"
        #padding: ["8dp","8dp"]
        size_hint: [None,1]
    MDIcon:
        icon: root.icon
        halign: "left"
        padding: ["12dp","12dp"]
        size_hint: [None,1]
    MDLabel:
        text: root.title
        halign: "left"
        padding: ["12dp","12dp"]
        size_hint: [1,1]

<-SVGPreviewControl>:
    orientation: "horizontal"
    size_hint: [1, None]
    adaptive_height: True
    Widget:
        size_hint: [1,None]
        height: 800
        padding: ["12dp", "12dp"]

'''

class SVGNode(BaseNode):
    value = ObjectProperty()

    def __init__(self, *args, **kw):
        self.title = kw.get("title", "SVG Image")
        self.actions = [["drawing", lambda x:x]]
        super().__init__(*args, **kw)
        self.bind(value=lambda src,val: Logger.info(f"UI_SVGNode {src},{val}"))

class SVGSource(BaseSource):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = "drawing"
        self.title = kw.get('title', "SVG Data")

class SVGSink(BaseSink):
    source = ObjectProperty()

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.icon = "drawing"
        self.title = kw.get('title', "SVG Data")

class SVGPreviewNode(BaseNode):

    def __init__(self, *args, **kw):
        self.title = kw.get("title", "SVG Image")
        self.actions = [["drawing", lambda x:x]]
        super().__init__(*args, **kw)


class SVGPreviewControl(BaseControl):
    description = StringProperty()
    extension = StringProperty()
    value = ObjectProperty()
    label_content = StringProperty()


    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

Builder.load_string(SVG_NODE_KV)
Factory.register('SVGNode', cls=SVGNode)
Factory.register('SVGSource', cls=SVGSource)
Factory.register('SVGSink', cls=SVGSink)
Factory.register('SVGPreviewNode', cls=SVGPreviewNode)
Factory.register('SVGPreviewControl', cls=SVGPreviewControl)
