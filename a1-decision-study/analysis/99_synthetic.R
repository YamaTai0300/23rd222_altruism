# 99_synthetic.R — 解析パイプラインの動作確認用の合成データ（v0.3; v0.5 の列構成: scale_order, hex_item_order, HEXACO 1–5、自己予測・入力確認・属性なし）
# 本物のデータの代わりではない。列名を oTree のエクスポート CSV（altruism_study.csv）に合わせてあるので、
#   A1_RAW_DIR=raw/synthetic A1_DATA_DIR=data_synthetic A1_OUT_DIR=output_synthetic で 01 → 02 → 04 を通せる
#   （run_analysis.sh synthetic / run_analysis.bat synthetic）。本データの raw/final・data・output には書かない。
# 生成モデル（検証のための仮置き。真の値は未知）: HG の潜在変数 → 5 項目（1–6）、渡すか否かは HG に依存するロジット、
#   渡す額は log 正規。注意チェック不合格・理解確認不合格・短すぎる所要時間を少数混ぜる。
# 使い方: Rscript analysis/99_synthetic.R [N] [seed]   （既定 N = 130, seed = 1）
source("analysis/00_setup.R")
args <- commandArgs(trailingOnly = TRUE)
N <- if (length(args) >= 1) as.integer(args[1]) else 130L
seed <- if (length(args) >= 2) as.integer(args[2]) else 1L
set.seed(seed)
endow <- 1000L

lik <- function(theta, loading = 0.8, n = length(theta)) pmin(6, pmax(1, round(3.5 + 0.9 * loading * theta + rnorm(n, 0, 0.9))))
hg <- rnorm(N); pp <- 0.3 * hg + rnorm(N, 0, 0.95); mc <- 0.4 * hg + rnorm(N, 0, 0.9)
items <- bind_cols(
  setNames(as_tibble(sapply(1:5, function(i) lik(hg)), .name_repair = "minimal"), HG_ITEMS),
  setNames(as_tibble(sapply(1:5, function(i) lik(pp)), .name_repair = "minimal"), PP_ITEMS),
  setNames(as_tibble(sapply(1:5, function(i) lik(mc)), .name_repair = "minimal"), MC_ITEMS)
)
task_order <- rep(c(1L, 2L), length.out = N)[sample(N)]
p_give <- plogis(0.6 + 0.9 * hg)                 # 0 円が 3 割程度
gives <- rbinom(N, 1, p_give)
amount <- round(pmin(endow, exp(5.4 + 0.25 * hg + rnorm(N, 0, 0.5))))
dg_give <- ifelse(gives == 1, amount, 0L)
scale_order <- rep(c(1L, 2L), length.out = N)[sample(N)]
cq1 <- ifelse(runif(N) < 0.05, sample(2:6, N, TRUE), 1L)
cq2 <- ifelse(runif(N) < 0.04, sample(1:5, N, TRUE), 6L)
check_attempts <- ifelse(runif(N) < 0.15, 2L, 1L)
check_pass <- ifelse(check_attempts == 2 & runif(N) < 0.3, 0L, 1L)
duration <- round(exp(rnorm(N, log(600), 0.35)))
duration[sample(N, 3)] <- round(runif(3, 60, 120))    # 速すぎる回答
t0 <- as.POSIXct("2026-11-05 09:00:00", tz = "UTC") + cumsum(round(runif(N, 120, 3600)))
code <- replicate(N, paste(sample(c(letters, 0:9), 8, TRUE), collapse = ""))

fab_order <- replicate(N, paste(sample(c(HG_ITEMS, PP_ITEMS, MC_ITEMS, "cq1", "cq2")), collapse = ","))
hex_order <- replicate(N, paste(sample(sprintf("hex_%d", 1:10)), collapse = ","))
d <- tibble(
  `participant.id_in_session` = seq_len(N), `participant.code` = code, `participant.label` = "", `participant._is_bot` = 0,
  `participant._index_in_pages` = 17, `participant._max_page_index` = 17, `participant._current_app_name` = "altruism_study",
  `participant._current_page_name` = "End", `participant.time_started_utc` = format(t0, "%Y-%m-%d %H:%M:%S"), `participant.visited` = 1,
  `participant.mturk_worker_id` = "", `participant.mturk_assignment_id` = "", `participant.payoff` = 0,
  `player.id_in_group` = 1, `player.role` = "", `player.payoff` = 0,
  `player.task_order` = task_order, `player.scale_order` = scale_order, `player.lang` = "ja", `player.app_version` = "v0.6-synthetic", `player.git_commit` = "synthetic",
  `player.otree_version` = "5.11.5", `player.rand_seed` = 12345, `player.cfg_endowment` = endow, `player.cfg_dg_step` = 1, `player.cfg_fee` = 300, `player.cfg_use_hexaco` = 0,
  `player.user_agent` = "synthetic", `player.screen_width` = sample(c(375, 390, 1280), N, TRUE),
  # v0.6: 実験 ID（10 桁の数字、一意）
  `player.exp_id` = paste0(sample(1:9, N, TRUE), sapply(seq_len(N), function(i) paste(sample(0:9, 9, TRUE), collapse = ""))),
  `player.consent` = 1, `player.eligible_confirm` = 1
) %>%
  bind_cols(setNames(items, paste0("player.", names(items)))) %>%
  mutate(
    `player.cq1` = cq1, `player.cq2` = cq2, `player.cq1_pass` = as.integer(cq1 == 1), `player.cq2_pass` = as.integer(cq2 == 6),
    `player.fab_item_order` = fab_order, `player.hex_item_order` = hex_order
  )
