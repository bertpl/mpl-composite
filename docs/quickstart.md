# Quickstart

Build a figure by composing elements on a grid, then render it and save it.

## Compose, add, render

Every figure is built the same way:

- **Create** a `CompositeFigure`.
- **Add** elements to grid cells with `add(row, col, element)`, nesting a `Composite` for a sub-layout.
- **Render** with `render()`, then write the result out with `save_figure()`.

```python
from mpl_composite import CompositeFigure, Composite, Text, Spacer, save_figure

fig = CompositeFigure(fig_inch_per_unit=4.0)
fig.add(0, 0, Text(1.0, 0.15, "Quarterly report"))

body = Composite()
body.add(0, 0, Text(0.4, 0.1, "Revenue"))
body.add(0, 1, Spacer(0.1, 0.1))
body.add(1, 0, Spacer(0.1, 0.1))
body.add(1, 1, Text(0.4, 0.1, "Costs"))
fig.add(1, 0, body, margin=0.05)

rendered = fig.render()
save_figure(rendered, "report.png")
```

## What happens

Element sizes are given in **layout units**, and the figure sizes itself to its content; `fig_inch_per_unit` sets the overall scale in inches. `margin` insets a nested element within its cell.

For richer elements — plots, tables, legends — browse the [Gallery](gallery/index.md) and the [API Reference](reference/figure.md). The [Concepts](concepts.md) page explains the model underneath.
