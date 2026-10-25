# a1-decision-study — A-1 追試（FAB 質問紙 × 独裁者ゲーム）の oTree 実装（v0.4・日本語版）

Binder, Schultze, Chen & Windmann (2026, *Sci Rep* 16:11600) の「Help Giving → 独裁者ゲーム」を
日本の大学生で再現する一回完結のオンライン実験。設計はこの文書に従う:

- 要件定義・設計書: https://claude.ai/code/artifact/5f9cc974-cbb4-4fd0-840b-7836e6283d47
- 実験計画書 A-1: https://claude.ai/code/artifact/7d6d3bf2-110f-4096-87f7-f1ae9ec69219
- 再現要素一覧（Excel）: `../A-1_再現要素一覧.xlsx`
- 原研究の公開資料（OSF T5MF2）からの抜粋と対応表: `docs/osf_sources.md`、変更履歴: `CHANGELOG.md`

参加者は各自のスマホ・PC から募集期間中の好きな時刻に 1 人で参加する（完全非同期、約 15 分）。
WaitPage やグループは使わない。DG の相手とのペアは締切後に `tools/pairing.py` でオフラインに組む。

## 状態（2026-10-24, v0.4）

v0.2 で OSF T5MF2 の原資料（補足資料 S1、codebook、前処理・解析スクリプト、卒論付録の教示原文）に合わせて改訂し、
v0.3 で実験計画書の「記録・分析ノート・図表」と改訂した「分析計画」（判定基準・感度分析・不確実性の明示）を実装、
v0.4 で HEXACO の採用、完了者だけの保存、設定値の CSV からの読み取り、Page Times による速い回答の検出を加えた。
変更点の一覧は `CHANGELOG.md`。

できていること

- **HEXACO 正直さ-謙虚さ（v0.4）**: `use_hexaco=True` が既定。HEXACO-60 の 10 項目（英語は `texts/en.py`、hexaco.org と要照合）を
  FAB と一体でランダム提示（6 件法）。逆転項目は `codebook.csv` の `reverse` 列、平均 `hh_mean` は `01_clean.R`、探索 H5 は `02_main.R`
- **完了者だけを保存（v0.4）**: `tools/archive_export.py` が管理画面のエクスポートから `finished == 1` の行だけを `raw/<purpose>/` に保存し、
  Page Times も同じ参加者に絞って SHA-256 を記録する。未完了の行は保存しない（同意文にも明記）
- **設定値の読み取り（v0.4）**: `cfg_fee` を各回答に記録し、`tools/pairing.py` は元手と参加謝礼を CSV の `cfg_endowment`・`cfg_fee` から読む
- **Page Times（v0.4）**: `01_clean.R` がページごとの滞在秒数を出し、質問紙 < 2 秒/項目・DG 決定 < 5 秒を速い回答、
  1 ページ 10 分以上を中断としてフラグ（除外ではなく感度分析 (f)(g) と記録に使う）。閾値は `00_setup.R` の `CFG`

- **来歴の記録（v0.3）**: 各回答に `app_version`・`git_commit`・`otree_version`・設定値（`cfg_endowment`, `cfg_dg_step`, `cfg_use_hexaco`）・
  乱数シード `rand_seed`・ブラウザ `user_agent`・`screen_width` を残す。順序割り当てと項目順は `rand_seed` から再現できる
- **run ログ（v0.3）**: `tools/run_log.py` がエクスポート CSV からセッションごとの要約（設定・版・人数・MD5）を `docs/run_log.csv` に追記する
- **解析パイプライン（v0.3）**: `run_analysis.bat` / `run_analysis.sh` で 01（除外・記述統計）→ 02（主分析）→ 04（図）を順に実行。
  結果は `results.md`（人が読む）と `results.json`・CSV（機械可読）、分析ノート `analysis_notes.md`（入力の MD5・除外・検定・版・seed を自動記録）。
  合成データ（`analysis/99_synthetic.R`）で最後まで通ることを確認済み。出力先は本データと分けてある

- 全 26 ページ（同意 → コード → 質問紙 2 ページ → 属性 → DG 説明 → 理解確認 → 自己予測 → DG 決定 → 入力確認
  →（入力し直し）→ 事後評価 → 終了）を順序 2 群（質問紙→DG / DG→質問紙）で実装。順序はセッション作成時にブロックランダム化
