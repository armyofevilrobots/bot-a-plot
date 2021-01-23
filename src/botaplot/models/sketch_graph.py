from functools import wraps
import os.path
import logging
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


def from_dict(data, parent=None):
    if data is None:
        return None
    if isinstance(data, list):
        return [from_dict(item) for item in data]
    if isinstance(data, (int, str, float)):
        return data
    if "_type" not in data:
        child = {key:from_dict(val) for key,val in data.items()}
        return child
    if data['_type'] not in lookup_types:
        raise TypeError(f"Unknown type {data['_type']}")

    children = {key:from_dict(val) for key,val in data.items() if key != "_type"}
    tmp = lookup_types[data["_type"]](
        **children)
    # This is a bit... odd...
    # We create the children in a dict. Pass them in above as kwargs, and then after
    # we have generated that parent object, set the children who are serializable to
    # have a reference to their parent
    return tmp

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

    def controller_args(self):
        """Returns a dict of kwarg:value for building controls/widgets"""
        args = self.to_dict()
        print("Dict is", args)
        args = {kw:arg for (kw, arg) in args.items()
                if not kw.startswith("_") and kw is not "id" }
        return args


    @classmethod
    def from_dict(cls, data):
        return cls(data=data)

@register_type
class BaseControl(Serializable):
    _value=None
    description = "Null Control"
    value_hint="None"
    parent = None
    id = None

    def __init__(self, value="", description="", id=None):
        self.value = value or ""
        self.description = description or "Null control"
        self.id = id or str(uuid.uuid4())
        self.callbacks = list()

    def to_dict(self):
        base = super(BaseControl, self).to_dict()
        base['value'] = self.value
        base['description'] = self.description
        base['id'] = self.id
        return base


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        print("Value for",self, "changed to:", val)
        print("Parent is ", self.parent)
        print(self.__dict__)
        if self.parent and hasattr(self.parent, "on_value_changed"):
            print("Calling on_value_changed callback on parent")
            self.parent.on_value_changed(self, val)
        self._value = val


class SourceSinkBase(Serializable):

    def __init__(self, id=None):
        self.id = id or str(uuid.uuid4())

    def to_dict(self):
        base = super(SourceSinkBase, self).to_dict()
        return base

@register_type
class BaseSource(SourceSinkBase):
    """Consumer of some basic data"""
    parent = None  # This is a Node

    def __init__(self, id=None):
        SourceSinkBase.__init__(self, id)

@register_type
class BaseSink(SourceSinkBase):
    """Source of some basic data"""
    parent = None  # This is a Node
    source_type = BaseSource

    def __init__(self, id=None):
        SourceSinkBase.__init__(self, id)

@register_type
class Edge(Serializable):
    id = None  # Unique ID
    source = None  # This is a source
    sink = None  # This is a sink

    def __init__(self, source, sink, id=None):
        self.id = id or str(uuid.uuid4())
        self.source = source
        self.sink = sink

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

    @classmethod
    def create(cls, id=None):
        return cls(id=id)

    def on_value_changed(self, source, value):
        """Called by any change to the controls or sources"""
        print("%s on_value_changed via %s with new value %s" %(self, source, value))


@register_type
class SketchGraph(Serializable):
    """Represents a graph of nodes, sources, sinks, and connections all
    together in a nice little bundle, with JSON serialization for saving."""
    nodes = list()  # of nodes, eh
    edges = list()
    basedir = None
    by_uuid = dict()

    def __init__(self, nodes=None, edges=None, meta=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.nodes = nodes or list()
        self.edges = edges or list()
        self.meta = meta or dict()
        # We backlink all the things
        for node in self.nodes:
            for control in node.controls:
                control.parent = node
            for source in node.sources:
                source.parent = node
            for sink in node.sinks:
                sink.parent = node




    @classmethod
    def from_file(cls, path):
        path = os.path.normpath(path)
        data = hjson.load(open(path))
        new_graph = from_dict(data=data)
        return new_graph

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
