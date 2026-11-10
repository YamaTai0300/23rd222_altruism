#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A-1 追試 v0.6 の実験を Qualtrics で再現する QSF（調査定義ファイル）を生成する（r3, 2026-11-09）。

使い方: python make_qsf.py --texts <a1-decision-study>/altruism_study/texts/ja.py --out A-1_v0.6r3_ja.qsf

r3（2026-11-09、計画書 v0.6 = CrowdWorks 募集）での変更
- ★ 実験 ID: Survey Flow の先頭で埋め込みデータ exp_id に 10 桁の乱数（${rand://int/1000000000:9999999999}）を入れ、終了ページ／終了メッセージには
  ResponseID ではなく exp_id を表示する。参加者はこれを CrowdWorks の作業ページに入力し、tools/match_cw_ids.py（v0.6）で承認待ち一覧と照合する。
  ResponseID はこれまでどおりエクスポートに残る（変換で participant.label に入る）
- ★ 参加資格のチェックが「18 歳以上で、日本語が母語」になる（texts/ja.py v0.6 から読む）。終了文も「CW のフォームに入力」に変わる
- ★ 未完了回答の記録（--partial）の既定を +4 hours にした（研究室マニュアル: 締切から 4 時間待って確定）
- 多重回答防止（BallotBoxStuffingPrevention）は r2 から ON。CW 側の「重複を認めない」と合わせて二重の対策になる

取り込み: Qualtrics の Projects → Create project → Survey → "Import a QSF file"（新規プロジェクトになる）

文言の正本は oTree 版の altruism_study/texts/ja.py。参加者に見せる文言はすべてそこから読み、Qualtrics のビルダーでは直さない
（ビルダーで直した内容は QSF の作り直しで消える）。Qualtrics 版にしかない画面要素の文言だけ、下の QTEXT に置く。

oTree 版（v0.5）との対応（r2 で合わせた点に ★）
- 画面: 同意 → 質問紙 1/2（FAB + 注意チェック、2 ページ）→ 質問紙 2/2（HEXACO、1 ページ）→ DG 説明 → 理解確認（不正解なら 1 回だけ再回答）
  → 決定 → 事後評価 → 終了（実験 ID = 埋め込みデータ exp_id。r2 までは ResponseID）。順序群 2 は DG が先
- ★ 段階番号: 見出し「質問紙 1/2」「2/2」は埋め込みデータ fab_stage / hex_stage から埋める（scale_order 2 では HEXACO が 1/2）
- ★ 進捗: Qualtrics の進捗バーは切り、oTree 版と同じ「ページ k / 9」を各ページの先頭に出す（k は埋め込みデータ p_* で順序群ごとに設定）
- ★ FAB の項目順: 1 ブロックで 15 項目を Advanced Randomization、注意チェック cq1 / cq2 は固定位置（1 ページ目の 5 番目、2 ページ目の 4 番目）、
  Questions per Page でページを分ける（1 ページ目 9 項目、2 ページ目 8 項目。oTree 版の 17 項目一体シャッフル・9 + 8 分割に相当）
- ランダム化: Survey Flow の Randomizer（Evenly present）を 2 段に重ね、task_order（質問紙↔DG）と scale_order（FAB↔HEXACO）を
  Embedded Data に記録。oTree 版の 4 人ずつのブロック化・乱数シードは Qualtrics では再現できない（計画書に既知の差として書く）
- 検証: 必須（Force response）、理解確認・決定は 0〜1000 の整数（Content validation）
- ★ 記録: 変数名 = codebook と同じ（hg_1 … mc_23, cq1, cq2, hex_1 … hex_10, dg_check_answer1 / dg_check_answer2, dg_give, eval_*, comment_open、
  埋め込みデータ cfg_endowment, cfg_fee, cfg_dg_step, cfg_use_hexaco, lang, app_version, qsf_hash）。項目順は Qualtrics のエクスポート
  オプション「Export viewing order data for randomized surveys」で取れる。oTree 形式への変換は qualtrics_to_otree.py
- ★ 終了: 終了ページには実験 ID（埋め込みデータ exp_id、r3）を出す。--eos-message MS_xxx を渡すと終了ページをブロックではなく End of Survey のカスタムメッセージにする（到達した時点で回答が完了になる。
  メッセージは Library に手で 1 回作る。本文は eos_message.html に出力）。渡さないときは終了ブロックのまま、「次へ」で送信するよう促す文を出す
- ★ Survey Options: 多重回答防止 ON（--allow-multiple で OFF）、匿名化 ON（--keep-ip で OFF）、未完了回答の扱いは --partial（既定 +1 week）
- 時間（--full、有料ライセンス向け）: 各ページに Timing 質問（t_<page>: First Click / Last Click / Page Submit / Click Count）
- --meta: 同意ページに Meta Info 質問（ブラウザ・OS・画面解像度・User Agent）を入れる。無料アカウントで取り込めるかは未確認（403 なら外す）
- 元手 1,000 円・理解確認の正答 700 はこのスクリプトの定数（ENDOWMENT, CHECK_GIVE）
- Qualtrics の無料アカウント（2026-11 に取り込みで確認）では Timing 質問と質問の JavaScript が使えない（403）。既定はその 2 つを入れない
- SurveyBrandID は空だと取り込みで拒否される（--brand で指定。URL の <brand>.<dc>.qualtrics.com の <brand>）
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re

ENDOWMENT = 1000
CHECK_GIVE = 300
FEE = 300
DG_STEP = 1
CURRENCY = '円'
LANG = 'ja'
APP_VERSION = 'v0.6r3-qualtrics'
TOTAL_PAGES = 9
SURVEY_ID = 'SV_egt7X9VgLDhmk8C'   # 取り込み時には新しい ID が振られる（r1: SV_6PfFg1rhsV2G2uG「study_v5」、r2: SV_cSIPHEGOiULgN82「study_v6」2026-11-06、r3: 未取り込み）
BRAND_ID = 'qualtricsxmw5hysnkpn'   # 空だと ESDEF10 で拒否される
OWNER_ID = 'UR_1QAwVwSMYMfW9nn'
SURVEY_NAME = 'A-1 意思決定と日常行動に関する調査（v0.6r3 Qualtrics）'

HG = ['hg_1', 'hg_3', 'hg_7', 'hg_10', 'hg_13']
PP = ['pp_1', 'pp_8', 'pp_12', 'pp_14', 'pp_15']
MC = ['mc_1', 'mc_3', 'mc_18', 'mc_20', 'mc_23']
FAB = HG + PP + MC
HEX = [f'hex_{i}' for i in range(1, 11)]
EVAL = ['eval_understand', 'eval_difficult', 'eval_reflect', 'eval_distract']

# Qualtrics 版にしかない画面要素の文言（oTree 版には対応する要素がない）。参加者向けの文言の正本は texts/ja.py
QTEXT = dict(
    number_note='半角数字（{currency}）',
    # 無料版は JavaScript で取り分を即時表示できないので、代わりに 1 文で補う
    decision_note_static='入力した額が相手の受け取る額、{endowment} {currency} から引いた残りがあなたの取り分になります。',
    # 終了ページをブロックで出すとき（--eos-message なし）: 「次へ」を押すまで回答が完了にならないことを伝える
    end_submit='実験 ID を控えたら「次へ」を押して回答を送信してください。送信されるまで回答は完了になりません。',
)


class _Keep(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def fill(value, **kw):
    if isinstance(value, str):
        return value.format_map(_Keep(kw))
    if isinstance(value, dict):
        return {k: fill(v, **kw) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, **kw) for v in value]
    return value


def load_texts(path):
    spec = importlib.util.spec_from_file_location('ja_texts', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    kw = dict(endowment=f'{ENDOWMENT:,}', currency=CURRENCY, fee=f'{FEE:,}', check_amount=f'{CHECK_GIVE:,}', step=str(DG_STEP))
    return fill(mod.TEXT, **kw), fill(QTEXT, **kw)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def olist(items):
    """Qualtrics のテーマでは <ol> の番号が表示されないことがあるので、番号を文字で入れる。"""
    return '<ol>' + ''.join(f'<li>{i + 1}. {esc(o)}</li>' for i, o in enumerate(items)) + '</ol>'


def paras(lines, cls=''):
    attr = f' class="{cls}"' if cls else ''
    return ''.join(f'<p{attr}>{esc(p)}</p>' for p in lines)


def ed_ref(field):
    """埋め込みデータのパイプテキスト。"""
    return '${e://Field/' + field + '}'


# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, T, Q, full=False, meta=False):
        self.T = T
        self.Q = Q
        self.full = full
        self.meta = meta
        self.qid = 0
        self.flow_id = 0
        self.questions = []   # SQ elements
        self.blocks = []      # BL payload entries
        self.block_ids = {}

    def next_qid(self):
        self.qid += 1
        return f'QID{self.qid}'

    def next_fl(self):
        self.flow_id += 1
        return f'FL_{self.flow_id}'

    # ---- 共通の部品 --------------------------------------------------------
    def progress(self, page):
        """oTree 版の「ページ k / n」。page は数値か埋め込みデータ名（p_fab1 など）。"""
        k = str(page) if isinstance(page, int) else ed_ref(page)
        return '<p><small>' + esc(fill(self.T['progress_label'], page=k, pages=str(TOTAL_PAGES))) + '</small></p>'

    def stage_title(self, kind):
        """「質問紙 1/2」。段階番号は埋め込みデータ fab_stage / hex_stage（scale_order で変わる）。"""
        return esc(fill(self.T['survey_stage_title'], stage=ed_ref(f'{kind}_stage'), stages='2'))

    # ---- questions -------------------------------------------------------
    def add_question(self, payload, secondary):
        qid = self.next_qid()
        payload = dict(payload)
        payload['QuestionID'] = qid
        payload.setdefault('Language', [])
        self.questions.append({
            'SurveyID': SURVEY_ID, 'Element': 'SQ', 'PrimaryAttribute': qid,
            'SecondaryAttribute': secondary[:100], 'TertiaryAttribute': None, 'Payload': payload,
        })
        return qid

    def text(self, tag, html):
        return self.add_question({
            'QuestionText': html, 'DefaultChoices': False, 'DataExportTag': tag,
            'QuestionType': 'DB', 'Selector': 'TB', 'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText'}, 'QuestionDescription': re.sub('<[^>]+>', '', html)[:100],
            'ChoiceOrder': [], 'Validation': {'Settings': {'Type': 'None'}}, 'NextChoiceId': 4, 'NextAnswerId': 1,
        }, re.sub('<[^>]+>', '', html)[:60])

    def timing(self, tag):
        if not self.full:
            return None
        return self.add_question({
            'QuestionText': 'Timing', 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'Timing',
            'Selector': 'PageTimer', 'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText', 'MinSeconds': '0', 'MaxSeconds': '0'},
            'QuestionDescription': 'Timing',
            'Choices': {'1': {'Display': 'First Click'}, '2': {'Display': 'Last Click'}, '3': {'Display': 'Page Submit'}, '4': {'Display': 'Click Count'}},
            'ChoiceOrder': ['1', '2', '3', '4'], 'Validation': {'Settings': {'Type': 'None'}}, 'NextChoiceId': 5, 'NextAnswerId': 1,
        }, f'Timing {tag}')

    def meta_info(self, tag='meta'):
        """ブラウザ・OS・画面解像度・User Agent（oTree 版の user_agent / screen_width に相当）。参加者には見えない。"""
        if not self.meta:
            return None
        labels = ['Browser', 'Version', 'Operating System', 'Screen Resolution', 'Flash Version', 'JavaScript Support', 'User Agent']
        return self.add_question({
            'QuestionText': 'Browser Meta Info', 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'Meta',
            'Selector': 'Browser', 'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText'}, 'QuestionDescription': 'Browser Meta Info',
            'Choices': {str(i + 1): {'Display': l} for i, l in enumerate(labels)},
            'ChoiceOrder': [str(i + 1) for i in range(len(labels))],
            'Validation': {'Settings': {'Type': 'None'}}, 'NextChoiceId': len(labels) + 1, 'NextAnswerId': 1,
        }, 'Browser Meta Info')

    def likert(self, tag, text, labels):
        n = len(labels)
        choices = {str(i + 1): {'Display': f'{i + 1}. {lbl}'} for i, lbl in enumerate(labels)}
        return self.add_question({
            'QuestionText': esc(text), 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'MC', 'Selector': 'SAVR',
            'SubSelector': 'TX', 'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText'}, 'QuestionDescription': text[:100],
            'Choices': choices, 'ChoiceOrder': [str(i + 1) for i in range(n)],
            'Validation': {'Settings': {'ForceResponse': 'ON', 'ForceResponseType': 'ON', 'Type': 'None'}},
            'RecodeValues': {str(i + 1): str(i + 1) for i in range(n)}, 'VariableNaming': {str(i + 1): lbl for i, lbl in enumerate(labels)},
            'NextChoiceId': n + 1, 'NextAnswerId': 1,
        }, text[:60])

    def checkboxes(self, tag, text, labels, min_choices):
        n = len(labels)
        return self.add_question({
            'QuestionText': text, 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'MC', 'Selector': 'MAVR',
            'SubSelector': 'TX', 'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText'}, 'QuestionDescription': re.sub('<[^>]+>', '', text)[:100],
            'Choices': {str(i + 1): {'Display': esc(lbl)} for i, lbl in enumerate(labels)}, 'ChoiceOrder': [str(i + 1) for i in range(n)],
            'Validation': {'Settings': {'ForceResponse': 'ON', 'ForceResponseType': 'ON', 'Type': 'MinChoices', 'MinChoices': str(min_choices)}},
            'RecodeValues': {str(i + 1): '1' for i in range(n)}, 'NextChoiceId': n + 1, 'NextAnswerId': 1,
        }, re.sub('<[^>]+>', '', text)[:60])

    def number(self, tag, html, lo, hi, js=None):
        p = {
            'QuestionText': html, 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'TE', 'Selector': 'SL',
            'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText', 'InputWidth': 120, 'InputHeight': 1},
            'QuestionDescription': re.sub('<[^>]+>', '', html)[:100], 'ChoiceOrder': [],
            'Validation': {'Settings': {'ForceResponse': 'ON', 'ForceResponseType': 'ON', 'Type': 'ContentType', 'ContentType': 'ValidNumber',
                                        'ValidNumber': {'Min': str(lo), 'Max': str(hi), 'NumDecimals': '0'}}},
            'SearchSource': {'AllowFreeResponse': 'false'}, 'NextChoiceId': 4, 'NextAnswerId': 1,
        }
        if js and self.full:
            p['QuestionJS'] = js
        if js and not self.full:
            p['QuestionText'] += paras([self.Q['decision_note_static']], 'small')
        return self.add_question(p, re.sub('<[^>]+>', '', html)[:60])

    def essay(self, tag, html):
        return self.add_question({
            'QuestionText': html, 'DefaultChoices': False, 'DataExportTag': tag, 'QuestionType': 'TE', 'Selector': 'ML',
            'DataVisibility': {'Private': False, 'Hidden': False},
            'Configuration': {'QuestionDescriptionOption': 'UseText', 'InputWidth': 300, 'InputHeight': 3},
            'QuestionDescription': re.sub('<[^>]+>', '', html)[:100], 'ChoiceOrder': [],
            'Validation': {'Settings': {'ForceResponse': 'OFF', 'ForceResponseType': 'ON', 'Type': 'None'}},
            'SearchSource': {'AllowFreeResponse': 'false'}, 'NextChoiceId': 4, 'NextAnswerId': 1,
        }, re.sub('<[^>]+>', '', html)[:60])

    # ---- blocks ----------------------------------------------------------
    def block(self, key, description, qids, fixed_order=None, randomize=None, per_page=None):
        bid = f'BL_{key}'
        qids = [q for q in qids if q]              # Timing / Meta を入れない版では None が混じる
        elems = [{'Type': 'Question', 'QuestionID': q} for q in qids]
        opts = {'BlockLocking': 'false', 'RandomizeQuestions': 'false', 'BlockVisibility': 'Collapsed'}
        if randomize:
            fixed_order = [q for q in fixed_order if q]
            opts = {
                'BlockLocking': 'false', 'RandomizeQuestions': 'Advanced',
                'Randomization': {'Advanced': {'FixedOrder': fixed_order, 'RandomizeAll': randomize, 'RandomSubSet': [], 'Undisplayed': [],
                                               'TotalRandSubset': '0', 'QuestionsPerPage': str(per_page or 0)},
                                  'EvenPresentation': False},
                'BlockVisibility': 'Collapsed',
            }
        self.blocks.append({'Type': 'Standard', 'Description': description, 'ID': bid, 'BlockElements': elems, 'Options': opts})
        self.block_ids[key] = bid
        return bid


