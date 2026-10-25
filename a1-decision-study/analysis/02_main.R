# 02_main.R — A-1 追試: 主分析（設計書 §13、実験計画書 A-1「分析計画」、v0.3）
# 原研究の解析（OSF T5MF2: analysis.Rmd）に合わせた点:
#   - H2 は二部（ハードル）モデル: 渡すか否かのロジスティック + 渡した人の log(額) の線形モデル。
#     原研究と同じく HG を主予測子にし、PP・MC を同時に投入する（弁別妥当性 H3 の検証を兼ねる）。
#     単一研究なので研究ランダム効果はなく、代わりに順序群（task_order）を固定効果で入れる
#   - 係数は OR と「原尺度での % 変化」(exp(b) - 1) * 100 で報告（原研究: OR 4.99、+40.1%）
#   - 予測子は原研究と同じく CFA 因子得点（lavaan, MLR, FIML）を優先し、lavaan がない／N が小さいときは下位尺度平均の z 得点
# v0.3 で変えた点（実験計画書「分析計画」1〜8、スキル パート B）:
#   - 乱数 seed を固定し、ブートストラップ CI（95% と 90%）と n をすべての統計量に添える
#   - H1 の判定を 3 段階（再現 / 効果なし（同等） / 判定保留）にし、SESOI r = .10 で判定。原研究の .27 が CI に含まれるかは参考
#   - 事前に固定した感度分析 (a)〜(e) を 1 つの表に出す（結論が変わるかを見る）
#   - 結果は results.md（人が読む）と results.json・*.csv（機械可読）の両方に出し、表の数値は手で転記しない
#   - 図は 04_figures.R に分離（パート C の方針で描く）
# 入力: $A1_DATA_DIR/clean.csv
# 出力: $A1_OUT_DIR/results.md, results.json, model_coefficients.csv, sensitivity.csv, corr_matrix_r.csv, corr_matrix_p.csv, analysis_notes.md（追記）
# 実行: Rscript analysis/02_main.R（01_clean.R の後）
source("analysis/00_setup.R")
suppressPackageStartupMessages(library(psych))
has_lavaan <- requireNamespace("lavaan", quietly = TRUE)
set.seed(CFG$seed)

d_all <- read_csv(data_path("clean.csv"), show_col_types = FALSE)
d <- d_all %>% filter(!excluded)
res <- list(n_analysis = nrow(d), n_finished = nrow(d_all), seed = CFG$seed, boot_R = CFG$boot_R, sesoi = CFG$sesoi)
out <- c("# A-1 追試 主分析", "",
         sprintf("N（分析対象）= %d / 完了 %d。乱数 seed = %d、ブートストラップ R = %d（パーセンタイル法）、SESOI r = %.2f。",
                 nrow(d), nrow(d_all), CFG$seed, CFG$boot_R, CFG$sesoi),
         "CI はすべて 95%（判定には 90% CI も使う）。n は各統計量の有効回答数。", "")

# =============================================================================
# H1（主検定）: Spearman 相関 + ブートストラップ CI + 3 段階判定
# =============================================================================
h1 <- spearman_boot(d$hg_mean_fab, d$dg_give)
h1$verdict <- verdict(h1$r, h1$p, h1$ci90)
h1$original_in_ci95 <- h1$ci95[1] <= CFG$original_r && CFG$original_r <= h1$ci95[2]
res$H1 <- h1
out <- c(out, "## H1（主検定）Spearman 相関（HG 平均 × 分配額）",
         fmt_r(h1),
         sprintf("判定（事前登録の基準）: **%s**（再現 = 同方向で p < .05 かつ 90%% CI 下限 > %.2f; 効果なし = 90%% CI が [−%.2f, %.2f] 内）",
                 h1$verdict, CFG$sesoi, CFG$sesoi, CFG$sesoi),
         sprintf("参考: 原研究の r = %.2f は 95%% CI に%s。", CFG$original_r, ifelse(h1$original_in_ci95, "含まれる", "含まれない")), "")

# =============================================================================
# 測定モデルと因子得点（原研究 analysis.Rmd の cfa_model と同じ）
# =============================================================================
cfa_model <- '
  hg_fs =~ hg_1 + hg_3 + hg_7 + hg_10 + hg_13
  mc_fs =~ mc_1 + mc_3 + mc_18 + mc_20 + mc_23
  pp_fs =~ pp_1 + pp_8 + pp_12 + pp_14 + pp_15
