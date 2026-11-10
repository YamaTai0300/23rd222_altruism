# 23rd222_altruism — A-1 追試（自己評価の利他性 × 独裁者ゲーム）

Binder, Schultze, Chen & Windmann (2026, *Scientific Reports* 16:11600; OSF [T5MF2](https://osf.io/t5mf2/)) の
「自己報告の Help Giving（FAB 尺度）と独裁者ゲーム（DG）の分配額の関係」を、日本の CrowdWorks ワーカーで再現する追試の作業リポジトリ。

- 募集: CrowdWorks（日本語母語・18 歳以上・承認率 95%・PC、定員 150）
- 実施: 研究室 Qualtrics が第一候補、oTree 版が代替
- 1 人で完結するオンライン実験（約 10 分）。質問紙（FAB 6 件法・HEXACO 正直さ-謙虚さ 5 件法）と DG の順序、質問紙 2 段階の順序をランダム化

## 最初に見るもの

| 見たいもの | 場所 |
| --- | --- |
| 研究の計画（目的・仮説・手続き・分析） | 実験計画書 A-1（Claude Docs。リンクは研究者に問い合わせ） |
| 参加者が見る画面 | `a1-decision-study/docs/screens_v0.5_ja.pdf`（v0.6 は文言の変更のみ） |
| 参加者が見る文言（日本語の正本） | `a1-decision-study/altruism_study/texts/ja.py` |
| 決まっていること・未決のこと | `docs/研究の決定事項と未決事項.md` |
| 質問紙（FAB・HEXACO）の文言と出典 | `docs/質問紙_FABとHEXACO.md` |
| 前の版からの変更点 | `a1-decision-study/CHANGELOG.md`、`qualtrics/README.md` |
| 原研究との対応 | `A-1_再現要素一覧.xlsx`、`a1-decision-study/docs/osf_sources.md` |

## 現在の状態（2026-11-11）

| 対象 | 版 | 状態 |
| --- | --- | --- |
| 実験計画書 A-1 | v0.6（2026-11-09） | HEXACO 日本語版の出典などを追記予定 |
| oTree 実装 `a1-decision-study/` | v0.6 + 未リリースの変更 | HEXACO を若林（2014）日本語版に差し替え、同意文・終了画面の文言を修正（`CHANGELOG.md`）。変更後のボットテストは未実行 |
| Qualtrics 版 `qualtrics/` | r3 | ja.py の 2026-11-10 の変更は未反映。QSF の再生成（r4）と取り込みは未 |
| FAB 和訳 | `FAB_和訳作業シート.xlsx` | 訳案あり。バックトランスレーション未（0 / 15） |
| HEXACO-HH 日本語 | `HEXACO-HH_比較リスト.xlsx` | 若林（2014）を改変せずに使用。英語原文・逆転指定は hexaco.org と照合済み |

## フォルダー構成

```
23rd222_altruism/
├─ a1-decision-study/        oTree 実装（現行 v0.6）
│   ├─ altruism_study/       アプリ本体。texts/ja.py が文言の正本
│   ├─ analysis/             R の解析パイプライン（00_setup → 01_clean → 02_main → 04_figures、合成データ 99）
│   ├─ tools/                エクスポートの保存・CrowdWorks との照合・ペアリングなど
│   ├─ docs/                 OSF 資料との対応表、版間の比較、画面 PDF
│   └─ README.md             実装の詳しい説明と動かし方
├─ qualtrics/                Qualtrics 版（現行 r3）。make_qsf.py で QSF を生成
├─ original-dg-replica/      原研究の DG 部分を画面で再現した oTree プロジェクト（説明用）
├─ A-1_再現要素一覧.xlsx      原研究から再現する要素の一覧
├─ FAB_和訳作業シート.xlsx    FAB 15 項目・教示・手順・HEXACO-HH の和訳作業
├─ HEXACO-HH_比較リスト.xlsx  英語原文 × 直訳 × 若林版 × ja.py の対応
└─ docs/                     研究全体の資料
    ├─ 研究の決定事項と未決事項.md
    ├─ 質問紙_FABとHEXACO.md
    └─ materials/            HEXACO-60 日本語版の原本（hexaco.org 配布。再配布しない）
```

## 過去の版

`main` には最新版だけを置き、過去の版は Git のタグで残している。GitHub では **Tags**（または Releases）から各版のファイル一式を見たりダウンロードしたりできる。

| タグ | 日付 | 内容 |
| --- | --- | --- |
| `v0.4` | 2026-10-25 | oTree 実装 v0.4（HEXACO 採用、完了者のみ保存、Page Times） |
| `v0.5` | 2026-10-29 | 画面を 9 ページに、質問紙を FAB / HEXACO の 2 段階に |
| `qualtrics-r1` | 2026-11-05 | Qualtrics 版 r1（v0.5 を再現） |
| `qualtrics-r2` | 2026-11-06 | Qualtrics 版 r2（oTree 版との齟齬を解消） |
| `v0.6`（= `qualtrics-r3`） | 2026-11-09 | CrowdWorks 募集に対応（10 桁の実験 ID、参加資格） |

差分は `git diff v0.5 v0.6 -- a1-decision-study/` のように見られる。版を上げるときは、同じフォルダーを更新してコミットし、タグを付ける
（`CHANGELOG.md` にも書く）。

## 動かし方（oTree 版、Windows）

1. Python 3.10〜3.12（3.11 推奨。3.13 は不可）を用意する。
2. `a1-decision-study\run_dev.bat` をダブルクリック → デモ用リンクがブラウザで開く。
3. ボットテストは `run_tests.bat`、解析は `run_analysis.bat`（R が必要）。

詳しい手順とつまずきやすい点は `a1-decision-study/README.md` の「動かし方」。Qualtrics 版の QSF の生成:

```
cd qualtrics
python make_qsf.py --texts ../a1-decision-study/altruism_study/texts/ja.py --out A-1_v0.6r3_ja.qsf
```

オプションと取り込み手順は `qualtrics/README.md`。

## 作業のルール

- **文言の正本は `a1-decision-study/altruism_study/texts/ja.py`**。Qualtrics のビルダーでは文言を直さず、ja.py を直して QSF を作り直す。
- **HEXACO 正直さ-謙虚さの項目・選択肢は若林（2014）日本語版を改変しない**（新たに訳さない）。句読点「，」も原文のまま。
- **本番データはコミットしない**。oTree のエクスポートは `raw/`・`payout/`、Qualtrics の回答エクスポートや CrowdWorks の一覧は `private/` に置く（`.gitignore` 対象）。
  参加者の連絡先は集めない。Qualtrics・研究室アカウントの ID やパスワードもここに書かない。

## 出典

- Binder, Schultze, Chen & Windmann (2026). *Scientific Reports, 16*, 11600. 公開資料: https://osf.io/t5mf2/
- HEXACO-60: Ashton, M. C., & Lee, K. (2009). *Journal of Personality Assessment, 91*(4), 340–345.
- HEXACO-60 日本語版: Wakabayashi, A. (2014). *Japanese Psychological Research, 56*(3), 211–223. doi:10.1111/jpr.12045
  （hexaco.org 配布の `Japanese_self60.doc`。研究目的の無償利用、項目の改変不可）
