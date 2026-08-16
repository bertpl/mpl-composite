# Concepts

## The element lifecycle

Every visual piece — a figure, a plot, a table, a text label — is an **element**, and rendering runs each element through three steps:

- **measure** — the element reports its size in layout units; nothing is drawn.
- **place** — given a region, the element builds its drawing canvas and places any children.
- **draw** — the element draws itself and its children onto that canvas.

Elements are composed into a tree first, then rendered. An element's size is fixed once placed, so the whole layout is resolved before anything is drawn.

## Composition and grids

A `CompositeFigure` is the root element, and layouts build up from a few pieces:

- **Grid placement** — `add(row, col, element)` places an element in a grid cell, with an optional `margin` insetting it.
- **Nesting** — a `Composite` holds a sub-grid inside a cell, so layouts can be built hierarchically.
- **Auto-sizing** — you never set an overall figure size; the figure measures its content and sizes itself to fit, and `fig_inch_per_unit` converts the measured layout to inches.

## Coordinate systems

Three coordinate spaces show up, depending on where you are drawing:

- **Layout units** — the abstract units elements are sized and placed in, scaled to physical inches by `fig_inch_per_unit` at render time.
- **Data coordinates** — inside a plot, x and y run in the data's own units, mapped through the axis (linear, log, or lin-log) onto the canvas.
- **Table plot coordinates** — inside a table, x runs over the summed column widths and y is the row index, top-down.
