# 変更履歴

## 未リリース（2026-11-10）— HEXACO 正直さ-謙虚さの日本語版と文言の修正

v0.6 のあとの変更。Qualtrics 版の QSF（r3）にはまだ反映していない（次の r4 で反映する）。変更後のボットテストは未実行。

- texts/ja.py: HEXACO 10 項目（`hex_1`〜`hex_10`）、選択肢 `likert5`、教示 `hex_intro` / `hex_intro_short` を若林（2014）日本語版
  （hexaco.org 配布 `Japanese_self60.doc`）に差し替え。項目・選択肢は改変しない（句読点「，」も原文のまま）。
  若林版の「3 をできるだけ選ばない」注意書きはコメントアウトで保持（入れるかは未決）。英語原文（en.py）と逆転指定は hexaco.org と照合済み。
- texts/ja.py: 同意文「いったん始めたら中断せずに最後まで一度にお答えください」→「一度始めたら中断せずに最後までお答えください」。
- texts/ja.py: 終了画面から「入力がないと報酬をお支払いできません。」を削除。

## v0.6-pilot（2026-11-09）— CrowdWorks 募集に合わせる（研究室マニュアル『Qualtrics とクラウドワークスの使い方』、計画書 v0.6）

研究室のオンライン実験マニュアル（募集は CrowdWorks のタスク、実施は Qualtrics、終了画面の ID を CW に入力して照合・承認）に合わせた。
修正前（v0.5）は `../a1-decision-study_v0.5/` にそのまま残し、比較は `docs/compare_v0.5_v0.6.md`、ソースの差分は `docs/diff_v0.5_to_v0.6.patch`。
画面構成（9 ページ）、変数（`exp_id` の追加以外）、解析スクリプトは v0.5 のまま。Qualtrics 版は `../qualtrics/`（r3）で同じ変更をした。

### 1. 参加資格と文言（texts/ja.py, en.py, codebook.csv）
- `eligible_check`: 「18 歳以上で、[大学名] に在籍する学生」→「18 歳以上で、日本語を母語としています」（CW の対象 = 日本語母語の 18 歳以上。
  学生の限定をやめた）。変数 `eligible_confirm` はそのまま（codebook のラベルを更新）。
- 同意文の「参加者コード（ランダムな文字列）」→「実験 ID（ランダムな数字）」。終了画面の文言を「実験 ID を CrowdWorks の作業ページのフォームに入力して
  『作業を完了する』を押す」「入力がないと報酬を支払えない」に。`end_code_label` = 実験 ID。

### 2. 実験 ID（__init__.py, End.html 経由の表示, tests.py, codebook.csv）
- `Player.exp_id`（文字列、10 桁の数字）を追加。`creating_session` で `secrets.randbelow` により発行し、セッション内で一意にする
  （乱数シード `rand_seed` とは独立なので、割り当てから推測できない）。終了画面は `exp_id` を表示（`participant.code` は内部用・エクスポートに残る）。
- 10 桁にした理由: マニュアルの推奨（6 桁では使い回し・偶然の一致が起きた）。数字だけにしたのは入力ミス（O/0、l/1）を減らすため。
- tests.py: 終了時に `exp_id` が 10 桁の数字で、同じセッションに重複がないことを検査（ボットテストは v0.6 ではまだ実行していない）。

### 3. 照合と支払いのツール（tools/match_cw_ids.py 新規, tools/pairing.py）
- `tools/match_cw_ids.py`: CW の承認待ち一覧（CSV / TSV / HTML、UTF-8 か CP932）と調査データ（Qualtrics の生 CSV か oTree 形式）を実験 ID で照合し、
  approve（完了回答に 1 対 1 で存在）/ check（未完了、同じ ID の最初の入力、1 文字違いの近い ID）/ reject（存在しない、形式違い、同じ ID の 2 件目以降）と
  理由を `payout/match_<date>.csv` に出す。未申告の完了回答は `unclaimed_<date>.csv`、承認分の `code, cw_user, cw_profile_url, work_id` は
  `contacts_<date>.csv`（pairing.py の `--contacts`）。CW 規約の非承認の上限（3 件か総数の 30%）を超えると警告。合成データで動作確認済み。