- FAB 15 項目は Supplement S1 の確定文言（英語は原文、日本語は訳案）。変数名は原研究と同じ `hg_1 … mc_23`
- 注意チェック 2 項目（`cq1` = 全くそう思わない, `cq2` = 強くそう思う。原研究の control question と同じ文言・正答）を
  FAB と一体でランダム順に提示し、順序を `fab_item_order` に記録
- DG は原研究と同じく 0〜元手の任意の額を数値入力（刻みは `dg_step`）。入力後に確認画面（原研究 Study 09 の `dg_correct`）、
  「いいえ」なら 1 回だけ入力し直せる（`dg_give_1`, `dg_give_2`, 最終 `dg_give`）
- 未回答チェック（回答済みの選択を保持したまま未回答項目を赤枠で表示）、理解確認の 1 回だけの再回答、
  DG 決定画面の取り分の即時表示、終了画面から連絡先フォームへ参加者コード付きで誘導
- 事後評価 4 項目（原研究 Study 11 の評価項目）と自由記述
- 所要時間・完了・アプリ内除外フラグ（注意チェック・理解確認）の記録
- ボットテスト 7 ケース（`otree test a1_ja` / `a1_en`）が `dg_step` = 1 と 100 の両方で通る
- `tools/pairing.py`（ペアリング・役割抽選・支払額）、`tools/export_check.py`（CSV とコードブックの突合）、
  `analysis/`（コードブック、除外・主分析・原データとの比較の R スクリプト）

まだのもの（必ず対応してから予備実験に使う）

1. **FAB の和訳の確定**: `altruism_study/texts/ja.py` の 15 項目はすべて訳案。バックトランスレーション
   （和訳 → 別の人が英訳 → S1 の原文と比較 → 修正）を経た確定版に置き換える。英語原文は `en.py` と `docs/osf_sources.md`
2. **連絡先フォーム**: Google フォーム（参加者コード + メールアドレス）を作り、事前入力 URL を
   `settings.py` の `contact_form_url` に入れる（`entry.NNNN=` の後ろにコードが付く）
3. **同意文の固有情報**: `consent_body` の [研究者名・所属・メールアドレス]、`student_check` の [大学名]
4. **決めること（CHANGELOG「確認が必要な点」）**: DG の刻み（既定 1 円）、注意チェックの正答（両端）、
   所要時間の除外閾値（中央値の 1/4）、事後評価を入れるか、混ぜる尺度（HEXACO）を使うか
5. `docs/screens_v0.2_ja.pdf`（v0.2 の全 18 画面、スマホ幅）を見て文言・レイアウトを確認する（v0.4 で同意文・DG 説明・終了画面の
   謝礼に関する文言を変えたので撮り直す）
8. **HEXACO 日本語版 10 項目の転記**: `texts/ja.py` の `hex_1〜hex_10` は未転記。若林 (2014) の日本語版から
   `../FAB_和訳作業シート.xlsx`「HEXACO-HH」の対応表（HEXACO-60 の項目番号・逆転）に沿って転記する。英語原文も hexaco.org と照合する
9. **謝礼の種類・支払い方法**: 未決。画面の文言は方法を指定しない形にしてある（「謝礼としてお支払い」「受け取り方法はメールで案内」）。
   決まったら実験計画書と文言（`consent_body`, `dg_intro_body`, `end_body`）に入れる
6. **R の解析環境**: R 4.2 以上と `install.packages(c("tidyverse", "psych", "GPArotation", "lavaan", "boot", "jsonlite", "digest", "patchwork"))`
   を入れ、`run_analysis.bat synthetic` が最後まで通ることを確認する（下の「解析」）
7. **事前登録**: 実験計画書の判定基準（SESOI r = .10 の 3 段階）・感度分析 (a)〜(e)・停止規則を AsPredicted / OSF に転記し、
   `analysis/` のスクリプトをデータ収集前に凍結する

## 動かし方（ローカル）

### いちばん簡単な方法（Windows）: `run_dev.bat` をダブルクリック

