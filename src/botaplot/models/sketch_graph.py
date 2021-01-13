from functools import wraps
import uuid
from enum import Enum
import hjson

lookup_types = {}

def register_type(klass):
    """Pass a class for a node type """
    lookup_types[klass._hname()] = klass
    return klass

def register_widget(klass):
    """Pass a class for a widget """
    widget_types[klass._hname()] = klass
    def wrapper(klass):
        return klass


def from_dict(data):
    if isinstance(data, list):
        return [from_dict(item) for item in data]
    if isinstance(data, (int, str, float)):
        return data
    if "_type" not in data:
        return {key:from_dict(val) for key,val in data.items()}
    if data['_type'] not in lookup_types:
        raise TypeError(f"Unknown type {data['_type']}")
    
    return lookup_types[data["_type"]](
        **{key:from_dict(val) for key,val in data.items() if key != "_type"}
    )

class Serializable:

    @property
    def hname(self):
        return self.__class__._hname()

    @classmethod
    def _hname(cls):
        return getattr(cls, "name", cls.__name__)

    def to_dict(self):
        base = {"_type": self.hname}
        if hasattr(self, "id"):
            base['id'] = self.id
        return base

    @classmethod
    def from_dict(cls, data):
        return cls(data=data)



@register_type
class MediaType(Serializable, Enum):
    NULL=0
    SVG=1
    PLOTTABLE=2

    def to_dict(self):
        data = {"_type":"MediaType", "value":self.value}
        return data


class SourceSinkBase(Serializable):

    def __init__(self, media_type, parent, id=None):
        self.id = id or str(uuid.uuid4())
        self.parent = parent
        self.media_type = media_type

    def to_dict(self):
        base = super(SourceSinkBase, self).to_dict()
        base["media_type"]=self.media_type.to_dict()
        base["parent"] = self.parent
        return base

@register_type
class BaseSink(SourceSinkBase):
    """Source of some basic data"""
    media_type = MediaType.NULL
    parent = None  # This is a Node

    def __init__(self, media_type, parent, id=None):
        SourceSinkBase.__init__(self, media_type, parent, id)

@register_type
class BaseSource(SourceSinkBase):
    """Consumer of some basic data"""
    media_type = MediaType.NULL
    parent = None  # This is a Node

    def __init__(self, media_type, parent, id=None):
        SourceSinkBase.__init__(self, media_type, parent, id)

@register_type
class Edge(Serializable):
    id = None  # Unique ID
    media_type = MediaType.NULL  # We have to match source&sink
    last_hash = None  # What was the hash of the last output?
    last_cycle = None  # What was the UUID of the last render cycle
    source = None  # This is a source
    sink = None  # This is a sink

    def __init__(self, source, sink, id=None):
        self.id = id or str(uuid.uuid4())
        self.source = source
        self.sink = sink
        if source.media_type != sink.media_type:
            raise TypeError("Media types do not match.")
        self.media_type = source.media_type

    def to_dict(self):
        base = super(Edge, self).to_dict()
        base['source'] = self.source.to_dict()
        base['sink'] = self.sink.to_dict()
        return base

@register_type
class BaseNode(Serializable):
    """Object that represents a configurable
    group of sources and sinks"""

    # I/O
    sources=list()  # No sources
    sinks=list()    # No sinks either

    controls = list()  # These are widgets
    meta = dict()  # This contains layout data, and other meta

    def __init__(self, sources=None, sinks=None, controls=None, meta=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.sources = sources or list()
        self.sinks = sinks or list()
        self.controls = controls or list()
        self.meta = meta or dict()



    def to_dict(self):
        base = super(BaseNode, self).to_dict()
        base.update({
            "meta": self.meta,
            "sinks": [sink.to_dict() for sink in self.sinks],
            "sources": [source.to_dict() for source in self.sources],
            "controls": [control.to_dict() for control in self.controls],
            })
        return base

@register_type
class SketchGraph(Serializable):
    """Represents a graph of nodes, sources, sinks, and connections all
    together in a nice little bundle, with JSON serialization for saving."""
    nodes = list()  # of nodes, eh
    edges = list()

    def __init__(self, nodes=None, edges=None, meta=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.nodes = nodes or list()
        self.edges = edges or list()
        self.meta = meta or dict()

    def to_dict(self):
        base = super(SketchGraph, self).to_dict()
        base.update({
            "meta": self.meta,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            })
        return base

    def traverse(self):
        """Return an ordered list of items to render"""
        sink2edge = {edge.sink:edge for edge in self.edges}
        source2edge = {edge.source:edge for edge in self.edges}
        starts = [node for node in self.nodes
                  if not [sink2edge.get(sink) for sink in node.sinks]]
        if not starts:
            raise RuntimeError("No nodes to start from. We have a cycle.")

        for start in starts:
            pass


    def render(self):
        """Cycle through the nodes and run their calculations, generating
        outputs on their sources, consuming their sinks (if possible). Cycles
        until it finds recursion, or until there is no further nodes to hit.
        """
