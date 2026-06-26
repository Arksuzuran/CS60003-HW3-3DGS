$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

try {
    # 中文报告需用 XeLaTeX（xeCJK 依赖 XeTeX 引擎）
    if (Get-Command xelatex -ErrorAction SilentlyContinue) {
        xelatex -interaction=nonstopmode report.tex
        if (Test-Path references.bib) {
            bibtex report
            xelatex -interaction=nonstopmode report.tex
            xelatex -interaction=nonstopmode report.tex
        }
        exit $LASTEXITCODE
    }

    if (Get-Command latexmk -ErrorAction SilentlyContinue) {
        latexmk -xelatex report.tex
        exit $LASTEXITCODE
    }

    throw "未找到 xelatex。中文报告需要 XeLaTeX，请安装 TeX Live 或 MiKTeX（含 xelatex 与中文字体），然后重新运行 .\build.ps1"
}
finally {
    Pop-Location
}
