from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Iterable, Literal

import pandas as pd


SelectionKind = Literal["intersection", "set"]


@dataclass(frozen=True)
class Selection:
    kind: SelectionKind
    id: str
    label: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.id, "label": self.label}

    @classmethod
    def from_value(cls, value: "Selection | dict[str, Any] | None") -> "Selection | None":
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        kind = value.get("kind")
        if kind not in {"intersection", "set"}:
            return None
        selected_id = value.get("id")
        if selected_id is None:
            return None
        return cls(kind=kind, id=str(selected_id), label=str(value.get("label", selected_id)))


def compute_exclusive_intersections(
    items: pd.DataFrame | Iterable[dict[str, Any]],
    set_columns: list[str],
    *,
    min_size: int = 1,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Return exclusive UpSet intersections for boolean set columns.

    Each row represents exactly one membership pattern. For example, with
    set_columns ["A", "B"], pattern "10" means present in A and absent in B.
    """

    item_df = _as_frame(items)
    min_size = max(int(min_size or 1), 1)
    rows: list[dict[str, Any]] = []

    if item_df.empty or not set_columns:
        return _intersection_frame(rows)

    memberships = _membership_frame(item_df, set_columns)
    for bits_tuple in product((False, True), repeat=len(set_columns)):
        if not any(bits_tuple):
            continue

        mask = pd.Series(True, index=memberships.index)
        for col, expected in zip(set_columns, bits_tuple):
            mask &= memberships[col] == expected

        size = int(mask.sum())
        if size < min_size:
            continue

        active_sets = [col for col, active in zip(set_columns, bits_tuple) if active]
        bits = "".join("1" if active else "0" for active in bits_tuple)
        rows.append(
            {
                "intersection_id": bits,
                "label": " & ".join(active_sets),
                "active_sets": active_sets,
                "degree": len(active_sets),
                "size": size,
                "pattern": dict(zip(set_columns, bits_tuple)),
            }
        )

    rows.sort(key=lambda row: (-row["size"], -row["degree"], row["label"]))
    if top_n:
        rows = rows[: int(top_n)]
    for idx, row in enumerate(rows):
        row["x"] = idx
    return _intersection_frame(rows)


def compute_set_sizes(items: pd.DataFrame | Iterable[dict[str, Any]], set_columns: list[str]) -> pd.DataFrame:
    item_df = _as_frame(items)
    memberships = _membership_frame(item_df, set_columns)
    rows = [{"set": col, "size": int(memberships[col].sum())} for col in set_columns]
    return pd.DataFrame(rows).sort_values(["size", "set"], ascending=[True, True], ignore_index=True)


def selected_items(
    items: pd.DataFrame | Iterable[dict[str, Any]],
    set_columns: list[str],
    selection: Selection | dict[str, Any] | None,
) -> pd.DataFrame:
    """Return the rows represented by a Dash/Plotly click selection."""

    item_df = _as_frame(items)
    selection_obj = Selection.from_value(selection)
    if item_df.empty or selection_obj is None:
        return item_df.iloc[0:0].copy()

    memberships = _membership_frame(item_df, set_columns)
    if selection_obj.kind == "set":
        if selection_obj.id not in set_columns:
            return item_df.iloc[0:0].copy()
        return item_df.loc[memberships[selection_obj.id]].copy()

    bits = list(selection_obj.id or "")
    if len(bits) != len(set_columns):
        return item_df.iloc[0:0].copy()

    mask = pd.Series(True, index=item_df.index)
    for col, bit in zip(set_columns, bits):
        mask &= memberships[col] == (bit == "1")
    return item_df.loc[mask].copy()


def parse_click_data(click_data: dict[str, Any] | None) -> dict[str, str] | None:
    """Parse Dash Graph clickData produced by make_upset_figure."""

    if not click_data:
        return None
    points = click_data.get("points") or []
    if not points:
        return None
    customdata = points[0].get("customdata")
    if customdata is None or len(customdata) < 3:
        return None
    kind = str(customdata[0])
    if kind not in {"intersection", "set"}:
        return None
    return Selection(kind=kind, id=str(customdata[1]), label=str(customdata[2])).to_dict()


def demo_items() -> pd.DataFrame:
    """Small deterministic Iris-style dataset for examples and tests."""

    rows = [
        ("iris_001", "setosa", 5.1, 3.5, 1.4, 0.2, True, True, False),
        ("iris_002", "setosa", 4.9, 3.0, 1.4, 0.2, False, True, False),
        ("iris_003", "setosa", 5.0, 3.6, 1.4, 0.2, True, True, False),
        ("iris_004", "versicolor", 6.4, 3.2, 4.5, 1.5, True, False, True),
        ("iris_005", "versicolor", 5.9, 3.0, 4.2, 1.5, True, False, True),
        ("iris_006", "versicolor", 5.5, 2.3, 4.0, 1.3, True, False, True),
        ("iris_007", "virginica", 6.3, 3.3, 6.0, 2.5, True, True, True),
        ("iris_008", "virginica", 5.8, 2.7, 5.1, 1.9, True, False, True),
        ("iris_009", "virginica", 7.1, 3.0, 5.9, 2.1, True, False, True),
        ("iris_010", "setosa", 4.7, 3.2, 1.3, 0.2, False, False, False),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "item_id",
            "species",
            "sepal_length",
            "sepal_width",
            "petal_length",
            "petal_width",
            "long_sepal",
            "wide_sepal",
            "long_petal",
        ],
    )


def _as_frame(items: pd.DataFrame | Iterable[dict[str, Any]]) -> pd.DataFrame:
    if isinstance(items, pd.DataFrame):
        return items.copy()
    return pd.DataFrame(list(items))


def _membership_frame(item_df: pd.DataFrame, set_columns: list[str]) -> pd.DataFrame:
    if not set_columns:
        return pd.DataFrame(index=item_df.index)
    missing = [col for col in set_columns if col not in item_df.columns]
    if missing:
        raise KeyError(f"Missing set column(s): {', '.join(missing)}")
    return item_df[set_columns].fillna(False).astype(bool)


def _intersection_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    columns = ["intersection_id", "label", "active_sets", "degree", "size", "pattern", "x"]
    return pd.DataFrame(rows, columns=columns)
