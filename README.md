# svg2stl

This repository provides a script which takes as input an SVG such as this one:

![example.svg]

It outputs an [STL file](https://www.wikiwand.com/en/STL_(file_format)) like this one:

![example.png]

The resulting solid is a cuboid with holes in it. It essentially adds a third dimension to the SVG file. The purpose of the output STL is to be fed into a 3D printer. The end goal is to make a physical [stencil](https://www.wikiwand.com/en/Stencil) for artistic purposes.

## Installation

```sh
git clone https://github.com/MaxHalford/svg2stl
cd svg2stl
pip install -r requirements.txt
```

## Usage

You can generate an STL with the same name as the input file like this:

```py
python svg2stl.py example.svg --thickness 4
```

You can also show what this looks like in a GUI:

```py
python svg2stl.py example.svg --thickness 4 --show
```

## How it works

- The SVG file is parsed into a sequence of steps thanks to [`svg.path`](https://github.com/regebro/svg.path).
- Each step is turned into 2D geometric coordinates by sampling from each step's parametric equation with [`numpy`](https://numpy.org/).
- Each coordinate is duplicated so that there are top and bottom coordinates.
- The coordinates are stitched together to define panes: a floor, a ceiling, and many walls.
- [`pygmsh`](https://github.com/nschloe/pygmsh) does the heavy lifting. It generates a mesh of triangles from the panes through [constrained Delaunay triangulation](https://www.wikiwand.com/en/Constrained_Delaunay_triangulation).

## Motivation

There are some websites out there that already do this. Like [this](https://svg2stl.com/), [this](https://activmap.github.io/svg-to-stl/), and [this](https://github.com/rcalme/svg-to-stl). But they're websites, and sometimes it's nice to be able to do this from the command line. Especially if you want to process many SVGs.

## License

The MIT License (MIT). Please see the [license file](LICENSE) for more information.
