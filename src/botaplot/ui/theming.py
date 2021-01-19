from kivy.properties import AliasProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

from kivymd.theming import ThemeManager
from kivymd.material_resources import DEVICE_TYPE

class DesktopThemeClass(ThemeManager):
    """Overrides for desktop"""

    def _get_standard_increment(self):
        if DEVICE_TYPE != "mobile":
            return dp(36)
        else:
            return super(DesktopThemeClass, self)._get_standard_increment(self)

    standard_increment = AliasProperty(
        _get_standard_increment, bind=["device_orientation"]
    )


    def _get_text_color(self, opposite=False):
        theme_style = self._get_theme_style(opposite)
        if theme_style == "Light":
            color = get_color_from_hex("000000")
            color[3] = 0.87
        elif theme_style == "Dark":
            color = get_color_from_hex("BFBFBF")
        return color

    text_color = AliasProperty(_get_text_color, bind=["theme_style"])

    def _get_op_text_color(self):
        return self._get_text_color(True)

    opposite_text_color = AliasProperty(
        _get_op_text_color, bind=["theme_style"]
    )