'
use_fs <- FALSE
if (has_lavaan && nrow(d) >= CFG$cfa_min_n) {
  fit <- tryCatch(lavaan::cfa(cfa_model, data = d, estimator = "MLR", missing = "FIML", std.lv = TRUE), error = function(e) NULL)
  if (!is.null(fit) && lavaan::lavInspect(fit, "converged")) {
    fm <- lavaan::fitMeasures(fit, c("cfi.robust", "rmsea.robust", "srmr"))
    res$cfa <- list(cfi = unname(fm[1]), rmsea = unname(fm[2]), srmr = unname(fm[3]), n = nrow(d))
    out <- c(out, "## 測定モデル（CFA, MLR, FIML; 参考値）",
             sprintf("CFI = %.3f, RMSEA = %.3f, SRMR = %.3f（原研究 .94 / .05 / .04）, n = %d", fm[1], fm[2], fm[3], nrow(d)),
             "因子間相関:", "", md_table(as.data.frame(round(unclass(lavaan::lavInspect(fit, "cor.lv")), 2)) %>% rownames_to_column("var")), "")
    fs <- as.data.frame(lavaan::lavPredict(fit, method = "regression"))
    fs <- as.data.frame(scale(fs))  # 1 単位 = 因子得点 1 SD（原研究の「one-unit = one SD」の解釈に合わせる）
    d <- bind_cols(d, fs)
    use_fs <- TRUE
  }
}
if (!use_fs) {
  out <- c(out, "## 測定モデル",
           sprintf("lavaan が使えないか N < %d のため、因子得点の代わりに下位尺度平均の z 得点を予測子にした。", CFG$cfa_min_n), "")
  d <- d %>% mutate(hg_fs = as.numeric(scale(hg_mean_fab)), pp_fs = as.numeric(scale(pp_mean_fab)), mc_fs = as.numeric(scale(mc_mean_fab)))
}
d <- d %>% mutate(order_f = factor(task_order),
                  hg_z = as.numeric(scale(hg_mean_fab)), pp_z = as.numeric(scale(pp_mean_fab)), mc_z = as.numeric(scale(mc_mean_fab)))
res$predictor_main <- if (use_fs) "CFA factor scores (1 unit = 1 SD)" else "subscale mean z-scores"

