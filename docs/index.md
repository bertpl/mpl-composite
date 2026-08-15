# mpl-composite

A matplotlib wrapper for building composite figures — layouts assembled from reusable elements
(plots, tables, legends, text) placed on a grid, instead of hand-managed subplot axes.

Every visual piece is an **element** with a `measure → place → draw` lifecycle. A `CompositeFigure`
composes elements on a grid, sizes itself from their measured content, and renders to a matplotlib
figure you can save in any format.

## Install

```bash
pip install mpl-composite
```

## A first figure

```python
from mpl_composite import CompositeFigure, Text, save_figure

fig = CompositeFigure(fig_inch_per_unit=4.0)
fig.add(0, 0, Text(1.0, 0.15, "Hello, composite"))

rendered = fig.render()
save_figure(rendered, "hello.png")
```