hh <- 0.3 * hg + rnorm(N, 0, 0.95)                         # HEXACO H-H（HG と弱く相関）。5 件法（1–5）。逆転項目は 2,4,5,7,8,10
lik5 <- function(theta, loading = 0.8, n = length(theta)) pmin(5, pmax(1, round(3 + 0.8 * loading * theta + rnorm(n, 0, 0.8))))
hex_rev <- c(2, 4, 5, 7, 8, 10)
for (i in 1:10) { v <- lik5(hh); if (i %in% hex_rev) v <- 6 - v; d[[sprintf("player.hex_%d", i)]] <- v }
d$`player.cfg_use_hexaco` <- 1
d <- d %>% mutate(
  `player.dg_check` = ifelse(check_pass == 1, endow - 300, endow - 200), `player.dg_check_answer1` = ifelse(check_attempts == 1, endow - 300, 300),
  `player.dg_check_answer2` = ifelse(check_attempts == 2, ifelse(check_pass == 1, endow - 300, endow - 200), NA),
  `player.dg_check_attempts` = check_attempts, `player.dg_check_pass` = check_pass,
  `player.dg_give` = dg_give, `player.dg_share` = as.integer(dg_give > 0),
  `player.eval_understand` = sample(3:6, N, TRUE), `player.eval_difficult` = sample(1:5, N, TRUE),
  `player.eval_reflect` = sample(2:6, N, TRUE), `player.eval_distract` = sample(1:6, N, TRUE, prob = c(.4, .25, .15, .1, .06, .04)),
  `player.comment_open` = "", `player.t_start` = format(t0, "%Y-%m-%dT%H:%M:%S+00:00"),
  `player.t_end` = format(t0 + duration, "%Y-%m-%dT%H:%M:%S+00:00"), `player.duration_sec` = duration, `player.finished` = 1,
  `player.excluded_in_app` = as.integer(!(cq1 == 1 & cq2 == 6) | check_pass == 0),
  `player.exclude_reason_in_app` = paste0(ifelse(!(cq1 == 1 & cq2 == 6), "cq", ""), ifelse(!(cq1 == 1 & cq2 == 6) & check_pass == 0, ",", ""), ifelse(check_pass == 0, "check", "")),
  `group.id_in_subsession` = seq_len(N), `subsession.round_number` = 1, `session.code` = "synth001", `session.label` = "",
  `session.mturk_HITId` = "", `session.mturk_HITGroupId` = "", `session.comment` = "", `session.is_demo` = 0
)
dir.create("raw/synthetic", showWarnings = FALSE, recursive = TRUE)
path <- "raw/synthetic/altruism_study_synthetic.csv"
write_csv(d, path, na = "")

# --- Page Times（oTree 管理画面 Data → Page Times と同じ列）。所要時間をページに配分し、速い回答者と中断者を少数混ぜる ---
# v0.5 のページ構成: 同意 → 質問紙 2 段階（scale_order で HEXACO が FAB の前か後）→ DG 説明・理解確認・決定（task_order で前後）→ 事後評価 → 終了
survey_pages <- function(sfx, so) if (so == 2) c(paste0("HexFirst", sfx), paste0("FabPage1", sfx), paste0("FabPage2", sfx)) else c(paste0("FabPage1", sfx), paste0("FabPage2", sfx), paste0("HexLast", sfx))
dg_pages <- function(sfx) paste0(c("DGIntro", "DGCheck", "DGDecision"), sfx)
weight <- function(p) switch(sub("^Hex(First|Last)$", "HexPage", sub("[AB]$", "", p)), Consent = 4, FabPage1 = 9, FabPage2 = 9, HexPage = 6,
                             DGIntro = 6, DGCheck = 3, DGDecision = 4, PostSurvey = 3, End = 0.5)
speeders <- sample(N, 5); breakers <- sample(setdiff(seq_len(N), speeders), 3)
pt <- bind_rows(lapply(seq_len(N), function(i) {
  pages <- if (task_order[i] == 1) c("Consent", survey_pages("A", scale_order[i]), dg_pages("A"), "PostSurvey", "End") else c("Consent", dg_pages("B"), survey_pages("B", scale_order[i]), "PostSurvey", "End")
  w <- sapply(pages, weight); secs <- duration[i] * w / sum(w)
  if (i %in% speeders) secs[grepl("^FabPage|^Hex|^DGDecision", pages)] <- secs[grepl("^FabPage|^Hex|^DGDecision", pages)] * 0.1
  if (i %in% breakers) secs[grepl("^DGIntro", pages)] <- secs[grepl("^DGIntro", pages)] + 900
  secs <- pmax(1, round(secs))
  tibble(session_code = "synth001", participant_id_in_session = i, participant_code = code[i], page_index = seq_along(pages),
         app_name = "altruism_study", page_name = pages, epoch_time_completed = as.integer(as.numeric(t0[i])) + cumsum(secs),
         round_number = 1, timeout_happened = 0, is_wait_page = 0)
}))
write_csv(pt, "raw/synthetic/PageTimes_synthetic.csv")
cat(sprintf("wrote %s (N = %d, seed = %d). SYNTHETIC DATA — never mix with real data.\n", path, N, seed))
