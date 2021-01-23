"""Default controls"""
from .sketch_graph import BaseControl, register_type


@register_type
class FileSelectorControl(BaseControl):

    description="File selector"
    extension=None
    type_hint="file_path"

    def __init__(self, value=None, extension=None, description=None, id=None):
        super(FileSelectorControl, self).__init__(
            value=value, description=description,
            id=id)
        self.extension = extension

    def to_dict(self):
        base = super(FileSelectorControl, self).to_dict()
        base['extension'] = self.extension
        return base



@register_type
class BoundedNumericControl(BaseControl):

    description="Numeric Range"
    type_hint="bounded_numeric"
    valrange="0.0<x<1.0"  # ie: 2.0<x<3.0

    def __init__(self, value=None, description=None, valrange=None, id=None):
        if not "<x<" in valrange:
            raise ValueError("Invalid range expression: %s" % valrange)
        for part in valrange.split("<x<"):
            float(part)  # Raises valueError if can't be converted
        bottom, top = valrange.split("<x<")
        if top<=bottom:
            raise ValueError("%f is greater than %f" % (bottom, top))
        self.valrange = valrange
        super(BoundedNumericControl, self).__init__(
            value=value, description=description,
            id=id)

    def to_dict(self):
        base = super(BoundedNumericControl, self).to_dict()
        base['valrange'] = self.valrange
        return base

    def in_range(self, value):
        bottom, top = [float(x) for x in self.valrange.split("<x<")]
        if bottom<value<top:
            return True
        return False

    def clamp(self, value):
        bottom, top = [float(x) for x in self.valrange.split("<x<")]
        return min(max(value, bottom), top)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if not self.in_range(val):
            raise ValueError("%f is not in %s" % (val, self.valrange))
        self._value = val