- `tools/pairing.py`: code に `player.exp_id` を使う（なければ `participant.code`）。連絡先の列は `cw_user` / 「作業者」も自動判定。
  `--realize-pairs N`（計画書の案 B: 抽選で N ペアだけ決定どおり支払い、残りは参加謝礼のみ。`realized` 列）。
  `cw_extra_yen` 列（= payout − fee。参加謝礼はタスク報酬で支払い済みなので、CW で個別発注する額）。合成データで案 A / B とも動作確認済み。
- 連絡先（メールアドレス）は集めない。CW のユーザー名・作業 ID は回答データと別フォルダーに置き、検収後に削除する（計画書「倫理」）。

### 4. そのほか
- settings.py: `app_version` = `v0.6-pilot`、`participation_fee_yen` のコメント（= CW のタスク単価）、デモページの説明。
- run_dev.bat / run_tests.bat: コピー先を `%LOCALAPPDATA%\a1-decision-study_v0.6` に。
- 99_synthetic.R: `player.exp_id` 列と `app_version` = `v0.6-synthetic`（R は v0.6 ではまだ実行していない。01_clean.R は codebook で列を検査しないので、
  `exp_id` の有無で止まらない見込み）。
- README.md: v0.6 の状態、CW 募集ページの設定、締切後の手順（照合 → 承認 → pairing → 個別発注）。

### 確認が必要な点（v0.6 で増えた分）
- 案 A（全ペア実現）か案 B（`--realize-pairs`）か。CW の受取額（契約額の約 86%）と「決定どおり」の読み方。
- 注意チェックの位置: oTree 版はページの端に置かない制約が v0.5 からある。Qualtrics 版は固定位置（1 ページ目 5 番目、2 ページ目 4 番目）。
- CW の作業時間の上限（60 分）、入力フォームの文字数（20 文字以下）、「重複を認めない」の設定は CW の募集ページ側で行う（コードにはない）。

## v0.5-pilot（2026-10-29）— 画面を必要最低限に、質問紙を 2 段階に、参加者の手間を減らす、使い回せるデモ URL

デモ（v0.4）を見ての修正。修正前（v0.4）は `../a1-decision-study/` にそのまま残し、比較は `docs/compare_v0.4_v0.5.md`、
`docs/compare_screens_v0.4_v0.5_ja.pdf`（画面の並列比較）、`docs/diff_v0.4_to_v0.5.patch`（ソースの差分）。

### 1. 画面を実験に必要な最低限にした（__init__.py, texts/ja.py, en.py, テンプレート, settings.py, codebook.csv）
- 謝礼（額・受け取り方法）と連絡先（お問い合わせ、Google フォーム）の案内を画面から外した。リンクを配布するときに伝える。
  `contact_form_url` を削除。`participation_fee_yen` は画面に出さず `cfg_fee` としてデータに残す（pairing.py が使う）。
- 削除した画面: 参加者コード（開始時）、質問紙の教示ページ、属性、自己予測、入力の確認と入力し直し。
  参加者コードは終了画面にだけ表示。来歴の hidden 項目（user_agent, screen_width）と t_start は同意ページで取る。
- 同意のチェックを 2 つに（同意／18 歳以上かつ [大学名] の学生 = `eligible_confirm`）。所要時間の目安を約 10 分に。
- 参加者が通るページ数 13 → 9。削除した変数: age_confirm, student_confirm, age, gender, grade, game_exp, dg_predict, dg_give_1, dg_give_2, dg_correct。

### 2. 質問紙を FAB と HEXACO の 2 段階にした（__init__.py, texts, SurveyPage.html, codebook.csv）
- 質問紙 1/2 = FAB 15 + 注意チェック 2（6 件法、2 ページ、原研究と同じくランダム順・注意チェックはページの端に置かない）、
  質問紙 2/2 = HEXACO 正直さ-謙虚さ 10（**原版と同じ 5 件法**、1 ページ、ランダム順、教示文は HEXACO-60 の要約）。
- 段階の順序 `scale_order`（1 = FAB→HEXACO, 2 = HEXACO→FAB）を参加者ごとにランダム化。`task_order` と 2 × 2 の 4 通りを 4 人ずつブロック。
- `hex_item_order` を記録。`fab_item_order` は 17 項目。HEXACO の逆転は解析側で 6 − x（codebook の min/max から）。
- 日本語の HEXACO 10 項目と選択肢の語は若林 (2014) からの転記待ち（文言は【未転記】のまま）。

