from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, callback_context, dash_table, dcc, html

from dash_plotly_upset import (
    DEFAULT_GRAPH_CONFIG,
    demo_items,
    make_upset_figure,
    parse_click_data,
    selected_items,
)


ITEMS = demo_items()
SET_COLUMNS = ["long_sepal", "wide_sepal", "long_petal"]


app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Dash Plotly UpSet example"),
        html.Div(
            [
                html.Button("Clear", id="clear", n_clicks=0),
                html.Label("Min size"),
                dcc.Input(id="min-size", type="number", value=1, min=1, step=1),
                html.Label("Top N"),
                dcc.Input(id="top-n", type="number", value=20, min=1, step=1),
            ],
            style={"display": "flex", "gap": "10px", "alignItems": "center", "marginBottom": "12px"},
        ),
        dcc.Store(id="selection"),
        dcc.Graph(id="upset", config=DEFAULT_GRAPH_CONFIG),
        html.H2(id="selection-title"),
        dcc.Graph(id="selection-species"),
        dash_table.DataTable(
            id="selection-table",
            page_size=8,
            sort_action="native",
            columns=[{"name": col, "id": col} for col in ITEMS.columns],
        ),
    ],
    style={"fontFamily": "Arial, sans-serif", "margin": "24px auto", "maxWidth": "1180px"},
)


@app.callback(
    Output("selection", "data"),
    Input("upset", "clickData"),
    Input("clear", "n_clicks"),
    State("selection", "data"),
    prevent_initial_call=True,
)
def update_selection(click_data, _clear_clicks, current_selection):
    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]["prop_id"] == "clear.n_clicks":
        return None
    return parse_click_data(click_data) or current_selection


@app.callback(
    Output("upset", "figure"),
    Input("selection", "data"),
    Input("min-size", "value"),
    Input("top-n", "value"),
)
def update_upset(selection, min_size, top_n):
    return make_upset_figure(
        ITEMS,
        SET_COLUMNS,
        selected=selection,
        min_size=min_size or 1,
        top_n=top_n,
    )


@app.callback(
    Output("selection-title", "children"),
    Output("selection-species", "figure"),
    Output("selection-table", "data"),
    Input("selection", "data"),
)
def update_downstream(selection):
    selected_df = selected_items(ITEMS, SET_COLUMNS, selection)
    if selected_df.empty:
        selected_df = pd.DataFrame(columns=ITEMS.columns)
        title = "No selection"
    else:
        title = f"{selection['kind']}: {selection['label']} ({len(selected_df)} rows)"

    fig = px.histogram(
        selected_df,
        x="species",
        title="Species counts for selected rows",
        template="plotly_white",
    )
    fig.update_layout(height=360)
    return title, fig, selected_df.to_dict("records")


if __name__ == "__main__":
    app.run(debug=True)
