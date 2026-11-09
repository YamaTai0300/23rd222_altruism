# Qualtrics 版（A-1 v0.6 の再現）r3

作成: 2026-11-05（r1）／ 改訂: 2026-11-06（r2: oTree 版 v0.5 との齟齬を解消）／ 2026-11-09（r3: 計画書 v0.6 = CrowdWorks 募集に対応。実験 ID、参加資格、未完了回答 4 時間）。oTree 版 `../a1-decision-study_v0.6/` と同じ 9 ページ構成を Qualtrics で再現したもの。r1 のファイルは `r1/`、r2 のファイル（`make_qsf.py`、`A-1_v0.5r2_ja*.qsf`、eos HTML、`qualtrics_to_otree.py`、`README.md`）は `r2/` にそのまま残してある。r2 → r3 の差分は `diff_r2_r3_make_qsf.patch`（`qualtrics_to_otree.py` の差分も含む）。**r3 の QSF はまだ Qualtrics に取り込んでいない**（取り込み先は研究室アカウントか自分のアカウントかを計画書の決定に合わせて決める）。Qualtrics のプロジェクトは、r2 が **study_v6**（調査 ID `SV_cSIPHEGOiULgN82`、2026-11-06 に `A-1_v0.5r2_ja.qsf` を取り込み）、r1 が **study_v5**（`SV_6PfFg1rhsV2G2uG`）。ブランドは `qualtricsxmw5hysnkpn.hnd1`。r1 → r2 の差分は `diff_r1_r2_make_qsf.patch`。齟齬の一覧はプロジェクト doc「A-1 Qualtrics 版と oTree 版の齟齬一覧（2026-11-05）」。

## 正本と直し方

- 参加者に見せる文言の正本は oTree 版の `../a1-decision-study_v0.6/altruism_study/texts/ja.py`。Qualtrics のビルダーでは文言を直さない（ビルダーで直した内容は QSF の作り直しで消える）。
- 直すときは `texts/ja.py`（または `make_qsf.py`）を直し、QSF を作り直して **新規プロジェクト** として取り込む（既存プロジェクトの上書きはできない）。
- Qualtrics 版にしかない画面要素の文言（「半角数字（円）」、無料版の取り分の説明文、終了ブロックの送信の案内）だけ `make_qsf.py` の `QTEXT` にある。

## ファイル

| ファイル | 内容 |
| --- | --- |
| `make_qsf.py` | 生成スクリプト（r3）。`python make_qsf.py --texts ../a1-decision-study_v0.6/altruism_study/texts/ja.py --out A-1_v0.6r3_ja.qsf` |
| `A-1_v0.6r3_ja.qsf` | 無料アカウント向け（Timing・JavaScript・Meta Info なし、43 質問、qsf_hash `6971821f2cc9`） |
| `A-1_v0.6r3_ja_full.qsf` | 有料ライセンス向け（`--full --meta`: 各ページの Timing 質問 `t_*`、決定画面の取り分の即時表示 JavaScript、同意ページの Meta Info 質問。53 質問、qsf_hash `ed33a08222b3`） |
| `A-1_v0.6r3_ja_eos_message.html`（`_full_` も同じ） | 終了メッセージ（End of Survey）の本文（実験 ID を表示）。Library に 1 回だけ手で作る（下の「終了ページ」） |
| `qualtrics_to_otree.py` | Qualtrics のエクスポート CSV → oTree 版のエクスポート形式（`altruism_study_<date>.csv`、Timing があれば `PageTimes_<date>.csv`）。r3: `participant.code` ← `exp_id`、`participant.label` ← `ResponseId`、`player.exp_id` を追加。`analysis/01_clean.R`・`tools/pairing.py`・`tools/match_cw_ids.py` をそのまま使うため |
| `A-1_v0.5r2_ja*.qsf`、`A-1_v0.5r2_ja*_eos_message.html` | r2 の成果物（study_v6 に取り込み済み。`r2/` にも同じものがある） |
| `r2/` | 2026-11-06 の版（study_v6 に取り込んだもの） |
| `r1/` | 2026-11-05 の版（study_v5 に取り込んだもの） |

