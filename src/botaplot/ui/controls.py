from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.lang import Builder
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

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
    MDLabel:
        text: root.value
        halign: "left"
        padding: ["8dp","8dp"]
        size_hint: [1,1]


'''

class BaseControl(MDCard):
    description = StringProperty()
    value = ObjectProperty()

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.description = kw.get('description', "BaseControl")
        if kw.get('value') is not None:
            self.value = kw.get('value')

class FileSelectorControl(BaseControl):
    value = StringProperty()

    def __init__(self, *args, **kw):
        print("Creating widget with kw: ", kw)
        super().__init__(*args, **kw)
        self.value = kw.get('value', "")



Builder.load_string(BASECONTROL)
