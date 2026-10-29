# A-1 追試 分析ノート

生成: 2026-10-29 10:07:11 JST（スクリプトが自動生成。手で編集しない）
設定: seed = 20261024, boot_R = 5000, duration_fraction = 0.25, SESOI r = 0.10, cfa_min_n = 100
入出力: raw_dir = raw/synthetic, data_dir = data_synthetic, out_dir = output_synthetic

## 入力
- ファイル: raw/synthetic/altruism_study_synthetic.csv
- MD5: 1fac165093f81a89ee102b37bbce9605
- 重複リスト: なし
- Page Times: raw/synthetic/PageTimes_synthetic.csv (MD5 10a1a98a1dcfbe850e60be4ecfe8cc7b)

## 来歴
- セッション: synth001
- 行数 130、開始 130、完了 130
| app_version | git_commit | otree_version | cfg_endowment | cfg_dg_step | cfg_use_hexaco | lang | n_finished |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v0.5-synthetic | synthetic | 5.11.5 | 1000 | 1 | 1 | ja | 130 |

## 除外（リストワイズ。原研究 preprocessing.R と同じ基準）
- 所要時間の閾値: 中央値 614 秒 × 0.25 = 153 秒
- 重複判定: dup_list なし（0 件として処理）
| reason | label | n_flagged | n_only_this | n_order1 | n_order2 |
| --- | --- | --- | --- | --- | --- |
| finished | 完了（支払い対象） | 130 |  | 65 | 65 |
| cq | 注意チェック不正解（cq1 != 1 または cq2 != 6） | 12 | 12 | 5 | 7 |
| check | 理解確認に 2 度不正解 | 6 | 6 | 4 | 2 |
| duration | 所要時間 < 中央値 614 秒 × 0.25 = 153 秒 | 3 | 3 | 2 | 1 |
| dup | 重複回答（同じメールアドレス、最初の回答以外） | 0 | 0 | 0 | 0 |
| excluded_any | いずれかに該当（リストワイズ除外） | 21 |  | 11 | 10 |
| analysis_sample | 分析対象 | 109 |  | 54 | 55 |
| info_fast_survey | 参考: 質問紙が速すぎる（< 2.0 秒/項目、分析対象のうち） | 5 | 0 | 1 | 4 |
| info_fast_dg | 参考: DG 決定ページが速すぎる（< 5 秒、分析対象のうち） | 1 | 0 | 0 | 1 |
| info_break | 参考: 1 ページに 600 秒以上滞在（中断の疑い、分析対象のうち） | 3 | 0 | 2 | 1 |

基準の重なり（除外者の内訳）:

| pattern | n |
| --- | --- |
| cq | 12 |
| check | 6 |
| duration | 3 |

## Page Times（ページごとの滞在秒数。1 ページ目の同意は前がないので除く）
- 速い回答の基準: 質問紙 < 2.0 秒/項目、DG 決定 < 5 秒。中断の基準: 1 ページ >= 600 秒。いずれも除外せずフラグのみ（感度分析 (f)(g)）
| page_base | page_type | n | median_sec | q10_sec | q90_sec | min_sec | max_sec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FabPage1 | survey | 130 | 121.000 | 71.800 | 205.400 | 9 | 296 |
| FabPage2 | survey | 130 | 121.000 | 71.800 | 205.400 | 9 | 296 |
| DGIntro | dg_intro | 130 | 85.000 | 52.000 | 145.200 | 9 | 986 |
| HexPage | survey | 130 | 80.500 | 47.800 | 136.400 | 6 | 197 |
| DGDecision | dg_decision | 130 | 54.000 | 31.900 | 91.200 | 4 | 132 |
| DGCheck | dg_check | 130 | 41.500 | 26.000 | 68.200 | 4 | 99 |
| PostSurvey | other | 130 | 41.500 | 26.000 | 68.200 | 4 | 99 |
| End | other | 130 | 7.000 | 4.000 | 11.100 | 1 | 16 |

