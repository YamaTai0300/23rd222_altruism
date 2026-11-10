# 質問紙: FAB（日本語訳案）と HEXACO 正直さ-謙虚さ（若林, 2014 日本語版）

A-1 追試（Binder et al., 2026 の追試）の質問紙 2 段階、FAB 15 項目 + 注意チェック 2 と HEXACO-60 正直さ-謙虚さ 10 項目の文言・出典・得点化をまとめる。
参加者に見せる文言の正本は `a1-decision-study/altruism_study/texts/ja.py`（英語原文は `texts/en.py`）。

## 1. 前提

- **公刊されている日本語版は HEXACO だけ**。FAB 尺度（Windmann, Binder & Schultze, 2021; Binder et al., 2026）には日本語版がないので、A-1 では研究室で和訳する（現状は訳案、バックトランスレーション未了）。
- HEXACO は若林（2014）の日本語版（hexaco.org 配布の `Japanese_self60.doc`）を **改変せずに使う**。新たに訳すことも、バックトランスレーションもしない。
- 英語原文 10 項目は hexaco.org の `English_self60.doc` と照合済みで、`texts/en.py` と一字一句一致。逆転項目の指定も `ScoringKeys_60.pdf` と一致
  （Sincerity 6, 30R, 54 / Fairness 12R, 36, 60R / Greed Avoidance 18, 42R / Modesty 24R, 48R）。

## 2. 書誌と使用条件

### HEXACO 日本語版
- Wakabayashi, A. (2014). A sixth personality domain that is independent of the Big Five domains: The psychometric properties of the HEXACO Personality Inventory in a Japanese sample. *Japanese Psychological Research, 56*(3), 211–223. https://doi.org/10.1111/jpr.12045
  - 日本人 492 名（平均年齢 20.4 歳）、うち 307 名は NEO-FFI・IPIP Big Five も回答。6 因子構造を確認し、正直さ-謙虚さ（H）は Big Five と弱〜中程度の重なりしかない独立の次元であると結論。
- 原版: Ashton, M. C., & Lee, K. (2009). The HEXACO-60: A short measure of the major dimensions of personality. *Journal of Personality Assessment, 91*(4), 340–345.
- 配布: hexaco.org の Downloads（https://hexaco.org/hexaco-inventory）に日本語版 60 項目（`Japanese_self60.doc`）と 100 項目（`Japanese_self100.doc`）。
  **研究目的の使用は無償**だが、項目の改変や形式の変更（観察者評定化など）は著者の承認が必要（https://hexaco.org/translations）。
  論文・卒論では Ashton & Lee (2009) と Wakabayashi (2014) の両方を引用する。原本の写しは `docs/materials/HEXACO60_Japanese_self60_hexaco.org.doc`（2026-11-10 取得。再配布しない）。
- 著作権表示（配布物のまま）: © Kibeom Lee, Ph.D., & Michael C. Ashton, Ph.D. / Translation: Akio Wakabayashi, Ph.D.

### FAB 尺度
- Windmann, S., Binder, L., & Schultze, M. (2021). Constructing the Facets of Altruistic Behaviors (FAB) scale. *Social Psychology, 52*(5), 299–313.
- Binder, L., Schultze, M., Chen, X., & Windmann, S. (2026). *Scientific Reports, 16*, 11600. 15 項目の確定文言（英・独）は OSF T5MF2 の Supplement S1。
- 日本語版: なし。A-1 用の和訳案（§4）を研究室で作り、バックトランスレーション後に確定する（作業は `FAB_和訳作業シート.xlsx`）。

## 3. HEXACO-60 正直さ-謙虚さ 10 項目（若林 2014 日本語版）

### 3.1 教示文と選択肢

日本語版の「回答の仕方」（配布物の原文）:

