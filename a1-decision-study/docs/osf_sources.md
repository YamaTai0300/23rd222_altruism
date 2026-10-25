# OSF T5MF2 から取得した原資料（2026-10-18）

## FAB 教示文（英語、Study 11 codebook の QUESTION 列）
"Please state honestly and spontaneously how you would typically behave or act."
回答: 1 strongly disagree / 2 disagree / 3 rather disagree / 4 rather agree / 5 agree / 6 strongly agree
ドイツ語: 1 trifft überhaupt nicht zu / 2 trifft nicht zu / 3 trifft eher nicht zu / 4 trifft eher zu / 5 trifft zu / 6 trifft vollkommen zu

## 注意チェック（control question）
EN (Study 09/11, cq1/cq2):
- 'Please tick the option "strongly disagree" for this question. This is a control question.'
- 'Please tick the option "strongly agree" for this question. This is a control question.'
DE (Study 03 thesis p.14):
- „Bei dieser Frage kreuzen Sie bitte einfach die Option ‚trifft vollkommen zu' an. Es handelt sich um eine Kontrollfrage."
- „Bei dieser Frage kreuzen Sie bitte einfach die Option ‚trifft überhaupt nicht zu' an. Es handelt sich um eine Kontrollfrage."
→ FAB 項目に混ぜて提示（Study 11 では FAB 15 + cq1 + forgiveness 等が同じスケールブロック）

## ボット識別質問（Study 11, AG10_01）
"What do you see inside the house on the picture?"（自由記述、画像つき）→ water|can|mug|jug|kettle|pot|pitcher|sprinkler|shower|cup を含まない回答は除外

## 除外基準（09/11 preprocessing.R）
1. 所要時間 TIME_SUM < 0.25 × 中央値 → 除外
2. 注意チェック 2 問のいずれか不正解 → 除外（事前登録どおり）
3. 18 歳未満 → 除外；英語 fluent 未満（engl < 4）→ 除外
4. ボット質問の回答が非現実的 → 除外
5. (11) 罰に $20 超を使おうとした → 除外
6. (09) 自由記述が 2 名のコーダーにボット判定 → 除外；TPI メッセージが賛同的 → 除外
除外はリストワイズ。

## DG 変数（SoSci）
- dg_give: "Abgabe: $"（自由入力の数値、0〜10.70、任意の額）
- dg_total, dg_payout（計算値）
- Study 09: dg_correct "Korrekte Eingabe?" Yes/No → No なら dg_give_2 で再入力（前処理で dg_give を置換）
- 原研究の DG は「刻みなし（0〜10.70 の任意額を入力）」

## DG 教示（Study 03 卒論 付録 p.44、ドイツ語原文）
Runde: Glück und Pech
Sie haben Glück! Sie sind in unsere Gewinn-Gruppe geraten. Sie sind in dieser Runde ein*e Gewinner*in.
Die derzeit zur Verfügung stehende Summe beträgt 10,70 Euro. Wir schenken Ihnen diesen Betrag.
Sie haben nun folgende Möglichkeiten:
1. Sie können 10,70 Euro behalten.
2. Sie können das Geld mit einer anderen teilnehmenden Person dieser Studie teilen, die nicht in unsere Gewinn-Gruppe geraten ist und kein Geldgeschenk erhalten hat. Diese Person bleibt für Sie anonym und auch Sie bleiben für die Person anonym.
Wieviel von den 10,70 Euro geben Sie an eine Person in der Pech-Gruppe ab? ___ Euro

## 一般教示（Study 03 p.43）
- 複数の意思決定場面に参加、他の参加者とはユーザー名のみで相互作用
- 役割（Gewinner*in, Verlierer*in, Diktator*in, Gutachter*in, Investor*in, Richter*in）はランダムに配分
- 基本支払い 5 ユーロ、最後に 1 場面をランダムに選んで精算
- 「自分の身元が分からないユーザー名を入力してください」

## カバーストーリー
「参加者間の経済行動の研究」(Untersuchung wirtschaftlichen Verhaltens unter Teilnehmenden)、デブリーフィング時の研究名「FABS und Persönlichkeit」

## ゲーム後の評価項目（Study 11, AG11_01〜06、6 件法）
- Completing this survey took too long.
- It was difficult to make decisions in the interactive situations.
- Interactions with other fictional participants felt unrealistic.
- My decisions in these online situations reflect my decisions in real-life interaction.
- Overall, these interactive situations were easy to understand.
- I was distracted while participating.
+ 自由記述 2 問（Evaluation 2, 3）

## 人口統計（Study 11）
- What best describes your gender? female / male / prefer to self-describe: ___
- How old are you? I am ___ years old.
- What is your highest professional qualification?（13 択）
- How would you describe your English language skills? Beginner/Intermediate/Proficient/Fluent/Native

## 変数名（整形済み data.csv）
hg_1 hg_3 hg_7 hg_10 hg_13 / pp_1 pp_8 pp_12 pp_14 pp_15 / mc_1 mc_3 mc_18 mc_20 mc_23 / cq1 cq2 / dg_give / gender (f/m/nb) / age / edu / engl / TIME_SUM / tp_decision (0/1) / sp_pun sp_costs / ug_mao
