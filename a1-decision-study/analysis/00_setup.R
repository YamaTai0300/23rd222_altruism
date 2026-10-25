# 00_setup.R — 解析スクリプト共通の設定・ヘルパー（v0.3）
# 各スクリプトの先頭で source("analysis/00_setup.R") する。
# 方針（実験計画書「分析計画」「記録・分析ノート・図表」）:
#   - 定数（seed、ブートストラップ回数、除外閾値、SESOI）は 1 か所で決め、分析ノートに自動で残す
#   - 入出力の場所は環境変数で切り替えられる → 合成データやパイロットの結果が本データの出力を上書きしない
#       A1_RAW_DIR  (既定 raw/final)   A1_DATA_DIR (既定 data)   A1_OUT_DIR (既定 output)
#       A1_FIG_LANG (既定 en: 図の軸ラベルの言語。ja は日本語フォントが必要)   A1_FIG_FONT (ja のフォント名)
#   - 図は Okabe–Ito パレット、ベクタ（PDF）+ PNG、誤差の種類と n をキャプションに書く
suppressPackageStartupMessages({
  library(tidyverse)
  library(jsonlite)
  library(digest)
})

CFG <- list(
  seed              = 20261024L,  # ブートストラップ等の乱数 seed
  boot_R            = 5000L,      # ブートストラップの反復数
  duration_fraction = 0.25,       # 所要時間 < 中央値 × この値 を除外（原研究 preprocessing.R）
  sesoi             = 0.10,       # 最小関心効果量（Spearman r）。判定基準の境界
  original_r        = 0.27,       # 原研究 HG × DG の Spearman r（Binder et al., 2026）
  original_or       = 4.99,       # 原研究 二部モデル Part 1 の OR（HG 1 SD）
  original_pct      = 40.1,       # 原研究 Part 2 の % 変化（HG 1 SD）
  original_zero_pct = 35.2,       # 原研究 0 を渡した割合（%）
  distract_cut      = 5L,         # 感度分析 (d): eval_distract >= この値 を除く
  cfa_min_n         = 100L,       # CFA 因子得点を主分析に使う最小 N
  # Page Times による極端に速い回答・中断の検出（v0.4。除外基準ではなく感度分析 (f)(g) と記録に使う）
  fast_item_sec     = 2.0,        # 質問紙ページ: 1 項目あたりの秒数がこれ未満なら fast_survey_flag
  fast_dg_sec       = 5,          # DG 決定ページ: 滞在秒数がこれ未満なら fast_dg_flag
  break_sec         = 600,        # どれかのページに これ以上（10 分）滞在したら break_flag（一度に回答していない疑い）
  raw_dir  = Sys.getenv("A1_RAW_DIR",  "raw/final"),
  dup_dir  = Sys.getenv("A1_DUP_DIR",  "payout"),
  data_dir = Sys.getenv("A1_DATA_DIR", "data"),
  out_dir  = Sys.getenv("A1_OUT_DIR",  "output"),
  fig_lang = Sys.getenv("A1_FIG_LANG", "en")
)

HG_ITEMS <- c("hg_1", "hg_3", "hg_7", "hg_10", "hg_13")
HEX_ITEMS <- sprintf("hex_%d", 1:10)  # HEXACO-60 正直さ-謙虚さ（逆転は codebook の reverse 列で 7 - x 済み）
PP_ITEMS <- c("pp_1", "pp_8", "pp_12", "pp_14", "pp_15")
MC_ITEMS <- c("mc_1", "mc_3", "mc_18", "mc_20", "mc_23")

