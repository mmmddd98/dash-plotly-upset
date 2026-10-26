from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any


DEFAULT_ASSETS_ROUTE = "/dash-plotly-upset-assets"
CLIENTSIDE_SCRIPT_NAMES = ("upsetPlot.js", "upsetCursor.js")


def package_assets_path() -> Path:
    """Return the directory containing the optional Dash clientside JS assets."""

    return Path(str(files("dash_plotly_upset") / "assets"))


def clientside_script_urls(route: str = DEFAULT_ASSETS_ROUTE) -> list[str]:
    """Return URLs for the bundled clientside Dash scripts."""

    clean_route = route.rstrip("/")
    asset_dir = package_assets_path()
    urls = []
    for name in CLIENTSIDE_SCRIPT_NAMES:
        path = asset_dir / name
        version = int(path.stat().st_mtime) if path.exists() else 0
        urls.append(f"{clean_route}/{name}?v={version}")
    return urls


def attach_clientside_assets(app: Any, route: str = DEFAULT_ASSETS_ROUTE) -> list[str]:
    """Serve bundled JS assets from a Dash app and return their script URLs.

    Use this before creating the Dash layout:

        app = Dash(__name__, external_scripts=clientside_script_urls())
        attach_clientside_assets(app)

    The helper registers a Flask route on ``app.server`` that serves the
    package's bundled ``upsetPlot.js`` and ``upsetCursor.js`` files.
    """

    try:
        from flask import send_from_directory
    except ImportError as exc:
        raise ImportError("attach_clientside_assets requires Flask, which is installed with Dash.") from exc

    clean_route = route.rstrip("/")
    endpoint = f"dash_plotly_upset_assets_{abs(hash(clean_route))}"

    if endpoint not in app.server.view_functions:

        @app.server.route(f"{clean_route}/<path:filename>", endpoint=endpoint)
        def _serve_dash_plotly_upset_asset(filename: str):
            return send_from_directory(package_assets_path(), filename)

    return clientside_script_urls(clean_route)
