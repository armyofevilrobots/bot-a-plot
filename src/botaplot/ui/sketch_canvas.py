from weakref import WeakValueDictionary
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.toast import toast
from kivy.factory import Factory
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Bezier, Line, Callback, Rectangle
from kivy.uix.scatterlayout import ScatterLayout
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.core.window import Window
from uuid import uuid4
from statistics import mean, median
from ..models import *
from ..models.sketch_graph import SketchGraph
from ..models.svg_node import SVGNode
from .controls import BaseControl
from .svg_node import SVGNode, SVGSource
from .node import BaseNode as UIBaseNode
from .node import BaseSource as UIBaseSource
from .node import BaseSink as UIBaseSink


class SketchLayout(ScatterPlane):
    """Canvas that displays a sketch graph"""
    sketch_model = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(SketchLayout, self).__init__(*args, **kwargs)
        self.bind(pos=self.spline_redraw, size=self.spline_redraw, sketch_model=self.trigger_redraw)
        # These are the spline edges, which are just bezier lines
        self.edge_splines = WeakValueDictionary()  # source_uuid-sink_uuid
        # And these are the child nodes themselves
        self.nodes = dict()  # by uuid
        # Dict of source/sink IDs pointing at their parents
        self.hint_con = WeakValueDictionary()
        # Sources and Sinks : Weakref dict of source/sink id to actual widgets
        self.source_sink_lookup = WeakValueDictionary()
        self.connecting_arc = None
        self.connecting_spline = list()
        self.connecting_source_widget = None
        self.sink_watchers = WeakValueDictionary()
        # Window.bind(on_motion=self.on_motion)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, source, point):
        """Used to capture mouse moves when we are moving connectors."""
        swx, swy = self.to_window(*self.pos)
        mx, my = point[0], point[1]  #-swx, point[1]-swy
        in_scatter = False
        cx, cy = ((mx-swx)/self.scale, (my-swy)/self.scale)
        # print("swx, swy, mx, my", swx, swy, mx, my)
        # # print("Scale", self.scale)
        # print("CalcXY = ", cx, cy, "in", self.bbox, "scale", self.scale)
        if self.connecting_arc != None:
            # tmp_bezier = self.connecting_spline.copy()
            tmp_bezier = self.calc_bezier_coords(self.connecting_source_widget, None)
            tmp_bezier = tmp_bezier[:4] + [
                cx - 200, cy,
                cx, cy]
            self.connecting_spline = tmp_bezier
            self.connecting_arc.bezier = tmp_bezier


    def on_start(self, *args, **kw):
        super(SketchLayout, self).on_start(*args, **kw)

    def trigger_redraw(self, *args, **kw):
        self.center_on_content()

    def _spline_redraw(self, *args):
        """Actually redraw the spline on an update."""
        for key, spline in self.edge_splines.items():
            # source_id, sink_id = key.split("_")
            sink_id = key
            sink = self.source_sink_lookup[sink_id]
            source_id = sink.model.source.id
            source = self.source_sink_lookup[source_id]
            spline.bezier = self.calc_bezier_coords(source, sink)

    def spline_redraw(self, *args):
        """
        This is done via a scheduled action, because position updates on
        widgets lag, or don't match the actual events. This way, we get the
        spline redraw to match the widgets after they settle. It adds a bit
        of lag, but overall it looks better than the jitter we otherwise get
        """
        self._spline_redraw()
        Clock.schedule_once(self._spline_redraw)

    @staticmethod
    def _spline_name(source, sink):
        return f"{source.id}-{sink.id}"

    @staticmethod
    def _get_connector_widget(connector):
        if isinstance(connector, UIBaseSource):
            conn_widget = connector.ids["source_connect"]
        elif isinstance(connector, UIBaseSink):
            conn_widget = connector.ids["sink_connect"]
        else:
            raise RuntimeError("Invalid connector %s" % connector)
        return conn_widget

    def _calc_connector_pos(self, connector):
        conn_widget = self._get_connector_widget(connector)
        card_parent = conn_widget.parent
        list_parent = card_parent.parent
        box_parent = list_parent.parent
        node_parent = box_parent.parent
        connector_pos = node_parent.to_parent(
            *box_parent.to_parent(
                *list_parent.to_parent(
                    *card_parent.to_parent(
                        *conn_widget.to_parent(*conn_widget.center)))))
        return connector_pos

    def calc_bezier_coords(self, source, sink):
        source_conn = self._get_connector_widget(source)
        source_pos = self._calc_connector_pos(source)
        if sink is not None:
            sink_conn = self._get_connector_widget(sink)
            sink_pos = self._calc_connector_pos(sink)
        elif isinstance(sink, (tuple, list)) and len(sink) == 2:
            sink_pos = sink
        else:
            sink_pos = source_pos
        return [source_pos[0], source_pos[1],
                source_pos[0] + 200, source_pos[1],
                sink_pos[0] - 200, sink_pos[1],
                sink_pos[0], sink_pos[1]]

    def create_edge_spline(self, source, sink=None, color=(0.6, 0.0, 0.0)):
        # python = MDApp.get_running_app().root.ids.python_source_a
        # postproc = MDApp.get_running_app().root.ids.post_processor_b
        with self.canvas:
            Color(*color)
            bezier = Line(
                bezier=self.calc_bezier_coords(source, sink),
                segments=4,
                width=12)
        return bezier

    def update(self, model: SketchGraph):
        """Cleans out old entries, creates a new graph, redraws"""
        for key in self.edge_splines.keys():
            self.canvas.remove(self.edge_splines[key])
        for nid in [key for key in self.nodes.keys()]:
            node = self.nodes[nid]
            if nid not in [node.id for node in model.nodes]:
                self.remove_widget(self.nodes[nid])
                try:
                    del self.nodes[nid]  # It's a weakref, so already deleted
                except:
                    Logger.info(f"Node {nid} already deleted")
        Logger.info("Done deleting all orphaned widgets")

        # If no meta on position, use this as xpos, with y=0
        x_hint = -(len(model.nodes) * 800.0) / 2.0
        for node in model.nodes:
            Logger.info("Adding node %s." % node)
            if node.id in self.nodes:
                Logger.info("Skipping, already in UI")
                continue
            widget = self._build_widget_for_node(node, x_hint)
            x_hint += 800  # Magic!
            self.add_widget(widget)
            self.nodes[node.id] = widget

        # Now connect them up
        for node in model.nodes:
            Logger.info(f"Creating sink connections for node {node.id}:{node} :: {node.sinks}")
            for sinkm in node.sinks:
                self.watch_sink_connections(sinkm)
                if sinkm.source is not None:
                    self.create_viz_sink_conn(sinkm)
        self.sketch_model = model
        self.center_on_content()

        # This ensures we redraw the spline with it's endpoints in the right spots
        def _on_change_all_nodes(*args):
            for node in model.nodes:
                node.on_value_changed(self, node.value)

        Clock.schedule_once(self._spline_redraw)
        Clock.schedule_once(_on_change_all_nodes)

    def create_viz_sink_conn(self, sinkm):
        # sourcem_id = sinkm.source.id  # Cached so we can delete in callback
        sourcew = self.source_sink_lookup[sinkm.source.id]
        sinkw = self.source_sink_lookup[sinkm.id]
        self.edge_splines[sinkm.id] = \
            self.create_edge_spline(sourcew, sinkw)

    @staticmethod
    def get_ui_class_for_model(model):
        try:
            child_cls = getattr(Factory, model.__class__.__name__, None)
        except:
            Logger.error("Could not find a UI widget for: %s" % model)
            child_cls = None
        Logger.info("Creating a %s for %s" % (child_cls, model))
        return child_cls

    def watch_sink_connections(self, sink):
        if sink.source is not None:
            sourcew = self.source_sink_lookup[sink.source.id]
        else:
            sourcew = None
        sinkw = self.source_sink_lookup[sink.id]

        def _on_connect(source, sourcem):
            """Called whenever a connection happens."""
            old_watcher = self.sink_watchers.get(sink.id)
            if old_watcher is not None:
                Logger.info(f"Unwatching sink {sink}")
                sink.unwatch(on_connect=old_watcher)
            if sink.id in self.edge_splines.keys():
                self.canvas.remove(self.edge_splines[sink.id])
            if sourcem is not None:
                new_sourcew = self.source_sink_lookup[sourcem.id]
                self.edge_splines[sink.id] = \
                    self.create_edge_spline(new_sourcew, sinkw)
        self.sink_watchers[sink.id] = _on_connect
        sink.watch(on_connect=_on_connect)



    def _add_children_to_node(self, widget, node):
        """Add all the sources and sinks to a widget for a node"""
        for control in node.controls:
            child_cls = self.get_ui_class_for_model(control)
            if child_cls is None:
                Logger.error("Not adding UI component for model %s" % control)
                continue
            Logger.info(f"Child control args: {control.controller_args()}")
            child = child_cls(
                **control.controller_args()
            )

            _control = control
            def on_value_changed(obj, val):
                Logger.info(f"On_value_change bind for {obj} with {val}")
                _control.value = val  # This is the MODEL control change

            child.bind(value=on_value_changed)
            # if child.value:
            #     on_value_changed(child, child.value)
            if control.value:
                Logger.info(f"We have a value of {control.value} on control {control}")
                control.value = control.value  # Trigger rebuild
            widget.ids.component_list.add_widget(child)

        for sink in node.sinks:
            sink_ui_cls = getattr(Factory, sink.__class__.__name__, None)
            child = sink_ui_cls(**sink.controller_args())
            child.model = sink
            widget.ids.component_list.add_widget(child)
            self.hint_con[sink.id] = node
            self.source_sink_lookup[sink.id] = child

            def _connect_accept(*args, **kw):
                Logger.info(f"Got a connect with {args} {kw}")
                if child.model.source != None and self.connecting_source_widget:
                    toast("Only one incoming connection per sink is allowed.")

                elif child is not None \
                        and self.connecting_source_widget \
                        and self.connecting_arc \
                        and child.model and child.model.source == None:
                    child.model.source = self.connecting_source_widget.model
                    self.canvas.remove(self.connecting_arc)
                    # self.create_viz_sink_conn(child.model)

                    Logger.info("Should be connected")
                    self.connecting_source_widget.is_connecting = False  # We're done
                    self.connecting_source_widget = None
                    self.connecting_arc = None
                    self.connecting_spline = list()
                else:
                    Logger.info("Connection failed for s:{self.connecting_source_widget}")

            child.bind(on_press=_connect_accept)
            self.watch_sink_connections(sink)

        for source in node.sources:
            source_ui_cls = getattr(Factory, source.__class__.__name__, None)
            child = source_ui_cls(**source.controller_args())
            child.model = source
            widget.ids.component_list.add_widget(child)
            self.hint_con[source.id] = node
            self.source_sink_lookup[source.id] = child

            def _on_connecting(msource, value, **kw):
                if value:
                    Logger.info(f"We are connecting something: s:{source}c:{child}, {value}")
                    self.connecting_spline = self.calc_bezier_coords(child, None)
                    self.connecting_arc = self.create_edge_spline(child, None, color=(0,0,1))
                    self.connecting_source_widget = child


            child.bind(is_connecting=_on_connecting)


    def _build_widget_for_node(self, node, x_hint=0.0):
        widget_type = getattr(Factory, node.__class__.__name__, None)
        widget = widget_type(
            pos=node.meta.get('position', (x_hint, 0)),
            size=node.meta.get('size', (640, 0)),
            title=node.meta.get('title', node.__class__.__name__)
        )
        widget.model = node

        def _update_widget_viewmodel(source, value):
            Logger.info(f"Updating viewmodel on {widget} with {value}")
            widget.value = value
        node.watch(_update_widget_viewmodel)
        Logger.info("We found widget type: %s for node %s", widget_type, node)
        self._add_children_to_node(widget, node)
        widget.bind(pos=self.spline_redraw, size=self.spline_redraw)

        def _update_meta(obj, event):
            node.meta["xpos"] = event[0]
            node.meta["ypos"] = event[1]

        widget.bind(pos=_update_meta)
        return widget

    def center_on_content(self):
        if len(self.children):
            mean_x = mean([w.center_x for w in self.children])
            mean_y = mean([w.center_y for w in self.children])
            width = max([w.center_x for w in self.children]) - min([w.center_x for w in self.children])
            height = max([w.center_y for w in self.children]) - min([w.center_y for w in self.children])

            if width > 0 and height > 0:
                optscale = min(self.width / width, self.height / height)
                self.scale = max(0.25, min(optscale, 2.0))
            else:
                self.scale = 1

            dx, dy = self.to_parent(mean_x, mean_y)
            self.center = self.parent.width / 2 + self.center[0] - dx, self.parent.height / 2 + self.center[1] - dy
        else:
            self.scale = 0.25
            self.center_x = self.parent.width / 2
            self.center_y = self.parent.height / 2 - 400

    def on_touch_down(self, touch):
        """Resize the scatter when the mouse is scrolled"""
        if touch.is_double_tap:
            self.center_on_content()

        elif touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.scale < 2:
                    self.apply_transform(Matrix().scale(1.05, 1.05, 1.05),
                                         anchor=touch.pos)
            elif touch.button == 'scrollup':
                if self.scale > 0.25:
                    self.apply_transform(Matrix().scale(1.0 / 1.05, 1.0 / 1.05, 1.0 / 1.05),
                                         anchor=touch.pos)

        # If some other kind of "touch": Fall back on Scatter's behavior
        else:
            super(SketchLayout, self).on_touch_down(touch)


Factory.register('SketchLayout', cls=SketchLayout)