# =============================================================================
# H2 + H3: 二部（ハードル）モデル。HG を主予測子、PP・MC を同時投入（原研究 Table 2 と同じ構成）
# =============================================================================
vif <- function(m) {  # 多重共線性の確認（原研究の performance::check_collinearity に相当）
  X <- model.matrix(m)[, -1, drop = FALSE]
  setNames(sapply(seq_len(ncol(X)), function(j) 1 / (1 - summary(lm(X[, j] ~ X[, -j, drop = FALSE]))$r.squared)), colnames(X))
}
hurdle <- function(dd, sfx, label) {
  f1 <- as.formula(sprintf("dg_binary ~ hg_%s + pp_%s + mc_%s + order_f", sfx, sfx, sfx))
  f2 <- as.formula(sprintf("log(dg_give) ~ hg_%s + pp_%s + mc_%s + order_f", sfx, sfx, sfx))
  m1 <- glm(f1, family = binomial(link = "logit"), data = dd)
  d2 <- filter(dd, dg_give > 0)
  m2 <- lm(f2, data = d2)
  or <- exp(cbind(coef(m1), confint.default(m1)))
  pct <- (exp(cbind(coef(m2), confint(m2))) - 1) * 100
  v <- vif(m1)
  nm <- paste0(c("hg_", "pp_", "mc_"), sfx)
  rows <- bind_rows(
    tibble(analysis = label, part = "1: gave anything (logistic)", term = nm, estimate_type = "OR per 1 SD",
           estimate = or[nm, 1], ci_low = or[nm, 2], ci_high = or[nm, 3], p = summary(m1)$coefficients[nm, 4],
           n = nrow(dd), vif = v[nm]),
    tibble(analysis = label, part = "2: amount among givers (log-linear)", term = nm, estimate_type = "% change per 1 SD",
           estimate = pct[nm, 1], ci_low = pct[nm, 2], ci_high = pct[nm, 3], p = summary(m2)$coefficients[nm, 4],
           n = nrow(d2), vif = NA)
  )
  acc <- mean(as.integer(predict(m1, type = "response") >= 0.5) == dd$dg_binary)
  txt <- c(sprintf("### %s", label),
           sprintf("Part 1: 渡すか否か（ロジスティック, n = %d）", nrow(dd)),
           sprintf("- %s: OR = %.2f [%.2f, %.2f], p = %.3f, VIF = %.1f", nm, or[nm, 1], or[nm, 2], or[nm, 3], summary(m1)$coefficients[nm, 4], v[nm]),
           sprintf("- 分類精度（閾値 .5）= %.2f", acc),
           sprintf("Part 2: 渡した人の分配額（log, 原尺度での %% 変化, n = %d）", nrow(d2)),
           sprintf("- %s: %+.1f%% [%+.1f, %+.1f], p = %.3f", nm, pct[nm, 1], pct[nm, 2], pct[nm, 3], summary(m2)$coefficients[nm, 4]), "")
  list(rows = rows, txt = txt, m1 = m1, m2 = m2)
}
main_label <- if (use_fs) "主分析: CFA 因子得点（1 単位 = 1 SD）" else "主分析: 下位尺度平均の z 得点"
hm <- hurdle(d, "fs", main_label)
coef_rows <- hm$rows
h2_txt <- hm$txt
if (use_fs) { hz <- hurdle(d, "z", "感度分析 (e): 下位尺度平均の z 得点"); coef_rows <- bind_rows(coef_rows, hz$rows); h2_txt <- c(h2_txt, hz$txt) }
hg1 <- coef_rows %>% filter(analysis == main_label, part == "1: gave anything (logistic)", term == "hg_fs")
hg2 <- coef_rows %>% filter(analysis == main_label, part == "2: amount among givers (log-linear)", term == "hg_fs")
pp_mc <- coef_rows %>% filter(analysis == main_label, term != "hg_fs")
h3_support <- all(abs(coef_rows$estimate[coef_rows$analysis == main_label & coef_rows$part == "1: gave anything (logistic)" & coef_rows$term == "hg_fs"] >=
                        coef_rows$estimate[coef_rows$analysis == main_label & coef_rows$part == "1: gave anything (logistic)" & coef_rows$term != "hg_fs"])) &&
  all(pp_mc$ci_low <= 0 & pp_mc$ci_high >= 0 | (pp_mc$estimate_type == "OR per 1 SD" & pp_mc$ci_low <= 1 & pp_mc$ci_high >= 1))
res$H2 <- list(or_hg = hg1$estimate, or_ci = c(hg1$ci_low, hg1$ci_high), or_p = hg1$p, n1 = hg1$n,
               pct_hg = hg2$estimate, pct_ci = c(hg2$ci_low, hg2$ci_high), pct_p = hg2$p, n2 = hg2$n,
               supported = hg1$estimate > 1 && hg1$p < .05,
               original_or_in_ci = hg1$ci_low <= CFG$original_or && CFG$original_or <= hg1$ci_high)
res$H3 <- list(supported = h3_support)
out <- c(out, sprintf("## H2 二部モデル（原研究: HG OR = %.2f, 額 %+.1f%%; PP 額 −8.7%%）", CFG$original_or, CFG$original_pct), h2_txt,
         sprintf("H2 判定: %s（OR > 1 かつ p < .05）。原研究の OR %.2f は 95%% CI に%s。",
                 ifelse(res$H2$supported, "支持", "不支持"), CFG$original_or, ifelse(res$H2$original_or_in_ci, "含まれる", "含まれない")),
         "## H3 弁別妥当性",
         sprintf("判定: %s（HG の OR が最大で、PP・MC の 95%% CI が帰無値を含む）。VIF > 5 なら因子得点の共線性に注意し、感度分析 (e) の結果を優先する。",
                 ifelse(h3_support, "支持", "不支持")), "")

