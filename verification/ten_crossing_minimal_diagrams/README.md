# Ten-crossing minimal-diagram certificates

This directory certifies that every minimal diagram of each unresolved
ten-crossing knot in the input snapshot has diagram unknotting number exactly
three.

## Pair obstruction

`two_change_determinants.json` contains all 45 crossing pairs for each of ten
standard minimal alternating PD diagrams. Every changed diagram has determinant
different from one, so none is the unknot. The file also contains controls on
`5_1` and `7_1`.

## Three-change witnesses

`three_change_unknot_certificates.json` contains one triple for each knot. For
every changed PD code it records the Wirtinger presentation and nine explicit
Tietze eliminations to a presentation with one free generator and no relators.
The presentation code includes positive and negative controls on `3_1`, `4_1`,
`5_1`, and `7_1`.

By the minimal-diagram alternating theorem and the Tait flyping theorem, the pair
obstruction and triple witnesses transport to every minimal diagram.

Rebuild the files with

```bash
python3 code/exhaust_two_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/two_change_determinants.json
python3 code/certify_three_changes_minimal_diagrams.py "$WORKBOOK" \
  --output build/three_change_unknot_certificates.json --quiet
```

This is a diagram-level theorem. It does not assert that the ordinary unknotting
number of any of these knots is three.
