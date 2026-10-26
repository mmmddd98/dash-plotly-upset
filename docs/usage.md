# dash-plotly-upset

Reusable interactive UpSet plots for Plotly and Dash.

The package returns a normal `plotly.graph_objects.Figure`, so it drops into any
Dash app through `dcc.Graph`. Clicks on intersection bars, matrix dots, or set
size bars carry `customdata`, which lets your callbacks recover the selected
intersection and filter the original rows for any downstream plot.

## Install

From this repo:

```bash
pip install -e .
```

With Dash helpers:

```bash
pip install -e ".[dash]"
```

## Basic Plotly Usage

```python
from dash_plotly_upset import demo_items, make_upset_figure

items = demo_items()
set_columns = ["long_sepal", "wide_sepal", "long_petal"]

fig = make_upset_figure(items, set_columns, min_size=1, top_n=35)
fig.show()
```

Your input data is a `pandas.DataFrame` or list of records. Each row is one
item/entity, and each set column is boolean-like:

```text
item_id   species     sepal_length  petal_length  long_sepal  wide_sepal  long_petal
iris_001  setosa      5.1           1.4           True        True        False
iris_004  versicolor  6.4           4.5           True        False       True
```

## Dash Usage

There are two useful Dash integration styles:

- **Python figure callback:** Python builds the Plotly figure on the server.
  This is the easiest path.
- **Clientside figure callback:** the browser builds the Plotly figure using
  the included `upsetPlot.js` asset. This avoids a server roundtrip when filters
  or selections change.

### Python Figure Callback

```python
from dash import Dash, Input, Output, State, dcc, html
from dash_plotly_upset import make_upset_figure, parse_click_data, selected_items

items = your_dataframe
set_columns = ["long_sepal", "wide_sepal", "long_petal"]

app = Dash(__name__)
app.layout = html.Div([
    dcc.Store(id="upset-selection"),
    dcc.Graph(id="upset"),
    dcc.Graph(id="downstream-plot"),
])

@app.callback(
    Output("upset-selection", "data"),
    Input("upset", "clickData"),
    State("upset-selection", "data"),
)
def store_selection(click_data, current):
    return parse_click_data(click_data) or current

@app.callback(
    Output("upset", "figure"),
    Input("upset-selection", "data"),
)
def draw_upset(selection):
    return make_upset_figure(items, set_columns, selected=selection)

@app.callback(
    Output("downstream-plot", "figure"),
    Input("upset-selection", "data"),
)
def draw_downstream(selection):
    selected_df = selected_items(items, set_columns, selection)
    return make_any_plotly_figure_you_like(selected_df)
```

### Clientside Figure Callback

```python
from dash import Dash, Input, Output, dcc, html
from dash_plotly_upset import attach_clientside_assets, clientside_script_urls, demo_items

items = demo_items()
set_columns = ["long_sepal", "wide_sepal", "long_petal"]

app = Dash(__name__, external_scripts=clientside_script_urls())
attach_clientside_assets(app)
app.layout = html.Div([
    dcc.Store(id="items", data=items.to_dict("records")),
    dcc.Store(id="set-columns", data=set_columns),
    dcc.Store(id="selection"),
    dcc.Graph(id="upset"),
])

app.clientside_callback(
    """
    function(items, setCols, selected) {
        return window.upsetPlot.makeFigure({
            items: items || [],
            setCols: setCols || [],
            selected: selected,
            multiSelected: [],
            minSize: 1,
            topN: 35
        });
    }
    """,
    Output("upset", "figure"),
    Input("items", "data"),
    Input("set-columns", "data"),
    Input("selection", "data"),
)
```

In this mode the rows and set-column names live in Dash stores as JSON. Dash
sends those stores to the browser, `upsetPlot.js` computes the exclusive
intersections in the browser, and the callback returns a normal Plotly
`{data, layout}` figure object to `dcc.Graph`.

The browser-side figure builder also supports an optional `multiSelected`
argument. Use it when another part of your app lets users keep several
intersections or sets highlighted at the same time. Each entry should use the
same `kind` and `id` shape as a normal click selection; `color` is optional:

```javascript
window.upsetPlot.makeFigure({
    items: items || [],
    setCols: setCols || [],
    selected: selected,
    multiSelected: [
        {kind: "intersection", id: "101", label: "long_sepal & long_petal", color: "#2563eb"},
        {kind: "set", id: "wide_sepal", label: "wide_sepal", color: "#16a34a"}
    ],
    minSize: 1,
    topN: 35
});
```

`multiSelected` is capped at five entries in the plot renderer. If it is omitted
or empty, the figure behaves like the regular single-selection plot.

That last callback is the useful part: `selected_items(...)` gives you the exact
rows for the clicked exclusive intersection or the clicked set. You can use
those rows for histograms, scatter plots, tables, summary cards, or anything
else.

## Run the Example

```bash
pip install -e ".[dash]"
python examples/basic_dash_app.py
```

For the browser-side figure builder:

```bash
python examples/clientside_dash_app.py
```

Then open the local Dash URL printed by the command.

## API

- `make_upset_figure(items, set_columns, selected=None, min_size=1, top_n=35)`
  returns a Plotly figure.
- `parse_click_data(clickData)` turns Dash `dcc.Graph.clickData` into
  `{"kind": "intersection" | "set", "id": "...", "label": "..."}`.
- `selected_items(items, set_columns, selection)` returns the original rows
  represented by the selection.
- `compute_exclusive_intersections(items, set_columns)` returns the intersection
  table if you want to inspect or test the set logic directly.
- `demo_items()` returns a tiny example dataset.
- `clientside_script_urls()` returns the script URLs for the bundled browser
  assets.
- `attach_clientside_assets(app)` registers the Flask route that serves the
  bundled browser assets from an installed package.
- `window.upsetPlot.makeFigure({items, setCols, selected, multiSelected,
  minSize, topN})` builds the browser-side Plotly figure. `multiSelected` is
  optional and accepts up to five `{kind, id, label, color}` entries for
  simultaneous intersection or set highlights.