> 次のページから並んでいる項目の内容について，自分にどの程度あてはまっているかあてはまっていないかを考えて，以下の尺度の数字を使って各文の左側にある下線部に回答してください。
>
> 1 = あてはまらない（そうではない）
> 2 = どちらかといえば，あてはまらない
> 3 = どちらともいえない
> 4 = どちらかといえば，あてはまる
> 5 = あてはまる（そうである）
>
> なお，「３：どちらともいえない」は，できるだけ選択しないようにしてください。（どうしてもどちらとも決められない場合にのみ３に○を付けるようにしてください）

英語原版の DIRECTIONS（参考）: 各文を読み、どの程度同意するか／しないかを決める。5 = strongly agree / 4 = agree / 3 = neutral (neither agree nor disagree) / 2 = disagree / 1 = strongly disagree。確信がもてなくても、すべての文に答える。

`texts/ja.py` での扱い:
- `likert5`: 若林版の 5 語をそのまま使う。
- `hex_intro`: 若林版の 1 文目を画面用に整えた文（「各文の左側にある下線部に回答」→「5 段階から選んでお答えください」）。`hex_intro_short` はその要約。
- 「3 をできるだけ選ばない」注意書き: 英語原版にはない。**入れるかは未決**（入れれば若林版に忠実、外せば英語原版・FAB と条件がそろう）。`ja.py` ではコメントアウトして保持し、既定では表示しない。決めたら計画書の「原研究からの変更点」に記録する。
- 配布物にある授業用の文言（「出席点として加算します」、年齢・性別の記入欄）は尺度の一部ではないので使わない。

### 3.2 項目（提示はランダム順。変数名は `texts/ja.py`・`analysis/codebook.csv` のもの）

| 変数名 | HEXACO-60 番号 | 下位側面 | 逆転 | 日本語（若林 2014、原文どおり） | 英語原文（hexaco.org 照合済み） |
|---|---|---|---|---|---|
| hex_1 | 6 | Sincerity（誠実さ） | – | たとえそうすればうまくいくと思っても，仕事の上で昇進するためにお世辞を言ったりしようとは思わない。 | I wouldn't use flattery to get a raise or promotion at work, even if I thought it would succeed. |
| hex_2 | 12 | Fairness（公正さ） | R | もし決して捕まらないとわかっているのなら，私は1億円を盗もうと思う。 | If I knew that I could never get caught, I would be willing to steal a million dollars. |
| hex_3 | 18 | Greed Avoidance（強欲の回避） | – | 大金を持つことは，自分にとって特に重要なことではない。 | Having a lot of money is not especially important to me. |
| hex_4 | 24 | Modesty（謙虚さ） | R | 私は，平均的な人間よりも，尊重される権利があると思う。 | I think that I am entitled to more respect than the average person is. |
| hex_5 | 30 | Sincerity（誠実さ） | R | もし，何かをある人から手に入れようと思っているときには，その人がくだらない冗談を言っても笑うだろう。 | If I want something from someone, I will laugh at that person's worst jokes. |
| hex_6 | 36 | Fairness（公正さ） | – | たとえどんなに大金でも，賄賂は決して受け取らない。 | I would never accept a bribe, even if it were very large. |
| hex_7 | 42 | Greed Avoidance（強欲の回避） | R | 高価で贅沢なものを所有することで，多くの楽しみが得られる。 | I would get a lot of pleasure from owning expensive luxury goods. |
| hex_8 | 48 | Modesty（謙虚さ） | R | 私が高い地位にいる重要な人間であることを他の人に知ってほしい。 | I want people to know that I am an important person of high status. |
| hex_9 | 54 | Sincerity（誠実さ） | – | 誰かに私のたのみを聞いてもらうために，その人を好きなふりをしようとは思わない。 | I wouldn't pretend to like someone just to get that person to do favors for me. |
| hex_10 | 60 | Fairness（公正さ） | R | もし絶対に捕まらないなら，偽札を使ってみたい。 | I'd be tempted to use counterfeit money, if I were sure I could get away with it. |

