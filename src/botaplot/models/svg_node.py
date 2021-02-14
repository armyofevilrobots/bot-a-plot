from .sketch_graph import BaseNode, BaseSource, BaseSink, register_type
from botaplot.models.controls import *
# from svgpathtools import svg2paths, wsvg
import logging
from svgelements import SVG
from ..util.svg_util import read_svg_in_original_dimensions


@register_type
class SVGSource(BaseSource):
    parent = None

    def __init__(self, id=None):
        super().__init__(id)
        # self._paths, self._attributes = None, None
        self._svg = None

    @property
    def value(self):
        try:
            # self._paths, self._attributes = svg2paths(self.parent.value)
            self._svg = svg2paths(self.parent.value)
        except:
            self._svg = None
            return None
        # return zip(self._paths, self._attributes)
        return self._svg

    @classmethod
    def create(cls, id=None):
        return cls(id)

    # We should override onvaluechanged here so that we can handle
    # the svg file changing, or NOT changing, and have a cache.
    def on_value_changed(self, source, new_value):
        if isinstance(source, SVGNode):
            logging.info(f"Updating value from SVG Source {self} to {new_value.__class__}")
            logging.info(f"Outgoing value is {self.value}")
            for sink in self.sinks:
                logging.info(f"Source {self} is Updating sink: {sink}")
                if hasattr(sink, "on_value_changed"):
                    sink.on_value_changed(source, new_value)


@register_type
class SVGSink(BaseSink):
    source_type = SVGSource




@register_type
class SVGNode(BaseNode):

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        self._svg_path_cache = None
        super().__init__(sources, sinks, controls, meta, id)


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
        if isinstance(source, FileSelectorControl):
            logging.info(f"Setting {self.__class__}:{self} value to svg @{value}")
            # self.value = value
            self.value = read_svg_in_original_dimensions(value)
            logging.info(f"Loaded SVG with {self.value.values}")
            self._svg_path_cache = value
            super().on_value_changed(self, self.value)
        else:
            self.value = value




@register_type
class SVGPreviewControl(BaseControl):
    def __init__(self, value="", description="", id=None):
        super().__init__(value, description, id)

    def on_value_changed(self, source, value):
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

    def on_value_changed(self, source, value):
        logging.info(f"On sink changed for SVGPreviewNode {self}")
        if isinstance(source, SVGSink):
            logging.info(f"Source is my SVG sink with value {value.__class__}")
        self.value = value