### 3. 参加者の手間を減らす（_templates/global/Page.html, progress.html, style.css, テンプレート）
- 進捗「ページ k / n」とバー（参加者ごとに実際に通るページで計算。`progress()`）。
- 未回答・誤りの項目まで自動スクロール。行全体をタップで選択、選択済みを薄い青 + ✓ で表示。「次へ」の二重送信を防ぐ。
- 各段階の 1 ページ目に教示と選択肢の一覧を枠で表示、2 ページ目は短い教示だけ。
- 理解確認: 説明を折りたたみでいつでも読み直せる（再回答時は開く）。入力欄を大きく、自動フォーカス。決定のヒントに「次へで確定」を明記。

### 4. 使い回せるデモ URL（settings.py ROOMS, tools/ensure_room.py, run_dev.bat）
- Room `demo` を追加。`run_dev.bat` はサーバー起動後に `tools/ensure_room.py` でセッション（`DEMO_ROOM_PARTICIPANTS` = 100 人）を作り、
  開くたびに新しい参加者で始まる使い回しリンク `/join/<code>` をブラウザで開く。固定リンク `/room/demo` も表示（同じブラウザは続きから）。
  リンクは `__demo_links.txt` にも書く。`run_dev.bat [port] [a1_ja|a1_en]`。
- 実行時のコピー先を `%LOCALAPPDATA%\a1-decision-study_v0.5` に変え、v0.4 と共存できるようにした。

### 5. 解析・ツール・テストの同期（analysis/, tools/, tests.py）
- 01_clean.R: 逆転を `(min + max) − x`、ページ名（FabPage*, Hex*）、`revised`・`dg_predict`・`age` の削除。
- 02_main.R: 自己予測の分析を削除、感度分析 (b) は欠番、H5 の注記（5 件法・別段階）、`scale_order` ごとの HG・HH を記述的に表示。
- 04_figures.R: 図 d を HEXACO × 分配額（探索 H5）に置き換え。99_synthetic.R: v0.5 の列構成。合成データ N = 130 で最後まで通ることを確認（R 4.3.3）。
- tests.py: 6 ケース（revise を削除）、HEXACO 段階（範囲外 6 の拒否、未回答の拒否）、scale_order・hex_item_order の検査。
  `otree test a1_ja/a1_en 24` が use_hexaco = True/False、dg_step = 1/100 で通る。export_check OK（64 変数）。
- tools/browser_walk.py: 4 人分を通して全種類の画面を撮り `--pdf` でまとめる。tools/compare_screens.py（新規）: v0.4/v0.5 の並列比較 PDF。
- 画面: `docs/screens_v0.5_ja.pdf`, `docs/screens_v0.5_en.pdf`。

### 確認が必要な点
- 謝礼・連絡先・参加者コードの扱いを「リンク配布時の案内文」として書く（計画書「倫理・謝礼」）。
- HEXACO の日本語 10 項目と 5 件法の選択肢の語（若林 2014）の転記。
- 計画書の材料・手続き・分析計画（自己予測と感度分析 (b) の削除、段階順のランダム化）を v0.5 に合わせる。

## v0.4-pilot（2026-10-24）— HEXACO 採用、完了者だけの保存、設定値の読み取り、Page Times

実験計画書の「不足」への回答（2026-10-24）に沿った変更。画面の構成は変えていないが、謝礼に関する文言を変えた。

### 1. HEXACO 正直さ-謙虚さを採用（settings.py, texts/en.py, codebook.csv, 01_clean.R, 02_main.R, 99_synthetic.R）
- `use_hexaco=True` を既定に。HEXACO-60（Ashton & Lee, 2009; hexaco.org、研究目的は無償）の正直さ-謙虚さ 10 項目
  （項目 6, 12R, 18, 24R, 30R, 36, 42R, 48R, 54, 60R）を `hex_1〜hex_10` に対応づけ、英語原文を `texts/en.py` に入れた
  （記憶からの転記なので hexaco.org と要照合）。日本語版（若林, 2014）は未転記（`FAB_和訳作業シート.xlsx`「HEXACO-HH」）。
