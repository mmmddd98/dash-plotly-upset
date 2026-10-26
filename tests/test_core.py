from dash_plotly_upset import (
    compute_exclusive_intersections,
    demo_items,
    parse_click_data,
    selected_items,
)


SET_COLUMNS = ["long_sepal", "wide_sepal", "long_petal"]


def test_compute_exclusive_intersections_counts_patterns() -> None:
    items = demo_items()
    intersections = compute_exclusive_intersections(items, SET_COLUMNS)
    counts = dict(zip(intersections["intersection_id"], intersections["size"]))

    assert counts["101"] == 5
    assert counts["111"] == 1
    assert counts["010"] == 1


def test_selected_items_filters_exclusive_intersection() -> None:
    items = demo_items()
    selected = selected_items(items, SET_COLUMNS, {"kind": "intersection", "id": "101", "label": "long_sepal & long_petal"})

    assert selected["item_id"].tolist() == ["iris_004", "iris_005", "iris_006", "iris_008", "iris_009"]


def test_selected_items_filters_set() -> None:
    items = demo_items()
    selected = selected_items(items, SET_COLUMNS, {"kind": "set", "id": "long_petal", "label": "long_petal"})

    assert len(selected) == 6
    assert selected["long_petal"].all()


def test_parse_click_data() -> None:
    click_data = {"points": [{"customdata": ["intersection", "101", "long_sepal & long_petal"]}]}

    assert parse_click_data(click_data) == {
        "kind": "intersection",
        "id": "101",
        "label": "long_sepal & long_petal",
    }
