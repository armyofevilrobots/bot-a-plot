from .sketch_graph import BaseNode, BaseSource
from botaplot.models.controls import *
from svgpathtools import svg2paths, wsvg
import logging


class SVGSource(BaseSource):
    def __init__(self, parent, id=None):
        super().__init__(parent, id)

    @classmethod
    def create(cls, parent, id=None):
        return cls(parent, id)

    @property
    def value(self):
        try:
            self._paths, self._attributes = svg2paths(self.parent.value)
        except:
            return None, None
        return zip(self._paths, self._attributes)

    # We should override onvaluechanged here so that we can handle
    # the svg file changing, or NOT changing, and have a cache.


class SVGNode(BaseNode):

    # Reserved for caching
    _paths = None
    _attributes = None

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        super().__init__(sources, sinks, controls, meta, id)

    @classmethod
    def create(cls, id=None):
        node = super().create(id=id)
        node.controls.append(FileSelectorControl(
            value="", extension="svg", description="SVG FILE"))
        node.sources.append(SVGSource.create(node))


