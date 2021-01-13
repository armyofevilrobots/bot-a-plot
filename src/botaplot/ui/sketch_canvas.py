from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivy.factory import Factory
from kivy.uix.widget import Widget
from kivy.uix.scatter import ScatterPlane
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.graphics import Color, Bezier, Line, Callback
from kivy.uix.scatterlayout import ScatterLayout
from kivy.logger import Logger
from uuid import uuid4

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
        self.bind(pos=self.redraw, size=self.redraw)


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

    def on_touch_down(self, touch):
        """Resize the scatter when the mouse is scrolled"""
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.scale < 2:
                    self.scale = self.scale * 1.1
            elif touch.button == 'scrollup':
                if self.scale > 0.25:
                    self.scale = self.scale * 0.8
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
        print("My size is", self.size)
        for child in self.walk(True):
            print("CHILD: %s" % child)
            try:
                print("WIDTH, HEIGHT", child.texture_size)
            except:
                print("NO TX SIZE")
            print(dir(child))
        if not self.collide_point(*touch.pos):
            return False
        workspace = self.parent.parent.parent.parent
        grid = self.parent
        menu = self.parent.parent.parent
        if "MainLayout" in str(workspace):
            grid.remove_widget(self)
            workspace.remove_widget(menu)

            # the following code assumes that workspace is the entire Window
            self.x = Window.mouse_pos[0] - (touch.pos[0] - self.x)
            self.y = Window.mouse_pos[1] - (touch.pos[1] - self.y)
            workspace.add_widget(self)
            touch.pos = Window.mouse_pos
        return super(DragCard, self).on_touch_down(touch)


Factory.register('SketchLayout', cls=SketchLayout)
Factory.register('DragCard', cls=DragCard)