`make_qsf.py` のオプション: `--full`（Timing + JS）、`--meta`（Meta Info 質問。無料アカウントで取り込めるかは未確認。403 なら外す）、`--eos-message MS_xxx`（終了メッセージ。下記）、`--allow-multiple`（多重回答防止を切る。デモ用）、`--keep-ip`（匿名化を切る）、`--partial '+4 hours'`（未完了回答を記録するまでの期間。r3 の既定）、`--brand`（SurveyBrandID）。

## r3 で変えた点（計画書 v0.6 = CrowdWorks 募集、研究室マニュアルの運用）

| 項目 | r2 | r3 |
| --- | --- | --- |
| 終了ページに出す ID | `${e://Field/ResponseID}`（`R_` + 15 文字） | 埋め込みデータ `exp_id` = `${rand://int/1000000000:9999999999}`（10 桁の数字。Survey Flow の先頭で発行）。参加者が CrowdWorks の作業ページのフォームに入力し、`../a1-decision-study_v0.6/tools/match_cw_ids.py` で承認待ち一覧と照合する。ResponseID はエクスポートに残る |
| 参加資格のチェック | 「18 歳以上で、[大学名] に在籍する学生」 | 「18 歳以上で、日本語を母語としています」（`texts/ja.py` v0.6） |
| 終了文 | 参加者コードを控える | 実験 ID を控え、CW の作業ページに戻って入力する（`texts/ja.py` v0.6）。終了ブロックの送信の案内も「実験 ID」に |
| 未完了回答の記録 | 1 週間後 | 4 時間後（`--partial` の既定）。募集の締切から 4 時間待ってデータを確定し、そのあと照合・承認 |
| 来歴 | `app_version` = `v0.5r2-qualtrics` | `v0.6r3-qualtrics` |

## r2 で oTree 版に合わせた点

| 項目 | r1 | r2 |
| --- | --- | --- |
| 質問紙の段階番号 | 「質問紙 1/2」= FAB、「2/2」= HEXACO に固定（HEXACO が先の群で逆順に見えた） | 埋め込みデータ `fab_stage` / `hex_stage` をパイプ（scale_order 2 では HEXACO が 1/2） |
| 進捗表示 | Qualtrics の進捗バー（分岐があるため不正確） | 進捗バーを切り、oTree 版と同じ「ページ k / 9」を各ページの先頭に表示（k は埋め込みデータ `p_fab1` `p_fab2` `p_hex` `p_dgi` `p_chk` `p_dec`。同意 = 1、事後評価 = 8、終了 = 9） |
| FAB の項目順 | ページごとに別ブロック。どの項目が 1 ページ目かは固定（HG 5 項目が常に 1 ページ目） | 1 ブロックで 15 項目を Advanced Randomization、cq1 / cq2 は固定位置（1 ページ目の 5 番目・2 ページ目の 4 番目）、Questions per Page = 10 で 9 + 8 項目に分ける（oTree 版の 17 項目一体シャッフル・9 + 8 分割に相当。ページ区切りはランダム化で無視されるため Questions per Page を使う） |
| 理解確認の変数名 | `dg_check`（1 回目）、`dg_check2`（2 回目）。oTree 版の `dg_check` は最終回答 | `dg_check_answer1` / `dg_check_answer2`。`dg_check`・`dg_check_attempts`・`dg_check_pass` は変換で作る |
| 設定値・来歴 | `endowment`, `participation_fee_yen`, `app_version` | codebook と同じ `cfg_endowment`, `cfg_fee`, `cfg_dg_step`, `cfg_use_hexaco`, `lang`, `app_version`（`v0.5r2-qualtrics`）、`qsf_hash`（質問・ブロック・フローのハッシュ。oTree 版の `git_commit` に相当） |
| ブラウザ・画面幅 | なし | `--meta` で Meta Info 質問（ブラウザ・OS・画面解像度・User Agent） |
| 終了 | 終了ブロック。「次へ」を押さないと完了（Finished）にならないのに「閉じてよい」と案内 | `--eos-message` で End of Survey のカスタムメッセージに参加者コードを出す（到達した時点で完了）。渡さないときは終了ブロックのまま「次へ」で送信するよう案内 |
| Survey Options | 既定（多重回答防止なし、IP を記録） | 多重回答防止 ON、匿名化（IP・位置情報を記録しない）ON、未完了回答は 1 週間後に記録（`Finished` で区別。変換は完了者だけ残す） |
| 文言の二重定義 | 「選択肢」「参加するには…」「質問紙 1/2」などをスクリプトに直書き | `texts/ja.py` の `scale_heading` `consent_error` `survey_stage_title` `survey_page_note` `progress_label` `check_unit` を使う |

