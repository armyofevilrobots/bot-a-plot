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


kv_stub = '''
<-MDFileSaveManager>
    md_bg_color: root.theme_cls.bg_normal
    BoxLayout:
        orientation: "vertical"
        spacing: dp(5)
        padding: dp(8)
        MDToolbar:
            id: toolbar
            title: root.current_path
            right_action_items: [["close-box", lambda x: root.exit_manager(1)]]
            left_action_items: [["chevron-left", lambda x: root.back()]]
            elevation: 10
            
        MDBoxLayout:
            adaptive_height: True
            md_bg_color: app.theme_cls.bg_normal 
            spacing: [dp(8), dp(8)]
            
            MDTextField:
                id: file_name_entry
                color_mode: "primary"
                hint_text: "Filename to save"
                helper_text: "Enter a filename"
                helper_text_mode: "persistent"
        RecycleView:
            id: rv
            key_viewclass: "viewclass"
            key_size: "height"
            bar_width: dp(4)
            bar_color: root.theme_cls.primary_color
            #on_scroll_stop: root._update_list_images()
            RecycleGridLayout:
                # padding: dp(10)
                cols: 3 if root.preview else 1
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
'''

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    start_path = ObjectProperty(None)

class MDFileSaveManager(MDFileManager):
    """Exactly the same, but lets you enter a filename"""

class FileOpener(EventDispatcher):
    dialog_cls = MDFileManager
    valid = BooleanProperty(False)
    path = StringProperty("")

    def __init__(self,
                 success=None,
                 fail=None,
                 rootpath=os.path.expanduser("~"),
                 extensions=False,
                 enter_file=False):

        Logger.info("Using %s as allowed extensions" % extensions)
        self.filemanager = self.dialog_cls(
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


class FileSaver(FileOpener):
    dialog_cls = MDFileSaveManager

    def select_path(self, path=None):
        Logger.info("Selecting path in file manager")
        Logger.info("Entered filename is %s" % self.filemanager.ids.file_name_entry.text)
        fname = str(self.filemanager.ids.file_name_entry.text)
        Logger.info("FNAME IS '%s'" % fname)
        if fname and not fname.endswith(".bap") and not fname.endswith(".botaplot"):
            # Only if fname is actually set, otherwise leave empty
            fname = f"{fname}.botaplot"
        self.path = path
        Logger.info(f"Path is currently: {self.path}")
        if path is not None and fname:
            self.path = os.path.join(self.path, fname)
        self.valid = (self.path is not None) and os.path.isdir(os.path.dirname(self.path))
        Logger.info(f"{self.path} is valid? {self.valid}")
        self.filemanager.close()
        if self.valid and self.success is not None:
            self.success(self, path)
        elif self.fail is not None:
            self.fail(self)


Builder.load_string(kv_stub)


Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('SaveDialog', cls=SaveDialog)