- 句読点は配布物どおり全角カンマ「，」。画面表示で「、」に統一するなら全項目をそろえ、文言の改変ではなく「表記の統一」として記録する。
- 得点化: 逆転項目（hex_2, 4, 5, 7, 8, 10）を 6 − x で反転し、10 項目の平均を `hh_mean`（1〜5）とする。`analysis/01_clean.R` は codebook の min / max から `(min + max) − x` で逆転する。

### 3.3 英語原文との対応で気づいた点（公刊版なので直さない。読み合わせ用）
- 項目 6: 「a raise or promotion」→「昇進」のみ。
- 項目 12: 「a million dollars」→「1 億円」（ローカライズ。計画書の「原研究からの変更点」に記録する）。
- 項目 54: 「just（〜ためだけに）」は訳出なし。
- 項目 60: 「be tempted to」→「使ってみたい」。
- 選択肢は「あてはまる／あてはまらない」系で、FAB の 6 件法「そう思う／そう思わない」系と語感が違う。そのため 2 つの尺度を別段階・別ページにし、段階の冒頭で件法を明示する。

## 4. FAB 尺度（A-1 和訳案。Binder et al. 2026 Supplement S1 に基づく）

状態: 15 項目・教示・選択肢・注意チェックはすべて訳案あり、確定 0 / 15。バックトランスレーションは `FAB_和訳作業シート.xlsx` の手順で研究室が行う。

### 4.1 教示文と選択肢
- 原文: "Please state honestly and spontaneously how you would typically behave or act."
- 和訳案（各ページの上部にも短縮版）: 「以下の文は、日常生活でのふるまいや行動に関するものです。それぞれの文について、あなたが普段どのようにふるまい、行動するかを、正直に、直感的にお答えください。回答は 6 段階です。正解や不正解はありません。」
- 6 件法（原研究: 1 = strongly disagree … 6 = strongly agree、独語 trifft überhaupt nicht zu … trifft vollkommen zu）:
  1 全くそう思わない ／ 2 そう思わない ／ 3 あまりそう思わない ／ 4 ややそう思う ／ 5 そう思う ／ 6 強くそう思う
- 逆転項目なし（15 項目すべて正方向）。項目は常にランダム順。下位尺度は各 5 項目の平均。主仮説に使うのは Help Giving。

### 4.2 項目（変数名は原研究の整形済みデータと同じ）

| 変数名 | 下位尺度 | 和訳案 | 原文（英語・S1） |
|---|---|---|---|
| hg_1 | Help Giving | 迷ったときは、私は強い側よりも弱い側に味方する。 | When unsure, I rather stand with the weak than the strong. |
| hg_3 | Help Giving | 飢えや病気に苦しむ人を助けるためなら、私は自分の生活や健康を犠牲にしてもかまわない。 | I would jeopardize my own well-being in order to help the sick and hungry. |
| hg_7 | Help Giving | 緊急事態では、私はおそらくとっさに自分の命を危険にさらしてでも、見ず知らずの人を助けるだろう。 | In an emergency I would probably spontaneously risk my own life to save complete strangers. |
| hg_10 | Help Giving | 自分に負担がかかるとしても、私は知り合いかどうかに関係なく人を支援する。 | Despite potential costs I might incur, I support people whether or not I know them personally. |
| hg_13 | Help Giving | 私は、見返りや下心なしに、他の人のためによいことをすることがよくある。 | I often do good things for others without reservation or expectations. |
| pp_1 | Peer Punishment | 誰かが自分だけ特別扱いを要求したら、私はその人を止めるために協力してくれる仲間を探す。 | When someone demands special privileges for themselves, I look for others with whom I can try to stop them. |
| pp_8 | Peer Punishment | 誰かがわざとみんな（共同体）を利用したら、私は何らかの形でこっそり仕返しをする。 | When someone purposely takes advantage of the community, I discretely get back at them in one way or another. |
| pp_12 | Peer Punishment | 私は、チームの中で誰かが不適切なふるまいをしていないか、注意深く見ている。 | I pay close attention to whether someone misbehaves in a team. |
| pp_14 | Peer Punishment | 誰かが他のみんなを犠牲にして得をしているなら、私はその人がうまくいかないように、人知れず働きかける。 | If someone benefits at the expense of everyone else, I secretly try to ensure that they don't succeed. |
| pp_15 | Peer Punishment | ルールを自分に都合よく解釈する人は、遅かれ早かれ私と仲間によって責任を取らされることになる。 | Those who construe the rules to their advantage will sooner or later be held accountable by my friends and me. |
| mc_1 | Moral Courage | 私は、権威のある人や上司の決定に、公然と疑問を投げかける。 | I openly question the decisions of authorities or superiors. |
| mc_3 | Moral Courage | 私は、自分の道徳的な信念のために、人の気分を害したことがある。 | It has happened that I have affronted others due to my moral convictions. |
| mc_18 | Moral Courage | 私は、世間が反対していても、みんなにとって重要な方針を貫こうとする。 | I try to carry through with policies that are important for everyone, even if the general public disagrees with them. |
| mc_20 | Moral Courage | 私は、たとえ得るものより失うものが大きくても、「上」からの不当な指示には抵抗する。 | I fight against unjust instructions from authorities, even if it costs me more than it benefits me. |
| mc_23 | Moral Courage | 争いが起きたら、私は加害者に立ち向かう。 | In a conflict, I confront the attacker. |