1. Python を用意する。oTree 5 は **3.10・3.11・3.12** で動く（3.11 推奨。3.13 は依存パッケージがビルドできない）。
   `run_dev.bat` は次の順で探す: 環境変数 `A1_PYTHON`（python.exe のフルパス）→ `py -3.11` / `py -3.12` / `py -3.10`
   （python.org の installer で「py launcher」を入れた場合）→ conda 環境 `a1`（`conda create -n a1 python=3.11 -y`。
   miniconda3 / anaconda3 の `envs\a1` を自動で見つける）→ PATH 上の `python` が 3.10〜3.12 の場合。
   見つからないと黒い窓にエラーと 3 つの対処が表示され、キーを押すと閉じる。
2. `run_dev.bat` をダブルクリック。初回は 2〜3 分かかる（仮想環境の作成とパッケージの取得）。
3. ブラウザで http://localhost:8000/demo が開く → 「A-1 日本語版（予備実験）」→ 参加者リンクのどれかを開く。
   スマホ表示を見るにはブラウザの開発者ツール（F12）→ デバイスツールバーで幅 375 にする。
4. 止めるときは黒い窓で Ctrl+C。

`run_dev.bat` は、このフォルダー（OneDrive 配下）の中身を `%LOCALAPPDATA%\a1-decision-study` にコピーしてから
起動する。OneDrive の同期と `db.sqlite3` の書き込みがぶつかるのを避けるため。**コードの編集はこのフォルダーで行い、
編集後に `run_dev.bat` をもう一度実行する**（コピー先を直接編集すると次回上書きされる）。ポートが使用中なら
`run_dev.bat 8001` のように引数で変えられる。

ボットテストと CSV 出力は `run_tests.bat`（引数で人数、既定 14 = 7 ケース × 2）。結果は `%LOCALAPPDATA%\a1-decision-study\__temp_bots\`。

### 手動で行う場合（PowerShell / macOS / Linux）

```powershell
py -3.11 -m venv .venv            # macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
$env:OTREE_ADMIN_PASSWORD = "admin"  # macOS/Linux: export OTREE_ADMIN_PASSWORD=admin
otree devserver                   # http://localhost:8000 → Demo → 「A-1 日本語版（予備実験）」
otree test a1_ja 14               # ボット 14 名 × 7 ケース
otree test a1_ja 40 --export __temp_bots   # CSV を書き出す
python tools/export_check.py __temp_bots/altruism_study.csv
```

### 画面だけ先に見たいとき

`docs/screens_v0.2_ja.pdf` に、v0.2 のスマホ幅の全 18 画面（エラー表示・再回答・入力し直し・事後評価を含む）が入っている。v0.1 は `screens_v0.1_ja.pdf`。

### つまずきやすい点

- 黒い窓に「No usable Python was found」と出てキーを押すと閉じる → 3.10〜3.12 の Python が見つかっていない。
  python.org の 3.11 を py launcher 付きで入れるか、conda で `conda create -n a1 python=3.11 -y` を作って再実行
- `pip install` で websockets / sqlalchemy のビルドエラー → Python 3.13 で動かしている。3.10〜3.12 を使う
- 「database is locked」や起動のたびにデータが消える → OneDrive 配下で直接 `otree devserver` を実行している。`run_dev.bat` を使う
- 画面の下に「Debug info」が出る → devserver の正常な表示。本番（`OTREE_PRODUCTION=1`）では出ない
- 英語版（`a1_en`）を試すとき → `settings.py` の `LANGUAGE_CODE` を `'en'` にする（「次へ」などの定型文の言語）

## 構成

```
settings.py                  SESSION_CONFIGS（a1_ja / a1_en）、ROOMS（pilot / main）、言語・通貨
altruism_study/
  __init__.py                定数 C、Player モデル、ページ、page_sequence、creating_session
  texts/ja.py, en.py         すべての表示文言（テンプレートには文言を書かない）。FAB 項目は S1 の原文／訳案
  *.html                     画面テンプレート 12 種（順序群で共用）
  tests.py                   ボットテスト 7 ケース