- 逆転項目 6 つを `codebook.csv` の `reverse` 列に設定（`01_clean.R` が 7 − x で逆転）。`hh_mean` を作る。
- `02_main.R` に探索 H5（HH × 分配額、HH × HG、α）。先行研究で最も安定した関連なので、HG × DG が出ないときの切り分けに使う。
- 注意: FAB と同じ 6 件法で提示する（原版は 5 件法）。計画書に明記。所要時間 +2 分程度。

### 2. 完了者だけを保存（texts/ja.py, en.py, tools/archive_export.py）
- 同意文に「いったん始めたら中断せずに最後まで一度に回答する。途中でやめた回答は保存されない」を明記。
- `tools/archive_export.py`（新規）: 管理画面のエクスポートから `finished == 1` の行だけを `raw/<purpose>/altruism_study_<date>.csv` に保存し、
  Page Times も同じ参加者に絞り、SHA-256 を記録する。未完了の行は保存しない。既存ファイルは上書きしない。

### 3. 設定値を CSV から読む（__init__.py, codebook.csv, tools/pairing.py）
- `cfg_fee`（参加謝礼）を各回答に記録（codebook 71 変数）。
- `pairing.py` は元手と参加謝礼を CSV の `cfg_endowment`・`cfg_fee` から読む。値が複数あれば止まる。`--endowment`/`--fee` は
  cfg_* 列のない古い CSV 用で、記録値と食い違えば止まる（`--force` で引数を優先）。

### 4. 謝礼に関する文言を方法を指定しない形に（texts/ja.py, en.py）
- 「ギフトコード」「1 週間以内に送付」を外し、「謝礼としてお支払い」「受け取り方法と時期はメールで案内」にした。
  謝礼の種類・購入手続き・送付手順は未決で、決定後に計画書と文言に入れる。

### 5. Page Times による速い回答・中断の検出（00_setup.R, 01_clean.R, 02_main.R, 99_synthetic.R）
- `01_clean.R` が `$A1_RAW_DIR/PageTimes*.csv` を読み、ページごとの滞在秒数（`data/page_times.csv`）とページ別の要約
  （`output/page_time_summary.csv`）を出す。フラグ: `fast_survey_flag`（質問紙 < 2.0 秒/項目）、`fast_dg_flag`（DG 決定 < 5 秒）、
  `speeder_flag`、`break_flag`（1 ページ ≥ 600 秒）。除外表に参考行として件数を出す。除外基準には入れない（原研究に合わせる）。
- `02_main.R` の感度分析に (f) 速い回答を除く、(g) 中断を除く、を追加。閾値は `CFG`。
- `99_synthetic.R` が Page Times も生成（速い回答者 5 名、中断 3 名を混ぜる）。合成データで (f)(g) まで通ることを確認。

### 6. その他
- run_dev.bat: Python の検出を 3.10〜3.12 に広げ、`A1_PYTHON` / py launcher / conda 環境 `a1` / PATH 上の python の順で探す
  （oTree 5.11.5 が 3.10 でもボットテストを通ることを確認。3.13 は不可）。見つからないときの案内を表示。
- tests.py: `cfg_fee` の検査。`otree test a1_ja` / `a1_en` が `use_hexaco=True` で通ることを確認（項目 27 = FAB 15 + cq 2 + HEXACO 10）。
- README: 状態・残作業（HEXACO の転記、謝礼の未決）・解析の入力（archive_export → 01_clean）を更新。

## v0.3-pilot（2026-10-24）— 記録・判定基準・解析パイプラインの整備

実験計画書 A-1 の改訂（ml-experiment-analysis スキルのチェックリスト: 確証的／探索的の区別、判定基準、統制、反復単位と不確実性、
多重比較、データの扱い、記録、ネガティブ結果、誠実な図表）に合わせて、プログラムと解析を変えた。画面の文言・手続きは変えていない。

### 1. 来歴の記録（altruism_study/__init__.py, ParticipantCode.html, codebook.csv）
- 各回答に `git_commit`（環境変数 `A1_GIT_COMMIT` か `git rev-parse`、なければ unknown）、`otree_version`、`rand_seed`、
  `cfg_endowment`、`cfg_dg_step`、`cfg_use_hexaco`、`user_agent`（先頭 300 文字）、`screen_width` を保存。
  条件の違い（設定・版）を後から機械的に確認できる。
- 参加者コード画面の hidden input を JS で埋める。取得できなくても進める（blank=True）。

