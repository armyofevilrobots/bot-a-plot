from .sketch_graph import BaseNode, BaseSource, BaseSink, register_type
from botaplot.models.controls import *
from svgpathtools import svg2paths, wsvg
import logging


@register_type
class SVGSource(BaseSource):
    parent = None

    def __init__(self, id=None):
        super().__init__(id)

    @classmethod
    def create(cls, id=None):
        return cls(id)

    @property
    def value(self):
        try:
            self._paths, self._attributes = svg2paths(self.parent.value)
        except:
            return None, None
        return zip(self._paths, self._attributes)

    # We should override onvaluechanged here so that we can handle
    # the svg file changing, or NOT changing, and have a cache.

@register_type
class SVGSink(BaseSink):
    source_type = SVGSource

@register_type
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


