#!/usr/bin/env python3
from fractions import Fraction
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import unknotting_number_one_d_invariant_obstruction as obs

name = sys.argv[1]
fracs = [Fraction(x) for x in sys.argv[2:]]
r = obs.test_knot(name, fracs)
out = {
    'det_plumbing': r['D'],
    'maps_per_orientation': r['maps_per_orientation'],
    'basic_graph': r['basic_counts']['graph'],
    'basic_minus_graph': r['basic_counts']['minus_graph'],
    'niwu_graph': r['niwu_counts']['graph'],
    'niwu_minus_graph': r['niwu_counts']['minus_graph'],
    'obstructed_basic': (r['basic_counts']['graph'] == 0 and r['basic_counts']['minus_graph'] == 0),
    'obstructed_full': (r['niwu_counts']['graph'] == 0 and r['niwu_counts']['minus_graph'] == 0),
}
print(json.dumps(out))
