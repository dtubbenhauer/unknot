#!/usr/bin/env python3
"""Generate the five rectilinear PLink figures used to organize the paper."""
from __future__ import annotations

import ast
import csv
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import database_knotinfo
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
TARGETS = ["10_47", "10_100", "11n_3", "11a_14", "12n_873"]
COORD = re.compile(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)")


def locate_snapshot() -> Path:
    root = Path(database_knotinfo.__file__).resolve().parent
    matches = list(root.rglob("knotinfo_data_complete.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one KnotInfo CSV, found {matches}")
    return matches[0]


def main() -> None:
    with locate_snapshot().open(newline="", encoding="utf-8") as handle:
        rows = {
            row["name"]: ast.literal_eval(row["pd_notation"])
            for row in csv.DictReader(handle, delimiter="|")
            if row.get("name") in TARGETS
        }
    if set(rows) != set(TARGETS):
        raise RuntimeError(f"missing PD rows: {sorted(set(TARGETS) - set(rows))}")

    helper_text = textwrap.dedent(
        r'''
        import ast, sys
        from pathlib import Path
        from spherogram import Link
        import plink
        name, pd_literal, output = sys.argv[1], sys.argv[2], Path(sys.argv[3])
        viewer = plink.LinkDisplay(title=name)
        Link(ast.literal_eval(pd_literal)).view(viewer=viewer)
        viewer.window.update_idletasks(); viewer.window.update()
        viewer.zoom_to_fit()
        viewer.window.update_idletasks(); viewer.window.update()
        viewer.save_as_tikz(str(output), 'gray')
        viewer.window.destroy()
        '''
    )
    with tempfile.TemporaryDirectory() as directory:
        helper = Path(directory) / "plink_one.py"
        helper.write_text(helper_text)
        for name in TARGETS:
            tikz_path = HERE / f"{name}_plink.tex"
            subprocess.run(
                ["xvfb-run", "-a", "python", str(helper), name, repr(rows[name]), str(tikz_path)],
                check=True,
            )
            segments = []
            for line in tikz_path.read_text().splitlines():
                if "\\draw " not in line:
                    continue
                points = [(float(x), float(y)) for x, y in COORD.findall(line)]
                if len(points) >= 2:
                    segments.append(points)
            xs = [x for segment in segments for x, _ in segment]
            ys = [y for segment in segments for _, y in segment]
            xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
            margin = 0.10 * max(xmax - xmin, ymax - ymin)
            side = max(xmax - xmin, ymax - ymin) + 2 * margin
            cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
            figure = plt.figure(figsize=(5.2, 5.2), dpi=180)
            axes = figure.add_axes([0, 0, 1, 1])
            for segment in segments:
                axes.plot(
                    [point[0] for point in segment],
                    [point[1] for point in segment],
                    color="black",
                    linewidth=5.6,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                )
            axes.set_xlim(cx - side / 2, cx + side / 2)
            axes.set_ylim(cy - side / 2, cy + side / 2)
            axes.set_aspect("equal")
            axes.axis("off")
            figure.savefig(HERE / f"{name}_plink.png", dpi=180, facecolor="white")
            plt.close(figure)
            print(f"wrote {name}")


if __name__ == "__main__":
    main()
