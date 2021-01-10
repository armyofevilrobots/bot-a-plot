import importlib.resources
from os.path import normpath


def resource_path(resource_type, filename):
    with importlib.resources.path(
            "botaplot.resources.%s" % resource_type, filename) as path:
        return normpath(path)
