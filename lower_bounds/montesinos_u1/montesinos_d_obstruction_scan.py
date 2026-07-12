#!/usr/bin/env python3
"""Batch correction-term scan for the Montesinos [1,a] targets up to 13 crossings.

This script is self-contained except for the helper functions in
unknotting_number_one_d_invariant_obstruction.py.  It reruns the finite
Ni-Wu parity/sign obstruction for the 50 parseable KnotInfo Montesinos entries
found in the scan.  The expected outcome is that 49 entries are obstructed and
12n_309 is not obstructed by this test.
"""
from fractions import Fraction
import csv, json, subprocess, sys
from pathlib import Path

KNOTS = {
    '11n_3': {'interval': '[1,2]', 'crossing': 11, 'determinant': 43, 'montesinos': 'K(1/2;-3/5;5/7)', 'fractions': [Fraction('1/2'), Fraction('-3/5'), Fraction('5/7')]},
    '11n_17': {'interval': '[1,2]', 'crossing': 11, 'determinant': 47, 'montesinos': 'K(1/2;3/5;-3/7)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-3/7')]},
    '11n_51': {'interval': '[1,2]', 'crossing': 11, 'determinant': 29, 'montesinos': 'K(1/2;2/3;-8/11)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-8/11')]},
    '11n_54': {'interval': '[1,2]', 'crossing': 11, 'determinant': 43, 'montesinos': 'K(1/2;2/3;-8/13)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-8/13')]},
    '11n_60': {'interval': '[1,2]', 'crossing': 11, 'determinant': 31, 'montesinos': 'K(1/2;-2/3;7/11)', 'fractions': [Fraction('1/2'), Fraction('-2/3'), Fraction('7/11')]},
    '11n_122': {'interval': '[1,2]', 'crossing': 11, 'determinant': 27, 'montesinos': 'K(2/3;-2/3;3/7)', 'fractions': [Fraction('2/3'), Fraction('-2/3'), Fraction('3/7')]},
    '11n_138': {'interval': '[1,2]', 'crossing': 11, 'determinant': 15, 'montesinos': 'K(2/3;-1/3;-4/7)', 'fractions': [Fraction('2/3'), Fraction('-1/3'), Fraction('-4/7')]},
    '12n_11': {'interval': '[1,2]', 'crossing': 12, 'determinant': 61, 'montesinos': 'K(1/2;-3/5;7/9)', 'fractions': [Fraction('1/2'), Fraction('-3/5'), Fraction('7/9')]},
    '12n_12': {'interval': '[1,2]', 'crossing': 12, 'determinant': 79, 'montesinos': 'K(1/2;3/5;-2/9)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-2/9')]},
    '12n_41': {'interval': '[1,2]', 'crossing': 12, 'determinant': 19, 'montesinos': 'K(1/2;-3/5;3/11)', 'fractions': [Fraction('1/2'), Fraction('-3/5'), Fraction('3/11')]},
    '12n_42': {'interval': '[1,2]', 'crossing': 12, 'determinant': 59, 'montesinos': 'K(1/2;-3/5;7/11)', 'fractions': [Fraction('1/2'), Fraction('-3/5'), Fraction('7/11')]},
    '12n_43': {'interval': '[1,2]', 'crossing': 12, 'determinant': 81, 'montesinos': 'K(1/2;3/5;-4/11)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-4/11')]},
    '12n_44': {'interval': '[1,2]', 'crossing': 12, 'determinant': 51, 'montesinos': 'K(1/2;3/5;-7/11)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-7/11')]},
    '12n_45': {'interval': '[1,2]', 'crossing': 12, 'determinant': 37, 'montesinos': 'K(1/2;-3/5;5/13)', 'fractions': [Fraction('1/2'), Fraction('-3/5'), Fraction('5/13')]},
    '12n_47': {'interval': '[1,2]', 'crossing': 12, 'determinant': 59, 'montesinos': 'K(1/2;3/5;-4/9)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-4/9')]},
    '12n_48': {'interval': '[1,2]', 'crossing': 12, 'determinant': 49, 'montesinos': 'K(1/2;3/5;-5/9)', 'fractions': [Fraction('1/2'), Fraction('3/5'), Fraction('-5/9')]},
    '12n_154': {'interval': '[1,2]', 'crossing': 12, 'determinant': 47, 'montesinos': 'K(1/2;2/3;-12/17)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-12/17')]},
    '12n_159': {'interval': '[1,2]', 'crossing': 12, 'determinant': 55, 'montesinos': 'K(1/2;-2/3;12/17)', 'fractions': [Fraction('1/2'), Fraction('-2/3'), Fraction('12/17')]},
    '12n_160': {'interval': '[1,2]', 'crossing': 12, 'determinant': 53, 'montesinos': 'K(1/2;-2/3;12/19)', 'fractions': [Fraction('1/2'), Fraction('-2/3'), Fraction('12/19')]},
    '12n_162': {'interval': '[1,2]', 'crossing': 12, 'determinant': 61, 'montesinos': 'K(1/2;2/3;-12/19)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-12/19')]},
    '12n_167': {'interval': '[1,3]', 'crossing': 12, 'determinant': 67, 'montesinos': 'K(1/2;2/3;-4/13)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-4/13')]},
    '12n_170': {'interval': '[1,2]', 'crossing': 12, 'determinant': 81, 'montesinos': 'K(1/2;2/3;-4/15)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-4/15')]},
    '12n_238': {'interval': '[1,2]', 'crossing': 12, 'determinant': 31, 'montesinos': 'K(1/2;2/3;-10/13)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-10/13')]},
    '12n_241': {'interval': '[1,2]', 'crossing': 12, 'determinant': 59, 'montesinos': 'K(1/2;2/3;-10/17)', 'fractions': [Fraction('1/2'), Fraction('2/3'), Fraction('-10/17')]},
    '12n_286': {'interval': '[1,2]', 'crossing': 12, 'determinant': 45, 'montesinos': 'K(2/3;-2/3;5/13)', 'fractions': [Fraction('2/3'), Fraction('-2/3'), Fraction('5/13')]},
    '12n_288': {'interval': '[1,2]', 'crossing': 12, 'determinant': 49, 'montesinos': 'K(1/2;5/7;-5/7)', 'fractions': [Fraction('1/2'), Fraction('5/7'), Fraction('-5/7')]},
    '12n_295': {'interval': '[1,2]', 'crossing': 12, 'determinant': 107, 'montesinos': 'K(2/3;3/5;-3/8)', 'fractions': [Fraction('2/3'), Fraction('3/5'), Fraction('-3/8')]},
    '12n_301': {'interval': '[1,2]', 'crossing': 12, 'determinant': 67, 'montesinos': 'K(2/3;-3/5;-5/8)', 'fractions': [Fraction('2/3'), Fraction('-3/5'), Fraction('-5/8')]},
    '12n_302': {'interval': '[1,2]', 'crossing': 12, 'determinant': 111, 'montesinos': 'K(2/3;2/3;-5/13)', 'fractions': [Fraction('2/3'), Fraction('2/3'), Fraction('-5/13')]},
    '12n_304': {'interval': '[1,3]', 'crossing': 12, 'determinant': 71, 'montesinos': 'K(1/2;5/7;-1/5)', 'fractions': [Fraction('1/2'), Fraction('5/7'), Fraction('-1/5')]},
    '12n_307': {'interval': '[1,3]', 'crossing': 12, 'determinant': 77, 'montesinos': 'K(1/2;5/7;-3/7)', 'fractions': [Fraction('1/2'), Fraction('5/7'), Fraction('-3/7')]},
    '12n_309': {'interval': '[1,2]', 'crossing': 12, 'determinant': 1, 'montesinos': 'K(1/2;-5/7;1/5)', 'fractions': [Fraction('1/2'), Fraction('-5/7'), Fraction('1/5')]},
    '12n_337': {'interval': '[1,2]', 'crossing': 12, 'determinant': 103, 'montesinos': 'K(2/3;3/5;-2/7)', 'fractions': [Fraction('2/3'), Fraction('3/5'), Fraction('-2/7')]},
    '12n_444': {'interval': '[1,2]', 'crossing': 12, 'determinant': 27, 'montesinos': 'K(2/3;-2/3;3/11)', 'fractions': [Fraction('2/3'), Fraction('-2/3'), Fraction('3/11')]},
    '12n_457': {'interval': '[1,2]', 'crossing': 12, 'determinant': 11, 'montesinos': 'K(2/3;-1/4;-2/7)', 'fractions': [Fraction('2/3'), Fraction('-1/4'), Fraction('-2/7')]},
    '12n_470': {'interval': '[1,2]', 'crossing': 12, 'determinant': 41, 'montesinos': 'K(2/3;-3/4;4/7)', 'fractions': [Fraction('2/3'), Fraction('-3/4'), Fraction('4/7')]},
    '12n_471': {'interval': '[1,2]', 'crossing': 12, 'determinant': 71, 'montesinos': 'K(2/3;3/4;-4/7)', 'fractions': [Fraction('2/3'), Fraction('3/4'), Fraction('-4/7')]},
    '12n_475': {'interval': '[1,2]', 'crossing': 12, 'determinant': 7, 'montesinos': 'K(2/3;-3/4;1/5)', 'fractions': [Fraction('2/3'), Fraction('-3/4'), Fraction('1/5')]},
    '12n_478': {'interval': '[1,2]', 'crossing': 12, 'determinant': 29, 'montesinos': 'K(2/3;-3/4;3/7)', 'fractions': [Fraction('2/3'), Fraction('-3/4'), Fraction('3/7')]},
    '12n_479': {'interval': '[1,2]', 'crossing': 12, 'determinant': 83, 'montesinos': 'K(2/3;3/4;-3/7)', 'fractions': [Fraction('2/3'), Fraction('3/4'), Fraction('-3/7')]},
    '12n_500': {'interval': '[1,2]', 'crossing': 12, 'determinant': 51, 'montesinos': 'K(1/2;-4/7;4/5)', 'fractions': [Fraction('1/2'), Fraction('-4/7'), Fraction('4/5')]},
    '12n_501': {'interval': '[1,2]', 'crossing': 12, 'determinant': 49, 'montesinos': 'K(1/2;4/7;-4/7)', 'fractions': [Fraction('1/2'), Fraction('4/7'), Fraction('-4/7')]},
    '12n_522': {'interval': '[1,3]', 'crossing': 12, 'determinant': 23, 'montesinos': 'K(2/3;-1/4;-4/5)', 'fractions': [Fraction('2/3'), Fraction('-1/4'), Fraction('-4/5')]},
    '12n_523': {'interval': '[1,2]', 'crossing': 12, 'determinant': 13, 'montesinos': 'K(2/3;-1/4;-4/7)', 'fractions': [Fraction('2/3'), Fraction('-1/4'), Fraction('-4/7')]},
    '12n_550': {'interval': '[1,2]', 'crossing': 12, 'determinant': 33, 'montesinos': 'K(2/3;-1/3;-8/13)', 'fractions': [Fraction('2/3'), Fraction('-1/3'), Fraction('-8/13')]},
    '12n_564': {'interval': '[1,2]', 'crossing': 12, 'determinant': 39, 'montesinos': 'K(2/3;-1/3;-8/11)', 'fractions': [Fraction('2/3'), Fraction('-1/3'), Fraction('-8/11')]},
    '12n_577': {'interval': '[1,2]', 'crossing': 12, 'determinant': 27, 'montesinos': 'K(2/3;-2/3;3/10)', 'fractions': [Fraction('2/3'), Fraction('-2/3'), Fraction('3/10')]},
    '12n_578': {'interval': '[1,2]', 'crossing': 12, 'determinant': 93, 'montesinos': 'K(2/3;2/3;-3/10)', 'fractions': [Fraction('2/3'), Fraction('2/3'), Fraction('-3/10')]},
    '12n_721': {'interval': '[1,3]', 'crossing': 12, 'determinant': 25, 'montesinos': 'K(1/2;4/5;-4/5)', 'fractions': [Fraction('1/2'), Fraction('4/5'), Fraction('-4/5')]},
    '12n_723': {'interval': '[1,2]', 'crossing': 12, 'determinant': 19, 'montesinos': 'K(1/2;4/7;-4/5)', 'fractions': [Fraction('1/2'), Fraction('4/7'), Fraction('-4/5')]},
}