def dg_intro_html(T):
    body = T['dg_intro_body']
    return (f'<h2>{esc(T["dg_intro_title"])}</h2><p><b>{esc(T["dg_round_name"])}</b></p>' + paras(body[:3]) +
            olist(T['dg_options']) + paras(body[3:]) + f'<p><b>{esc(T["dg_intro_example"])}</b></p>')


def end_html(T, progress_html, close_note):
    return (progress_html + f'<h2>{esc(T["end_title"])}</h2>' + paras(T['end_body']) + f'<p>{esc(T["end_code_label"])}</p>'
            '<p><b><span style="font-family:monospace;font-size:1.6rem;letter-spacing:.1em">${e://Field/exp_id}</span></b></p>'
            + paras([close_note], 'small'))


def build(T, Q, full=False, meta=False, eos_message=None, allow_multiple=False, keep_ip=False, partial='+4 hours'):
    b = Builder(T, Q, full, meta)
    scale6 = T['likert6']
    scale5 = T['likert5']
    items = T['items']

    # ---- 1. 同意（ページ 1）----
    consent_html = b.progress(1) + f'<h2>{esc(T["consent_title"])}</h2>' + paras(T['consent_body'])
    q_t = b.timing('t_consent')
    q_meta = b.meta_info()
    q_consent_text = b.text('consent_text', consent_html)
    q_consent = b.checkboxes('consent', esc(T['consent_error']), [T['consent_check'], T['eligible_check']], 2)
    b.block('consent', '1 同意', [q_t, q_meta, q_consent_text, q_consent])

    # ---- 2. 質問紙 FAB + 注意チェック（2 ページ、1 ブロック）----
    # oTree 版: 17 項目を一体でシャッフルして 9 + 8 に分け、注意チェックはページの端に来ないようにする。
    # Qualtrics 版: 15 項目を Advanced Randomization、cq1 を 1 ページ目の 5 番目、cq2 を 2 ページ目の 4 番目に固定し、
    # Questions per Page でページを分ける（ページ区切りはランダム化で無視されるため）。教示（DB 質問）もページ数に数える
    fab_q = {f: b.likert(f, items[f], scale6) for f in FAB}
    cq_q = {cq: b.likert(cq, items[cq], scale6) for cq in ('cq1', 'cq2')}
    t1 = b.timing('t_fab1')
    intro1 = b.text('fab_intro', (b.progress('p_fab1') + f'<h2>{b.stage_title("fab")}</h2>' +
                                  paras([fill(T['survey_page_note'], page='1', pages='2')], 'small') +
                                  paras(T['fab_intro']) + f'<p><small>{esc(T["scale_heading"])}</small></p>' + olist(scale6)))
    t2 = b.timing('t_fab2')
    intro2 = b.text('fab_intro2', (b.progress('p_fab2') + f'<h2>{b.stage_title("fab")}</h2>' +
                                   paras([fill(T['survey_page_note'], page='2', pages='2')], 'small') +
                                   paras([T['fab_intro_short']])))
    R = '{~Randomized~}'
    page1_fixed = [t1, intro1] + [R] * 4 + [cq_q['cq1']] + [R] * 4      # 9 項目（FAB 8 + cq1）
    page2_fixed = [t2, intro2] + [R] * 3 + [cq_q['cq2']] + [R] * 4      # 8 項目（FAB 7 + cq2）
    per_page = len([q for q in page1_fixed if q])
    b.block('fab', '2-3 質問紙 FAB + 注意チェック（2 ページ）',
            [t1, intro1] + [fab_q[f] for f in FAB] + [cq_q['cq1'], t2, intro2, cq_q['cq2']],
            fixed_order=page1_fixed + page2_fixed, randomize=[fab_q[f] for f in FAB], per_page=per_page)

    # ---- 3. 質問紙 HEXACO（1 ページ）----
    t3 = b.timing('t_hex')
    intro3 = b.text('hex_intro', (b.progress('p_hex') + f'<h2>{b.stage_title("hex")}</h2>' + paras(T['hex_intro']) +
                                  f'<p><small>{esc(T["scale_heading"])}</small></p>' + olist(scale5)))
    hex_q = [b.likert(h, items[h], scale5) for h in HEX]
    b.block('hex', '4 質問紙 HEXACO', [t3, intro3] + hex_q, fixed_order=[t3, intro3] + [R] * 10, randomize=hex_q)

    # ---- 4. DG 説明 ----
    dg_html = dg_intro_html(T)
    t4 = b.timing('t_dg_intro')
    q_dg_intro = b.text('dg_intro', b.progress('p_dgi') + dg_html)
    b.block('dg_intro', '5 意思決定課題の説明', [t4, q_dg_intro])

    # ---- 5. 理解確認（1 回目）----
    check_html = (b.progress('p_chk') + f'<h2>{esc(T["check_title"])}</h2>' + paras([T['check_lead']], 'small') +
                  f'<p><b>{esc(T["check_question"])}</b></p>' + paras([Q['number_note']], 'small'))
    recap = '<details><summary>' + esc(T['dg_reread']) + '</summary>' + dg_html + '</details>'
    t5 = b.timing('t_dg_check')
    q_check = b.number('dg_check_answer1', check_html + recap, 0, 100000)
    b.block('dg_check', '6 理解確認', [t5, q_check])
    # 再回答（1 回目が不正解のときだけ Survey Flow の分岐で表示。oTree 版と同じく進捗は同じページ番号）
    t5b = b.timing('t_dg_check2')
    retry_html = (b.progress('p_chk') + f'<h2>{esc(T["check_title"])}</h2><p><b>{esc(T["check_retry"])}</b></p>' + dg_html +
                  f'<p><b>{esc(T["check_question"])}</b></p>' + paras([Q['number_note']], 'small'))
    q_check2 = b.number('dg_check_answer2', retry_html, 0, 100000)
    b.block('dg_check2', '6b 理解確認（再回答）', [t5b, q_check2])

    # ---- 6. 決定 ----
    js = (
        "Qualtrics.SurveyEngine.addOnReady(function(){"
        "var endowment=%d, unit='%s'; var inp=this.getQuestionContainer().querySelector('input[type=text]'); if(!inp){return;}"
        "inp.setAttribute('inputmode','numeric'); inp.setAttribute('autocomplete','off');"
        "var box=document.createElement('div'); box.style.cssText='display:none;background:#f1f5f9;border-radius:10px;padding:.75rem 1rem;margin:.75rem 0;font-size:1.1rem;';"
        "inp.parentNode.appendChild(box);"
        "function upd(){var g=parseInt(inp.value,10); if(isNaN(g)||g<0||g>endowment){box.style.display='none';return;}"
        "box.innerHTML='%s: <b>'+(endowment-g).toLocaleString()+' '+unit+'</b><br>%s: <b>'+g.toLocaleString()+' '+unit+'</b>'; box.style.display='block';}"
        "inp.addEventListener('input',upd); upd();});"
    ) % (ENDOWMENT, CURRENCY, T['decision_keep'], T['decision_other'])
    decide_html = (b.progress('p_dec') + f'<h2>{esc(T["decision_title"])}</h2>' + paras([T['decision_lead']]) +
                   f'<p><b>{esc(T["decision_question"])}</b></p>' + paras([T['decision_hint']], 'small'))
    t6 = b.timing('t_dg_decide')
    q_give = b.number('dg_give', decide_html, 0, ENDOWMENT, js=js)
    b.block('dg_decide', '7 決定', [t6, q_give])

    # ---- 7. 事後評価（ページ 8）----
    t7 = b.timing('t_post')
    q_post_intro = b.text('post_intro', b.progress(8) + f'<h2>{esc(T["post_title"])}</h2>' + paras([T['post_intro']], 'small'))
    post_q = [b.likert(k, T['post_items'][k], scale6) for k in EVAL]
    q_comment = b.essay('comment_open', esc(T['post_comment']))
    b.block('post', '8 事後評価', [t7, q_post_intro] + post_q + [q_comment])

    # ---- 8. 終了（ページ 9）----
    # --eos-message あり: End of Survey のカスタムメッセージ（Library の MS_xxx）で参加者コードを出す。到達した時点で回答が完了になる。
    # なし: 終了ブロック。「次へ」を押して送信するよう促す（押さないと Finished にならない）
    eos_html = end_html(T, b.progress(TOTAL_PAGES), T['end_close'])      # Library に貼る本文（eos_message.html）
    if not eos_message:
        q_end = b.text('end_text', end_html(T, b.progress(TOTAL_PAGES), Q['end_submit']))
        b.block('end', '9 終了', [q_end])

    # ---- Survey Flow ----
    fl = b.next_fl  # shorthand
    B = b.block_ids

    def ed(**fields):
        return {'Type': 'EmbeddedData', 'FlowID': fl(),
                'EmbeddedData': [{'Description': k, 'Type': 'Custom', 'Field': k, 'VariableType': 'String', 'DataVisibility': [], 'AnalyzeText': False, 'Value': str(v)}
                                 for k, v in fields.items()]}

    def blk(key):
        return {'Type': 'Standard', 'ID': B[key], 'FlowID': fl(), 'Autofill': []}

    def survey_stage(first_page):
        """質問紙の 2 段階。first_page はこの段階の最初のページ番号（質問紙先行群 2、DG 先行群 5）。"""
        o = first_page
        return {'Type': 'BlockRandomizer', 'FlowID': fl(), 'SubSet': 1, 'EvenPresentation': True, 'Flow': [
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'scale_order 1: FAB → HEXACO',
             'Flow': [ed(scale_order=1, fab_stage=1, hex_stage=2, p_fab1=o, p_fab2=o + 1, p_hex=o + 2), blk('fab'), blk('hex')]},
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'scale_order 2: HEXACO → FAB',
             'Flow': [ed(scale_order=2, fab_stage=2, hex_stage=1, p_hex=o, p_fab1=o + 1, p_fab2=o + 2), blk('hex'), blk('fab')]},
        ]}

    def dg_stage(first_page):
        d = first_page
        branch = {'Type': 'Branch', 'FlowID': fl(), 'Description': '理解確認が不正解なら 1 回だけ再回答',
                  'BranchLogic': {'0': {'0': {'LogicType': 'Question', 'QuestionID': q_check, 'QuestionIsInLoop': 'no',
                                              'ChoiceLocator': f'q://{q_check}/ChoiceTextEntryValue', 'Operator': 'NotEqualTo',
                                              'RightOperand': str(ENDOWMENT - CHECK_GIVE), 'LeftOperand': f'q://{q_check}/ChoiceTextEntryValue',
                                              'Type': 'Expression', 'Description': f'<span class="ConjDesc">If</span> <span class="QuestionDesc">理解確認</span> <span class="LeftOpDesc">Text Response</span> <span class="OpDesc">Is Not Equal to</span> <span class="RightOpDesc"> {ENDOWMENT - CHECK_GIVE} </span>'},
                                        'Type': 'If'}, 'Type': 'BooleanExpression'},
                  'Flow': [blk('dg_check2')]}
        return [ed(p_dgi=d, p_chk=d + 1, p_dec=d + 2), blk('dg_intro'), blk('dg_check'), branch, blk('dg_decide')]

    root_flow = [
        # 設定値・来歴（codebook と同じ列名）と、順序群で決まる埋め込みデータの初期値（列を必ず作る）
        # exp_id（r3）: 10 桁の乱数。パイプテキストはこのフロー要素に達した時点で評価され、回答に固定される
        ed(exp_id='${rand://int/1000000000:9999999999}',
           cfg_endowment=ENDOWMENT, cfg_fee=FEE, cfg_dg_step=DG_STEP, cfg_use_hexaco=1, lang=LANG, app_version=APP_VERSION,
           qsf_hash='', task_order='', scale_order='', fab_stage='', hex_stage='',
           p_fab1='', p_fab2='', p_hex='', p_dgi='', p_chk='', p_dec=''),
        blk('consent'),
        {'Type': 'BlockRandomizer', 'FlowID': fl(), 'SubSet': 1, 'EvenPresentation': True, 'Flow': [
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'task_order 1: 質問紙 → DG', 'Flow': [ed(task_order=1), survey_stage(2)] + dg_stage(5)},
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'task_order 2: DG → 質問紙', 'Flow': [ed(task_order=2)] + dg_stage(2) + [survey_stage(5)]},
        ]},
        blk('post'),
    ]
    if not eos_message:
        root_flow.append(blk('end'))
    root_flow.append({'Type': 'EndSurvey', 'FlowID': fl()})
    flow = {'Type': 'Root', 'FlowID': 'FL_root', 'Flow': root_flow, 'Properties': {'Count': b.flow_id + 1, 'RemovedFieldsets': []}}

    # 来歴: 質問・ブロック・フローの内容のハッシュ（日付やハッシュ自身を除く）。各回答の qsf_hash 列に入る
    digest_src = json.dumps([b.questions, b.blocks, flow], ensure_ascii=False, sort_keys=True)
    qsf_hash = hashlib.sha256(digest_src.encode('utf-8')).hexdigest()[:12]
    for e in root_flow[0]['EmbeddedData']:
        if e['Field'] == 'qsf_hash':
            e['Value'] = qsf_hash

    now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    blocks_payload = {str(i): blk_ for i, blk_ in enumerate(b.blocks)}
    blocks_payload[str(len(b.blocks))] = {'Type': 'Trash', 'Description': 'Trash / Unused Questions', 'ID': 'BL_trash', 'BlockElements': []}
    # 2026-11-06 の取り込みで、値が null の項目と AutoConfirmTarget は「許可されていないプロパティ」(ESDEF10) として拒否された → 入れない
    so = {
        'BackButton': 'false', 'SaveAndContinue': 'true', 'SurveyProtection': 'PublicSurvey',
        'BallotBoxStuffingPrevention': 'false' if allow_multiple else 'true',
        'NoIndex': 'Yes', 'SecureResponseFiles': 'true', 'SurveyExpiration': 'None',
        'SurveyTermination': 'DisplayMessage' if eos_message else 'DefaultMessage',
        'Header': '', 'Footer': '', 'ProgressBarDisplay': 'None', 'PartialData': partial, 'ValidationMessage': '',
        'PreviousButton': ' ← ', 'NextButton': ' 次へ ', 'SurveyTitle': T['title'], 'SkinLibrary': '', 'SkinType': 'MQ', 'Skin': 'MQ',
        'EOSMessage': eos_message or '',
        'ShowExportTags': 'false', 'CollectGeoLocation': 'false',
        'SurveyMetaDescription': T['title'], 'AvailableLanguages': {'JA': []}, 'ProtectSelectionIds': True,
        'SurveyLanguage': 'JA', 'PasswordProtection': 'No', 'AnonymizeResponse': 'No' if keep_ip else 'Yes', 'RefererCheck': 'No',
        'ResponseSummary': 'No', 'EmailThankYou': 'false',
        'ValidateMessage': 'false', 'InactiveSurvey': 'DefaultMessage',
    }
    if eos_message:
        so['EOSMessageLibrary'] = OWNER_ID
    elements = [
        {'SurveyID': SURVEY_ID, 'Element': 'BL', 'PrimaryAttribute': 'Survey Blocks', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': blocks_payload},
        {'SurveyID': SURVEY_ID, 'Element': 'FL', 'PrimaryAttribute': 'Survey Flow', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': flow},
        {'SurveyID': SURVEY_ID, 'Element': 'SO', 'PrimaryAttribute': 'Survey Options', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': so},
        {'SurveyID': SURVEY_ID, 'Element': 'SCO', 'PrimaryAttribute': 'Scoring', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': {
            'ScoringCategories': [], 'ScoringCategoryGroups': [], 'ScoringSummaryCategory': None, 'ScoringSummaryAfterQuestions': 0,
            'ScoringSummaryAfterSurvey': 0, 'DefaultScoringCategory': None, 'AutoScoringCategory': None}},
        {'SurveyID': SURVEY_ID, 'Element': 'PROJ', 'PrimaryAttribute': 'CORE', 'SecondaryAttribute': None, 'TertiaryAttribute': '1.1.0', 'Payload': {'ProjectCategory': 'CORE', 'SchemaVersion': '1.1.0'}},
        {'SurveyID': SURVEY_ID, 'Element': 'STAT', 'PrimaryAttribute': 'Survey Statistics', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': {'MobileCompatible': True, 'ID': 'Survey Statistics'}},
        {'SurveyID': SURVEY_ID, 'Element': 'QC', 'PrimaryAttribute': 'Survey Question Count', 'SecondaryAttribute': str(len(b.questions)), 'TertiaryAttribute': None, 'Payload': None},
        {'SurveyID': SURVEY_ID, 'Element': 'RS', 'PrimaryAttribute': 'RS_a1v05default', 'SecondaryAttribute': 'Default Response Set', 'TertiaryAttribute': None, 'Payload': None},
    ] + b.questions
    qsf = {
        'SurveyEntry': {
            'SurveyID': SURVEY_ID, 'SurveyName': SURVEY_NAME, 'SurveyDescription': None, 'SurveyOwnerID': OWNER_ID, 'SurveyBrandID': BRAND_ID,
            'DivisionID': None, 'SurveyLanguage': 'JA', 'SurveyActiveResponseSet': 'RS_a1v05default', 'SurveyStatus': 'Inactive',
            'SurveyStartDate': '0000-00-00 00:00:00', 'SurveyExpirationDate': '0000-00-00 00:00:00', 'SurveyCreationDate': now,
            'CreatorID': OWNER_ID, 'LastModified': now, 'LastAccessed': '0000-00-00 00:00:00', 'LastActivated': '0000-00-00 00:00:00', 'Deleted': None,
        },
        'SurveyElements': elements,
    }
    return qsf, b, qsf_hash, eos_html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--texts', required=True, help='a1-decision-study/altruism_study/texts/ja.py')
    ap.add_argument('--out', default='A-1_v0.6r3_ja.qsf')
    ap.add_argument('--full', action='store_true', help='Timing 質問と JavaScript を入れる（有料ライセンス向け）')
    ap.add_argument('--meta', action='store_true', help='同意ページに Meta Info 質問（ブラウザ・OS・画面解像度）を入れる。無料アカウントで通るか未確認')
    ap.add_argument('--eos-message', default=None, help='終了メッセージの Library ID（MS_xxx）。渡すと終了ブロックの代わりに End of Survey メッセージで参加者コードを出す')
    ap.add_argument('--allow-multiple', action='store_true', help='多重回答防止（BallotBoxStuffingPrevention）を切る')
    ap.add_argument('--keep-ip', action='store_true', help='匿名化（IP・位置情報を記録しない）を切る')
    ap.add_argument('--partial', default='+4 hours', help='未完了回答を記録するまでの期間（Survey Options の PartialData。既定 +4 hours = 研究室マニュアルの運用）')
    ap.add_argument('--brand', default=None, help='SurveyBrandID（既定: スクリプトの BRAND_ID）')
    args = ap.parse_args()
    global BRAND_ID
    if args.brand:
        BRAND_ID = args.brand
    T, Q = load_texts(args.texts)
    qsf, b, qsf_hash, eos_html = build(T, Q, full=args.full, meta=args.meta, eos_message=args.eos_message,
                                       allow_multiple=args.allow_multiple, keep_ip=args.keep_ip, partial=args.partial)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(qsf, f, ensure_ascii=False, indent=1)
    eos_path = re.sub(r'\.qsf$', '', args.out) + '_eos_message.html'
    with open(eos_path, 'w', encoding='utf-8') as f:
        f.write(eos_html + '\n')
    tags = [q['Payload']['DataExportTag'] for q in b.questions]
    print(f'wrote {args.out}: {len(b.questions)} questions, {len(b.blocks)} blocks, {b.flow_id} flow elements, qsf_hash {qsf_hash}')
    print(f'wrote {eos_path}: End of Survey メッセージの本文（Library → Messages → End of Survey Messages に貼る）')
    print('export tags:', ', '.join(tags))


if __name__ == '__main__':
    main()
