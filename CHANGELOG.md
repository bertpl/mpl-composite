# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Classic x/y plot element family: framed plot area with grid, drawn axes with ticks and labels, title

### Changed

### Deprecated

### Removed

### Fixed

### Security

## 0.1.0 (2026-07-07)

### Added

- Geometry primitives for composite layout: ranges, grids, alignment, margins
- Vectorized linear/log/lin-log coordinate transforms and line/text/theme style objects
- Data axes with linear/log/lin-log scales and automatic tick generation
- Element-local drawing canvas with renderer-based text measurement
- The composite-figure engine: element tree, grid layout with margins and alignment, nested z-ordering, auto-sized figures
## 0.0.3 (2026-07-07)

### Added

- Package now ships type information (`py.typed`)
- PyPI metadata: supported Python versions, typing and license classifiers

### Changed

- Project is now MIT licensed (was Apache-2.0)
- README badges and splash are now served from the repo / shields.io instead of GitHub Pages

### Security

- Releases now ship SLSA build provenance and a GitHub Release with the changelog excerpt
## 0.0.2 (2025-11-07)

### Changed

- Internal development-workflow changes only; no functional changes

## 0.0.1 (2025-11-01)

### Added

- Initial project setup & framework
