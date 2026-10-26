from __future__ import annotations

from typing import Any, Iterable

import pandas as pd
import plotly.graph_objects as go

from .core import Selection, compute_exclusive_intersections, compute_set_sizes


def make_upset_figure(
    items: pd.DataFrame | Iterable[dict[str, Any]],
    set_columns: list[str],
    *,
    selected: Selection | dict[str, Any] | None = None,
    min_size: int = 1,
    top_n: int | None = 35,
    title: str = "Interactive UpSet plot",
    height: int = 640,
    template: str = "plotly_white",
) -> go.Figure:
    """Build an interactive UpSet plot as a normal Plotly Figure."""

    selection = Selection.from_value(selected)
    intersections = compute_exclusive_intersections(items, set_columns, min_size=min_size, top_n=top_n)
    set_sizes = compute_set_sizes(items, set_columns)
    matrix_set_order = set_sizes["set"].tolist() if not set_sizes.empty else list(set_columns)

    fig = go.Figure()
    if intersections.empty:
        fig.update_layout(
            template=template,
            height=height,
            margin={"l": 40, "r": 35, "t": 95, "b": 35},
            annotations=[
                {
                    "text": "No intersections found with the current filters.",
                    "x": 0.5,
                    "y": 0.5,
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 15, "color": "#333333"},
                }
            ],
        )
        return fig

    n_intersections = len(intersections)
    x_range = [-0.75, n_intersections - 0.5]
    has_selection = selection is not None

    bar_x = intersections["x"].tolist()
    bar_y = intersections["size"].tolist()
    bar_colors = ["#111111" if _focus_intersection(row, selection) else "#CFCFCF" for row in intersections.to_dict("records")]
    bar_line_widths = [
        2.5 if selection and selection.kind == "intersection" and row["intersection_id"] == selection.id else 0
        for row in intersections.to_dict("records")
    ]
    intersection_customdata = [
        ["intersection", row["intersection_id"], row["label"]]
        for row in intersections.to_dict("records")
    ]

    fig.add_trace(
        go.Bar(
            x=bar_x,
            y=bar_y,
            width=0.65,
            xaxis="x2",
            yaxis="y2",
            marker={"color": bar_colors, "line": {"color": "#111111", "width": bar_line_widths}},
            text=[str(value) for value in bar_y],
            textposition="outside",
            textfont={"size": 11, "color": "#111111"},
            cliponaxis=False,
            customdata=intersection_customdata,
            hovertemplate="<b>Click to select intersection</b><br>"
            + "Intersection: %{customdata[2]}<br>"
            + "ID: %{customdata[1]}<br>"
            + "Items: %{y}<extra></extra>",
            name="Intersection size",
        )
    )

    set_names = set_sizes["set"].tolist()
    set_values = set_sizes["size"].tolist()
    set_bar_colors = ["#111111" if _focus_set(set_name, selection, intersections) else "#CFCFCF" for set_name in set_names]
    set_bar_line_widths = [
        2.5 if selection and selection.kind == "set" and selection.id == set_name else 0
        for set_name in set_names
    ]
    max_set_label_len = max((len(str(name)) for name in set_names), default=0)
    set_size_domain_end = min(0.30, max(0.22, 0.12 + max_set_label_len * 0.006))
    matrix_domain_start = min(0.39, set_size_domain_end + 0.045)

    fig.add_trace(
        go.Bar(
            orientation="h",
            x=set_values,
            y=set_names,
            xaxis="x3",
            yaxis="y3",
            marker={"color": set_bar_colors, "line": {"color": "#111111", "width": set_bar_line_widths}},
            text=[str(value) for value in set_values],
            textposition="outside",
            textfont={"size": 11, "color": "#111111"},
            cliponaxis=False,
            customdata=[["set", set_name, set_name] for set_name in set_names],
            hovertemplate="<b>Click to select set</b><br>Set: %{customdata[1]}<br>Items: %{x}<extra></extra>",
            name="Set size",
        )
    )

    for row in intersections.to_dict("records"):
        _add_matrix_column(fig, row, matrix_set_order, selection)

    fig.update_layout(
        template=template,
        title={"text": title, "x": 0.02, "y": 0.98, "yanchor": "top", "xanchor": "left", "font": {"size": 18, "color": "#111111"}},
        height=height,
        margin={"l": 40, "r": 35, "t": 95, "b": 35},
        showlegend=False,
        bargap=0.28,
        plot_bgcolor="white",
        paper_bgcolor="white",
        hoverlabel={"bgcolor": "white", "font_size": 12, "font_color": "#111111", "bordercolor": "#BBBBBB"},
        clickmode="event+select",
        dragmode=False,
        annotations=[
            {
                "text": _subtitle(selection, intersections, set_sizes),
                "x": 0.02,
                "y": 1.08,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "align": "left",
                "font": {"size": 12, "color": "#444444"},
            }
        ],
        xaxis2={
            "anchor": "y2",
            "domain": [matrix_domain_start, 1.0],
            "range": x_range,
            "fixedrange": True,
            "showticklabels": False,
            "showgrid": False,
            "zeroline": False,
            "showline": False,
        },
        yaxis2={
            "anchor": "x2",
            "domain": [0.45, 1.0],
            "title": {"text": "Intersection size", "font": {"size": 12}},
            "showgrid": True,
            "gridcolor": "#E8E8E8",
            "zeroline": False,
            "showline": True,
            "linecolor": "#111111",
            "ticks": "outside",
            "tickfont": {"size": 11},
        },
        xaxis3={
            "anchor": "y3",
            "domain": [0.0, set_size_domain_end],
            "range": [0, max(set_values, default=1) * 1.2],
            "title": {"text": "Set size", "font": {"size": 12}},
            "showgrid": True,
            "gridcolor": "#E8E8E8",
            "zeroline": False,
            "showline": True,
            "linecolor": "#111111",
            "ticks": "outside",
            "tickfont": {"size": 11},
            "automargin": True,
        },
        yaxis3={
            "anchor": "x3",
            "side": "left",
            "automargin": True,
            "domain": [0.0, 0.36],
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "tickfont": {"size": 12, "color": "#111111"},
            "categoryorder": "array",
            "categoryarray": matrix_set_order,
        },
        xaxis4={
            "anchor": "y4",
            "domain": [matrix_domain_start, 1.0],
            "range": x_range,
            "fixedrange": True,
            "showticklabels": False,
            "showgrid": False,
            "zeroline": False,
            "showline": False,
        },
        yaxis4={
            "anchor": "x4",
            "domain": [0.0, 0.36],
            "showticklabels": False,
            "showgrid": False,
            "zeroline": False,
            "showline": False,
            "categoryorder": "array",
            "categoryarray": matrix_set_order,
        },
    )
    return fig


