import io

from kivy.logger import Logger
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image

from . import BaseControl
from .node import BaseNode, BaseSource, BaseSink
from ..resources import resource_path

import cairosvg

SVG_NODE_KV = '''

# <--SVGNode>:
#     drag_rectangle: self.x, self.y, self.width, self.height
#     drag_timeout: 10000000
#     drag_distance: 0
#     width: 600
#     height: component_tools.height+sum([child.height for child in component_list.children])
#     MDBoxLayout:
#         id: component_box
#         size_hint: [1, None]
#         orientation: 'vertical'
#         MDToolbar:
#             id: component_tools
#             title: root.title
#             right_action_items: root.actions
#             font_size: "12sp"
#         MDList:
#             id: component_list
#             size_hint: [1, 1]

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

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.title = kw.get("title", "SVG Image")
        self.actions = [["drawing", lambda x:x]]
        print(self.ids.component_list)
        self.preview_img = Image(
            source=resource_path("images", "no_such_image.png"),
            size_hint = [None, None],
            # height=550,
            # size_hint=[1, None],
            # center=[0.5, 0.5]
            )
        self.ids.component_list.add_widget(self.preview_img)
        self.bind(value=self.update_preview)



    def update_preview(self, src, val):
        for child in self.ids.component_list.children:
            print(child, child.height)
        Logger.info(f"UI_SVGNode on value change {src},{val}")
        png_img =cairosvg.svg2png(url=self.value)
        texture = CoreImage(io.BytesIO(png_img), ext="png").texture
        self.preview_img.texture = texture
        if self.preview_img.width<500:
            self.preview_img.width = 500
        self.preview_img.height = self.preview_img.width
        self.height = self.ids.component_tools.height+sum([child.height for child in self.ids.component_list.children])
        self.do_layout()




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
