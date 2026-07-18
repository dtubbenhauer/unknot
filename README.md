# Categorification of some Penrose polynomials

This repository contains supplementary computational material for joint work with
Daniel W. Collison, titled

> Categorification of some Penrose polynomials

The arXiv version will be available at

> https://arxiv.org/abs/2607.01632

The repository contains one main file:

1. `mobius_homology_colab.ipynb`, a self-contained Google Colab notebook for
   computing the homology associated with a perfect-matching ribbon graph using
   the Möbius Frobenius algebra construction.

The goal is transparency: the notebook gives an executable version of the
construction, including the local Frobenius algebra maps, the cube of
smoothings, the differentials, the check that the differential squares to zero,
and the resulting homology dimensions.

## Contact

If you find any errors in the paper **please email me**:

[dtubbenhauer@gmail.com](mailto:dtubbenhauer@gmail.com?subject=[GitHub]%web-reps)

Same goes for any errors related to this page.

## Main file

### `mobius_homology_colab.ipynb`

This notebook is the recommended entry point. It is self-contained and is meant
to run directly in Google Colab.

The input is a finite graph together with a chosen perfect matching. The
matching edges are the edges that are smoothed. Each smoothing choice gives a
state of a cube, and each state gives a collection of circles.

For a state \(\alpha\), the notebook forms the chain-group summand

$$
    V_\alpha = V^{\otimes k_\alpha},
$$

where \(k_\alpha\) is the number of circles in the smoothing associated with
\(\alpha\). The homological degree is the number of one-smoothings in
\(\alpha\).

The Frobenius algebra used in the notebook is

$$
    V=\mathbb Q[x,y]/(x^n, y^3-xy).
$$

For the default value `n = 1`, this specializes to

$$
    V=\mathbb Q[y]/(y^3),
$$

with basis

$$
    1,\quad y,\quad y^2.
$$

The Frobenius trace is chosen so that, for `n = 1`,

$$
    \epsilon(y^2)=3,
$$

and the trace is zero on the other basis elements. From this data, the notebook
constructs multiplication, the Frobenius pairing, and the corresponding
comultiplication.

The differential is assembled edge-by-edge in the cube of smoothings. Along a
cube edge, exactly one smoothing changes. The notebook compares the actual
circle decompositions before and after the change and applies the corresponding
local map:

- multiplication \(\mu\), when two circles merge into one;
- comultiplication \(\Delta\), when one circle splits into two;
- the Möbius map \(m\), when one circle remains one circle but passes through a
  Möbius-type local change.

The notebook tracks the actual circle components, not just the number of
circles. This matters because the local map has to be applied to the correct
tensor factor or tensor factors inside \(V^{\otimes k}\).

The signs in the differential are the usual cube signs: when changing the
\(j\)-th smoothing coordinate, the sign is determined by the number of
one-smoothings before coordinate \(j\).

After building the differentials, the notebook checks

$$
    d_{i+1}d_i=0
$$

for all homological degrees. It then computes

$$
    H^i = \ker(d_i)/\mathrm{im}(d_{i-1})
$$

using exact rational linear algebra.

The final output includes:

- the number of circles in every smoothing state;
- whether \(d^2=0\);
- the homology dimensions by homological degree;
- the corresponding Poincare polynomial.

## Requirements

The notebook is designed for Google Colab. No Sage installation is required.

It uses:

1. `sympy`, for exact rational matrices, ranks, and kernels;
2. `itertools`, `collections`, and other standard-library Python modules.

Google Colab already provides `sympy`. If running locally instead, install it
with

```bash
python3 -m pip install sympy
```

The computation avoids floating-point linear algebra. Matrix ranks, nullities,
and homology dimensions are computed over exact rational numbers.

## Examples

Open `mobius_homology_colab.ipynb` in Google Colab and run all cells from top to
bottom.

The editable input cell has the form

```python
pairs = [[2, 3], [3, 2], [1, 0], [0, 1]]
matching = [[0, 1], [2, 3]]
n = 1

MH = MobiusHomology(pairs, matching, n=n)

print("circle counts:", MH.state_circle_counts())
print("d^2 = 0:", MH.check_d_squared())
print("homology dimensions:", MH.homology_dimensions())
print("Poincare polynomial:", MH.poincare_polynomial())
```

Here:

- `pairs` encodes the ordinary graph-edge pairings;
- `matching` encodes the perfect-matching edges whose smoothings form the cube;
- `n` is the Frobenius algebra parameter.

For this example, the expected output is

```text
circle counts: [[2], [1, 1], [1]]
d^2 = 0: True
homology dimensions: [6, 1, 1]
Poincare polynomial: t**2 + t + 6
```

This means that the cube of smoothings has one state with two circles in
homological degree zero, two states with one circle in homological degree one,
and one state with one circle in homological degree two. The resulting homology
has dimensions

$$
    \dim H^0=6,\qquad \dim H^1=1,\qquad \dim H^2=1,
$$

so the Poincare polynomial is

$$
    6+t+t^2.
$$

## What the notebook is doing

The computation proceeds in five steps.

First, the notebook enumerates all smoothing states. If there are \(r\)
matching edges, then there are \(2^r\) states. A state is a binary vector of
length \(r\).

Second, for each state, the notebook constructs the actual smoothed circle
components. These components are stored combinatorially, so that the code knows
which tensor factor corresponds to which circle.

Third, the notebook constructs the cube differential. It only connects states
that differ in exactly one smoothing coordinate. This avoids the common mistake
of connecting all states in adjacent homological degrees.

Fourth, along each genuine cube edge, the notebook identifies the local change
in the circle decomposition. Depending on the change, it inserts \(\mu\),
\(\Delta\), or \(m\), together with identity maps on all unaffected tensor
factors.

Fifth, the notebook assembles the differential matrices, checks that their
successive products are zero, and computes the homology by exact rank-nullity
linear algebra.

Thus the notebook computes the actual chain complex, not only the graded Euler
characteristic and not only the number of circles in each smoothing.

## Important conventions

The notebook uses the following conventions.

- Homological degree is the number of one-smoothings.
- Cube signs are determined by the number of earlier one-smoothings.
- The local map is chosen from the actual circle change:
  \(2\to 1\) gives \(\mu\), \(1\to 2\) gives \(\Delta\), and \(1\to 1\) gives
  the Möbius map \(m\).
- Linear algebra is over \(\mathbb Q\).
- The displayed Poincare polynomial records only homological degree.

## Relation to the paper

The computations are intended to support examples and checks in the paper

> TBA

joint with Daniel W. Collison.

The arXiv placeholder is

```text
arXiv:TBA
```

The suggested citation is:

```bibtex
@misc{CollisonTubbenhauerMobiusHomologyData,
  author = {Collison, D.W. and Tubbenhauer, D.},
  title = {Code, data and more for ``{C}ategorification of some {P}enrose polynomials''},
  year = {2026},
  url = \url{https://github.com/dtubbenhauer/graphhomology}
}
```

## Repository contents

Current intended contents:

```text
README.md
LICENSE
mobius_homology_colab.ipynb
```

Additional examples, corrected notebooks, or output files may be added later.

## Erratum

Empty so far.
