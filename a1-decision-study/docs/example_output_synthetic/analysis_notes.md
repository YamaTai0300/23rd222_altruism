# A-1 追試 分析ノート

生成: 2026-10-24 12:53:34 JST（スクリプトが自動生成。手で編集しない）
設定: seed = 20261024, boot_R = 5000, duration_fraction = 0.25, SESOI r = 0.10, cfa_min_n = 100
入出力: raw_dir = raw/synthetic, data_dir = data_synthetic, out_dir = output_synthetic

## 入力
- ファイル: raw/synthetic/altruism_study_synthetic.csv
- MD5: 8dad1df6df64af9d798a6fe441cee4b5
- 重複リスト: なし
- Page Times: raw/synthetic/PageTimes_synthetic.csv (MD5 247596ad0caf0bb306481299b8757ecd)

## 来歴
- セッション: synth001
- 行数 130、開始 130、完了 130
| app_version | git_commit | otree_version | cfg_endowment | cfg_dg_step | cfg_use_hexaco | lang | n_finished |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v0.3-synthetic | synthetic | 5.11.5 | 1000 | 1 | 1 | ja | 130 |

## 除外（リストワイズ。原研究 preprocessing.R と同じ基準）
- 所要時間の閾値: 中央値 603 秒 × 0.25 = 151 秒
- 重複判定: dup_list なし（0 件として処理）
| reason | label | n_flagged | n_only_this | n_order1 | n_order2 |
| --- | --- | --- | --- | --- | --- |
| finished | 完了（支払い対象） | 130 |  | 65 | 65 |
| cq | 注意チェック不正解（cq1 != 1 または cq2 != 6） | 11 | 11 | 5 | 6 |
| check | 理解確認に 2 度不正解 | 4 | 4 | 4 | 0 |
| duration | 所要時間 < 中央値 603 秒 × 0.25 = 151 秒 | 3 | 3 | 3 | 0 |
| dup | 重複回答（同じメールアドレス、最初の回答以外） | 0 | 0 | 0 | 0 |
| excluded_any | いずれかに該当（リストワイズ除外） | 18 |  | 12 | 6 |
| analysis_sample | 分析対象 | 112 |  | 53 | 59 |
| info_fast_survey | 参考: 質問紙が速すぎる（< 2.0 秒/項目、分析対象のうち） | 4 | 0 | 3 | 1 |
| info_fast_dg | 参考: DG 決定ページが速すぎる（< 5 秒、分析対象のうち） | 2 | 0 | 2 | 0 |
| info_break | 参考: 1 ページに 600 秒以上滞在（中断の疑い、分析対象のうち） | 2 | 0 | 1 | 1 |

基準の重なり（除外者の内訳）:

| pattern | n |
| --- | --- |
| cq | 11 |
| check | 4 |
| duration | 3 |

## Page Times（ページごとの滞在秒数。1 ページ目の同意は前がないので除く）
- 速い回答の基準: 質問紙 < 2.0 秒/項目、DG 決定 < 5 秒。中断の基準: 1 ページ >= 600 秒。いずれも除外せずフラグのみ（感度分析 (f)(g)）
| page_base | page_type | n | median_sec | q10_sec | q90_sec | min_sec | max_sec |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SurveyPage1 | survey | 130 | 122.500 | 71.800 | 191.200 | 9 | 259 |
| SurveyPage2 | survey | 130 | 122.500 | 71.800 | 191.200 | 9 | 259 |
| DGIntro | dg_intro | 130 | 75.500 | 48.900 | 118.100 | 9 | 1023 |
| DGDecision | dg_decision | 130 | 49.000 | 28.900 | 76.100 | 4 | 104 |
| DGCheck | dg_check | 130 | 37.000 | 24.900 | 58.100 | 5 | 85 |
| Demographics | other | 130 | 37.000 | 24.900 | 58.100 | 5 | 85 |
| PostSurvey | other | 130 | 37.000 | 24.900 | 58.100 | 5 | 85 |
| DGPredict | other | 130 | 25.000 | 16.000 | 39.000 | 3 | 57 |
| DGConfirm | other | 130 | 12.000 | 8.000 | 19.100 | 2 | 28 |
| ParticipantCode | other | 130 | 12.000 | 8.000 | 19.100 | 2 | 28 |
| SurveyIntro | other | 130 | 12.000 | 8.000 | 19.100 | 2 | 28 |
| End | other | 130 | 6.000 | 4.000 | 10.000 | 1 | 14 |