# =============================================================================
# H4（探索）: 順序効果
# =============================================================================
g1 <- spearman_boot(d$hg_mean_fab[d$task_order == 1], d$dg_give[d$task_order == 1])
g2 <- spearman_boot(d$hg_mean_fab[d$task_order == 2], d$dg_give[d$task_order == 2])
zt <- psych::r.test(n = g1$n, r12 = g1$r, n2 = g2$n, r34 = g2$r)
m_int <- glm(dg_binary ~ hg_fs * order_f + pp_fs + mc_fs, family = binomial, data = d)
b_int <- coef(m_int)["hg_fs:order_f2"]; p_int <- summary(m_int)$coefficients["hg_fs:order_f2", 4]
res$H4 <- list(order1 = g1, order2 = g2, fisher_z = unname(zt$z), fisher_p = unname(zt$p), interaction_b = unname(b_int), interaction_p = unname(p_int))
out <- c(out, "## H4 順序効果（探索。p 値は記述的に扱い、有意でないことを「順序効果なし」と読まない）",
         sprintf("質問紙→DG: %s", fmt_r(g1)), sprintf("DG→質問紙: %s", fmt_r(g2)),
         sprintf("差の検定（Fisher z）: z = %.2f, p = %.3f; HG × 順序の交互作用（Part 1）: b = %.3f, p = %.3f", zt$z, zt$p, b_int, p_int), "")

# =============================================================================
# 探索: 自己予測 vs 実際
# =============================================================================
w <- wilcox.test(d$dg_predict, d$dg_give, paired = TRUE, exact = FALSE, conf.int = TRUE)
pr_hg <- spearman_boot(d$dg_predict, d$hg_mean_fab)
pr_dg <- spearman_boot(d$dg_predict, d$dg_give)
res$prediction <- list(n = sum(complete.cases(d$dg_predict, d$dg_give)), mean_pred = mean(d$dg_predict), mean_actual = mean(d$dg_give),
                       hl_estimate = unname(w$estimate), hl_ci = unname(w$conf.int), p = w$p.value, rs_pred_hg = pr_hg, rs_pred_actual = pr_dg)
out <- c(out, "## 探索: 自己予測 vs 実際",
         sprintf("予測 M = %.0f, 実際 M = %.0f（n = %d）; 差の Hodges–Lehmann 推定値 = %.0f 円, 95%% CI [%.0f, %.0f], Wilcoxon p = %.3f",
                 mean(d$dg_predict), mean(d$dg_give), res$prediction$n, w$estimate, w$conf.int[1], w$conf.int[2], w$p.value),
         sprintf("予測 × HG: %s", fmt_r(pr_hg)), sprintf("予測 × 実際: %s", fmt_r(pr_dg)), "")

# =============================================================================
# H5（探索）: HEXACO 正直さ-謙虚さ × DG。先行研究で最も安定して再現される関連（r ≈ .2〜.3）なので、
# HG × DG が出なかったときに「手続きの問題か、FAB の翻訳の問題か」を切り分ける比較基準（ベースライン）にする
# =============================================================================
if ("hh_mean" %in% names(d) && sum(!is.na(d$hh_mean)) >= 10) {
  h5 <- spearman_boot(d$hh_mean, d$dg_give)
  hh_pp <- spearman_boot(d$hh_mean, d$hg_mean_fab)
  rel_hh <- { x <- d %>% select(all_of(HEX_ITEMS)) %>% filter(complete.cases(.)); c(alpha = psych::alpha(x)$total$raw_alpha, n = nrow(x)) }
  res$H5 <- list(rs_hh_dg = h5, rs_hh_hg = hh_pp, alpha_hh = unname(rel_hh["alpha"]), note = "exploratory; HEXACO-60 H-H on the FAB 6-point scale")
  out <- c(out, "## H5 探索: HEXACO 正直さ-謙虚さ × 分配額（先行研究 r ≈ .2〜.3 の比較基準。6 件法で提示した点は原版と異なる）",
           sprintf("HH × 分配額: %s", fmt_r(h5)), sprintf("HH × HG: %s", fmt_r(hh_pp)),
           sprintf("HH の alpha = %.2f（n = %d）", rel_hh["alpha"], rel_hh["n"]), "")
}

