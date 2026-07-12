#!/usr/bin/env python3
"""
Core routines for the Montesinos correction-term obstruction.

Input: Montesinos fractions from the KnotInfo table.
Output: for each knot, compute d-invariants of the negative-definite Seifert
plumbing for the branched double cover (or its reverse), then test every affine
identification compatible with the linking form against the Ni-Wu correction-term
formula for D/2 surgery.

The dictionary below keeps the original six 11-crossing examples as a small
smoke test.  The full batch used in the paper is run by
montesinos_d_obstruction_scan.py.

Dependencies: Python 3, sympy.
"""
from fractions import Fraction
from itertools import product
import sympy as sp
from math import floor

KNOTS = {
    '11n_138': [Fraction(2,3), Fraction(-1,3), Fraction(-4,7)],
    '11n_122': [Fraction(2,3), Fraction(-2,3), Fraction(3,7)],
    '11n_51' : [Fraction(1,2), Fraction(2,3), Fraction(-8,11)],
    '11n_60' : [Fraction(1,2), Fraction(-2,3), Fraction(7,11)],
    '11n_17' : [Fraction(1,2), Fraction(3,5), Fraction(-3,7)],
    '11n_3'  : [Fraction(1,2), Fraction(-3,5), Fraction(5,7)],
}

def fmt_frac(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"

def neg_cf(alpha, beta):
    """Negative continued fraction alpha/beta=[a1,...,ak]^-, ai>=2."""
    a = []
    x = Fraction(alpha, beta)
    while x.denominator != 1:
        ai = (x.numerator + x.denominator - 1)//x.denominator
        a.append(ai)
        x = 1/(Fraction(ai,1)-x)
    a.append(x.numerator)
    return a

def normalize_fracs(fracs):
    b = 0
    pairs = []
    for r in fracs:
        fl = floor(r)
        b += fl
        s = r - fl
        if s:
            pairs.append((s.denominator, s.numerator))
    return b, pairs

def reverse_seifert(b, pairs):
    n = len(pairs)
    return -b-n, [(a, a-beta) for a, beta in pairs]

def seifert_e(b, pairs):
    e = Fraction(b,1)
    for a,beta in pairs:
        e += Fraction(beta, a)
    return e

def star_matrix(b, pairs):
    weights = [b]
    edges = []
    arms = []
    for alpha,beta in pairs:
        cf = neg_cf(alpha,beta)
        arms.append(cf)
        prev = 0
        for ai in cf:
            idx = len(weights)
            weights.append(-ai)
            edges.append((prev,idx))
            prev = idx
    n = len(weights)
    Q = sp.zeros(n)
    for i,w in enumerate(weights):
        Q[i,i] = w
    for i,j in edges:
        Q[i,j] = Q[j,i] = 1
    return Q, weights, arms

def frac_mod1(x):
    x = Fraction(x)
    return x - (x.numerator//x.denominator)

def key_of_x(Qinv, x):
    n = len(x)
    out = []
    for i in range(n):
        val = sum(Fraction(int(Qinv[i,j].p), int(Qinv[i,j].q))*x[j] for j in range(n))
        out.append(frac_mod1(val))
    return tuple(out)

def d_plumbing(Q, weights):
    """d via max_{Char class} (K^2+n)/4 for this negative-definite plumbing."""
    n = len(weights)
    Qinv = Q.inv()
    diag = [int(Q[i,i]) for i in range(n)]
    ranges = []
    for w in diag:
        ranges.append([v for v in range(w, -w+1) if (v-w) % 2 == 0])
    best = {}
    bestk = {}
    for k in product(*ranges):
        x = [(k[i]-diag[i])//2 for i in range(n)]
        key = key_of_x(Qinv, x)
        k2 = Fraction(0,1)
        for i in range(n):
            for j in range(n):
                qij = Qinv[i,j]
                k2 += Fraction(int(qij.p), int(qij.q))*k[i]*k[j]
        d = (k2+n)/4
        if key not in best or d > best[key]:
            best[key] = d
            bestk[key] = k
    reps = {key: tuple((bestk[key][i]-diag[i])//2 for i in range(n)) for key in best}
    return best, reps

def add_key(Qinv, reps, a, b):
    x = tuple(reps[a][i] + reps[b][i] for i in range(len(reps[a])))
    return key_of_x(Qinv, x)

def scalar_key(Qinv, reps, a, m):
    x = tuple(m*reps[a][i] for i in range(len(reps[a])))
    return key_of_x(Qinv, x)

def self_link(Qinv, x):
    n = len(x)
    val = Fraction(0,1)
    for i in range(n):
        for j in range(n):
            val += Fraction(int(Qinv[i,j].p), int(Qinv[i,j].q))*x[i]*x[j]
    return frac_mod1(-val)

def order(Qinv, reps, a):
    zero = key_of_x(Qinv, tuple(0 for _ in reps[a]))
    k = zero
    for m in range(1, 10000):
        k = add_key(Qinv, reps, k, a)
        if k == zero:
            return m
    raise RuntimeError('order search failed')

def d_lens(p, q):
    from functools import lru_cache
    @lru_cache(None)
    def d(p,q,i):
        if p == 1:
            return Fraction(0,1)
        q %= p
        r = p % q
        j = i % q
        return Fraction(-1,4) + Fraction((2*i+1-p-q)**2, 4*p*q) - (Fraction(0,1) if q == 1 else d(q,r,j))
    return [d(p,q,i) for i in range(p)]

def possible_N(N):
    """Check N_i=max(V_floor(i/2), V_ceil((D-i)/2)) for nonincreasing V_j."""
    D = len(N)
    m = (D+1)//2
    constraints = []
    for i,nv in enumerate(N):
        a = i//2
        b = (D-i+1)//2
        constraints.append((a,b,nv))
    vals = sorted(set(N+[0]), reverse=True)
    V = [None]*(m+1)
    def ok_partial():
        for j in range(m):
            if V[j] is not None and V[j+1] is not None and V[j] < V[j+1]:
                return False
        for a,b,nv in constraints:
            va, vb = V[a], V[b]
            if va is not None and va > nv: return False
            if vb is not None and vb > nv: return False
            if va is not None and vb is not None and max(va,vb) != nv: return False
        return True
    def rec(j):
        if j == m+1:
            return V.copy() if ok_partial() else None
        upper = max(vals) if j == 0 else V[j-1]
        for val in vals:
            if val <= upper:
                V[j] = val
                if ok_partial():
                    ans = rec(j+1)
                    if ans is not None:
                        return ans
        V[j] = None
        return None
    return rec(0)

def test_knot(name, fracs):
    b, pairs = normalize_fracs(fracs)
    e = seifert_e(b,pairs)
    if e > 0:
        b_use, pairs_use = reverse_seifert(b,pairs)
        orientation = 'reverse of KnotInfo Montesinos orientation'
    else:
        b_use, pairs_use = b, pairs
        orientation = 'KnotInfo Montesinos orientation'
    Q, weights, arms = star_matrix(b_use, pairs_use)
    D = abs(int(Q.det()))
    if not all(complex(ev.evalf()).real < -1e-9 for ev in Q.eigenvals()):
        raise RuntimeError(f'{name}: plumbing is not negative definite')
    dmap, reps = d_plumbing(Q, weights)
    if len(dmap) != D:
        raise RuntimeError(f'{name}: expected {D} spin-c classes, got {len(dmap)}')
    Qinv = Q.inv()
    gens = []
    for key,x in reps.items():
        if order(Qinv, reps, key) == D:
            sl = self_link(Qinv, x)
            if sl in (Fraction(2,D), frac_mod1(Fraction(-2,D))):
                gens.append((key,sl))
    L = d_lens(D,2)
    counts = {'graph':0, 'minus_graph':0}
    niwu_counts = {'graph':0, 'minus_graph':0}
    examples = {}
    for sign,label in [(1,'graph'), (-1,'minus_graph')]:
        for g,sl in gens:
            for c in reps.keys():
                N = []
                basic = True
                for i in range(D):
                    key = add_key(Qinv, reps, c, scalar_key(Qinv, reps, g, i))
                    dy = sign*dmap[key]
                    diff = L[i]-dy
                    if diff.denominator != 1 or diff < 0 or diff % 2 != 0:
                        basic = False
                        break
                    N.append(int(diff//2))
                if basic:
                    counts[label] += 1
                    V = possible_N(N)
                    if V is not None:
                        niwu_counts[label] += 1
                        examples[label] = (sl,N,V)
    return {
        'name': name,
        'fractions': fracs,
        'normalized': (b,pairs,e),
        'used': (b_use,pairs_use,seifert_e(b_use,pairs_use)),
        'orientation': orientation,
        'weights': weights,
        'arms': arms,
        'D': D,
        'num_generators': len(gens),
        'maps_per_orientation': len(gens)*D,
        'basic_counts': counts,
        'niwu_counts': niwu_counts,
        'd_values_sorted': sorted(dmap.values()),
    }

def main():
    print('Correction-term obstruction for u(K)=1')
    print('Testing both orientations and every affine H1-identification with self-linking ±2/D.\n')
    all_ok = True
    for name, fracs in KNOTS.items():
        r = test_knot(name, fracs)
        print(f"{name}: D={r['D']}, fractions=({', '.join(fmt_frac(x) for x in r['fractions'])})")
        b,pairs,e = r['normalized']
        bu,pu,eu = r['used']
        print(f"  normalized Seifert data: b={b}, pairs={pairs}, e={fmt_frac(e)}")
        print(f"  negative-definite data used: b={bu}, pairs={pu}, e={fmt_frac(eu)}")
        print(f"  plumbing weights: {r['weights']} ; arms={r['arms']}")
        print(f"  candidate generators: {r['num_generators']}; affine maps per orientation: {r['maps_per_orientation']}")
        print(f"  basic Ni-Wu even/nonnegative maps: graph={r['basic_counts']['graph']}, minus_graph={r['basic_counts']['minus_graph']}")
        print(f"  full Ni-Wu compatible maps: graph={r['niwu_counts']['graph']}, minus_graph={r['niwu_counts']['minus_graph']}")
        if r['niwu_counts']['graph'] or r['niwu_counts']['minus_graph']:
            all_ok = False
        print()
    if all_ok:
        print('Conclusion: all six are obstructed by the correction-term test, assuming the standard Montesinos-cover orientation conventions above.')
    else:
        print('Conclusion: at least one knot passed the test; inspect output.')

if __name__ == '__main__':
    main()