# ---- パス ----
dir.create(CFG$data_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(CFG$out_dir,  showWarnings = FALSE, recursive = TRUE)
data_path <- function(name) file.path(CFG$data_dir, name)
out_path  <- function(name) file.path(CFG$out_dir, name)
file_md5  <- function(path) digest::digest(file = path, algo = "md5")

# ---- 分析ノート（output/analysis_notes.md）----
# 01_clean.R が note_init() で作り直し、以降のスクリプトは note() で追記する
NOTES_FILE <- out_path("analysis_notes.md")
note_init <- function(title) {
  writeLines(c(sprintf("# %s", title), "",
               sprintf("生成: %s（スクリプトが自動生成。手で編集しない）", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
               sprintf("設定: seed = %d, boot_R = %d, duration_fraction = %.2f, SESOI r = %.2f, cfa_min_n = %d",
                       CFG$seed, CFG$boot_R, CFG$duration_fraction, CFG$sesoi, CFG$cfa_min_n),
               sprintf("入出力: raw_dir = %s, data_dir = %s, out_dir = %s", CFG$raw_dir, CFG$data_dir, CFG$out_dir), ""),
             NOTES_FILE)
}
note <- function(...) {
  lines <- unlist(list(...))
  cat(lines, file = NOTES_FILE, sep = "\n", append = TRUE)
  cat("", file = NOTES_FILE, sep = "\n", append = TRUE)
  invisible(lines)
}
note_session <- function() {
  si <- sessionInfo()
  pk <- c(si$otherPkgs, si$loadedOnly)
  note("## ソフトウェア", si$R.version$version.string, sprintf("Platform: %s", si$platform),
       paste(sprintf("%s %s", names(pk), sapply(pk, function(p) p$Version)), collapse = ", "))
}

# ---- 表を Markdown のパイプ表にする（print(data.frame) は幅で折り返し、ロケールによっては日本語をエスケープするため）----
md_table <- function(df, digits = 3) {
  df <- as.data.frame(df)
  for (j in seq_along(df)) {
    x <- df[[j]]
    df[[j]] <- if (is.numeric(x)) ifelse(is.na(x), "", trimws(formatC(x, digits = digits, format = if (all(x[!is.na(x)] == round(x[!is.na(x)]))) "d" else "f"))) else ifelse(is.na(x), "", as.character(x))
  }
  c(paste0("| ", paste(names(df), collapse = " | "), " |"),
    paste0("|", paste(rep(" --- ", ncol(df)), collapse = "|"), "|"),
    apply(df, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |")))
}

# ---- 統計のヘルパー ----
fmt <- function(x, d = 3) formatC(x, digits = d, format = "f")

# Spearman 相関 + パーセンタイル・ブートストラップの 95% / 90% CI（seed は呼び出し側で固定する）
spearman_boot <- function(x, y, R = CFG$boot_R, method = "spearman") {
  ok <- complete.cases(x, y)
  x <- x[ok]; y <- y[ok]; n <- length(x)
  ct <- suppressWarnings(cor.test(x, y, method = method, exact = FALSE))
  bs <- replicate(R, { i <- sample.int(n, n, replace = TRUE); suppressWarnings(cor(x[i], y[i], method = method)) })
  bs <- bs[is.finite(bs)]
  list(n = n, r = unname(ct$estimate), p = ct$p.value,
       ci95 = unname(quantile(bs, c(.025, .975))), ci90 = unname(quantile(bs, c(.05, .95))),
       method = method, R = R)
}

# 判定（実験計画書「分析計画」1）: 再現 / 効果なし（同等） / 判定保留
verdict <- function(r, p, ci90, sesoi = CFG$sesoi) {
  if (r > 0 && p < .05 && ci90[1] > sesoi) return("再現")
  if (ci90[1] > -sesoi && ci90[2] < sesoi) return("効果なし（同等）")
  "判定保留"
}

fmt_r <- function(s, label = "rs") {
  sprintf("%s = %s, 95%% CI [%s, %s], 90%% CI [%s, %s], p = %s, n = %d",
          label, fmt(s$r), fmt(s$ci95[1]), fmt(s$ci95[2]), fmt(s$ci90[1]), fmt(s$ci90[2]), fmt(s$p, 4), s$n)
}

# ---- 図（パート C）----
# Okabe–Ito パレット。色だけで区別しない（形・線種・直接ラベルを併用する）
OI <- c(orange = "#E69F00", skyblue = "#56B4E9", green = "#009E73", yellow = "#F0E442",
        blue = "#0072B2", vermillion = "#D55E00", purple = "#CC79A7", black = "#000000", grey = "#999999")
PAL_ORDER <- c(`1` = OI[["blue"]], `2` = OI[["vermillion"]])
SHAPE_ORDER <- c(`1` = 16, `2` = 17)

LAB <- if (CFG$fig_lang == "ja") list(
  order = c(`1` = "質問紙→DG", `2` = "DG→質問紙"), hg = "Help Giving（1–6、5 項目の平均）",
  give = "相手に分けた額（円）", predict = "自己予測額（円）", count = "人数", rs = "Spearman rs（HG × 分配額）",
  all = "全体", actual = "実際", pred = "予測", group = "順序群"
) else list(
  order = c(`1` = "Survey first", `2` = "DG first"), hg = "Help Giving (1-6, mean of 5 items)",
  give = "Amount given (yen)", predict = "Predicted amount (yen)", count = "Participants", rs = "Spearman rs (HG x amount given)",
  all = "All", actual = "Actual", pred = "Predicted", group = "Order"
)
# 日本語の図のフォント。環境変数 A1_FIG_FONT で変更（Windows: "Yu Gothic" / "Meiryo"、macOS: "Hiragino Sans"）。
# 日本語が「…」や □ になるときはロケールが UTF-8 でないかフォントがない（run_analysis.sh は UTF-8 を設定する）
FIG_FAMILY <- if (CFG$fig_lang == "ja") Sys.getenv("A1_FIG_FONT", "Noto Sans CJK JP") else ""

theme_a1 <- function(base_size = 9) {
  theme_minimal(base_size = base_size, base_family = FIG_FAMILY) +
    theme(panel.grid.minor = element_blank(), legend.position = "bottom",
          plot.tag = element_text(face = "bold"), plot.title = element_text(size = base_size + 1))
}
mm <- function(x) x / 25.4

# PDF（ベクタ）と PNG（300 dpi）を同じ名前で書き出す。幅は掲載幅（1 段 89 mm / 2 段 183 mm）で指定
save_fig <- function(p, name, width_mm = 89, height_mm = 70) {
  pdf_dev <- if (CFG$fig_lang == "ja") grDevices::cairo_pdf else "pdf"
  ggsave(out_path(paste0(name, ".pdf")), p, width = mm(width_mm), height = mm(height_mm), device = pdf_dev)
  ggsave(out_path(paste0(name, ".png")), p, width = mm(width_mm), height = mm(height_mm), dpi = 300, bg = "white")
  invisible(c(out_path(paste0(name, ".pdf")), out_path(paste0(name, ".png"))))
}
