"""NBL Media Desk: an AI post-game newsroom with a deterministic fact-check gate."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nbl-media-desk")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
