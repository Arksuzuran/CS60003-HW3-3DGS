# NeurIPS LaTeX Template

This folder contains the official NeurIPS 2026 style files plus a simplified
starter document for writing a course report.

## Files

- `neurips_2026.sty`: official style file from NeurIPS
- `neurips_2026.tex`: official formatting instructions sample
- `checklist.tex`: official NeurIPS checklist template
- `report.tex`: recommended starting point for your report
- `references.bib`: BibTeX file for your references
- `figures/`: put images and plots here
- `build.ps1`: local build script

## Recommended workflow

1. Edit `report.tex`
2. Add citations to `references.bib`
3. Put figures into `figures/`
4. Compile with `.\build.ps1`

## Notes

- `report.tex` uses `\usepackage[preprint]{neurips_2026}` so author names are
  shown, which is more suitable for a class report than anonymous submission.
- If you later need a real anonymous submission version, change that line to
  `\usepackage{neurips_2026}`.
- The current environment does not have `pdflatex`, `latexmk`, or `tectonic`
  installed yet, so the template is prepared but not compiled here.
