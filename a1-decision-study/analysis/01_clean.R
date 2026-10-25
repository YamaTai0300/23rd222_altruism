# 01_clean.R — A-1 追試: エクスポート CSV から分析用データを作る（設計書 §13、実験計画書「参加者」、v0.3）
# 原研究の前処理（OSF T5MF2: Studies/09/09_preprocessing.R, 11/11_preprocessing.R）に合わせた点:
#   - 所要時間の閾値は「中央値の 1/4 未満」（原研究・AsPredicted #40376 と同じ）
#   - 注意チェック（cq1 = 1, cq2 = 6）のいずれか不正解で除外。除外はリストワイズ
#   - 変数名は原研究の整形済みデータ（hg_1 … mc_23, dg_give）と同じなので、原データとそのまま結合できる
# v0.3 で追加した点（スキル「ML 実験の設計・分析・可視化」パート A/B）:
#   - 来歴の確認: app_version・設定値・Git コミットが 1 通りでなければ止める（設定の違うデータを混ぜない）
#   - 除外表に「基準の重なり」「閾値の実値」「順序群ごとの件数」を出す
#   - 記述統計表（n・平均・SD・中央値・最小・最大、全体と順序群ごと）を output/descriptives.csv に出す
#   - 入力ファイルの MD5・除外・集計方法を output/analysis_notes.md に自動で残す
# v0.4: Page Times（$A1_RAW_DIR/PageTimes*.csv）からページごとの滞在時間を出し、極端に速い回答と中断を検出する（感度分析用のフラグ）。
#       HEXACO 正直さ-謙虚さ（hex_1〜10、逆転は codebook）の平均 hh_mean を作る
# 入力: $A1_RAW_DIR/altruism_study*.csv（tools/archive_export.py で完了者だけにした CSV。最新のものを使う）
#       $A1_RAW_DIR/PageTimes*.csv（管理画面 Data → Page Times。任意だが推奨）
#       $A1_DUP_DIR/dup_list_*.csv（tools/pairing.py の重複判定、任意）
# 出力: $A1_DATA_DIR/clean.csv, exclusion_table.csv; $A1_OUT_DIR/descriptives.csv, analysis_notes.md
# 実行: Rscript analysis/01_clean.R   （合成データ: run_analysis.sh synthetic / run_analysis.bat synthetic）
source("analysis/00_setup.R")

raw_file <- tail(sort(list.files(CFG$raw_dir, pattern = "^altruism_study.*\\.csv$", full.names = TRUE)), 1)
pt_file  <- tail(sort(list.files(CFG$raw_dir, pattern = "^PageTimes.*\\.csv$", full.names = TRUE)), 1)
dup_file <- tail(sort(list.files(CFG$dup_dir, pattern = "^dup_list.*\\.csv$", full.names = TRUE)), 1)
if (length(raw_file) != 1) stop(sprintf("入力 CSV がありません: %s/altruism_study*.csv", CFG$raw_dir))
codebook <- read_csv("analysis/codebook.csv", show_col_types = FALSE)

note_init("A-1 追試 分析ノート")
note("## 入力", sprintf("- ファイル: %s", raw_file), sprintf("- MD5: %s", file_md5(raw_file)),
     if (length(dup_file) == 1) sprintf("- 重複リスト: %s (MD5 %s)", dup_file, file_md5(dup_file)) else "- 重複リスト: なし",
     if (length(pt_file) == 1) sprintf("- Page Times: %s (MD5 %s)", pt_file, file_md5(pt_file)) else "- Page Times: なし（速い回答・中断のフラグは NA）")

d0 <- read_csv(raw_file, show_col_types = FALSE, guess_max = 10000)
names(d0) <- sub("^player\\.", "", names(d0))
names(d0) <- sub("^participant\\.", "p_", names(d0))
names(d0) <- sub("^session\\.", "s_", names(d0))
n_rows <- nrow(d0)
n_started <- sum(!is.na(d0$t_start) & as.character(d0$t_start) != "")

d <- d0 %>%
  filter(finished == 1) %>%
  rename(code = p_code)