### 4.3 注意チェック（FAB 項目に混ぜて提示。原研究の control question）
- cq1（正答 = 選択肢 1）: 「この質問では、「全くそう思わない」を選んでください。これは確認のための質問です。」
- cq2（正答 = 選択肢 6）: 「この質問では、「強くそう思う」を選んでください。これは確認のための質問です。」
- 指定する語は選択肢 1・6 の訳と一字一句同じにする（選択肢の訳を変えたら連動して直す）。

## 5. 質問紙としての組み立て

| | FAB | HEXACO 正直さ-謙虚さ |
|---|---|---|
| 項目数 | 15 + 注意チェック 2 | 10 |
| 件法 | 6 件法（そう思わない〜そう思う） | 5 件法（あてはまらない〜あてはまる、若林版） |
| 教示 | 「普段どうふるまうか」を正直に・直感的に | 「自分にどの程度あてはまるか」 |
| 提示 | 2 ページ、ランダム順 | 1 ページ、ランダム順 |
| 逆転 | なし | 6 項目（6 − x） |
| 段階の順序 | `scale_order` で FAB→HEXACO / HEXACO→FAB をランダム化 | 同左 |
| 役割 | 主仮説 H1（Help Giving × DG） | 探索 H5（比較基準） |

## 6. 状態（2026-11-11）

| 項目 | 状態 |
| --- | --- |
| HEXACO の `texts/ja.py` への転記 | 済み（2026-11-10）。変更後のボットテストは未実行 |
| HEXACO の Qualtrics 版への反映 | 未（QSF の再生成 r4 が必要） |
| HEXACO の「3 を選ばない」注意書き | 未決 |
| `FAB_和訳作業シート.xlsx` の HEXACO-HH シート | 若林版の転記は未（対応は `HEXACO-HH_比較リスト.xlsx` にある） |
| FAB のバックトランスレーション | 未（確定 0 / 15） |
| 計画書の「材料」「原研究からの変更点」への記載 | 未（出典、選択肢の語、注意書きの扱い、「1 億円」） |

## 出典
- hexaco.org Downloads: `Japanese_self60.doc`（Translation: Akio Wakabayashi）、`English_self60.doc`、`ScoringKeys_60.pdf`（https://hexaco.org/hexaco-inventory から取得、2026-11-10）
- hexaco.org Translations（翻訳の承認・使用条件）: https://hexaco.org/translations
- FAB: OSF T5MF2 Supplement S1（https://osf.io/t5mf2/）