_templates/global/Page.html  全ページ共通（スタイルシートの読み込み）
_static/study/style.css
tools/pairing.py             締切後: ペアリング・役割抽選・支払額 CSV（--seed 必須）
tools/export_check.py        エクスポート CSV を analysis/codebook.csv と突合
tools/archive_export.py      エクスポートから完了者だけを raw/<purpose>/ に保存し、Page Times を絞り、SHA-256 を記録（v0.4）
tools/run_log.py             エクスポート CSV からセッションの要約を docs/run_log.csv に追記（v0.3）
tools/browser_walk.py        Playwright で通し確認（任意）
run_dev.bat / run_tests.bat  Windows 用の起動・テスト（OneDrive 外にコピーして実行）
run_analysis.bat / .sh       解析パイプライン 01 → 02 → 04 を順に実行（synthetic / original モードあり）（v0.3）
docs/osf_sources.md          OSF T5MF2 から取得した原資料の抜粋（教示文・注意チェック・除外基準・変数名）
docs/screens_v0.2_ja.pdf     v0.2 の全画面のスクリーンショット（v0.1 は screens_v0.1_ja.pdf）
docs/run_log.csv             run ログ（セッションごとの設定・版・人数。tools/run_log.py が書く）（v0.3）
docs/example_output_synthetic/  合成データで作った出力の例（results.md, analysis_notes.md, fig_main.png など。本物のデータではない）
analysis/codebook.csv        変数定義（名前・型・範囲・画面・役割・原研究の対応変数）
analysis/00_setup.R          共通設定（seed・ブートストラップ回数・除外閾値・SESOI・入出力先・パレット）とヘルパー（v0.3）
analysis/01_clean.R          除外（中央値の 1/4・注意チェック・理解確認・重複）と尺度得点、除外表、記述統計表、来歴の確認、
                             Page Times による速い回答・中断のフラグ（v0.4）
