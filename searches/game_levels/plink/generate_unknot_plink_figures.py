from __future__ import annotations

import re
import subprocess
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt

OUT = Path('/mnt/data/unknot_plink_figs/figs')
OUT.mkdir(parents=True, exist_ok=True)

KNOTS = {
    '10_6': [[2,11,3,12],[4,16,5,15],[6,18,7,17],[8,20,9,19],[10,14,11,13],[12,1,13,2],[14,10,15,9],[16,6,17,5],[18,8,19,7],[20,4,1,3]],
    '10_11': [[2,15,3,16],[4,13,5,14],[6,2,7,1],[8,18,9,17],[10,20,11,19],[12,5,13,6],[14,3,15,4],[16,12,17,11],[18,10,19,9],[20,8,1,7]],
    '10_47': [[2,9,3,10],[4,11,5,12],[6,17,7,18],[8,1,9,2],[10,3,11,4],[12,5,13,6],[14,20,15,19],[16,14,17,13],[18,7,19,8],[20,16,1,15]],
    '10_51': [[2,18,3,17],[4,11,5,12],[6,13,7,14],[8,15,9,16],[10,19,11,20],[12,7,13,8],[14,5,15,6],[16,2,17,1],[18,9,19,10],[20,4,1,3]],
    '10_61': [[1,9,2,8],[3,16,4,17],[5,14,6,15],[7,1,8,20],[9,3,10,2],[11,19,12,18],[13,6,14,7],[15,4,16,5],[17,11,18,10],[19,13,20,12]],
    '10_76': [[2,11,3,12],[4,18,5,17],[6,20,7,19],[8,14,9,13],[10,16,11,15],[12,1,13,2],[14,10,15,9],[16,8,17,7],[18,6,19,5],[20,4,1,3]],
    '10_77': [[1,7,2,6],[3,14,4,15],[5,9,6,8],[7,3,8,2],[9,18,10,19],[11,20,12,1],[13,16,14,17],[15,4,16,5],[17,12,18,13],[19,10,20,11]],
    '10_79': [[6,2,7,1],[8,4,9,3],[12,6,13,5],[18,13,19,14],[16,9,17,10],[10,17,11,18],[20,15,1,16],[14,19,15,20],[2,8,3,7],[4,12,5,11]],
}

# The helper process needs a virtual display because PLink is Tk based.
HELPER = Path('/tmp/plink_one.py')
HELPER.write_text(textwrap.dedent(r'''
    import ast, sys
    from pathlib import Path
    from spherogram import Link
    import plink

    name, pd_literal, output = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    PD = ast.literal_eval(pd_literal)
    link = Link(PD)
    viewer = plink.LinkDisplay(title=name)
    link.view(viewer=viewer)
    viewer.window.update_idletasks()
    viewer.window.update()
    viewer.zoom_to_fit()
    viewer.window.update_idletasks()
    viewer.window.update()
    viewer.save_as_tikz(str(output), 'gray')
    viewer.window.destroy()
'''))

coord_re = re.compile(r'\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)')

for name, pd in KNOTS.items():
    tikz_path = OUT / f'{name}_plink.tex'
    cmd = ['xvfb-run', '-a', 'python', str(HELPER), name, repr(pd), str(tikz_path)]
    subprocess.run(cmd, check=True)

    text = tikz_path.read_text()
    segments = []
    for line in text.splitlines():
        if '\\draw ' not in line:
            continue
        pts = [(float(x), float(y)) for x, y in coord_re.findall(line)]
        if len(pts) >= 2:
            segments.append(pts)

    xs = [x for seg in segments for x, _ in seg]
    ys = [y for seg in segments for _, y in seg]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    width, height = xmax - xmin, ymax - ymin
    margin = 0.10 * max(width, height)

    # Keep a roughly square canvas, as in the existing PLink figures.
    side = max(width, height) + 2 * margin
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2

    fig = plt.figure(figsize=(5.2, 5.2), dpi=180)
    ax = fig.add_axes([0, 0, 1, 1])
    for seg in segments:
        x = [p[0] for p in seg]
        y = [p[1] for p in seg]
        ax.plot(x, y, color='black', linewidth=5.6, solid_capstyle='round', solid_joinstyle='round')
    ax.set_xlim(cx - side / 2, cx + side / 2)
    ax.set_ylim(cy - side / 2, cy + side / 2)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.savefig(OUT / f'{name}_plink.png', dpi=180, transparent=False, facecolor='white')
    plt.close(fig)

print(f'Wrote {len(KNOTS)} PLink diagrams to {OUT}')
