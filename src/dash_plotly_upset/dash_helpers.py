from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from .figure import make_upset_figure


DEFAULT_GRAPH_CONFIG = {
    "displayModeBar": True,
    "scrollZoom": False,
    "doubleClick": False,
    "modeBarButtonsToRemove": [
        "zoom2d",
        "pan2d",
        "select2d",
        "lasso2d",
        "zoomIn2d",
        "zoomOut2d",
        "autoScale2d",
        "resetScale2d",
    ],
}


def upset_graph(
    graph_id: str,
    items: pd.DataFrame | Iterable[dict[str, Any]],
    set_columns: list[str],
    *,
    selected: dict[str, Any] | None = None,
    min_size: int = 1,
    top_n: int | None = 35,
    title: str = "Interactive UpSet plot",
    height: int = 640,
    config: dict[str, Any] | None = None,
):
    """Create a Dash dcc.Graph with an UpSet figure.

    Dash is an optional dependency. Install with:
    pip install "dash-plotly-upset[dash]"
    """

    try:
        from dash import dcc
    except ImportError as exc:
        raise ImportError('Install Dash support with: pip install "dash-plotly-upset[dash]"') from exc

    return dcc.Graph(
        id=graph_id,
        figure=make_upset_figure(
            items,
            set_columns,
            selected=selected,
            min_size=min_size,
            top_n=top_n,
            title=title,
            height=height,
        ),
        config=DEFAULT_GRAPH_CONFIG if config is None else config,
    )

