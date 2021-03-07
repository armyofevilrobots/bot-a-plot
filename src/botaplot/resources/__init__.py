import importlib.resources
import os.path
import pkgutil
import sys


def resource_path(resource_type, filename):
    try:
        base_path = sys._MEIPASS
        return os.path.join(
            base_path,
            f"botaplot/resources/{resource_type}/{filename}")
    except AttributeError:
        with importlib.resources.path(
                "botaplot.resources.%s" % resource_type, filename) as path:
            return os.path.normpath(path)

