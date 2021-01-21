import os.path

from kivy.logger import Logger
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from .filechooser import FileOpener

BASECONTROL = '''
<BaseControl>:
    orientation: "horizontal"
    size_hint: [1,1]

    MDIcon:
        icon: "block-helper"
        halign: "left"
        padding: ["8dp","8dp"]
        size_hint: [None,1]
    MDLabel:
        text: root.description
        halign: "left"
        padding: ["8dp","8dp"]
        size_hint: [1,1]

<-FileSelectorControl>:
    orientation: "horizontal"
    size_hint: [1,1]
    MDIconButton:
        icon: "folder-open"
        halign: "left"
        padding: ["8dp","8dp"]
        size_hint: [None,1]
        on_release: root.browse_for_file()
    MDLabel:
        text: root.label_content
        halign: "left"
        padding: ["8dp","8dp"]
        size_hint: [1,1]
    MDIcon:
        icon: root.file_ok and "check-circle-outline" or "alert-outline"
        halign: "right"
        padding: ["8dp","8dp"]
        size_hint: [None,1]


'''

class BaseControl(MDCard):
    description = StringProperty()
    extension = StringProperty()
    value = ObjectProperty()
    label_content = StringProperty()

    def on_value(self, obj, value):
        pass

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.description = kw.get('description', "BaseControl")
        if kw.get('value') is not None:
            self.value = kw.get('value')

class FileSelectorControl(BaseControl):
    value = StringProperty()
    file_ok = BooleanProperty(False)
    label_content = StringProperty()

    #def on_value_change(self, obj, new_value):
    def on_value(self, obj, value):
        super().on_value(obj, value)
        Logger.info("On value change called with new value %s" % value)
        if not os.path.isfile(value):
            self.file_ok = False
            self.label_content=self.description
        else:
            self.file_ok = True
            if len(self.value) > 20:
                self.label_content = self.value[:8]+"\u2026"+self.value[-19:]
            else:
                self.label_content = self.value
            

    def browse_for_file(self):
        def set_file_value(obj, x):
            Logger.info(f"We got {obj},{x} for our params")
            self.value = x
        opener = FileOpener(set_file_value,
                            extensions=[self.extension, ])
        opener.show()


    def __init__(self, *args, **kw):
        Logger.debug("Creating widget with kw: ", kw)
        super().__init__(*args, **kw)
        self.file_ok = False
        self.value = kw.get('value', "")
        self.extensions = kw.get('extension', "")



Builder.load_string(BASECONTROL)