## 尺度得点
- HG/PP/MC = 各 5 項目の平均（1–6）。逆転項目なし。欠損は na.rm（必須項目なので通常は欠損なし）
- hh_mean = HEXACO-60 正直さ-謙虚さ 10 項目（1–5）の平均（codebook の reverse = 1 の項目は 6 - x で逆転してから）。use_hexaco = 0 のセッションは NA
- dg_binary = dg_give > 0。dg_give は 1 回の入力（v0.5 から確認画面・入力し直しなし）。scale_order = 質問紙の段階順（1 = FAB→HEXACO, 2 = HEXACO→FAB）
- 出力: data_synthetic/clean.csv, data_synthetic/exclusion_table.csv, output_synthetic/descriptives.csv（sd は標本 SD、n は有効回答数）

## 主分析（02_main.R）
- 乱数 seed = 20261024（set.seed）。ブートストラップ: パーセンタイル法, R = 5000, 参加者単位でリサンプル
- H1: Spearman 相関（cor.test, exact = FALSE）。判定は 90% CI と SESOI による 3 段階。原研究の値が 95% CI に含まれるかは参考
- H2/H3: 二部モデル。Part 1 glm(binomial, logit)、Part 2 lm(log(dg_give))。予測子 = CFA factor scores (1 unit = 1 SD)、順序を固定効果。OR の CI は Wald、% 変化の CI は t 分布
- H4: 群ごとの Spearman + ブートストラップ CI、psych::r.test（独立相関の差）、交互作用は Part 1 のロジスティック
- H5（探索）: HEXACO 正直さ-謙虚さの平均 × dg_give の Spearman + ブートストラップ。原版と同じ 5 件法、FAB とは別の段階（段階順はランダム化、scale_order で記述的に確認）
- 感度分析 (f)(g): Page Times のフラグ（01_clean.R）で速い回答・中断を除いた場合
- 多重比較: 主検定は H1 のみ。相関行列は Holm 補正（psych::corr.test）。H4・H5・段階順は探索的
- 信頼性: psych::alpha, psych::omega(nfactors = 1)。減衰補正は rs / sqrt(ω_HG)（探索）
- 出力: output_synthetic/results.md, output_synthetic/results.json, output_synthetic/model_coefficients.csv, output_synthetic/sensitivity.csv, output_synthetic/corr_matrix_r.csv, output_synthetic/corr_matrix_p.csv

## 図（04_figures.R）
- 乱数 seed = 20261024（ジッタ）。Okabe–Ito パレット。PDF（ベクタ）と PNG（300 dpi）
- 散布図のジッタ: x ±0.04（HG 平均は 0.2 刻み）、HEXACO 図は x ±0.02（HH 平均は 0.1 刻み）、y なし。分布図の階級: 0 / 1–99 / 100 円幅（左閉区間）
- ファイル: fig_a_scatter.pdf, fig_a_scatter.png, fig_b_hist.pdf, fig_b_hist.png, fig_c_order.pdf, fig_c_order.png, fig_d_hexaco.pdf, fig_d_hexaco.png, fig_main.pdf, fig_main.png
- キャプション案: output_synthetic/fig_captions.md

## ソフトウェア
R version 4.3.3 (2024-02-29)
Platform: x86_64-pc-linux-gnu (64-bit)
patchwork 1.2.0, digest 0.6.34, jsonlite 1.8.8, lubridate 1.9.3, forcats 1.0.0, stringr 1.5.1, dplyr 1.1.4, purrr 1.0.2, readr 2.1.5, tidyr 1.3.1, tibble 3.2.1, ggplot2 3.4.4, tidyverse 2.0.0, utf8 1.2.4, generics 0.1.3, stringi 1.8.3, lattice 0.22-5, hms 1.1.3, magrittr 2.0.3, grid 4.3.3, timechange 0.3.0, Matrix 1.6-5, mgcv 1.9-1, fansi 1.0.5, scales 1.3.0, textshaping 0.3.7, cli 3.6.2, rlang 1.1.3, crayon 1.5.2, bit64 4.0.5, munsell 0.5.0, splines 4.3.3, withr 2.5.0, tools 4.3.3, parallel 4.3.3, tzdb 0.4.0, colorspace 2.1-0, vctrs 0.6.5, R6 2.5.1, lifecycle 1.0.4, bit 4.0.5, vroom 1.6.5, ragg 1.2.7, pkgconfig 2.0.3, pillar 1.9.0, gtable 0.3.4, glue 1.7.0, systemfonts 1.0.5, tidyselect 1.2.0, farver 2.1.1, nlme 3.1-164, labeling 0.4.3, compiler 4.3.3