# --- 来歴の確認: 設定・版が 1 通りか（実験計画書「手続き」: 順序以外は同一条件で集める）---
prov_cols <- intersect(c("app_version", "git_commit", "otree_version", "cfg_endowment", "cfg_dg_step", "cfg_use_hexaco", "lang"), names(d))
prov <- d %>% count(across(all_of(prov_cols)), name = "n_finished")
print(prov)
if (nrow(prov) > 1 && Sys.getenv("A1_ALLOW_MIXED") != "1") {
  stop("app_version / 設定値 / Git コミットが複数あります。設定の違うセッションは本分析に混ぜない（計画書）。",
       "確認のうえ混ぜるなら A1_ALLOW_MIXED=1 を設定して再実行。")
}
sessions <- if ("s_code" %in% names(d)) paste(unique(d$s_code), collapse = ", ") else "(session.code 列なし)"
note("## 来歴", sprintf("- セッション: %s", sessions),
     sprintf("- 行数 %d、開始 %d、完了 %d", n_rows, n_started, nrow(d)),
     md_table(prov))

# --- 除外フラグ（原研究 preprocessing.R と同じ基準。リストワイズ）---
med <- median(d$duration_sec, na.rm = TRUE)
thr <- CFG$duration_fraction * med
dup_codes <- if (length(dup_file) == 1) read_csv(dup_file, show_col_types = FALSE)$code else character(0)
d <- d %>%
  mutate(
    duration_flag = !is.na(duration_sec) & duration_sec < thr,
    dup_flag      = code %in% dup_codes,
    cq_flag       = !(cq1_pass == 1 & cq2_pass == 1),
    check_flag    = dg_check_pass != 1,
    n_flags       = cq_flag + check_flag + duration_flag + dup_flag,
    excluded      = n_flags > 0
  )

# --- 尺度得点（S1 の 15 項目に逆転項目はない。codebook$reverse == 1 の項目があれば 7 - x にする）---
rev_items <- codebook %>% filter(reverse == 1) %>% pull(variable)
for (v in intersect(rev_items, names(d))) d[[v]] <- 7 - d[[v]]
d <- d %>%
  mutate(
    hg_mean_fab = rowMeans(across(all_of(HG_ITEMS)), na.rm = TRUE),  # 原研究 analysis.Rmd と同じ名前
    pp_mean_fab = rowMeans(across(all_of(PP_ITEMS)), na.rm = TRUE),
    mc_mean_fab = rowMeans(across(all_of(MC_ITEMS)), na.rm = TRUE),
    dg_binary   = as.integer(dg_give > 0),                            # 原研究の dg_binary
    revised     = as.integer(!is.na(dg_correct) & dg_correct == 2)
  )
# HEXACO 正直さ-謙虚さ（探索 H5）。use_hexaco = 0 のセッションでは NA
if (all(HEX_ITEMS %in% names(d))) {
  d <- d %>% mutate(hh_mean = ifelse(!is.na(cfg_use_hexaco) & cfg_use_hexaco == 1, rowMeans(across(all_of(HEX_ITEMS)), na.rm = TRUE), NA_real_))
} else {
  d$hh_mean <- NA_real_
}

