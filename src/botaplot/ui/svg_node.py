from kivy.logger import Logger
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.factory import Factory
from .node import BaseNode, BaseSource, BaseSink

SVG_NODE_KV = '''


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


'''

class SVGNode(BaseNode):

    def __init__(self, *args, **kw):
        self.title = kw.get("title", "SVG Image")
        self.actions = [["drawing", lambda x:x]]
        super().__init__(*args, **kw)

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

Builder.load_string(SVG_NODE_KV)
Factory.register('SVGNode', cls=SVGNode)
Factory.register('SVGSource', cls=SVGSource)
Factory.register('SVGSink', cls=SVGSink)
