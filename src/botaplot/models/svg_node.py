from .sketch_graph import BaseNode, BaseSource, BaseSink, register_type
from botaplot.models.controls import *
from svgpathtools import svg2paths, wsvg
import logging


@register_type
class SVGSource(BaseSource):
    parent = None

    def __init__(self, id=None):
        super().__init__(id)
        self._paths, self._attributes = None, None

    @property
    def value(self):
        try:
            self._paths, self._attributes = svg2paths(self.parent.value)
        except:
            return None, None
        return zip(self._paths, self._attributes)

    @classmethod
    def create(cls, id=None):
        return cls(id)

    # We should override onvaluechanged here so that we can handle
    # the svg file changing, or NOT changing, and have a cache.


@register_type
class SVGSink(BaseSink):
    source_type = SVGSource


@register_type
class SVGNode(BaseNode):

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        super().__init__(sources, sinks, controls, meta, id)
        self.value = ""

    @classmethod
    def create(cls, id=None):
        node = cls(id=id)
        node.controls.append(FileSelectorControl(
            value="", extension=".svg", description="SVG FILE"))
        node.controls.append(SVGPreviewControl())
        node.sources.append(SVGSource.create())
        return node

    def on_value_changed(self, source, value):
        """This is called when ANY child changes for ANY reason. By inspecting
        the 'source' field, we can determine what is changing, and how to consume
        it. For example, if a control changes, we'll get that for the source,
        and we can determine the action we take against our own value.
        ie: If an SVG file control changes in an SVG node, we can decide to
        change our internal SVG value, and update our sources.
        """
        logging.info(f"On value changed for the SVGNode {self} with value {value} via {source}")
        super().on_value_changed(source, value)
        if isinstance(source, FileSelectorControl):
            logging.info(f"Setting {self.__class__}:{self} value to {value}")
            self.value = value
        # for control in self.controls:
            # if isinstance(control, SVGPreviewControl):
            # if control
            #     control.on_value_change(source, value)


@register_type
class SVGPreviewControl(BaseControl):
    def __init__(self, value="", description="", id=None):
        super().__init__(value, description, id)

    def on_value_change(self, source, value):
        logging.info("On value change on the preview image")

@register_type
class SVGPreviewNode(BaseNode):
    """Generates a simple preview window of an SVG received on it's sink"""

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        super().__init__(sources, sinks, controls, meta, id)

    @classmethod
    def create(cls, id=None):
        node = cls(id=id)
        node.sinks.append(SVGSink.create())
        return node
