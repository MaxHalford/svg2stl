#!/usr/bin/env python

import argparse
import pathlib
from xml.dom import minidom

import gmsh
import numpy as np
from svg.path import parse_path
from svg.path import Close, CubicBezier, Line, Move


def parse_svg_into_steps(path: str) -> list:
    path_str = minidom.parse(path).getElementsByTagName("path")[0].getAttribute("d")
    return parse_path(path_str)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert an SVG into an STL.")
    parser.add_argument("svg_path", type=str, help="path towards an SVG file")
    parser.add_argument("--thickness", default=1, type=float)
    parser.add_argument("--definition", default=5, type=int)
    parser.add_argument("--show", dest="show", action="store_true", default=False)
    args = parser.parse_args()

    steps = parse_svg_into_steps(args.svg_path)

    # Interpolate points

    shapes = []
    shape = []

    for step in steps:

        if isinstance(step, Line):
            shape.append([step.start.real, step.start.imag])

        elif isinstance(step, Close):
            shapes.append(shape)
            shape = []

        elif not isinstance(step, Move):
            for t in np.linspace(0, 1, args.definition, endpoint=False):
                p = step.point(t)
                shape.append([p.real, p.imag])

    x_min, y_min = np.vstack(shapes).min(axis=0)
    x_max, y_max = np.vstack(shapes).max(axis=0)
    x_pad = 0.1 * (x_max - x_min)
    y_pad = 0.1 * (y_max - y_min)
    corners = [
        [x_min - x_pad, y_min - y_pad],
        [x_min - x_pad, y_max + y_pad],
        [x_max + x_pad, y_max + y_pad],
        [x_max + x_pad, y_min - y_pad],
    ]
    shapes.append(corners)

    # Build walls

    gmsh.initialize()
    gmsh.model.add("test")

    z_floor = 0
    z_ceiling = args.thickness

    factory = gmsh.model.geo
    floor_lines = []
    ceiling_lines = []
    wall_lines = []

    for shape in shapes:

        floor_lines.append([])
        floor_points = [factory.addPoint(*shape[0], z_floor)]
        for vertex in shape[1:]:
            floor_points.append(factory.addPoint(*vertex, z_floor))
            floor_lines[-1].append(factory.addLine(floor_points[-2], floor_points[-1]))
        floor_lines[-1].append(factory.addLine(floor_points[-1], floor_points[0]))

        ceiling_lines.append([])
        ceiling_points = [factory.addPoint(*shape[0], z_ceiling)]
        for vertex in shape[1:]:
            ceiling_points.append(factory.addPoint(*vertex, z_ceiling))
            ceiling_lines[-1].append(
                factory.addLine(ceiling_points[-2], ceiling_points[-1])
            )
        ceiling_lines[-1].append(factory.addLine(ceiling_points[-1], ceiling_points[0]))

        wall_lines.append([])
        for floor_point, ceiling_point in zip(floor_points, ceiling_points):
            wall_line = factory.addLine(floor_point, ceiling_point)
            wall_lines[-1].append(wall_line)

        for i in range(1, len(floor_lines[-1])):
            wall = factory.addCurveLoop(
                [
                    floor_lines[-1][i - 1],
                    wall_lines[-1][i],
                    -ceiling_lines[-1][i - 1],
                    -wall_lines[-1][i - 1],
                ]
            )
            factory.addPlaneSurface([wall])
        wall = factory.addCurveLoop(
            [
                floor_lines[-1][-1],
                wall_lines[-1][0],
                -ceiling_lines[-1][-1],
                -wall_lines[-1][-1],
            ]
        )
        factory.addPlaneSurface([wall])

    floor = []
    for lines in floor_lines:
        hole = factory.addCurveLoop(lines)
        floor.append(hole)
    factory.addPlaneSurface(floor)

    ceiling = []
    for lines in ceiling_lines:
        hole = factory.addCurveLoop(lines)
        ceiling.append(hole)
    factory.addPlaneSurface(ceiling)

    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate()

    gmsh.write(str(pathlib.Path(args.svg_path).with_suffix(".stl")))

    if args.show:
        gmsh.fltk.run()
