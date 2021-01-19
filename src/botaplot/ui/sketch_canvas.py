from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivy.factory import Factory
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Bezier, Line, Callback, Rectangle
from kivy.uix.scatterlayout import ScatterLayout
from kivy.logger import Logger
from kivy.graphics.transformation import Matrix
from uuid import uuid4
from statistics import mean, median

class SketchLayout(ScatterPlane):
#class SketchLayout(ScatterLayout):
    """Canvas that displays a sketch graph"""

    def __init__(self, *args, **kwargs):
        super(SketchLayout, self).__init__(*args, **kwargs)
        with self.canvas:
            Color(0.6, 0.0, 0.0)
            self.connector_cb = Callback(self._update_spline)
            self.bezier = Line(
                bezier=[-200,-100, 200,100, 300,200, 500,500, 800,400],
                segments=20,
                width=16.0
                    )
            Color(0,0,1.0)
            Line(points=(-15,-15,15,15), width=4)
            Line(points=(15,-15,-15,15), width=4)
        self.bind(pos=self.redraw, size=self.redraw)


    def on_start(self, *args, **kw):
        super(SketchLayout, self).on_start(*args, **kw)
        self.center_on_content()

    def redraw(self, *args):
        pass


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

    def shuttle_over(self, touched, invert=False):
        t = Matrix()
        ttouched = Matrix().translate(touched[0], touched[1],0)
        print("TOUCHED COORDS", self.to_parent(*touched))
        print("My Transform", self.transform)
        t = t.multiply(ttouched)
        dx, dy = (-t[12]+self.x, -t[13]+self.y)
        print("dx,dy:", dx, dy)
        if invert:
            self.center_x = self.center_x+dx*0.1
            self.center_y = self.center_y+dy*0.1
        else:
            self.center_x = self.center_x-dx*0.1
            self.center_y = self.center_y-dy*0.1


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



class DragCard(DragBehavior, MDCard):
    title = StringProperty()
    id = StringProperty()
    actions = [["language-python", lambda x:x]]

    def __init__(self, *args, **kw):
        super(DragCard, self).__init__(*args, **kw)
        if not self.id:
            self.id="drag_card_%s" % (uuid4().hex)


    def on_touch_down(self,touch):
        if not self.collide_point(*touch.pos):
            return False
        return super(DragCard, self).on_touch_down(touch)


Factory.register('SketchLayout', cls=SketchLayout)
Factory.register('DragCard', cls=DragCard)