# --- Page Times: ページごとの滞在時間 → 極端に速い回答・中断のフラグ（除外ではなく記録・感度分析用）---
page_summary <- NULL
if (length(pt_file) == 1) {
  pt <- read_csv(pt_file, show_col_types = FALSE) %>%
    filter(participant_code %in% d$code) %>%
    arrange(participant_code, page_index) %>%
    group_by(participant_code) %>%
    mutate(page_sec = epoch_time_completed - lag(epoch_time_completed)) %>%   # 1 ページ目（同意）は前がないので NA
    ungroup() %>%
    mutate(page_type = case_when(
      grepl("^SurveyPage", page_name) ~ "survey",
      grepl("^DGDecision", page_name) ~ "dg_decision",     # 入力し直し（DGDecisionAgain）も含む
      grepl("^DGIntro", page_name) ~ "dg_intro",
      grepl("^DGCheck", page_name) ~ "dg_check",
      TRUE ~ "other"))
  n_items <- 17 + ifelse(!is.na(d$cfg_use_hexaco) & d$cfg_use_hexaco == 1, 10, 0)
  per_p <- pt %>% group_by(code = participant_code) %>%
    summarise(survey_sec = sum(page_sec[page_type == "survey"], na.rm = TRUE),
              dg_decision_sec = sum(page_sec[page_type == "dg_decision"], na.rm = TRUE),
              dg_intro_sec = sum(page_sec[page_type == "dg_intro"], na.rm = TRUE),
              max_page_sec = suppressWarnings(max(page_sec, na.rm = TRUE)),
              n_pages = n(), .groups = "drop")
  d <- d %>% left_join(per_p, by = "code") %>%
    mutate(survey_sec_per_item = survey_sec / n_items,
           fast_survey_flag = !is.na(survey_sec) & survey_sec_per_item < CFG$fast_item_sec,
           fast_dg_flag = !is.na(dg_decision_sec) & dg_decision_sec < CFG$fast_dg_sec,
           speeder_flag = fast_survey_flag | fast_dg_flag,
           break_flag = !is.na(max_page_sec) & is.finite(max_page_sec) & max_page_sec >= CFG$break_sec)
  page_summary <- pt %>% filter(!is.na(page_sec)) %>%
    mutate(page_base = sub("[AB]$", "", page_name)) %>%
    group_by(page_base, page_type) %>%
    summarise(n = n(), median_sec = median(page_sec), q10_sec = quantile(page_sec, .10), q90_sec = quantile(page_sec, .90),
              min_sec = min(page_sec), max_sec = max(page_sec), .groups = "drop") %>% arrange(desc(median_sec))
  write_csv(pt %>% select(participant_code, page_index, page_name, page_type, epoch_time_completed, page_sec), data_path("page_times.csv"))
  write_csv(page_summary, out_path("page_time_summary.csv"))
} else {
  d <- d %>% mutate(survey_sec = NA_real_, dg_decision_sec = NA_real_, dg_intro_sec = NA_real_, max_page_sec = NA_real_, n_pages = NA_integer_,
                    survey_sec_per_item = NA_real_, fast_survey_flag = NA, fast_dg_flag = NA, speeder_flag = NA, break_flag = NA)
}

# --- 除外表: 基準ごとの件数・その基準だけで除外された件数・順序群ごと ---
flag_row <- function(name, flag, label) {
  tibble(reason = name, label = label,
         n_flagged = sum(flag), n_only_this = sum(flag & d$n_flags == 1),
         n_order1 = sum(flag & d$task_order == 1), n_order2 = sum(flag & d$task_order == 2))
}
excl <- bind_rows(
  tibble(reason = "finished", label = "完了（支払い対象）", n_flagged = nrow(d), n_only_this = NA,
         n_order1 = sum(d$task_order == 1), n_order2 = sum(d$task_order == 2)),
  flag_row("cq",       d$cq_flag,       "注意チェック不正解（cq1 != 1 または cq2 != 6）"),
  flag_row("check",    d$check_flag,    "理解確認に 2 度不正解"),
  flag_row("duration", d$duration_flag, sprintf("所要時間 < 中央値 %.0f 秒 × %.2f = %.0f 秒", med, CFG$duration_fraction, thr)),
  flag_row("dup",      d$dup_flag,      "重複回答（同じメールアドレス、最初の回答以外）"),
  tibble(reason = "excluded_any", label = "いずれかに該当（リストワイズ除外）", n_flagged = sum(d$excluded), n_only_this = NA,
         n_order1 = sum(d$excluded & d$task_order == 1), n_order2 = sum(d$excluded & d$task_order == 2)),
  tibble(reason = "analysis_sample", label = "分析対象", n_flagged = sum(!d$excluded), n_only_this = NA,
         n_order1 = sum(!d$excluded & d$task_order == 1), n_order2 = sum(!d$excluded & d$task_order == 2)),
  # 参考（除外しない。感度分析 (f)(g) に使う）
  flag_row("info_fast_survey", !is.na(d$fast_survey_flag) & d$fast_survey_flag & !d$excluded,
           sprintf("参考: 質問紙が速すぎる（< %.1f 秒/項目、分析対象のうち）", CFG$fast_item_sec)),
  flag_row("info_fast_dg", !is.na(d$fast_dg_flag) & d$fast_dg_flag & !d$excluded,
           sprintf("参考: DG 決定ページが速すぎる（< %d 秒、分析対象のうち）", CFG$fast_dg_sec)),
  flag_row("info_break", !is.na(d$break_flag) & d$break_flag & !d$excluded,
           sprintf("参考: 1 ページに %d 秒以上滞在（中断の疑い、分析対象のうち）", CFG$break_sec))
)
overlap <- d %>% filter(excluded) %>%
  transmute(pattern = paste0(ifelse(cq_flag, "cq+", ""), ifelse(check_flag, "check+", ""),
                             ifelse(duration_flag, "duration+", ""), ifelse(dup_flag, "dup+", ""))) %>%
  mutate(pattern = sub("\\+$", "", pattern)) %>% count(pattern, name = "n") %>% arrange(desc(n))