def _add_matrix_column(fig: go.Figure, row: dict[str, Any], matrix_set_order: list[str], selection: Selection | None) -> None:
    x = row["x"]
    intersection_id = row["intersection_id"]
    label = row["label"]
    is_focus_col = _focus_intersection(row, selection)
    is_selected_col = bool(selection and selection.kind == "intersection" and selection.id == intersection_id)

    active_color = "#111111" if is_focus_col else "#BDBDBD"
    inactive_color = "#D0D0D0" if is_focus_col else "#EEEEEE"
    line_color = "#111111" if is_focus_col else "#BDBDBD"
    opacity = 1.0 if is_focus_col else 0.28

    pattern = row["pattern"]
    active_sets = [set_name for set_name in matrix_set_order if pattern.get(set_name) is True]
    inactive_sets = [set_name for set_name in matrix_set_order if pattern.get(set_name) is not True]
    customdata = ["intersection", intersection_id, label]

    if len(active_sets) >= 2:
        fig.add_trace(
            go.Scatter(
                mode="lines",
                x=[x, x],
                y=[active_sets[0], active_sets[-1]],
                xaxis="x4",
                yaxis="y4",
                line={"color": line_color, "width": 2.8 if is_selected_col else 1.9},
                opacity=opacity,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    if inactive_sets:
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=[x] * len(inactive_sets),
                y=inactive_sets,
                xaxis="x4",
                yaxis="y4",
                marker={"size": 7, "color": inactive_color, "line": {"color": inactive_color, "width": 0}},
                opacity=opacity,
                customdata=[customdata] * len(inactive_sets),
                hovertemplate="<b>Click to select intersection</b><br>"
                + "Intersection: %{customdata[2]}<br>"
                + "ID: %{customdata[1]}<br>"
                + "Set: %{y}<br>"
                + "Included: no<extra></extra>",
                showlegend=False,
            )
        )

    if active_sets:
        fig.add_trace(
            go.Scatter(
                mode="markers",
                x=[x] * len(active_sets),
                y=active_sets,
                xaxis="x4",
                yaxis="y4",
                marker={
                    "size": 13 if is_selected_col else 11,
                    "color": active_color,
                    "line": {"color": "#111111", "width": 2.5 if is_selected_col else 0},
                },
                opacity=opacity,
                customdata=[customdata] * len(active_sets),
                hovertemplate="<b>Click to select intersection</b><br>"
                + "Intersection: %{customdata[2]}<br>"
                + "ID: %{customdata[1]}<br>"
                + "Set: %{y}<br>"
                + "Included: yes<extra></extra>",
                showlegend=False,
            )
        )


def _focus_intersection(row: dict[str, Any], selection: Selection | None) -> bool:
    if selection is None:
        return True
    if selection.kind == "intersection":
        return row["intersection_id"] == selection.id
    if selection.kind == "set":
        return row["pattern"].get(selection.id) is True
    return True


def _focus_set(set_name: str, selection: Selection | None, intersections: pd.DataFrame) -> bool:
    if selection is None:
        return True
    if selection.kind == "set":
        return set_name == selection.id
    if selection.kind == "intersection":
        matches = intersections.loc[intersections["intersection_id"] == selection.id]
        if matches.empty:
            return False
        return matches.iloc[0]["pattern"].get(set_name) is True
    return True


def _subtitle(selection: Selection | None, intersections: pd.DataFrame, set_sizes: pd.DataFrame) -> str:
    if selection is None:
        return "Click an intersection bar, dot, or set-size bar to inspect its items."
    if selection.kind == "intersection":
        matches = intersections.loc[intersections["intersection_id"] == selection.id]
        if matches.empty:
            return "Selected intersection is not visible with the current filters."
        row = matches.iloc[0]
        return f"Selected intersection: {row['label']} - {row['size']} items"
    if selection.kind == "set":
        matches = set_sizes.loc[set_sizes["set"] == selection.id]
        if not matches.empty:
            return f"Selected set: {selection.id} - {int(matches.iloc[0]['size'])} items"
    return "Click an intersection bar, dot, or set-size bar to inspect its items."
