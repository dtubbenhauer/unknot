.PHONY: verify verify-checksums reproduce-new rebuild-alexander-complete verify-alexander-witnesses rebuild-strengthening rebuild-full-owens rebuild-ten-crossing rebuild-11a14 rebuild-higher-montesinos rebuild-u1-index paper checksums

WORKBOOK ?= knotinfo_data_complete.xls
BUILD_DIR ?= build

verify:
	python3 verify_repository.py

verify-checksums:
	sha256sum -c SHA256SUMS

reproduce-new: rebuild-alexander-complete verify-alexander-witnesses rebuild-strengthening rebuild-full-owens rebuild-ten-crossing

rebuild-alexander-complete:
	mkdir -p $(BUILD_DIR)
	python3 code/complete_alexander_scan.py "$(WORKBOOK)" --output $(BUILD_DIR)/complete_alexander_scan.json

verify-alexander-witnesses: rebuild-alexander-complete
	mkdir -p $(BUILD_DIR)
	python3 code/verify_complete_alexander_witnesses.py "$(WORKBOOK)" --scan $(BUILD_DIR)/complete_alexander_scan.json --output $(BUILD_DIR)/direct_rank_verification.json

rebuild-strengthening:
	mkdir -p $(BUILD_DIR)/lower_bounds
	python3 code/knotinfo_strengthening_scan.py "$(WORKBOOK)" --tex paper/big_data_unknotting.tex --output-dir $(BUILD_DIR)/lower_bounds

rebuild-full-owens:
	mkdir -p $(BUILD_DIR)
	python3 code/full_owens_correction_terms.py "$(WORKBOOK)" --knots 10_6 10_47 10_61 10_76 10_100 --output $(BUILD_DIR)/full_owens_five_knots.json --quiet

rebuild-ten-crossing:
	mkdir -p $(BUILD_DIR)
	python3 code/exhaust_two_changes_minimal_diagrams.py "$(WORKBOOK)" --output $(BUILD_DIR)/two_change_determinants.json
	python3 code/certify_three_changes_minimal_diagrams.py "$(WORKBOOK)" --output $(BUILD_DIR)/three_change_unknot_certificates.json --quiet

rebuild-11a14:
	python3 verification/11a14/enumerate_minimal_diagrams.py
	python3 verification/11a14/check_one_crossing_changes.py
	python3 verification/11a14/run_11a14_minimal_pd_two_swap_scan_lean.py

rebuild-higher-montesinos:
	python3 lower_bounds/montesinos_signature_sharp/run_montesinos_spin_scan.py

rebuild-u1-index:
	python3 data/build_knotinfo_u1_jones_index.py

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error big_data_unknotting.tex

checksums:
	find . -type f ! -path './.git/*' ! -path './build/*' ! -path './.venv/*' ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.aux' ! -name '*.fdb_latexmk' ! -name '*.fls' ! -name '*.log' ! -name '*.out' ! -name '*.synctex.gz' ! -name '*.toc' ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