## 構成（oTree 版との対応）

- ブロック: 1 同意 → 2-3 質問紙 FAB + 注意チェック（1 ブロック、2 ページ）→ 4 質問紙 HEXACO（5 件法、1 ページ）→ 5 DG 説明 → 6 理解確認 → 6b 再回答（1 回目が不正解のときだけ）→ 7 決定 → 8 事後評価 → 9 終了（実験 ID = `${e://Field/exp_id}`。r2 までは ResponseID）
- Survey Flow: 埋め込みデータ（exp_id の乱数、cfg_*, lang, app_version, qsf_hash と順序群で決まる列の初期値）→ 同意 → ランダマイザー（均等に表示、task_order 1 / 2）→ 各群の中にランダマイザー（scale_order 1 / 2。ここで `fab_stage` `hex_stage` `p_*` を設定）→ 事後評価 → 終了。理解確認は「Text Response ≠ 700」で再回答ブロックに分岐
- 検証: 全項目必須。理解確認・決定は数値（決定は 0〜1,000 の整数）。同意は 2 項目とも必須（MinChoices = 2）
- 変数名（Export tag）: hg_1 … mc_23, cq1, cq2, hex_1 … hex_10, dg_check_answer1, dg_check_answer2, dg_give, eval_understand, eval_difficult, eval_reflect, eval_distract, comment_open, consent（consent_1, consent_2）。Likert は 1〜6（HEXACO は 1〜5）

## 終了ページ（End of Survey メッセージ）の作り方

1. Qualtrics の Library → Messages → New Message → Type「End of Survey Messages」。本文は `A-1_v0.6r3_ja_eos_message.html` の中身（HTML ソースとして貼る）。`${e://Field/exp_id}` が実験 ID になる
2. メッセージ ID（`MS_` で始まる）を控え、`python make_qsf.py --texts ... --eos-message MS_xxx --out A-1_v0.6r3_ja.qsf` で作り直して取り込む
3. プレビューの最後に 10 桁の実験 ID が出ることを確認する

メッセージを作らない場合（`--eos-message` なし）は終了ブロックが残り、参加者が「次へ」を押して初めて Finished = 1 になる。コードを控えて閉じた人は未完了として記録される（`Finished = 0`、ただし回答はすべて入っている）。その場合は `qualtrics_to_otree.py --keep-unfinished` で残し、`eval_*` がすべて入っている行を完了扱いにするか決める。

## 取り込み・公開前・エクスポート

