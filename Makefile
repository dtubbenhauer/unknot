.PHONY: verify rebuild-11a14 rebuild-higher-montesinos rebuild-u1-index checksums

verify:
	python verify_repository.py

rebuild-11a14:
	python verification/11a14/enumerate_minimal_diagrams.py
	python verification/11a14/check_one_crossing_changes.py
	python verification/11a14/run_11a14_minimal_pd_two_swap_scan_lean.py

rebuild-higher-montesinos:
	python lower_bounds/montesinos_signature_sharp/run_montesinos_spin_scan.py

rebuild-u1-index:
	python data/build_knotinfo_u1_jones_index.py

checksums:
	find . -type f ! -path './.git/*' ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
