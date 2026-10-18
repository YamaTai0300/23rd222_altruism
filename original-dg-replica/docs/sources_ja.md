# 文言と手続きの出典（OSF T5MF2）

各画面の文言がどこから来たかの一覧。`verbatim` = 原文そのまま（ドイツ語）、`translated` = 原文からの訳、`reconstructed` = 論文や codebook の記述から再構成（原文の画面は OSF に含まれていない）。
英語版の原画面（SoSci Survey）は OSF に収録されていないため、英語版は独語原文の訳＋論文 Methods との照合。

| 画面 / 文言 | de | en | ja | 出典 |
|---|---|---|---|---|
| カバーストーリー（「経済行動の研究」） | reconstructed | reconstructed | translated | Studies/03/03_thesis_blinded.pdf p.13「Untersuchung wirtschaftlichen Verhaltens unter Teilnehmenden」 |
| 同意・「実際のお金ではない」の確認 | reconstructed | reconstructed | translated | 同 p.14（Study 03 は架空のお金であることを確認させた） |
| 事前告知「相手は架空」 | reconstructed | reconstructed | translated | 論文 Methods: "disclosed beforehand and were asked to act as if there were other real participants involved" |
| 一般教示（役割、最大 10 秒待つ、基本支払い 5 ユーロ、1 場面を精算） | **verbatim** | translated | translated | 同 付録 p.43「Allgemeine Instruktionen」 |
| ユーザー名の入力 | **verbatim** | translated | translated | 同 p.43 末尾 |
| 待機画面 | reconstructed | reconstructed | translated | 一般教示の「maximal 10 Sekunden warten」と論文の "brief pauses simulated other players contemplating" |
| Runde: Glück und Pech（DG 教示・選択肢・質問） | **verbatim** | translated（論文 Methods と照合） | translated | 同 付録 p.44「Instruktionen Dictator Game」 |
| 金額の入力（0〜10.70 の任意額） | — | — | — | 同 p.16「jeden möglichen Betrag zwischen 0 und 10,70 Euro」、Studies/09 codebook `dg_give`（自由入力） |
| 入力は正しいか？（dg_correct） | reconstructed | reconstructed | translated | Studies/09/09_codebook_raw.xlsx `dg_correct`「Korrekte Eingabe?」Yes/No、`dg_give_2`；09_preprocessing.R で No のとき置換 |
| 結果（dg_total, dg_payout） | reconstructed | reconstructed | translated | codebook `dg_total`「Gewinn total」、`dg_payout`「Auszahlung」 |
| 報酬方式 | — | — | — | Study_overview.xlsx「Games only」: 03 なし、09 $0.50 定額、11 $1 定額、12/13/15 1:0.1 換算 |
| 事後評価 6 項目 | translated | **verbatim** | translated | Studies/11/11_codebook_raw.csv AG11_01〜06 |
| 属性（性別・年齢・学歴） | translated | **verbatim** | translated | 同 codebook（gender, age, quali） |
| デブリーフィング | **verbatim（抜粋）** | translated | translated | 同 付録 p.49「Aufklärung」 |

## 原文（ドイツ語、Study 03 付録 p.44）

> Runde: Glück und Pech
> Sie haben Glück! Sie sind in unsere Gewinn-Gruppe geraten. Sie sind in dieser Runde ein*e Gewinner*in.
> Die derzeit zur Verfügung stehende Summe beträgt 10,70 Euro. Wir schenken Ihnen diesen Betrag.
> Sie haben nun folgende Möglichkeiten:
> 1. Sie können 10,70 Euro behalten.
> 2. Sie können das Geld mit einer anderen teilnehmenden Person dieser Studie teilen, die nicht in unsere Gewinn-Gruppe geraten ist und kein Geldgeschenk erhalten hat. Diese Person bleibt für Sie anonym und auch Sie bleiben für die Person anonym.
> Wieviel von den 10,70 Euro geben Sie an eine Person in der Pech-Gruppe ab? ____ Euro

## 原研究 6 研究の DG 条件（Study_overview.xlsx より）

| Study | 言語 | 欺罔 | 報酬 | 間隔 | 入力確認 | N |
|---|---|---|---|---|---|---|
| 03 (A) | DE | あり | なし（架空のお金） | 2 週間 | — | 68 |
| 09 (B) | EN | なし | ゲームごと $0.50 定額 | なし | あり | 806 |
| 11 (C) | EN | なし | ゲームごと $1 定額 | なし | — | 226 |
| 12 (D) | EN | なし | 1 決定を 1:0.1 換算 | 2 週間 | — | 268 |
| 13 (E) | DE | なし | 同上 | 2 週間 | — | 294 |
| 15 (F) | DE | あり | 同上 | 順序ランダム + 2 週間 | — | 181 |
