# original-dg-replica — 原研究（Binder et al., 2026）の独裁者ゲーム部分の再現

「元の研究ではこうだった」を画面で見せるための oTree プロジェクト。本追試（`../a1-decision-study`）と並べて説明する。
対応表は `docs/comparison_ja.md`、文言の出典は `docs/sources_ja.md`、画面は `docs/screens_original_*.pdf`。

原資料: https://osf.io/t5mf2/ — Studies/03 卒論付録 p.43–44（一般教示・DG 教示のドイツ語原文）、Studies/09 codebook（入力確認）、
Studies/11 codebook（事後評価・属性）、Study_overview.xlsx（研究ごとの条件）、論文 Methods。

## 何が再現されているか

- 画面の流れ: 同意 →（欺罔なしの研究のみ）「相手は架空です」の事前告知 → 一般教示 + ユーザー名入力 → 待機画面（最大 10 秒）
  → **Runde: Glück und Pech**（当選グループ、10.70 のプレゼント、全額保持か匿名の相手と分けるか、任意の額を入力）
  →（Study 09 のみ）入力は正しいか？ → 再入力 → 結果 → 事後評価 6 項目 → 属性 →（欺罔ありの研究のみ）デブリーフィング → 終了
- 文言: ドイツ語版は Study 03 の付録の原文をそのまま使用。英語版は原文からの訳（論文 Methods と照合）。日本語版は説明用の和訳。
- 変数名は原研究と同じ（`dg_give`, `dg_give_2`, `dg_correct`, `dg_total`, `dg_payout`, `username`, `eval_1`〜`eval_6`）。
- 相手は原研究と同じく架空。ペアリングも相手への支払いもない。

## セッション設定（settings.py）

| 設定名 | 原研究 | 言語 | 欺罔 | 報酬 | 入力確認 |
|---|---|---|---|---|---|
| `orig_study03_de` | Study 03（Rahels Study） | de | あり | なし（架空のお金） | なし |
| `orig_study09_en` | Study 09（Big US） | en | なし | 定額 $0.50 | **あり** |
| `orig_study11_en` | Study 11（MTurk Pilot） | en | なし | 定額 $1 | なし |
| `orig_study13_de` | Study 13（German w/o deception） | de | なし | 1:0.1 換算 | なし |
| `orig_study15_de` | Study 15（German with deception） | de | あり | 1:0.1 換算 | なし |
| `orig_ja_demo` | Study 09 の条件を和訳 | ja | なし | 定額 $0.50 | あり |

共通: `endowment` 10.70、`base_payout` 5.00、`conversion_rate` 0.1、`waiting_seconds` 6（原研究は最大 10 秒）、`post_evaluation` True。
oTree の定型文（「次へ」ボタンなど）の言語は環境変数 `OTREE_LANGUAGE_CODE`（既定 ja。独語で見せるなら `de`、英語なら `en`）。

## 動かし方

Windows は `run_dev.bat` をダブルクリック（`../a1-decision-study/run_dev.bat` と同じ仕組みで、OneDrive 外にコピーしてから
http://localhost:8020/demo を開く）。独語の定型文で見せたいときは `run_dev.bat 8020 de`。

手動:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:OTREE_ADMIN_PASSWORD = "admin"
$env:OTREE_LANGUAGE_CODE = "de"     # 省略時 ja
otree devserver 8020                # http://localhost:8020/demo → 設定を選ぶ
otree test orig_study09_en 4        # ボットテスト（4 ケース）
```

## 構成

```
settings.py                      SESSION_CONFIGS（原研究の研究ごとの条件）
original_dg/__init__.py          ページ・フィールド・報酬計算
original_dg/texts/de.py          ドイツ語（原文 verbatim + 再構成部分。SOURCE に出典）
original_dg/texts/en.py          英語（原文からの訳 + Study 11 codebook の verbatim 項目）
original_dg/texts/ja.py          日本語（説明用の和訳）
original_dg/*.html               画面テンプレート 11 種
original_dg/tests.py             ボットテスト 4 ケース（全設定で通る）
tools/browser_walk.py            Playwright で通し + スクリーンショット
docs/comparison_ja.md            原研究 vs 本追試の対応表（説明用）
docs/sources_ja.md               文言の出典（verbatim / translated / reconstructed）
docs/screens_original_de_study03.pdf   Study 03 の条件（独語原文）の全画面
docs/screens_original_en_study09.pdf   Study 09 の条件（英語）の全画面
docs/screens_original_ja_study09.pdf   同・和訳
```

## 注意

- 英語版の原画面は OSF に含まれていない。英語の DG 教示は独語原文からの訳で、論文 Methods の表現（winner, gift, another unknown participant）と照合した。
- 「相手は架空です」の事前告知と待機画面の文言は、論文の記述から再構成したもの（原文は未入手）。
- これは説明・比較用で、データ収集には使わない（相手が架空なので倫理審査の対象が変わる）。
