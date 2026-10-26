from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html

from dash_plotly_upset import (
    DEFAULT_GRAPH_CONFIG,
    attach_clientside_assets,
    clientside_script_urls,
    demo_items,
    selected_items,
)


ITEMS = demo_items()
SET_COLUMNS = ["long_sepal", "wide_sepal", "long_petal"]


app = Dash(__name__, external_scripts=clientside_script_urls())
attach_clientside_assets(app)

app.layout = html.Div(
    [
        html.H1("Dash Plotly UpSet clientside example"),
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
        dcc.Store(id="items", data=ITEMS.to_dict("records")),
        dcc.Store(id="set-columns", data=SET_COLUMNS),
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


app.clientside_callback(
    """
    function(items, setCols, selected, minSize, topN) {
        return window.upsetPlot.makeFigure({
            items: items || [],
            setCols: setCols || [],
            selected: selected,
            minSize: minSize || 1,
            topN: topN || null
        });
    }
    """,
    Output("upset", "figure"),
    Input("items", "data"),
    Input("set-columns", "data"),
    Input("selection", "data"),
    Input("min-size", "value"),
    Input("top-n", "value"),
)


app.clientside_callback(
    """
    function(clickData, clearClicks, currentSelection) {
        const triggered = dash_clientside.callback_context.triggered;
        if (triggered.length > 0 && triggered[0].prop_id === "clear.n_clicks") {
            return null;
        }
        if (!clickData || !clickData.points || clickData.points.length === 0) {
            return currentSelection || null;
        }
        const cd = clickData.points[0].customdata;
        if (!cd || cd.length < 3) {
            return currentSelection || null;
        }
        return {kind: String(cd[0]), id: String(cd[1]), label: String(cd[2])};
    }
    """,
    Output("selection", "data"),
    Input("upset", "clickData"),
    Input("clear", "n_clicks"),
    State("selection", "data"),
    prevent_initial_call=True,
)


@app.callback(
    Output("selection-title", "children"),
    Output("selection-species", "figure"),
    Output("selection-table", "data"),
    Input("selection", "data"),
    State("items", "data"),
    State("set-columns", "data"),
)
def update_downstream(selection, items, set_columns):
    selected_df = selected_items(items or [], set_columns or [], selection)
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
