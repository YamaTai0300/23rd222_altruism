# 99_synthetic.R — 解析パイプラインの動作確認用の合成データ（v0.3）
# 本物のデータの代わりではない。列名を oTree のエクスポート CSV（altruism_study.csv）に合わせてあるので、
#   A1_RAW_DIR=raw/synthetic A1_DATA_DIR=data_synthetic A1_OUT_DIR=output_synthetic で 01 → 02 → 04 を通せる
#   （run_analysis.sh synthetic / run_analysis.bat synthetic）。本データの raw/final・data・output には書かない。
# 生成モデル（検証のための仮置き。真の値は未知）: HG の潜在変数 → 5 項目（1–6）、渡すか否かは HG に依存するロジット、
#   渡す額は log 正規。注意チェック不合格・理解確認不合格・短すぎる所要時間・入力し直しを少数混ぜる。
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
dg_give_1 <- ifelse(gives == 1, amount, 0L)
dg_correct <- ifelse(runif(N) < 0.06, 2L, 1L)
dg_give_2 <- ifelse(dg_correct == 2, pmin(endow, pmax(0, dg_give_1 + sample(c(-100, 100, 200), N, TRUE))), NA)
dg_give <- ifelse(dg_correct == 2, dg_give_2, dg_give_1)
dg_predict <- round(pmin(endow, pmax(0, dg_give + rnorm(N, 60, 120))))
cq1 <- ifelse(runif(N) < 0.05, sample(2:6, N, TRUE), 1L)
cq2 <- ifelse(runif(N) < 0.04, sample(1:5, N, TRUE), 6L)
check_attempts <- ifelse(runif(N) < 0.15, 2L, 1L)
check_pass <- ifelse(check_attempts == 2 & runif(N) < 0.3, 0L, 1L)
duration <- round(exp(rnorm(N, log(600), 0.35)))
duration[sample(N, 3)] <- round(runif(3, 60, 120))    # 速すぎる回答
t0 <- as.POSIXct("2026-11-05 09:00:00", tz = "UTC") + cumsum(round(runif(N, 120, 3600)))
code <- replicate(N, paste(sample(c(letters, 0:9), 8, TRUE), collapse = ""))

fab_order <- replicate(N, paste(sample(c(HG_ITEMS, PP_ITEMS, MC_ITEMS, "cq1", "cq2", sprintf("hex_%d", 1:10))), collapse = ","))
d <- tibble(
  `participant.id_in_session` = seq_len(N), `participant.code` = code, `participant.label` = "", `participant._is_bot` = 0,
  `participant._index_in_pages` = 24, `participant._max_page_index` = 24, `participant._current_app_name` = "altruism_study",
  `participant._current_page_name` = "End", `participant.time_started_utc` = format(t0, "%Y-%m-%d %H:%M:%S"), `participant.visited` = 1,
  `participant.mturk_worker_id` = "", `participant.mturk_assignment_id` = "", `participant.payoff` = 0,
  `player.id_in_group` = 1, `player.role` = "", `player.payoff` = 0,
  `player.task_order` = task_order, `player.lang` = "ja", `player.app_version` = "v0.3-synthetic", `player.git_commit` = "synthetic",
  `player.otree_version` = "5.11.5", `player.rand_seed` = 12345, `player.cfg_endowment` = endow, `player.cfg_dg_step` = 1, `player.cfg_fee` = 300, `player.cfg_use_hexaco` = 0,
  `player.user_agent` = "synthetic", `player.screen_width` = sample(c(375, 390, 1280), N, TRUE),
  `player.consent` = 1, `player.age_confirm` = 1, `player.student_confirm` = 1
) %>%
  bind_cols(setNames(items, paste0("player.", names(items)))) %>%
  mutate(
    `player.cq1` = cq1, `player.cq2` = cq2, `player.cq1_pass` = as.integer(cq1 == 1), `player.cq2_pass` = as.integer(cq2 == 6),
    `player.fab_item_order` = fab_order
  )
hh <- 0.3 * hg + rnorm(N, 0, 0.95)                         # HEXACO H-H（HG と弱く相関）。逆転項目は 2,4,5,7,8,10
hex_rev <- c(2, 4, 5, 7, 8, 10)
for (i in 1:10) { v <- lik(hh); if (i %in% hex_rev) v <- 7 - v; d[[sprintf("player.hex_%d", i)]] <- v }
d$`player.cfg_use_hexaco` <- 1
d <- d %>% mutate(
  `player.age` = sample(18:26, N, TRUE), `player.gender` = sample(1:4, N, TRUE, prob = c(.6, .35, .03, .02)),
  `player.grade` = sample(c("B1", "B2", "B3", "B4", "M1", "M2"), N, TRUE), `player.game_exp` = rbinom(N, 1, 0.2),
  `player.dg_check` = ifelse(check_pass == 1, endow - 300, endow - 200), `player.dg_check_answer1` = ifelse(check_attempts == 1, endow - 300, 300),
  `player.dg_check_answer2` = ifelse(check_attempts == 2, ifelse(check_pass == 1, endow - 300, endow - 200), NA),
  `player.dg_check_attempts` = check_attempts, `player.dg_check_pass` = check_pass,
  `player.dg_predict` = dg_predict, `player.dg_give` = dg_give, `player.dg_give_1` = dg_give_1, `player.dg_give_2` = dg_give_2,
  `player.dg_correct` = dg_correct, `player.dg_share` = as.integer(dg_give > 0),
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
pages_A <- c("Consent", "ParticipantCode", "SurveyIntroA", "SurveyPage1A", "SurveyPage2A", "DemographicsA",
             "DGIntroA", "DGCheckA", "DGPredictA", "DGDecisionA", "DGConfirmA", "PostSurvey", "End")
pages_B <- c("Consent", "ParticipantCode", "DGIntroB", "DGCheckB", "DGPredictB", "DGDecisionB", "DGConfirmB",
             "SurveyIntroB", "SurveyPage1B", "SurveyPage2B", "DemographicsB", "PostSurvey", "End")
weight <- function(p) switch(sub("[AB]$", "", p), Consent = 4, ParticipantCode = 1, SurveyIntro = 1, SurveyPage1 = 10, SurveyPage2 = 10,
                             Demographics = 3, DGIntro = 6, DGCheck = 3, DGPredict = 2, DGDecision = 4, DGConfirm = 1, PostSurvey = 3, End = 0.5)
speeders <- sample(N, 5); breakers <- sample(setdiff(seq_len(N), speeders), 3)
pt <- bind_rows(lapply(seq_len(N), function(i) {
  pages <- if (task_order[i] == 1) pages_A else pages_B
  w <- sapply(pages, weight); secs <- duration[i] * w / sum(w)
  if (i %in% speeders) secs[grepl("^SurveyPage|^DGDecision", pages)] <- secs[grepl("^SurveyPage|^DGDecision", pages)] * 0.1
  if (i %in% breakers) secs[grepl("^DGIntro", pages)] <- secs[grepl("^DGIntro", pages)] + 900
  secs <- pmax(1, round(secs))
  tibble(session_code = "synth001", participant_id_in_session = i, participant_code = code[i], page_index = seq_along(pages),
         app_name = "altruism_study", page_name = pages, epoch_time_completed = as.integer(as.numeric(t0[i])) + cumsum(secs),
         round_number = 1, timeout_happened = 0, is_wait_page = 0)
}))
write_csv(pt, "raw/synthetic/PageTimes_synthetic.csv")
cat(sprintf("wrote %s (N = %d, seed = %d). SYNTHETIC DATA — never mix with real data.\n", path, N, seed))