FIELDS = ['knot','crossing','interval','determinant','montesinos','det_plumbing',
          'maps_per_orientation','basic_graph','basic_minus_graph','niwu_graph',
          'niwu_minus_graph','obstructed_basic','obstructed_full','error']


def main():
    here = Path(__file__).resolve().parent
    worker = here / 'montesinos_d_obstruction_worker.py'
    outpath = here / 'montesinos_d_obstruction_scan_u1_targets_up_to_13.csv'
    rows = []
    for name, data in KNOTS.items():
        cmd = [sys.executable, str(worker), name] + [str(x) for x in data['fractions']]
        base = {'knot': name, 'crossing': data['crossing'], 'interval': data['interval'],
                'determinant': data['determinant'], 'montesinos': data['montesinos']}
        try:
            cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=240, check=False)
            if cp.returncode != 0:
                raise RuntimeError(cp.stderr.strip() or cp.stdout.strip())
            ans = json.loads(cp.stdout)
            base.update(ans)
            base['error'] = ''
        except Exception as e:
            base.update({'error': repr(e)})
        rows.append(base)
        print(name, 'obstructed=' + str(base.get('obstructed_full')), 'error=' + str(base.get('error')))
    with open(outpath, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in rows:
            for field in FIELDS:
                row.setdefault(field, '')
            w.writerow(row)
    obstructed = [r for r in rows if r.get('obstructed_full')]
    print('Wrote', outpath)
    print('Obstructed', len(obstructed), 'of', len(rows))

if __name__ == '__main__':
    main()
