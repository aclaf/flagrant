"""Specification-driven parsing and completion for command-line arguments, options, and subcommands."""  # noqa: E501

try:
    from importlib.metadata import version

    __version__ = version("flagrant")
except Exception:  # noqa: BLE001
    __version__ = "unknown"
