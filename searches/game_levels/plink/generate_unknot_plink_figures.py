#!/usr/bin/env python3
"""Regenerate all PLink/TikZ and PNG files listed in research_levels.json."""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT = BASE / "figures"
OUT.mkdir(parents=True, exist_ok=True)
COORD = re.compile(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)")


def levels():
    data = json.loads((BASE / "research_levels.json").read_text())
    for item in data["prime_panel"]:
        yield item["figure_stem"], item["pd"]
    for item in data["connected_sum_challenges"]:
        yield item["figure_stem"], item["pd"]


def main() -> None:
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
    records = list(levels())
    with tempfile.TemporaryDirectory() as directory:
        helper = Path(directory) / "plink_one.py"
        helper.write_text(helper_text)
        for stem, pd in records:
            output_stem = f"game_{stem}_plink"
            tikz_path = OUT / f"{output_stem}.tex"
            subprocess.run(
                ["xvfb-run", "-a", "python", str(helper), stem, repr(pd), str(tikz_path)],
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
            figure.savefig(OUT / f"{output_stem}.png", dpi=180, facecolor="white")
            plt.close(figure)
    print(f"wrote {len(records)} PLink diagrams to {OUT}")


if __name__ == "__main__":
    main()