analysis/02_main.R           主分析（H1 相関 + 3 段階判定、H2/H3 二部モデル、H4 順序、H5 HEXACO、自己予測、感度分析 (a)〜(g)、信頼性、相関行列）
analysis/03_compare_original.R  OSF の公開データで同じ指標を計算して比較基準を作る
analysis/04_figures.R        図 a〜d と結合図（Okabe–Ito、PDF + PNG、キャプション案）（v0.3）
analysis/99_synthetic.R      パイプライン確認用の合成データ（oTree のエクスポート形式）（v0.3）
CHANGELOG.md                 変更履歴（v0.1 → v0.2 → v0.3 の対応表）
```

## セッション設定（settings.py）

| キー | 既定 | 意味 |
| --- | --- | --- |
| `lang` | ja / en | 文言セット。`LANGUAGE_CODE`（oTree の定型文）も合わせる |
| `endowment` | 1000 | DG の元手（円）。理解確認の正答は `endowment - 300` |
| `dg_step` | 1 | DG の入力の刻み（円）。原研究は任意の額（刻みなし）。100 にすると 100 円単位 |
| `participation_fee_yen` | 300 | 参加謝礼（文言と pairing.py に使う） |
| `use_hexaco` | True | HEXACO-60 正直さ-謙虚さ 10 項目を質問紙に混ぜる（v0.4 で採用。日本語訳は未転記） |
| `contact_form_url` | 要差し替え | 連絡先フォームの事前入力 URL |
| `rand_seed` | 0 | 順序割り当て・項目順の乱数シード。0 = セッションコードから決定的に導く。各回答の `rand_seed` 列に記録される |
| `app_version` | v0.4-pilot | データに記録する版（Git タグと合わせる） |

これらはセッション作成画面でも上書きできる。

## 設計書との差分

- `order` は oTree の予約語のため、順序群の変数名は **`task_order`** にした（1 = 質問紙→DG, 2 = DG→質問紙）。
  コードブック・R スクリプトも `task_order`
- FAB・注意チェック・属性の各フィールドは `blank=True` にし、必須チェックは `error_message` で行う。
  こうすると未回答があっても回答済みの値を保存でき、再表示時に選択が消えない（設計書 §7 の意図どおり）
- ページのテンプレートは先頭で `{{ extends "global/Page.html" }}` を宣言する（oTree 5 では
  `_templates/global/Page.html` は自動では使われないため）
- v0.2 で原研究に合わせて変えた点（設計書・計画書の記述と異なる）: FAB の変数名（`hg_1` 形式）、注意チェックの正答（両端の 1 と 6）、
  DG の入力方式（任意の額の数値入力）と確認画面、所要時間の除外閾値（中央値の 1/4）、事後評価ページの追加。詳細は `CHANGELOG.md`

## 解析（analysis/）

実験計画書「分析計画」「記録・分析ノート・図表」をそのまま実装している。R 4.2 以上と上記パッケージが必要。

```
run_analysis.bat               本データ:  raw\final\altruism_study_*.csv → data\ → output\
run_analysis.bat synthetic     合成データ: analysis\99_synthetic.R → raw\synthetic → data_synthetic\ → output_synthetic\
run_analysis.bat original      analysis\03_compare_original.R（OSF の公開データで比較基準。ネットワークが必要）
```

- 出力: `results.md`（主分析の本文。H1 は 3 段階判定つき）、`results.json`・`model_coefficients.csv`・`sensitivity.csv`・
  `descriptives.csv`・`corr_matrix_*.csv`（機械可読）、`analysis_notes.md`（入力ファイルの MD5、除外の基準と件数、
  使った検定と前提、R とパッケージの版、seed、図の一覧を自動記録。手で編集しない）、`fig_a〜d`・`fig_main`（PDF + PNG）、`fig_captions.md`
- 定数（seed 20261024、ブートストラップ 5,000 回、除外閾値 0.25、SESOI r = .10、CFA の最小 N 100）は `analysis/00_setup.R` の `CFG` に集約。
  変えたら事前登録と計画書も変える
- 入出力先は環境変数 `A1_RAW_DIR` / `A1_DATA_DIR` / `A1_OUT_DIR` で切り替える。合成データ・パイロットの出力を本データと混ぜない
- `01_clean.R` は `app_version`・設定値・Git コミットが 1 通りでないと止まる（設定の違うセッションを混ぜない）。
  確認のうえ混ぜるときだけ `A1_ALLOW_MIXED=1`
- 図の軸ラベルは既定で英語（`A1_FIG_LANG=en`）。日本語にするときは `A1_FIG_LANG=ja` と `A1_FIG_FONT`（Windows: `Yu Gothic`）。
  `run_analysis.bat` は日本語を既定にしている。日本語が「…」や □ になるときはロケールが UTF-8 でないかフォントがない
- 収集中は `01_clean.R` だけを走らせて N と除外件数を見る。`02_main.R`（HG × DG の関連）は締切まで実行しない（計画書）
- 解析の入力は `tools/archive_export.py` で作った完了者だけの CSV（`raw/final/altruism_study_<date>.csv`）と、同じ日付の
  `PageTimes_<date>.csv`（管理画面 Data → Page Times からダウンロードして同じコマンドに `--page-times` で渡す）

## 運用・デプロイ

設計書 §11（ローカル → 研究室サーバー → クラウド）と §12（セッション作成・募集 URL・監視・エクスポート・
ペアリング・支払い・デブリーフィング・削除）に従う。要点:

- 本番は `.env`（`.env.example` をコピー）で `OTREE_PRODUCTION=1`、`OTREE_AUTH_LEVEL=STUDY`、
  `OTREE_ADMIN_PASSWORD`、`OTREE_SECRET_KEY` を設定し、`otree resetdb` → `otree prodserver`
- 募集 URL は Rooms → `pilot` / `main` にセッションをつないで表示される URL。参加者枠は累計の上限
- 本実験中は `otree resetdb` を実行しない（全データが消える）。毎日 CSV をエクスポートして保管し、
  `python tools/run_log.py raw/main/altruism_study_<date>.csv --purpose main` で run ログを更新する
- 起動前に環境変数 `A1_GIT_COMMIT` にコードのコミットを入れる（`run_dev.bat` は `git rev-parse` で自動設定。Git 管理していなければ
  `unknown` になるので、`app_version` を版ごとに必ず変える）
- 締切後: `python tools/pairing.py --data raw/final/altruism_study_<date>.csv --contacts raw/contacts_<date>.csv --seed <整数>`
  → `payout/pairs_<date>.csv` の `payout_yen` を支払う（元手・参加謝礼は CSV の記録値から読む。支払いの方法・送付手順は未決、計画書に記載予定）