## 主分析（02_main.R）
- 乱数 seed = 20261024（set.seed）。ブートストラップ: パーセンタイル法, R = 5000, 参加者単位でリサンプル
- H1: Spearman 相関（cor.test, exact = FALSE）。判定は 90% CI と SESOI による 3 段階。原研究の値が 95% CI に含まれるかは参考
- H2/H3: 二部モデル。Part 1 glm(binomial, logit)、Part 2 lm(log(dg_give))。予測子 = CFA factor scores (1 unit = 1 SD)、順序を固定効果。OR の CI は Wald、% 変化の CI は t 分布
- H4: 群ごとの Spearman + ブートストラップ CI、psych::r.test（独立相関の差）、交互作用は Part 1 のロジスティック
- H5（探索）: HEXACO 正直さ-謙虚さの平均 × dg_give の Spearman + ブートストラップ。原版と同じ 5 件法、FAB とは別の段階（段階順はランダム化、scale_order で記述的に確認）
- 感度分析 (f)(g): Page Times のフラグ（01_clean.R）で速い回答・中断を除いた場合
- 多重比較: 主検定は H1 のみ。相関行列は Holm 補正（psych::corr.test）。H4・H5・段階順は探索的
- 信頼性: psych::alpha, psych::omega(nfactors = 1)。減衰補正は rs / sqrt(ω_HG)（探索）
- 出力: output_synthetic/results.md, output_synthetic/results.json, output_synthetic/model_coefficients.csv, output_synthetic/sensitivity.csv, output_synthetic/corr_matrix_r.csv, output_synthetic/corr_matrix_p.csv

## 図（04_figures.R）
- 乱数 seed = 20261024（ジッタ）。Okabe–Ito パレット。PDF（ベクタ）と PNG（300 dpi）
- 散布図のジッタ: x ±0.04（HG 平均は 0.2 刻み）、HEXACO 図は x ±0.02（HH 平均は 0.1 刻み）、y なし。分布図の階級: 0 / 1–99 / 100 円幅（左閉区間）
- ファイル: fig_a_scatter.pdf, fig_a_scatter.png, fig_b_hist.pdf, fig_b_hist.png, fig_c_order.pdf, fig_c_order.png, fig_d_hexaco.pdf, fig_d_hexaco.png, fig_main.pdf, fig_main.png
- キャプション案: output_synthetic/fig_captions.md

## ソフトウェア
R version 4.3.3 (2024-02-29)
Platform: x86_64-pc-linux-gnu (64-bit)
patchwork 1.2.0, digest 0.6.34, jsonlite 1.8.8, lubridate 1.9.3, forcats 1.0.0, stringr 1.5.1, dplyr 1.1.4, purrr 1.0.2, readr 2.1.5, tidyr 1.3.1, tibble 3.2.1, ggplot2 3.4.4, tidyverse 2.0.0, utf8 1.2.4, generics 0.1.3, stringi 1.8.3, lattice 0.22-5, hms 1.1.3, magrittr 2.0.3, grid 4.3.3, timechange 0.3.0, Matrix 1.6-5, mgcv 1.9-1, fansi 1.0.5, scales 1.3.0, textshaping 0.3.7, cli 3.6.2, rlang 1.1.3, crayon 1.5.2, bit64 4.0.5, munsell 0.5.0, splines 4.3.3, withr 2.5.0, tools 4.3.3, parallel 4.3.3, tzdb 0.4.0, colorspace 2.1-0, vctrs 0.6.5, R6 2.5.1, lifecycle 1.0.4, bit 4.0.5, vroom 1.6.5, ragg 1.2.7, pkgconfig 2.0.3, pillar 1.9.0, gtable 0.3.4, glue 1.7.0, systemfonts 1.0.5, tidyselect 1.2.0, farver 2.1.1, nlme 3.1-164, labeling 0.4.3, compiler 4.3.3