### 2. seed 付きランダム化（__init__.py, settings.py）
- 順序のブロックランダム化と FAB 項目順のシャッフルを `random.Random(seed)` で行う。seed は session config の `rand_seed`
  （0 = セッションコードの SHA-256 から決定的に導く、既定）。各回答の `rand_seed` 列に記録され、割り当てを再現できる。

### 3. run ログ（tools/run_log.py, docs/run_log.csv）
- エクスポート CSV からセッションごとに日付・目的（pilot / main / bot-test / demo）・版・設定・乱数シード・人数（行・開始・完了・
  アプリ内除外・順序群別）・最初と最後の時刻・ファイル名と MD5 を追記・更新する。

### 4. 解析パイプライン（analysis/, run_analysis.bat, run_analysis.sh）
- `00_setup.R`（新規）: 定数（seed 20261024、ブートストラップ 5,000 回、除外閾値 0.25、SESOI r = .10、CFA の最小 N 100）、
  入出力先の環境変数、分析ノートのヘルパー、Spearman + ブートストラップ CI、3 段階判定、Okabe–Ito パレット、図の保存（PDF + PNG）。
- `01_clean.R`: 来歴の確認（設定・版が 1 通りでなければ停止）、除外表に「基準の重なり」「閾値の実値」「順序群ごとの件数」、
  記述統計表（全体・順序群、除外前後）、分析ノートの自動生成（入力の MD5、除外、尺度得点の作り方）。
- `02_main.R`: seed 固定。H1 に 95%・90% のブートストラップ CI と 3 段階判定（再現 / 効果なし（同等） / 判定保留）、
  原研究の .27 が CI に含まれるかは参考扱い。H2/H3 の係数表を CSV に。H4 は群ごとのブートストラップ CI。自己予測は Hodges–Lehmann 推定値と CI。
  感度分析 (a) 除外前 (b) 1 回目の入力 (c) Pearson (d) 気が散った ≥ 5 を除く (e) z 得点モデル を 1 つの表に。
  信頼性（α・ω）と減衰補正した r（探索）。結果を results.md と results.json・CSV に出す。図は 04 に分離。
- `04_figures.R`（新規）: (a) 参加者ごとの点の散布図（x だけジッタ）、(b) 分配額の分布（0 円を独立した階級、ゼロ基準）、
  (c) 順序群ごとの rs と 95% CI（点 + 線、原研究の値と SESOI 帯）、(d) 自己予測 × 実際。結合図 `fig_main`、キャプション案。
- `99_synthetic.R`（新規）: oTree のエクスポート形式の合成データ。`run_analysis.bat synthetic` で本データと別の出力先に通す。
- `03_compare_original.R` は変更なし。

### 5. その他
- settings.py: `rand_seed` 既定 0、`app_version` v0.3-pilot。
- tests.py: 来歴の列（設定値・版・seed・hidden 項目の長さ制限）の検査を追加。`otree test a1_ja` / `a1_en` が通ることを確認（oTree 5.11.5, Python 3.11）。
- run_dev.bat / run_tests.bat: `A1_GIT_COMMIT` を `git rev-parse` で設定（Git 管理していなければ unknown）。
- README: 状態・構成・「解析」節を更新。docs/example_output_synthetic/ に合成データの出力例。

### 確認が必要な点（v0.2 からの持ち越しに追加）
6. 判定基準の SESOI r = .10 と停止規則（有効 106 名未満なら 1 週間延長）を事前登録に書く。
7. 図の軸ラベルの言語（既定 en。日本語の卒論なら `A1_FIG_LANG=ja`）と投稿先の図表規定（幅・フォント）。規定未確認。
8. 感度分析 (d) の閾値（eval_distract ≥ 5）。

## v0.2-pilot（2026-10-18）— OSF T5MF2 の原資料に合わせた改訂

原資料: https://osf.io/t5mf2/（Binder, Schultze, Chen & Windmann, 2026, *Sci Rep* 16:11600 の補足資料）。
読んだファイル: Supplement.pdf（S1 FAB 項目）、Study_overview.xlsx、analysis.Rmd、Studies/09 と 11 の codebook・preprocessing.R、
Studies/03/03_thesis_blinded.pdf（付録に教示原文）。要点は `docs/osf_sources.md`。