## 尺度得点
- HG/PP/MC = 各 5 項目の平均（1–6）。逆転項目なし。欠損は na.rm（必須項目なので通常は欠損なし）
- hh_mean = HEXACO-60 正直さ-謙虚さ 10 項目の平均（codebook の reverse = 1 の項目は 7 - x で逆転してから）。use_hexaco = 0 のセッションは NA
- dg_binary = dg_give > 0。revised = 入力し直し（dg_correct = 2）。dg_give は最終決定、dg_give_1 は 1 回目の入力
- 出力: data_synthetic/clean.csv, data_synthetic/exclusion_table.csv, output_synthetic/descriptives.csv（sd は標本 SD、n は有効回答数）

## 主分析（02_main.R）
- 乱数 seed = 20261024（set.seed）。ブートストラップ: パーセンタイル法, R = 5000, 参加者単位でリサンプル
- H1: Spearman 相関（cor.test, exact = FALSE）。判定は 90% CI と SESOI による 3 段階。原研究の値が 95% CI に含まれるかは参考
- H2/H3: 二部モデル。Part 1 glm(binomial, logit)、Part 2 lm(log(dg_give))。予測子 = CFA factor scores (1 unit = 1 SD)、順序を固定効果。OR の CI は Wald、% 変化の CI は t 分布
- H4: 群ごとの Spearman + ブートストラップ CI、psych::r.test（独立相関の差）、交互作用は Part 1 のロジスティック
- 自己予測: wilcox.test(paired, conf.int) の Hodges–Lehmann 推定値。相関は Spearman + ブートストラップ
- H5（探索）: HEXACO 正直さ-謙虚さの平均 × dg_give の Spearman + ブートストラップ。6 件法で提示（原版は 5 件法）
- 感度分析 (f)(g): Page Times のフラグ（01_clean.R）で速い回答・中断を除いた場合
- 多重比較: 主検定は H1 のみ。相関行列は Holm 補正（psych::corr.test）。H4・自己予測は探索的
- 信頼性: psych::alpha, psych::omega(nfactors = 1)。減衰補正は rs / sqrt(ω_HG)（探索）
- 出力: output_synthetic/results.md, output_synthetic/results.json, output_synthetic/model_coefficients.csv, output_synthetic/sensitivity.csv, output_synthetic/corr_matrix_r.csv, output_synthetic/corr_matrix_p.csv

## 図（04_figures.R）
- 乱数 seed = 20261024（ジッタ）。Okabe–Ito パレット。PDF（ベクタ）と PNG（300 dpi）
- 散布図のジッタ: x ±0.04（HG 平均は 0.2 刻み）、y なし。予測図: ±6 円。分布図の階級: 0 / 1–99 / 100 円幅（左閉区間）
- ファイル: fig_a_scatter.pdf, fig_a_scatter.png, fig_b_hist.pdf, fig_b_hist.png, fig_c_order.pdf, fig_c_order.png, fig_d_predict.pdf, fig_d_predict.png, fig_main.pdf, fig_main.png
- キャプション案: output_synthetic/fig_captions.md

## ソフトウェア
R version 4.3.3 (2024-02-29)
Platform: x86_64-pc-linux-gnu (64-bit)
patchwork 1.2.0, digest 0.6.34, jsonlite 1.8.8, lubridate 1.9.3, forcats 1.0.0, stringr 1.5.1, dplyr 1.1.4, purrr 1.0.2, readr 2.1.5, tidyr 1.3.1, tibble 3.2.1, ggplot2 3.4.4, tidyverse 2.0.0, utf8 1.2.4, generics 0.1.3, stringi 1.8.3, lattice 0.22-5, hms 1.1.3, magrittr 2.0.3, grid 4.3.3, timechange 0.3.0, Matrix 1.6-5, mgcv 1.9-1, fansi 1.0.5, scales 1.3.0, textshaping 0.3.7, cli 3.6.2, rlang 1.1.3, crayon 1.5.2, bit64 4.0.5, munsell 0.5.0, splines 4.3.3, withr 2.5.0, tools 4.3.3, parallel 4.3.3, tzdb 0.4.0, colorspace 2.1-0, vctrs 0.6.5, R6 2.5.1, lifecycle 1.0.4, bit 4.0.5, vroom 1.6.5, ragg 1.2.7, pkgconfig 2.0.3, pillar 1.9.0, gtable 0.3.4, glue 1.7.0, systemfonts 1.0.5, tidyselect 1.2.0, farver 2.1.1, nlme 3.1-164, labeling 0.4.3, compiler 4.3.3

