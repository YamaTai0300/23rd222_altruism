# 04_figures.R — A-1 追試: 図（実験計画書「記録・分析ノート・図表」、スキル パート C、v0.3）
# 方針:
#   - 位置で読める形を優先し、参加者ごとの生データの点を必ず見せる（散布図は x 方向だけに小さなジッタ、y は実値）
#   - 棒グラフはゼロ基準。相関の比較は棒ではなく点 + 95% CI の線で描く
#   - 色は Okabe–Ito、色だけで区別しない（形・直接ラベルを併用）。誤差の種類と n をキャプションに書く
#   - PDF（ベクタ）と PNG（300 dpi）を同じ名前で出す。幅は 1 段 89 mm / 2 段 183 mm
#   - 図の数値はすべて 02_main.R の出力（results.json, analysis_sample.csv）から取り、手で転記しない
# 入力: $A1_DATA_DIR/analysis_sample.csv, $A1_OUT_DIR/results.json
# 出力: $A1_OUT_DIR/fig_a_scatter, fig_b_hist, fig_c_order, fig_d_predict, fig_main（.pdf/.png）, fig_captions.md
# 実行: Rscript analysis/04_figures.R（02_main.R の後）
source("analysis/00_setup.R")
set.seed(CFG$seed)  # ジッタの乱数も固定する
has_patchwork <- requireNamespace("patchwork", quietly = TRUE)

d <- read_csv(data_path("analysis_sample.csv"), show_col_types = FALSE) %>%
  mutate(order_f = factor(task_order, levels = c(1, 2), labels = LAB$order))
res <- read_json(out_path("results.json"))
n <- nrow(d)
endow <- max(d$cfg_endowment, na.rm = TRUE)
if (!is.finite(endow)) endow <- 1000
binw <- 100

# ---- (a) HG × 分配額の散布図。x だけジッタ（HG 平均は 0.2 刻みなので ±0.04）、y は実値 ----
p_a <- ggplot(d, aes(hg_mean_fab, dg_give)) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE, colour = OI[["black"]], fill = OI[["grey"]], linewidth = 0.5, alpha = 0.25) +
  geom_point(aes(colour = order_f, shape = order_f), position = position_jitter(width = 0.04, height = 0), alpha = 0.7, size = 1.6) +
  scale_colour_manual(values = unname(PAL_ORDER), name = LAB$group) +
  scale_shape_manual(values = unname(SHAPE_ORDER), name = LAB$group) +
  scale_x_continuous(limits = c(1, 6), breaks = 1:6) +
  scale_y_continuous(limits = c(0, endow), breaks = seq(0, endow, by = endow / 4)) +
  labs(x = LAB$hg, y = LAB$give,
       title = sprintf("rs = %.2f [%.2f, %.2f], n = %d", res$H1$r, res$H1$ci95[[1]], res$H1$ci95[[2]], res$H1$n)) +
  theme_a1()

# ---- (b) 分配額の分布（ゼロ基準の棒。0 円を独立した階級にし、以降は 100 円幅の階級） ----
brks <- c(0, 1, seq(binw, endow + binw, by = binw))
bin_labels <- c("0", sprintf("1-%d", binw - 1), sprintf("%d-%d", seq(binw, endow - binw, by = binw), seq(binw, endow - binw, by = binw) + binw - 1), sprintf("%d", endow))
d_b <- d %>% mutate(bin = cut(dg_give, breaks = brks, right = FALSE, include.lowest = TRUE, labels = bin_labels),
                    zero = dg_give == 0) %>% count(bin, zero, .drop = FALSE) %>% filter(n > 0 | !zero)
p_b <- ggplot(d_b, aes(bin, n, fill = zero)) +
  geom_col(width = 0.9) +
  scale_fill_manual(values = c(`FALSE` = OI[["blue"]], `TRUE` = OI[["vermillion"]]), guide = "none") +
  scale_x_discrete(drop = FALSE) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.08))) +
  annotate("text", x = Inf, y = Inf, hjust = 1.05, vjust = 1.3, size = 2.8, family = FIG_FAMILY,
           label = sprintf("0: %.0f%%  (n = %d)", res$descriptives$zero_pct, n)) +
  labs(x = LAB$give, y = LAB$count) + theme_a1() + theme(axis.text.x = element_text(angle = 45, hjust = 1))

