# Corrected Owens computations

The former zero-class batches are not retained. Their checkerboard orientation
was wrong; with the correct orientation, the zero class is equality and gives no
signature-sharp obstruction.

## Valid positive certificates

`valid_determinant_group_certificates.csv` contains the five conclusions that
survive stronger necessary conditions:

- one knot for which the Owens determinant equation has no solution;
- four knots for which every candidate matrix has the wrong discriminant group.

The exact group data are recorded as complete primary exponent profiles, not only
prime nullities.

## Full ten-crossing non-obstruction records

- `full_correction_terms_10_47_10_100.json`;
- `full_correction_terms_10_6_10_61_10_76.json`.

These files contain the oriented Goeritz correction-term functions, every allowed
Owens matrix, every candidate correction-term function, all group isomorphisms
tested, and the first failed condition for each rejected isomorphism. Each knot
has at least one surviving isomorphism, so the full Owens test does not establish
ordinary unknotting number three.

The files are reproduced by `code/knotinfo_strengthening_scan.py` and
`code/full_owens_correction_terms.py`.
