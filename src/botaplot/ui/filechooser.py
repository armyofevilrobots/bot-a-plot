from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.factory import Factory
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivymd.uix.filemanager import MDFileManager
import os.path

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)


class FileOpener(EventDispatcher):
    valid = BooleanProperty(False)
    path = StringProperty("")

    def __init__(self,
                 success=None,
                 fail=None,
                 rootpath=os.path.expanduser("~"),
                 extensions=False):

        self.filemanager = MDFileManager(
            ext=extensions or list(),
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            sort_by="name",
            preview=False
        )
        self.success = success
        self.fail = fail
        self.rootpath = rootpath

    def show(self, rootpath=None):
        self.valid = False
        self.path = ""
        self.filemanager.show(self.rootpath)

    def exit_manager(self, state=None):
        Logger.info("Exiting file manager")
        self.filemanager.close()
        if self.fail is not None and not self.valid:
            self.fail(self)

    def select_path(self, path=None):
        Logger.info("Selecting path in file manager")
        self.path = path
        self.valid = (path is not None)
        self.filemanager.close()
        if self.success is not None:
            self.success(self, path)
        elif self.fail is not None:
            self.fail(self)




Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SaveDialog', cls=SaveDialog)
