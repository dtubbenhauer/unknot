# Signature-four Owens certificates

`run_signature4_owens_scan.py` reconstructs positive Goeritz matrices from the
KnotInfo PD codes, enumerates the finite Owens candidate matrices and performs the
zero-class comparison using exact rational arithmetic.

The paper's fixed target list is `owens_u2_sharp_signature_kills.csv`.  Rebuild the
full certificates with

```bash
python lower_bounds/owens_u2/run_signature4_owens_scan.py \
  --targets lower_bounds/owens_u2/owens_u2_sharp_signature_kills.csv \
  -o lower_bounds/owens_u2/owens_u2_full_certificates.csv \
  --summary lower_bounds/owens_u2/owens_u2_summary.json
```

The KnotInfo CSV is located automatically from `database-knotinfo`; an explicit path
may be supplied as the positional argument.  The same table is also provided as `owens_u2_full_certificates.xlsx`.  There are 245 successful certificates:
237 exact values `u=3` and eight lower-bound improvements from `[2,4]` to `[3,4]`.