### 1. FAB 15 項目を確定文言に置き換え（texts/en.py, ja.py）
- 【仮項目】8 件を含む全 15 項目を Supplement S1 の英語原文に差し替えた（英語版は原文をそのまま使用）。
- 日本語版は 15 項目すべてを新たに訳した（**案**。バックトランスレーション後に確定版へ置き換える）。
  v0.1 で既知だった 7 項目の訳も S1 の原文に合わせて見直した（例: HG-2「他の人を助ける」→ hg_7「見ず知らずの人を助ける」、
  PP-1 は PAID 2024 の別訳だったので S1 の pp_1「協力してくれる仲間を探す」に変更）。
- 逆転項目はない（S1 の 15 項目はすべて正方向。analysis.Rmd の 7 − x 再コードは生データの別項目用）。

### 2. 変数名を原研究と同じにした（__init__.py, codebook.csv, R スクリプト, tests.py）
- `fab_hg1…fab_mc5` → `hg_1, hg_3, hg_7, hg_10, hg_13, pp_1, pp_8, pp_12, pp_14, pp_15, mc_1, mc_3, mc_18, mc_20, mc_23`
  （原研究の `Studies/XX/XX_data.csv` および analysis.Rmd の `cfa_model` と同じ）。原データとそのまま結合・比較できる。
- 注意チェック `att1/att2` → `cq1/cq2`（原研究の control question の名前）、`att*_pass` → `cq*_pass`、
  アプリ内除外理由 `'att'` → `'cq'`。
- codebook.csv に `original_variable` 列を追加（原研究の対応変数）。

### 3. 注意チェックの文言と正答を原研究に合わせた
- 原文（Studies/09, 11 codebook）: *Please tick the option "strongly disagree" for this question. This is a control question.* /
  同 *"strongly agree"*。
- v0.1 の「ややそう思う（4）」「そう思わない（2）」から、cq1 = 「全くそう思わない」(1)、cq2 = 「強くそう思う」(6) に変更
  （`C.CQ_EXPECTED`）。文言も「これは確認のための質問です」を付けた原文直訳にした。

### 4. 質問紙の教示文を原文に合わせた
- 原文（Studies/11 codebook の QUESTION 列）: *Please state honestly and spontaneously how you would typically behave or act.*
  → 「あなたが普段どのようにふるまい、行動するかを、正直に、直感的にお答えください。」（SurveyIntro と各ページ上部）。

### 5. DG の決定を「0〜元手の任意の額を数値入力」にした（DGDecision.html, DGPredict.html, settings.py）
- 原研究は「0 から 10.70 ユーロまでの任意の額を入力」（Study 03 卒論 p.16、codebook の `dg_give` は自由入力）。
  v0.1 の 100 円刻みのラジオボタンをやめ、数値入力欄（`type=number`）にした。取り分の即時表示は維持。
- 刻みは session config の `dg_step` で変えられる（既定 **1** = 原研究どおり。100 にすれば 100 円単位）。
  範囲外・刻み違いの値はサーバー側でも弾く（`dg_give_error_message`, `dg_predict_error_message`）。
- 自己予測（dg_predict）も同じ入力欄にした。

### 6. DG の教示を原文の構成に近づけた（texts）
- 原文（Study 03 付録 p.44）: 「あなたは運がよい！ 当たりグループに入りました…10.70 ユーロをプレゼントします。
  1. 全額を自分のものにする 2. 当たりグループに入らずプレゼントをもらえなかった別の参加者と分ける。お互いに匿名。
  10.70 ユーロのうち、いくらをはずれグループの人に分けますか」。
- 本追試は役割不確定法（欺罔なし）なので、「締切後にくじで当たり／はずれグループに分ける。いまは全員が当たりグループに
  なったつもりで決める」と書き換えたうえで、「当たり／はずれ」「プレゼント」「2 つの選択肢」「お互いに匿名」の構成を踏襲した。
  決定画面の問い「{endowment} のうち、いくらをはずれグループの相手に分けますか」も原文に対応。
- 選択肢 2 つは箇条書き（`dg_options`）。理解確認の再回答時の説明にも同じものを表示。

### 7. DG 入力の確認画面を追加（DGConfirm.html, DGDecisionAgain）
- 原研究 Study 09 の `dg_correct`（「入力は正しいですか？」Yes/No。No なら `dg_give_2` で再入力し、前処理で置換）を再現。
- 決定 → 確認（`dg_correct` 1 = 正しい / 2 = 入力し直す）→ 2 なら再入力画面（1 回だけ）。
  記録: `dg_give_1`（1 回目）、`dg_give_2`（再入力時のみ）、`dg_give`（最終決定）。

