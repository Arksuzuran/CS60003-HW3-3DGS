$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    if (Get-Command latexmk -ErrorAction SilentlyContinue) {
        latexmk -pdf report.tex
        exit $LASTEXITCODE
    }

    if (Get-Command pdflatex -ErrorAction SilentlyContinue) {
        pdflatex report.tex
        if (Test-Path references.bib) {
            bibtex report
            pdflatex report.tex
            pdflatex report.tex
        }
        exit $LASTEXITCODE
    }

    throw "No LaTeX engine found. Install TeX Live or MiKTeX, then rerun .\build.ps1"
}
finally {
    Pop-Location
}
