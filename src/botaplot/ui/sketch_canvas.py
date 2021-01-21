from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
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
from uuid import uuid4
from statistics import mean, median
from ..models.sketch_graph import SketchGraph
from .controls import BaseControl


class SketchLayout(ScatterPlane):
    """Canvas that displays a sketch graph"""

    def __init__(self, *args, **kwargs):
        super(SketchLayout, self).__init__(*args, **kwargs)
        # with self.canvas:
        #     Color(0.6, 0.0, 0.0)
        #     self.connector_cb = Callback(self._update_spline)
        #     self.bezier = Line(
        #         bezier=[-200,-100, 200,100, 300,200, 500,500, 800,400],
        #         segments=20,
        #         width=16.0
        #             )
        #     Color(0,0,1.0)
        #     Line(points=(-15,-15,15,15), width=4)
        #     Line(points=(15,-15,-15,15), width=4)
        self.bind(pos=self.redraw, size=self.redraw)
        # These are the spline edges, which are just bezier lines
        self.edge_splines = dict()  # source_uuid-sink_uuid
        # And these are the child nodes themselves
        self.nodes = dict()  # by uuid
        # Dict of source/sink IDs pointing at their parents
        self.hint_con = dict()


    def on_start(self, *args, **kw):
        super(SketchLayout, self).on_start(*args, **kw)
        self.center_on_content()

    def redraw(self, *args):
        pass

    @staticmethod
    def _spline_name(edge):
        source = edge.source.id
        sink = edge.sink.id
        return f"{edge.source.id}-{edge.sink.id}"

    def update(self, model: SketchGraph):
        """Cleans out old entries, creates a new graph, redraws"""
        edges_to_delete = set(self.edge_splines.keys()
                              ).difference([self._spline_name(edge)
                                            for edge in model.edges])
        Logger.info("Cleaning out old edges: %s" % edges_to_delete)
        for edge in edges_to_delete:
            self.canvas.remove(self.edge_splines[edge])
            del self.edge_splines[edge]
        for nid, widget in self.nodes.items():
            if nid not in [node.id for node in model.nodes]:
                self.canvas.remove(self.nodes[nid])
                del self.nodes[nid]
        for nid, widget in self.nodes.items():
            if nid not in [node.id for node in model.nodes]:
                self.canvas.remove(self.nodes[nid])
                del self.nodes[nid]
        Logger.info("Done deleting all orphaned widgets")

        #If no meta on position, use this as xpos, with y=0
        x_hint = -(len(model.nodes)*800.0)/2.0
        for node in model.nodes:
            Logger.info("Adding node %s." % node)
            if node.id in self.nodes:
                Logger.info("Skipping, already in UI")
                continue
            widget = self._build_widget_for_node(node, x_hint)
            x_hint += 800  # Magic!
            self.add_widget(widget)
            self.nodes[node.id] = widget


    def get_ui_class_for_model(self, model):
        try:
            child_cls = getattr(Factory, model.__class__.__name__, None)
        except:
            Logger.error("Could not find a UI widget for: %s" % model)
            child_cls = None
        Logger.info("Creating a %s for %s" % (child_cls, model))
        return child_cls


    def _add_children_to_node(self, widget, node):
        """Add all the sources and sinks to a widget for a node"""
        for control in node.controls:
            child_cls = self.get_ui_class_for_model(control)
            if child_cls is None:
                Logger.error("Not adding UI component for model %s" % control)
                continue
            child = child_cls(
                # value=control.value or "null",
                # description=control.description
                **control.controller_args()
            )
            print("Child we added is", child)
            widget.ids.component_list.add_widget(child)
        for sink in node.sinks:
            print("Adding sink:", sink)
            child = MDLabel(text=sink.__class__.__name__)
            widget.ids.component_list.add_widget(child)
        for source in node.sources:
            child = MDLabel(text=source.__class__.__name__)
            widget.ids.component_list.add_widget(child)



    def _build_widget_for_node(self, node, x_hint=0):
        widget = getattr(Factory, node.__class__.__name__, None)(
            pos=node.meta.get('position', (x_hint, 0)),
            size=node.meta.get('size', (640, 0)),
            title=node.meta.get('title', "BaseNode")
        )
        self._add_children_to_node(widget, node)
        return widget


    def _update_spline(self, instruction):
        pass

        # python = MDApp.get_running_app().root.ids.python_source_a
        # postproc = MDApp.get_running_app().root.ids.post_processor_b
        # #foo = widget.ids.component_list.children[0]
        # #foo = widget.children[0]
        # pypos = python.to_parent(python.x, python.y)
        # pppos = postproc.to_parent(postproc.x, postproc.y)
        
        # Logger.info("Widget A: %s", pypos)
        # Logger.info("Widget B: %s", pppos)

        # self.bezier.bezier = [pypos[0]+python.width,pypos[1],
        #                       pypos[0]+python.width*2, pypos[1],
        #                       #(pypos[0]+pppos[0])/2,(pypos[1]+pppos[1])/2,
        #                       pppos[0]-postproc.width,pppos[1],
        #                       pppos[0], pppos[1]]

    def center_on_content(self):
        if len(self.children):
            mean_x = mean([w.center_x for w in self.children])
            mean_y = mean([w.center_y for w in self.children])
            width = max([w.center_x for w in self.children]) - min([w.center_x for w in self.children])
            height = max([w.center_y for w in self.children]) - min([w.center_y for w in self.children])

            if width>0 and height>0:
                optscale = min(self.width/width, self.height/height)
                self.scale = max(0.25, min(optscale, 2.0))
            else:
                self.scale = 1

            dx, dy = self.to_parent(mean_x, mean_y)
            self.center = self.parent.width/2+self.center[0]-dx, self.parent.height/2+self.center[1]-dy
        else:
            self.scale = 0.25
            self.center_x = self.parent.width/2
            self.center_y = self.parent.height/2 - 400

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
                    self.apply_transform(Matrix().scale(1.0/1.05, 1.0/1.05, 1.0/1.05),
                                         anchor=touch.pos)

        # If some other kind of "touch": Fall back on Scatter's behavior
        else:
            super(SketchLayout, self).on_touch_down(touch)





Factory.register('SketchLayout', cls=SketchLayout)