### 8. 事後評価ページを追加（PostSurvey.html）
- 原研究 Study 11 の事後評価（AG11_01〜06）から 4 項目: 理解しやすかった／決定は難しかった／実生活の決定を反映／
  気が散っていた（6 件法、必須）＋ 自由記述「気づいたこと・感想」（任意、Study 03 の事後質問に対応）。
- 変数: `eval_understand, eval_difficult, eval_reflect, eval_distract, comment_open`。

### 9. 除外基準と解析を原研究に合わせた（analysis/）
- 01_clean.R: 所要時間の閾値を「中央値の 1/4 未満」に変更（原研究 preprocessing.R と AsPredicted #40376。v0.1 は 1/3）。
  下位尺度平均の変数名を `hg_mean_fab` 等（analysis.Rmd と同じ）に、送金有無を `dg_binary` にした。
- 02_main.R: H2 を原研究と同じ二部（ハードル）モデルにし、HG・PP・MC を同時投入（H3 を兼ねる）。
  OR と「原尺度での % 変化」(exp(b) − 1) × 100 で報告。予測子は lavaan が使えて N ≥ 100 なら原研究と同じ
  CFA 因子得点（MLR, FIML, 標準化）を主分析にし、下位尺度平均の z 得点を感度分析として併記（VIF も出す。
  N ≈ 120 では因子得点が共線になりやすいため）。Spearman 相関行列（Holm 補正）とヒートマップ、
  入力し直し・事後評価の記述統計を追加。01・02 は合成データ（N = 130）で最後まで動くことを確認。
- 03_compare_original.R（新規）: OSF の公開データ（Study 03, 09, 11, 12, 13, 15 の整形済み CSV）をダウンロードし、
  同じ指標（r, OR, % 変化, α）を研究ごとに計算して本追試の比較基準を作る。本追試と同条件（欺罔なし・間隔なし）は 09 と 11。
  （構文チェックのみ。OSF からのダウンロードを含むため、手元の R で実行して確認する）

### 10. その他
- settings.py: `dg_step` 既定 100 → 1、`app_version` v0.2-pilot。
- texts/__init__.py: 画面ごとの値（{give} {keep}）を埋める `fill()` を追加。未知のプレースホルダーはエラーにしない。
- tests.py: ケースを 5 → 7 に（`revise`: 入力し直し、`bad_amount`: 範囲外・刻み違いの拒否）。`att_fail` → `cq_fail`。
  `otree test a1_ja` / `a1_en` が dg_step = 1 と 100 の両方で通ることを確認（oTree 5.11, Python 3.11）。
- tools/browser_walk.py: 数値入力・確認画面・事後評価に対応。
- style.css: 選択肢の箇条書き、金額入力欄、確認文のスタイルを追加。
- README.md: 状態と残作業を更新。`docs/osf_sources.md`（原資料の抜粋と対応表）、`docs/screens_v0.2_ja.pdf`（全 18 画面）を追加。

### 変えていないこと（設計上の決定のまま）
- 役割不確定法・欺罔なし・一回完結・順序ランダム化・理解確認・自己予測（実験計画書 A-1 の決定）。
- 元手 1,000 円、参加謝礼 300 円、属性項目（年齢・性別・学年・経済ゲーム経験）。
- 同意文の [研究者名・所属・メールアドレス] [大学名]、連絡先フォーム URL、HEXACO 項目は未記入のまま。

### 確認が必要な点
1. DG の刻み: 原研究どおり 1 円単位（既定）でよいか。ギフトコードの最小単位に合わせて 10 円や 100 円にするなら `dg_step` を変更。
2. 注意チェックの正答を原研究と同じ両端（1 と 6）にしたこと（v0.1 の計画書は 4 と 2）。事前登録の記述もこれに合わせる。
3. FAB の和訳 15 項目はすべて案。バックトランスレーションの担当と手順を決める。
4. 所要時間の除外閾値を 1/4 にしたこと（計画書は 1/3）。事前登録に合わせて統一する。
5. 事後評価 4 項目を入れたこと（所要時間 +1 分弱）。不要なら `PostSurvey` を page_sequence から外す。