# ---- (c) 順序群ごとの rs と 95% CI（点 + 線。棒グラフにしない）。原研究の .27 と SESOI 帯を参照線に ----
d_c <- tibble(
  group = factor(c(LAB$all, LAB$order[["1"]], LAB$order[["2"]]), levels = c(LAB$all, LAB$order[["1"]], LAB$order[["2"]])),
  r = c(res$H1$r, res$H4$order1$r, res$H4$order2$r),
  lo = c(res$H1$ci95[[1]], res$H4$order1$ci95[[1]], res$H4$order2$ci95[[1]]),
  hi = c(res$H1$ci95[[2]], res$H4$order1$ci95[[2]], res$H4$order2$ci95[[2]]),
  n = c(res$H1$n, res$H4$order1$n, res$H4$order2$n)
)
p_c <- ggplot(d_c, aes(group, r)) +
  annotate("rect", xmin = -Inf, xmax = Inf, ymin = -CFG$sesoi, ymax = CFG$sesoi, fill = OI[["grey"]], alpha = 0.2) +
  geom_hline(yintercept = 0, linewidth = 0.3) +
  geom_hline(yintercept = CFG$original_r, linetype = "dashed", colour = OI[["black"]], linewidth = 0.4) +
  geom_errorbar(aes(ymin = lo, ymax = hi), width = 0.15, linewidth = 0.5) +
  geom_point(size = 2.2, colour = OI[["blue"]]) +
  geom_text(aes(label = sprintf("n = %d", n), y = hi), vjust = -0.6, size = 2.6, family = FIG_FAMILY) +
  annotate("text", x = 1.5, y = CFG$original_r, label = sprintf("original r = %.2f", CFG$original_r), hjust = 0.5, vjust = -0.5, size = 2.6, family = FIG_FAMILY) +
  scale_y_continuous(limits = c(min(-0.3, min(d_c$lo) - 0.05), max(0.7, max(d_c$hi) + 0.12))) +
  labs(x = NULL, y = LAB$rs) + theme_a1()

# ---- (d) 自己予測と実際（同一線つき） ----
p_d <- ggplot(d, aes(dg_predict, dg_give)) +
  geom_abline(slope = 1, intercept = 0, linetype = "dotted", colour = OI[["grey"]]) +
  geom_point(aes(colour = order_f, shape = order_f), position = position_jitter(width = 6, height = 6), alpha = 0.7, size = 1.6) +
  scale_colour_manual(values = unname(PAL_ORDER), name = LAB$group) +
  scale_shape_manual(values = unname(SHAPE_ORDER), name = LAB$group) +
  coord_equal(xlim = c(0, endow), ylim = c(0, endow)) +
  scale_x_continuous(breaks = seq(0, endow, by = endow / 4)) + scale_y_continuous(breaks = seq(0, endow, by = endow / 4)) +
  labs(x = LAB$predict, y = LAB$give,
       title = sprintf("HL diff = %.0f [%.0f, %.0f], n = %d", res$prediction$hl_estimate, res$prediction$hl_ci[[1]], res$prediction$hl_ci[[2]], res$prediction$n)) +
  theme_a1() + theme(plot.title.position = "plot")

files <- c(save_fig(p_a, "fig_a_scatter", 89, 75), save_fig(p_b, "fig_b_hist", 89, 60),
           save_fig(p_c, "fig_c_order", 89, 70), save_fig(p_d, "fig_d_predict", 89, 85))
if (has_patchwork) {
  library(patchwork)
  p_main <- (p_a + p_b) / (p_c + p_d) + plot_annotation(tag_levels = "a") + plot_layout(guides = "collect") & theme(legend.position = "bottom")
  files <- c(files, save_fig(p_main, "fig_main", 183, 150))
}

captions <- c(
  "# 図のキャプション案（数値は results.json から。手で転記しない）", "",
  sprintf("**Fig. a** Help Giving（5 項目の平均、1–6）と相手に分けた額（円）。点は参加者 1 人（n = %d）、x 方向に ±0.04 のジッタ、y は実値。形と色は順序群。線は OLS 回帰直線と 95%% 信頼帯（見やすさのための補助。検定は Spearman rs = %.2f、ブートストラップ 95%% CI [%.2f, %.2f]、R = %d）。",
          n, res$H1$r, res$H1$ci95[[1]], res$H1$ci95[[2]], CFG$boot_R),
  sprintf("**Fig. b** 相手に分けた額の分布（0 円を独立した階級にし、以降は %d 円幅の階級。縦軸はゼロ基準の人数）。0 円は別色（%.1f%%、n = %d）。", binw, res$descriptives$zero_pct, n),
  sprintf("**Fig. c** HG × 分配額の Spearman rs。全体と順序群ごと。誤差線はパーセンタイル・ブートストラップ 95%% CI（R = %d、参加者単位）。破線は原研究の r = %.2f、灰色の帯は SESOI ±%.2f。",
          CFG$boot_R, CFG$original_r, CFG$sesoi),
  sprintf("**Fig. d** DG 決定前の自己予測額と実際に分けた額（円）。点は参加者 1 人（n = %d）、±6 円のジッタ。点線は予測 = 実際。差（予測 − 実際）の Hodges–Lehmann 推定値 %.0f 円、95%% CI [%.0f, %.0f]。",
          res$prediction$n, res$prediction$hl_estimate, res$prediction$hl_ci[[1]], res$prediction$hl_ci[[2]]),
  "", "色: Okabe–Ito（青 #0072B2 = 質問紙→DG、朱 #D55E00 = DG→質問紙）。形でも区別（● / ▲）。"
)
writeLines(captions, out_path("fig_captions.md"))
cat(captions, sep = "\n")

note("## 図（04_figures.R）",
     sprintf("- 乱数 seed = %d（ジッタ）。Okabe–Ito パレット。PDF（ベクタ）と PNG（300 dpi）", CFG$seed),
     sprintf("- 散布図のジッタ: x ±0.04（HG 平均は 0.2 刻み）、y なし。予測図: ±6 円。分布図の階級: 0 / 1–%d / %d 円幅（左閉区間）", binw - 1, binw),
     sprintf("- ファイル: %s", paste(basename(files), collapse = ", ")),
     sprintf("- キャプション案: %s", out_path("fig_captions.md")))
note_session()
