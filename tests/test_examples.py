import importlib.util
from pathlib import Path
import pytest


def test_basic_dash_example_click_callback():
    pytest.importorskip("dash")
    path = Path(__file__).resolve().parents[1] / "examples/basic_dash_app.py"
    spec = importlib.util.spec_from_file_location("basic_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = module.app.server.test_client()
    response = client.post("/_dash-update-component", json={
        "output": "selection.data",
        "outputs": {"id": "selection", "property": "data"},
        "inputs": [
            {"id": "upset", "property": "clickData", "value": {
                "points": [{"customdata": ["intersection", "101", "Example"]}]}},
            {"id": "clear", "property": "n_clicks", "value": 0},
        ],
        "state": [{"id": "selection", "property": "data", "value": None}],
        "changedPropIds": ["upset.clickData"],
    })
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.json["response"]["selection"]["data"]["id"] == "101"


def test_figure_keeps_set_sizes_and_matrix_on_separate_axes():
    from dash_plotly_upset import demo_items, make_upset_figure
    fig = make_upset_figure(demo_items(), ["long_sepal", "wide_sepal", "long_petal"])
    for n in (2, 3, 4):
        assert fig.layout[f"xaxis{n}"].anchor == f"y{n}"
        assert fig.layout[f"yaxis{n}"].anchor == f"x{n}"
    assert fig.layout.xaxis3.range[1] > max(fig.data[1].x)