# --- 記述統計表（全体・順序群、除外後と除外前）---
desc_vars <- c("dg_give", "dg_give_1", "dg_predict", "hg_mean_fab", "pp_mean_fab", "mc_mean_fab", "hh_mean", "duration_sec",
               "survey_sec_per_item", "dg_decision_sec", "age")
describe_by <- function(dd, sample_label) {
  bind_rows(
    dd %>% mutate(group = "all"),
    dd %>% mutate(group = paste0("order", task_order))
  ) %>%
    select(group, any_of(desc_vars)) %>%
    pivot_longer(-group, names_to = "variable") %>%
    group_by(sample = sample_label, group, variable) %>%
    summarise(n = sum(!is.na(value)), mean = mean(value, na.rm = TRUE), sd = sd(value, na.rm = TRUE),
              median = median(value, na.rm = TRUE), min = suppressWarnings(min(value, na.rm = TRUE)),
              max = suppressWarnings(max(value, na.rm = TRUE)), .groups = "drop")
}
desc <- bind_rows(describe_by(filter(d, !excluded), "analysis"), describe_by(d, "all_finished")) %>%
  mutate(across(c(mean, sd, median), ~ round(.x, 3)))
# 注: sd は標本 SD（n − 1）。n は各変数の有効回答数。

# --- 出力 ---
write_csv(d, data_path("clean.csv"))
write_csv(excl, data_path("exclusion_table.csv"))
write_csv(desc, out_path("descriptives.csv"))
print(excl); print(overlap)
cat(sprintf("median duration (s): %.0f  threshold: %.0f  revised DG entry (dg_correct = 2): %d\n", med, thr, sum(d$revised)))

note("## 除外（リストワイズ。原研究 preprocessing.R と同じ基準）",
     sprintf("- 所要時間の閾値: 中央値 %.0f 秒 × %.2f = %.0f 秒", med, CFG$duration_fraction, thr),
     sprintf("- 重複判定: %s", if (length(dup_file) == 1) "tools/pairing.py の dup_list を使用" else "dup_list なし（0 件として処理）"),
     md_table(excl), "", "基準の重なり（除外者の内訳）:", "", md_table(overlap))
if (!is.null(page_summary)) {
  note("## Page Times（ページごとの滞在秒数。1 ページ目の同意は前がないので除く）",
       sprintf("- 速い回答の基準: 質問紙 < %.1f 秒/項目、DG 決定 < %d 秒。中断の基準: 1 ページ >= %d 秒。いずれも除外せずフラグのみ（感度分析 (f)(g)）",
               CFG$fast_item_sec, CFG$fast_dg_sec, CFG$break_sec),
       md_table(page_summary %>% mutate(across(where(is.numeric), ~ round(.x, 1)))))
}
note("## 尺度得点",
     "- HG/PP/MC = 各 5 項目の平均（1–6）。逆転項目なし。欠損は na.rm（必須項目なので通常は欠損なし）",
     "- hh_mean = HEXACO-60 正直さ-謙虚さ 10 項目の平均（codebook の reverse = 1 の項目は 7 - x で逆転してから）。use_hexaco = 0 のセッションは NA",
     "- dg_binary = dg_give > 0。revised = 入力し直し（dg_correct = 2）。dg_give は最終決定、dg_give_1 は 1 回目の入力",
     sprintf("- 出力: %s, %s, %s（sd は標本 SD、n は有効回答数）", data_path("clean.csv"), data_path("exclusion_table.csv"), out_path("descriptives.csv")))
