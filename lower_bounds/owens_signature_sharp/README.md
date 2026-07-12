# Higher signature-sharp Owens certificates

`run_signature_sharp_zero_class_scan.py` is the generalized exact zero-class
calculation.  It handles the signature-six and signature-eight batches by setting
`k=3` or `k=4`.

```bash
python lower_bounds/owens_signature_sharp/run_signature_sharp_zero_class_scan.py \
  --k 3 \
  -o lower_bounds/owens_signature_sharp/signature6_zero_class_results.csv \
  --summary lower_bounds/owens_signature_sharp/signature6_zero_class_summary.json

python lower_bounds/owens_signature_sharp/run_signature_sharp_zero_class_scan.py \
  --k 4 \
  -o lower_bounds/owens_signature_sharp/signature8_zero_class_results.csv \
  --summary lower_bounds/owens_signature_sharp/signature8_zero_class_summary.json
```

The KnotInfo CSV is located automatically from `database-knotinfo`; an explicit path
may be supplied first.  The CSV files are mirrored by formatted XLSX workbooks.  The signature-six batch gives 152 exact values `u=4` and
twelve improvements from `[3,5]` to `[4,5]`.  The signature-eight batch gives 24
exact values `u=5`.
