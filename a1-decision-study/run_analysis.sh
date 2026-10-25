#!/usr/bin/env bash
# 解析パイプラインを順に実行する（macOS / Linux）。Windows は run_analysis.bat。
#   ./run_analysis.sh            本データ: raw/final → data/ → output/
#   ./run_analysis.sh synthetic  合成データ: 99_synthetic.R で生成 → raw/synthetic → data_synthetic/ → output_synthetic/
#   ./run_analysis.sh original   03_compare_original.R（OSF の公開データで比較基準を作る。ネットワークが必要）
# 本データと合成データの出力先は分けてある（混ぜない）。
set -euo pipefail
cd "$(dirname "$0")"
# 日本語の文言・図のために UTF-8 ロケールにする（未設定のときだけ）
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-$LANG}"
mode="${1:-real}"
case "$mode" in
  synthetic)
    export A1_RAW_DIR=raw/synthetic A1_DATA_DIR=data_synthetic A1_OUT_DIR=output_synthetic
    Rscript analysis/99_synthetic.R "${2:-130}" "${3:-1}"
    ;;
  real) ;;
  original) Rscript analysis/03_compare_original.R; exit 0 ;;
  *) echo "usage: $0 [real|synthetic [N seed]|original]"; exit 1 ;;
esac
Rscript analysis/01_clean.R
Rscript analysis/02_main.R
Rscript analysis/04_figures.R
echo "done: ${A1_OUT_DIR:-output}/results.md, analysis_notes.md, fig_*.pdf"
