# 03_compare_original.R — 原研究（OSF T5MF2）の公開データで HG × DG の関連を再計算し、本追試の比較基準を作る
# 目的:
#   - 本追試と同じ条件（欺罔なし・質問紙とゲームの間隔なし）の Study 09（Big US, N=806）と 11（MTurk Pilot, N=226）、
#     および DG を含む 6 研究すべてで、HG 平均 × dg_give の Spearman r とハードルモデルの係数を出す
#   - 本追試の data/clean.csv があれば同じ指標を並べて出力する（変数名が原研究と同じなので結合できる）
# 入力: なし（OSF から CSV をダウンロードして data/original/ に保存。2 回目以降はキャッシュを使う）
# 出力: output/original_benchmarks.md
# 実行: Rscript analysis/03_compare_original.R
suppressPackageStartupMessages({
  library(tidyverse)
})

# OSF の整形済みデータ（Studies/XX/XX_data.csv）。ファイル ID は api.osf.io の一覧から取得（2026-10-18）
files <- tribble(
  ~study, ~label,                                   ~deception, ~interval, ~url,
  "03",   "Rahels Study (DE, 欺罔あり, 2 週間隔)",      1, 1, "https://osf.io/download/692579310aefda3324e64102/",
  "09",   "Big US Study (EN, 欺罔なし, 間隔なし)",       0, 0, "https://osf.io/download/6925820ca3488c8d601179a7/",
  "11",   "MTurk Pilot (EN, 欺罔なし, 間隔なし)",        0, 0, "https://osf.io/download/6925825ca3488c8d601179cf/",
  "12",   "Respondi Pilot (EN, 欺罔なし, 2 週間隔)",     0, 1, "https://osf.io/download/6925826ff6299072a81175f6/",
  "13",   "German w/o deception (DE, 2 週間隔)",        0, 1, "https://osf.io/download/69258287b2e3e84b9e9574e5/",
  "15",   "German with deception (DE, 順序ランダム)",    1, 1, "https://osf.io/download/692582b371b7b485a47701d5/"
)
dir.create("data/original", showWarnings = FALSE, recursive = TRUE)
dir.create("output", showWarnings = FALSE)

load_study <- function(id, url) {
  path <- file.path("data/original", sprintf("%s_data.csv", id))
  if (!file.exists(path)) download.file(url, path, mode = "wb", quiet = TRUE)
  read_csv(path, show_col_types = FALSE, guess_max = 5000) %>% mutate(study_id = id)
}

hg_items <- c("hg_1", "hg_3", "hg_7", "hg_10", "hg_13")
pp_items <- c("pp_1", "pp_8", "pp_12", "pp_14", "pp_15")
mc_items <- c("mc_1", "mc_3", "mc_18", "mc_20", "mc_23")

summarise_study <- function(d, label) {
  d <- d %>%
    filter(!is.na(dg_give)) %>%
    mutate(
      hg = rowMeans(across(all_of(hg_items)), na.rm = TRUE),
      pp = rowMeans(across(all_of(pp_items)), na.rm = TRUE),
      mc = rowMeans(across(all_of(mc_items)), na.rm = TRUE),
      dg_binary = as.integer(dg_give > 0),
      hg_z = as.numeric(scale(hg)), pp_z = as.numeric(scale(pp)), mc_z = as.numeric(scale(mc))
    )
  rs <- suppressWarnings(cor.test(d$hg, d$dg_give, method = "spearman", exact = FALSE))
  m1 <- glm(dg_binary ~ hg_z + pp_z + mc_z, family = binomial, data = d)
  m2 <- lm(log(dg_give) ~ hg_z + pp_z + mc_z, data = filter(d, dg_give > 0))
  tibble(
    study = label, n = nrow(d),
    zero_pct = 100 * mean(d$dg_give == 0),
    mean_give = mean(d$dg_give),
    rs_hg_dg = rs$estimate,
    or_hg = exp(coef(m1)["hg_z"]),
    pct_hg = 100 * (exp(coef(m2)["hg_z"]) - 1),
    alpha_hg = psych::alpha(d[hg_items])$total$raw_alpha
  )
}

orig <- pmap_dfr(files, function(study, label, deception, interval, url) {
  d <- load_study(study, url)
  summarise_study(d, sprintf("%s %s", study, label))
})
pooled <- summarise_study(bind_rows(lapply(seq_len(nrow(files)), function(i) load_study(files$study[i], files$url[i]))),
                          "原研究 6 研究プール（研究効果は無視）")
res <- bind_rows(orig, pooled)

if (file.exists("data/clean.csv")) {
  mine <- read_csv("data/clean.csv", show_col_types = FALSE) %>% filter(!excluded)
  if (nrow(mine) >= 10) res <- bind_rows(res, summarise_study(mine, "本追試（A-1, 分析対象）"))
}

out <- c("# 原研究の公開データによる比較基準（HG × DG）", "",
         "zero_pct = 0 を渡した割合, rs = Spearman r (HG 平均 × 額), or_hg = 渡すか否かの OR (HG 1SD), pct_hg = 渡した人の額の % 変化 (HG 1SD)",
         "注: 原研究の本文の値（OR 4.99, +40.1%, r = .27）は CFA 因子得点と研究ランダム効果を使った混合モデル。ここでは下位尺度平均の z 得点と研究ごとの単純なモデルなので数値は一致しない。", "",
         capture.output(print(as.data.frame(res %>% mutate(across(where(is.numeric), ~ round(.x, 3)))), row.names = FALSE)))
writeLines(out, "output/original_benchmarks.md")
cat(out, sep = "\n")