# =============================================================================
# 感度分析（事前に固定した一覧。主分析の結論が変わるかを見る）
# =============================================================================
sens <- bind_rows(
  { s <- h1; tibble(analysis = "main: analysis sample, final dg_give, Spearman", n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  { s <- spearman_boot(d_all$hg_mean_fab, d_all$dg_give); tibble(analysis = "(a) all finished (before exclusion)", n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  { s <- spearman_boot(d$hg_mean_fab, d$dg_give_1); tibble(analysis = "(b) first entry dg_give_1", n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  { s <- spearman_boot(d$hg_mean_fab, d$dg_give, method = "pearson"); tibble(analysis = "(c) Pearson r", n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  { dd <- filter(d, is.na(eval_distract) | eval_distract < CFG$distract_cut); s <- spearman_boot(dd$hg_mean_fab, dd$dg_give)
    tibble(analysis = sprintf("(d) excluding eval_distract >= %d", CFG$distract_cut), n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  if ("speeder_flag" %in% names(d) && any(!is.na(d$speeder_flag))) {
    dd <- filter(d, is.na(speeder_flag) | !speeder_flag); s <- spearman_boot(dd$hg_mean_fab, dd$dg_give)
    tibble(analysis = sprintf("(f) excluding speeders (survey < %.1f s/item or DG < %d s)", CFG$fast_item_sec, CFG$fast_dg_sec), n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) },
  if ("break_flag" %in% names(d) && any(!is.na(d$break_flag))) {
    dd <- filter(d, is.na(break_flag) | !break_flag); s <- spearman_boot(dd$hg_mean_fab, dd$dg_give)
    tibble(analysis = sprintf("(g) excluding interrupted (a page >= %d s)", CFG$break_sec), n = s$n, r = s$r, ci95_low = s$ci95[1], ci95_high = s$ci95[2], ci90_low = s$ci90[1], ci90_high = s$ci90[2], p = s$p, verdict = verdict(s$r, s$p, s$ci90)) }
)
res$sensitivity <- sens
out <- c(out, "## 感度分析（事前に固定。(e) z 得点モデルは H2 の表を参照。(f)(g) は Page Times があるときだけ）",
         md_table(sens %>% mutate(across(where(is.numeric), ~ round(.x, 3)))), "",
         sprintf("主分析と判定が異なる感度分析: %s", { x <- sens$analysis[sens$verdict != sens$verdict[1]]; if (length(x)) paste(x, collapse = "; ") else "なし" }), "")

# =============================================================================
# 相関行列（原研究 Fig. 1 / Supplement S2 に対応。Spearman, Holm 補正。探索的）
# =============================================================================
corr_df <- d %>% transmute(HG = hg_mean_fab, PP = pp_mean_fab, MC = mc_mean_fab, HH = hh_mean, `DG Share` = dg_give, `DG Predict` = dg_predict)
if (all(is.na(corr_df$HH))) corr_df$HH <- NULL
ct <- psych::corr.test(corr_df, method = "spearman", adjust = "holm")
write_csv(as.data.frame(round(ct$r, 3)) %>% rownames_to_column("var"), out_path("corr_matrix_r.csv"))
write_csv(as.data.frame(round(ct$p, 4)) %>% rownames_to_column("var"), out_path("corr_matrix_p.csv"))
out <- c(out, sprintf("## 相関行列（Spearman, n = %d; 下三角 r / 上三角 Holm 補正 p。探索的）", nrow(corr_df)),
         "Spearman r:", "", md_table(as.data.frame(round(ct$r, 2)) %>% rownames_to_column("var")), "", "Holm 補正 p:", "", md_table(as.data.frame(round(ct$p, 3)) %>% rownames_to_column("var")), "")

# =============================================================================
# 信頼性と減衰補正
# =============================================================================
rel <- function(items) {
  x <- d %>% select(all_of(items))
  a <- psych::alpha(x)$total$raw_alpha
  o <- tryCatch(suppressWarnings(suppressMessages(psych::omega(x, nfactors = 1, plot = FALSE)))$omega.tot, error = function(e) NA_real_)  # 1 因子では omega_t だけが意味をもつ
  c(alpha = a, omega = o)
}
r_hg <- rel(HG_ITEMS); r_pp <- rel(PP_ITEMS); r_mc <- rel(MC_ITEMS)
r_att <- if (is.finite(r_hg["omega"]) && r_hg["omega"] > 0) h1$r / sqrt(r_hg["omega"]) else NA_real_
res$reliability <- list(HG = r_hg, PP = r_pp, MC = r_mc, h1_attenuation_corrected = unname(r_att))
out <- c(out, "## 信頼性（原研究 ω = .74〜.79）",
         sprintf("HG: alpha = %.2f, omega = %.2f; PP: alpha = %.2f, omega = %.2f; MC: alpha = %.2f, omega = %.2f（n = %d）",
                 r_hg["alpha"], r_hg["omega"], r_pp["alpha"], r_pp["omega"], r_mc["alpha"], r_mc["omega"], nrow(d)),
         sprintf("探索: HG の ω で減衰補正した H1 の r = %.3f（rs / sqrt(ω_HG)。DG 側は補正しない）", r_att), "")

# =============================================================================
# 記述統計・手続きのチェック
# =============================================================================
res$descriptives <- list(dg_mean = mean(d$dg_give), dg_median = median(d$dg_give), zero_pct = 100 * mean(d$dg_give == 0),
                         equal_pct = 100 * mean(d$dg_give == max(d$cfg_endowment, na.rm = TRUE) / 2),
                         revised_n = sum(d$dg_correct == 2, na.rm = TRUE), check_retry_ok_n = sum(d$dg_check_attempts == 2 & d$dg_check_pass == 1, na.rm = TRUE))
out <- c(out, "## 記述統計（分析対象。全体・順序群の表は descriptives.csv）",
         sprintf("dg_give: M = %.0f, Md = %.0f, 0 円 %.1f%%（原研究 %.1f%%）, 均等 %.1f%%, n = %d",
                 mean(d$dg_give), median(d$dg_give), 100 * mean(d$dg_give == 0), CFG$original_zero_pct, res$descriptives$equal_pct, nrow(d)),
         sprintf("入力し直し (dg_correct = 2): %d 名; 理解確認 2 回目で正答: %d 名", res$descriptives$revised_n, res$descriptives$check_retry_ok_n),
         sprintf("事後評価 (1-6): 理解しやすさ M = %.2f, 難しさ M = %.2f, 実生活を反映 M = %.2f, 気が散った M = %.2f",
                 mean(d$eval_understand, na.rm = TRUE), mean(d$eval_difficult, na.rm = TRUE), mean(d$eval_reflect, na.rm = TRUE), mean(d$eval_distract, na.rm = TRUE)), "")

# =============================================================================
# 出力
# =============================================================================
write_csv(coef_rows %>% mutate(across(where(is.numeric), ~ round(.x, 4))), out_path("model_coefficients.csv"))
write_csv(sens %>% mutate(across(where(is.numeric), ~ round(.x, 4))), out_path("sensitivity.csv"))
write_json(res, out_path("results.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
write_csv(d, data_path("analysis_sample.csv"))  # 因子得点・z 得点つきの分析対象（04_figures.R が使う）
writeLines(out, out_path("results.md"))
cat(out, sep = "\n")

note("## 主分析（02_main.R）",
     sprintf("- 乱数 seed = %d（set.seed）。ブートストラップ: パーセンタイル法, R = %d, 参加者単位でリサンプル", CFG$seed, CFG$boot_R),
     "- H1: Spearman 相関（cor.test, exact = FALSE）。判定は 90% CI と SESOI による 3 段階。原研究の値が 95% CI に含まれるかは参考",
     sprintf("- H2/H3: 二部モデル。Part 1 glm(binomial, logit)、Part 2 lm(log(dg_give))。予測子 = %s、順序を固定効果。OR の CI は Wald、%% 変化の CI は t 分布", res$predictor_main),
     "- H4: 群ごとの Spearman + ブートストラップ CI、psych::r.test（独立相関の差）、交互作用は Part 1 のロジスティック",
     "- 自己予測: wilcox.test(paired, conf.int) の Hodges–Lehmann 推定値。相関は Spearman + ブートストラップ",
     "- H5（探索）: HEXACO 正直さ-謙虚さの平均 × dg_give の Spearman + ブートストラップ。6 件法で提示（原版は 5 件法）",
     "- 感度分析 (f)(g): Page Times のフラグ（01_clean.R）で速い回答・中断を除いた場合",
     "- 多重比較: 主検定は H1 のみ。相関行列は Holm 補正（psych::corr.test）。H4・自己予測は探索的",
     "- 信頼性: psych::alpha, psych::omega(nfactors = 1)。減衰補正は rs / sqrt(ω_HG)（探索）",
     sprintf("- 出力: %s", paste(out_path(c("results.md", "results.json", "model_coefficients.csv", "sensitivity.csv", "corr_matrix_r.csv", "corr_matrix_p.csv")), collapse = ", ")))
