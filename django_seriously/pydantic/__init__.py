# import from this module means we likely also want to have DRF and drf-spectacular ready
try:
    # attempt to register DRF fields if feasible
    import django_seriously.pydantic.drf_fields  # noqa: F401
except ImportError:
    pass

try:
    # attempt to load drf-spectacular extensions if feasible
    import django_seriously.pydantic.schema  # noqa: F401
except ImportError:
    pass
