#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CV_DIR="${ROOT_DIR}/assets/files/CV"
CV_TEX="${CV_DIR}/Phil_LeMaitre_CV.tex"
OUT_PDF="${CV_DIR}/Phil_LeMaitre_CV.pdf"

mkdir -p "${CV_DIR}"

BUILD_DIR="$(mktemp -d)"
trap 'rm -rf "${BUILD_DIR}"' EXIT
cp -R "${CV_DIR}" "${BUILD_DIR}/CV"

pushd "${ROOT_DIR}" >/dev/null
python3 scripts/update_talks_posters.py
python3 scripts/render_cv.py \
  --bib _bibliography/publications.bib \
  --out assets/files/CV/auto_publications.tex

pushd "${BUILD_DIR}/CV" >/dev/null
if command -v tectonic >/dev/null 2>&1; then
  tectonic -X compile "$(basename "${CV_TEX}")" --outdir .
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error "$(basename "${CV_TEX}")" >/dev/null
  pdflatex -interaction=nonstopmode -halt-on-error "$(basename "${CV_TEX}")" >/dev/null
else
  echo "Neither tectonic nor pdflatex is installed." >&2
  exit 1
fi

popd >/dev/null
popd >/dev/null

cp "${BUILD_DIR}/CV/Phil_LeMaitre_CV.pdf" "${OUT_PDF}"
echo "Wrote ${OUT_PDF}"
