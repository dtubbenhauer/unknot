# Correction notice

## Owens zero-class orientation

The earlier repository snapshot and an earlier paper draft used the wrong
orientation in the zero-class part of the Owens obstruction. For the correctly
oriented positive Goeritz lattice of an alternating knot,

```text
m_G(0) = -sigma(K)/4.
```

Consequently, the zero-class comparison is equality in the signature-sharp
setting and does not give the claimed obstruction. The former batches of 245
signature-four, 164 signature-six, and 24 signature-eight certificates have been
removed from this repository.

The corrected scan checks all 653 gapped signature-four targets, all 164 gapped
signature-six targets, and all 24 gapped signature-eight targets with the proper
orientation. It finds zero zero-class obstructions.

Five conclusions survive using stronger necessary conditions: one determinant
obstruction and four complete discriminant-group obstructions. They are recorded
in `lower_bounds/owens/valid_determinant_group_certificates.csv`.

## Ten-crossing knots

The corrected full Owens comparison does not prove ordinary unknotting number
three for `10_47`, `10_100`, or any of the other eligible ten-crossing knots.
Their ordinary unknotting intervals remain `[2,3]`.

What is proved is the diagrammatic statement that every minimal diagram of each
of the ten unresolved ten-crossing knots has diagram unknotting number exactly
three. The complete pair and triple certificates are in
`verification/ten_crossing_minimal_diagrams/`.

## KnotInfo input consistency

The source snapshot lists `12n873` with interval `[1,3]` and algebraic
unknotting number two. The corrected interval used here is `[2,3]`; see
`data/12n873_correction.csv`.
