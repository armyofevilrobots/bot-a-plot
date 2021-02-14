import io
import tempfile
import os
import os.path

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



class SVGToolpathNode(BaseNode):

    icon="chart-scatter-plot-hexbin"

    def __init__(self, *args, **kw):
        self.title = kw.get("title", "SVG Image")
        self.actions = [[self.icon, lambda x:x]]
        super().__init__(*args, **kw)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)


# Factory.register('SVGToolpathNode', cls=SVGToolpathNode)
