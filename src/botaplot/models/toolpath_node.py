from .sketch_graph import BaseNode, BaseSource, BaseSink, register_type
from botaplot.models.controls import *
from .svg_node import SVGSink
from .plottable import Plottable
import logging
from ..util.svg_util import subdivide_path, svg2lines, calculate_mm_per_unit



@register_type
class SVGToolpathNode(BaseNode):
    """Consumes an SVG Sink and generates a plottable source
    Also has controls for: scale, xofs, yofs, rotation
    """

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        super().__init__(sources, sinks, controls, meta, id)
        self.value = None


    @classmethod
    def create(cls, id=None):
        node = cls(id=id)
        node.sinks.append(SVGSink.create())
        return node

    def on_value_changed(self, source, value):
        logging.info(f"On sink changed for {self.__class__} {self}")
        logging.info(f"Value is now: {value}")
        if value is None:
            self.value = None
            return
        # self.value = value
        # Now we grab that SVG, process it, and generate a toolpath.
        # TODO: Launch this update in a subprocess or something.
        lines = svg2lines(value)
        logging.info("Max X: %f\n" % max([ max([p[0] for p in line]) for line in lines]))
        logging.info("Min X: %f\n" % min([ min([p[0] for p in line]) for line in lines]))

        def _callback(stage, remaining, total):
            pass

        plottable = Plottable([Plottable.Line(line) for line in lines], callback=_callback)
        scale = calculate_mm_per_unit(value)  # 25.4/72.0 #plottable.calculate_dpi_via_svg(svg)
        logging.info("Scale is %s\n" % scale)
        logging.info("Calc height is %s\n" % plottable.convert_svg_units_to_mm(
            value.values.get('height', "%fin" % (value.viewbox.height / 72.0))))
        plottable.transform_self(scale * value.viewbox.x,
                                 (-1.0 * scale * value.viewbox.y),
                                 scale, -scale)  # +post.bounds[1][1])
        self.value = plottable




