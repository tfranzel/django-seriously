from typing import Any, Dict, List

from django.utils.module_loading import import_string


def perform_import(val):
    if val is None:
        return None
    elif isinstance(val, str):
        return import_string(val)
    elif isinstance(val, (list, tuple)):
        return [import_string(item) for item in val]
    return val


class AppSettings:
    """
    Reusable settings container that handles import strings, defaults,
    reloading, and lazy evaluation.
    This class is shamelessly recycled from DRF's APISettings without
    introducing a dependency on DRF.
    """

    def __init__(
        self,
        user_settings: Dict[str, Any],
        defaults: Dict[str, Any],
        import_strings: List[str],
    ):
        self.user_settings = user_settings
        self.defaults = defaults
        self.import_strings = import_strings
        self._cached_attrs = set()

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")
