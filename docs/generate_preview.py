from pathlib import Path
from dash_plotly_upset import demo_items, make_upset_figure

figure = make_upset_figure(
    demo_items(), ["long_sepal", "wide_sepal", "long_petal"],
    min_size=1, top_n=20, title="Set intersections", height=600,
)
figure.update_layout(width=1100)
figure.write_image(Path(__file__).with_name("preview.png"), scale=1.5)
