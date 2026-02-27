#!/usr/bin/env bash
set -euo pipefail

CV_TEX="CV/Phil_LeMaitre_CV.tex"
OUT_DIR="assets/files/CV"
OUT_PDF="${OUT_DIR}/Phil_LeMaitre_CV.pdf"

mkdir -p "${OUT_DIR}"

# Tectonic writes the PDF to the same directory as the .tex by default.
# We compile into a temp build dir and then copy the output PDF where we want it.
BUILD_DIR="$(mktemp -d)"
cp -r cv "${BUILD_DIR}/cv"

pushd "${BUILD_DIR}/cv" >/dev/null

# Compile (run enough times automatically)
tectonic -X compile Phil_LeMaitre_CV.tex --outdir .

popd >/dev/null

cp "${BUILD_DIR}/CV/Phil_LeMaitre_CV.pdf" "${OUT_PDF}"
echo "Wrote ${OUT_PDF}"