- 取り込み: Projects → Create project → Survey → Import a QSF file（新規プロジェクトになる。Claude のアプリ内ブラウザから行うときはファイル入力に JavaScript でファイルを注入する）。Qualtrics の API はクラウドからも PC の VM からも到達できない
- 取り込みで拒否される点（r1 で確認）: `SurveyBrandID` は空不可（ESDEF10）、`ProtectSelectionIds` は boolean、`SurveyHistory` / `SurveyTitleText` / `NewScaling` / `PartialDataCloseSurvey` は不可。無料アカウントでは Timing 質問と質問の JavaScript が 403（`--full` なしで省く）。`<ol>` の番号やインライン style は落ちる（番号は本文に入れてある）
- 2026-11-06（r2 の取り込み）で追加で分かった点: Survey Options の値が null の項目（`EOSMessageLibrary` など）と `AutoConfirmTarget` は「Additional property … is not allowed」(ESDEF10) で拒否される（r1 を取り込んだ前日は通っていた）。`make_qsf.py` はこれらを出さない。取り込みのエラー内容はブラウザの開発者ツールで `POST /survey-projects/v1/projects/import` の応答（JSON の `ValidationErrors`）を見ると分かる
- プレビューで確認済み（2026-11-06、study_v6、順序群 1・2 の両方）: (1) FAB の 2 ページが 9 項目・8 項目に分かれ、cq1 が 1 ページ目の 5 番目、cq2 が 2 ページ目の 4 番目に出る（15 項目は 2 ページにまたがってシャッフル）。(2) 見出しが scale_order 2 で「質問紙 1/2（HEXACO）→ 2/2（FAB）」。(3) 各ページの「ページ k / 9」が 1 から 9 まで順に進む（再回答ページは同じ番号）。(4) 終了ページに ResponseID が出て、「次へ」で完了になる。未確認: 終了メッセージ（Library を作ってから）、`--meta` を入れた QSF が無料アカウントで取り込めるか
- 公開前: Survey Options の未完了回答の扱い（r3 の既定は 4 時間後に記録）、多重回答防止（ON）、匿名化（ON）、終了メッセージを確認。回答数の上限（無料アカウントは公開情報で 100 件程度）と CW の定員 150 の問題を研究室アカウントのライセンスで確認（計画書 v0.6「材料と尺度」）。テスト回答を 1 件入れてエクスポート → 変換 → `01_clean.R` を実際に通し、テスト回答は本番前に消す
- エクスポート: Data & Analysis → Export → CSV、「Use numeric values」、「Export viewing order data for randomized surveys」を ON。変換: `python qualtrics_to_otree.py <csv> --qsf A-1_v0.6r3_ja.qsf --out-dir ../a1-decision-study_v0.6/raw/main` → `raw/main/altruism_study_<date>.csv`（完了者だけ、プレビュー行は除く）。CW の承認前に `python ../a1-decision-study_v0.6/tools/match_cw_ids.py --cw <CW の承認待ち一覧 CSV/HTML> --data <Qualtrics の CSV か変換後の CSV>` で実験 ID を照合（approve / check / reject と未申告の一覧）。そのあとは oTree 版と同じく `run_analysis.bat` / `tools/pairing.py --contacts payout/contacts_<date>.csv`（`--realize-pairs N` で案 B）

## oTree 版と残る差（Qualtrics では直せない。計画書「変更点」と事前登録に書く）

- 順序群の割り付け: oTree 版は seed 付きで 4 人ずつのブロックランダム化（`rand_seed` を記録）。Qualtrics 版はランダマイザー「均等に表示」（seed なし。ランダマイザーに到達した全員で均等化するので、未完了者が多いと完了者ではずれる）
- 所要時間の起点: oTree 版の `t_start` は同意を送信した時刻、Qualtrics の `StartDate` は調査を開いた時刻（同意文を読む時間を含む）。閾値（中央値 × 1/4）は同じデータ内で決めるので解析上は問題ないが、2 つの版の所要時間は直接比較しない
- 無料アカウント: ページごとの時間（感度分析 (f)(g)）が取れない。決定画面の取り分の即時表示ができない（説明文 1 文で補う）。未回答への自動スクロールなどの JavaScript がない。ブラウザ・画面幅は Meta Info 質問が通れば取れる
- 細かい差: 同意のチェック質問の見出しに「参加するには 2 つの項目にチェックを入れてください。」を常に表示（oTree 版はエラー時だけ）。未回答・範囲外のエラー文は Qualtrics 標準。理解確認の分岐は文字列比較（「0700」は不正解扱い）。自由記述の字数制限なし。日本語のみ

## 残り

- r3 の QSF を取り込み（study_v7。研究室アカウントなら `--brand` をそのアカウントのブランド ID に）、プレビューで (1) 同意の「日本語が母語」、(2) 終了ページの実験 ID が 10 桁の数字で出ること（パイプテキスト `${rand://int/…}` が埋め込みデータの値として評価されること）、(3) Survey Options の未完了回答 = 4 時間、を確認する
- HEXACO 10 項目と 5 件法の語の転記（若林 2014）→ `texts/ja.py` を直して QSF を作り直す
- CrowdWorks の募集ページ（計画書「募集と実施の運用」の文案）。終了メッセージを Library に作り、`--eos-message` で作り直して取り込む
- 本実験のプラットフォーム（研究室 Qualtrics のライセンス・回答数上限）を確認する。有料なら `_full.qsf`
