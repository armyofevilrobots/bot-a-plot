"""Provides an SVG file with a source"""

from botaplot.models.sketch_graph import (register_type,
    MediaType, BaseSource, BaseSink, BaseNode)




@register_type
class SVGSource(BaseSource):
    """BaseSource subclassed to force type SVG. Mostly just makes the
    sketch files more legible."""
    media_type = MediaType.SVG

    def __init__(self, media_type, parent, id=None):
        if media_type != MediaType.SVG:
            raise TypeError("Invalid media type for SVG source: %s" % media_type)
        super(SVGSource, self).__init__(media_type, parent, id=None)

@register_type
class SVGFile(BaseNode):



