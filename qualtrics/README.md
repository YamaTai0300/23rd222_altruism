# Qualtrics 版（A-1 v0.5 の再現）

作成: 2026-11-05。oTree 版 v0.5（`../a1-decision-study_v0.5/`）と同じ 9 ページ構成を Qualtrics で再現したもの。

## できたもの

| 項目 | 内容 |
| --- | --- |
| Qualtrics のプロジェクト | **study_v5**（調査 ID `SV_6PfFg1rhsV2G2uG`、ブランド `qualtricsxmw5hysnkpn.hnd1`）。2026-11-05 に `A-1_v0.5_ja.qsf` を取り込んで作成。既存の `SV_egt7X9VgLDhmk8C`（利他性と自己評価_追試）はそのまま |
| `A-1_v0.5_ja.qsf` | 取り込んだ QSF（無料アカウント向け。Timing 質問と JavaScript なし、43 質問） |
| `A-1_v0.5_ja_full.qsf` | 有料ライセンス向け（各ページの Timing 質問 `t_*` と、決定画面の取り分の即時表示 JavaScript を含む、52 質問）。無料アカウントでは 403 で取り込めない |
| `make_qsf.py` | 生成スクリプト。文言は oTree 版の `altruism_study/texts/ja.py` から読む。`python make_qsf.py --texts ../a1-decision-study_v0.5/altruism_study/texts/ja.py`（`--full` で有料版、`--brand` でブランド ID） |

## 構成（oTree 版との対応）

- ブロック: 1 同意 → 2・3 質問紙 1/2（FAB + 注意チェック、2 ページ）→ 4 質問紙 2/2（HEXACO、5 件法、1 ページ）→ 5 DG 説明 → 6 理解確認 → 6b 再回答（1 回目が不正解のときだけ）→ 7 決定 → 8 事後評価 → 9 終了（参加者コード = `${e://Field/ResponseID}`）
- Survey Flow: 埋め込みデータ（endowment, participation_fee_yen, app_version, task_order, scale_order）→ 同意 → ランダマイザー（均等に表示、task_order 1 / 2）→ 各群の中にランダマイザー（scale_order 1 / 2）→ 事後評価 → 終了。理解確認は「Text Response ≠ 700」で再回答ブロックに分岐
- 項目順: FAB はブロック内の Advanced Randomization（注意チェック cq1 / cq2 はページの中央に固定）。HEXACO も同様。oTree 版と違い、どの FAB 項目が 1 ページ目か 2 ページ目かは固定（1 ページ目: hg_1〜hg_13, pp_1, pp_8, pp_12 + cq1。2 ページ目: pp_14, pp_15, mc_1〜mc_23 + cq2）
- 検証: 全項目必須。理解確認・決定は数値（決定は 0〜1,000 の整数）。同意は 2 項目とも必須（MinChoices = 2）
- 変数名（Export tag）: hg_1 … mc_23, cq1, cq2, hex_1 … hex_10, dg_check（1 回目）, dg_check2（再回答）, dg_give, eval_understand, eval_difficult, eval_reflect, eval_distract, comment_open, consent（consent_1, consent_2）。Likert は 1〜6（HEXACO は 1〜5）で記録
- 2026-11-05 のプレビューで確認: 同意の必須、理解確認の数値検証と再回答への分岐、決定の範囲検証（1,500 / −5 を拒否）、FAB 2 ページ（cq が中央）、HEXACO、事後評価、終了画面の ResponseID の表示。順序群 2（DG が先）の経路で通した

## 無料アカウントの制限で oTree 版と違う点

- ページごとの時間（Page Times 相当）が取れない。全体の所要時間は Qualtrics の `Duration (in seconds)` 列で取れる。感度分析 (f)（速い回答）は全体時間だけで行うか、有料版（`_full.qsf`）に切り替える
- 決定画面で取り分を即時表示できない（説明文で補っている）
- 無料アカウントは回答数・アクティブな調査数に上限がある（公開情報では回答 100 件程度）。目標 N = 120〜135 なので、本実験の前に大学のライセンスか上限を確認する
- 進捗バーはプレビューでは 0% のままに見えた。公開後に確認し、不要なら Look & Feel で非表示にする

## 残り

- HEXACO 10 項目と 5 件法の語の転記（若林 2014）。Qualtrics のビルダーで直接書き換えるか、`texts/ja.py` を直して QSF を作り直し、Create project → Import QSF で新しく取り込む（ビルダーで直した内容は QSF の作り直しで引き継がれないので、どちらか一方に決める）
- 同意文の [大学名]。リンク配布時の案内文（謝礼・連絡先・参加者コードの申告方法）
- 公開前: Survey Options の「Incomplete responses」（未完了の扱い）、`BallotBoxStuffingPrevention`（多重回答の防止）、Anonymize（IP の保存）を決める
- データのエクスポートは「数値」形式、「Export viewing order data for randomized surveys」をオンにすると項目順も出る。`analysis/01_clean.R` は oTree のエクスポート形式を前提にしているので、Qualtrics の列名への変換（`participant.code` → `ResponseID`、`player.*` → export tag、`finished` → `Finished`、Timing なし）を 1 枚かませる必要がある
