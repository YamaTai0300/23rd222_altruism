#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A-1 追試 v0.5 の実験を Qualtrics で再現する QSF（調査定義ファイル）を生成する。

使い方: python make_qsf.py --texts <a1-decision-study_v0.5>/altruism_study/texts/ja.py --out A-1_v0.5_ja.qsf
取り込み: Qualtrics の Projects → Create project → Survey → "Import a QSF file"（新規プロジェクトになる）

oTree 版（v0.5）との対応
- 画面: 同意 → 質問紙 1/2（FAB + 注意チェック、2 ページ）→ 質問紙 2/2（HEXACO、1 ページ）→ DG 説明 → 理解確認（不正解なら 1 回だけ再回答）
  → 決定（取り分の即時表示は JavaScript）→ 事後評価 → 終了（参加者コード = ResponseID）。順序群 2 は DG が先
- ランダム化: Survey Flow の Randomizer（Evenly present）を 2 段に重ね、task_order（質問紙↔DG）と scale_order（FAB↔HEXACO）を
  Embedded Data に記録。FAB の項目順はブロック内の Advanced Randomization（注意チェックはページ中央に固定）、HEXACO も同様
- 検証: 必須（Force response）、理解確認・決定は 0〜1000 の整数（Content validation）
- 時間: 各ページに Timing 質問（t_<page>: First Click / Last Click / Page Submit / Click Count）
- 記録: 変数名 = codebook と同じ（hg_1 … mc_23, cq1, cq2, hex_1 … hex_10, dg_check, dg_check2, dg_give, eval_*, comment_open）
  項目順は Qualtrics のエクスポートオプション「Export viewing order data for randomized surveys」で取れる
- 元手 1,000 円・理解確認の正答 700 はこのスクリプトの定数（ENDOWMENT, CHECK_GIVE）
- Qualtrics の無料アカウント（2026-11 に取り込みで確認）では Timing 質問と質問の JavaScript が使えない（403）。既定（--free）は
  その 2 つを入れない。有料ライセンスでは --full でページ時間（t_*）と取り分の即時表示を入れた版を作る
- SurveyBrandID は空だと取り込みで拒否される（--brand で指定。URL の <brand>.<dc>.qualtrics.com の <brand>）
"""
import argparse
import datetime as dt
import importlib.util
import json
import re

ENDOWMENT = 1000
CHECK_GIVE = 300
FEE = 300
CURRENCY = '円'
SURVEY_ID = 'SV_egt7X9VgLDhmk8C'   # 取り込み時には新しい ID が振られる（2026-11-05 の取り込み結果: SV_6PfFg1rhsV2G2uG「study_v5」）
BRAND_ID = 'qualtricsxmw5hysnkpn'   # 空だと ESDEF10 で拒否される
OWNER_ID = 'UR_1QAwVwSMYMfW9nn'
SURVEY_NAME = 'A-1 意思決定と日常行動に関する調査（v0.5 Qualtrics）'

HG = ['hg_1', 'hg_3', 'hg_7', 'hg_10', 'hg_13']
PP = ['pp_1', 'pp_8', 'pp_12', 'pp_14', 'pp_15']
MC = ['mc_1', 'mc_3', 'mc_18', 'mc_20', 'mc_23']
FAB = HG + PP + MC
HEX = [f'hex_{i}' for i in range(1, 11)]
EVAL = ['eval_understand', 'eval_difficult', 'eval_reflect', 'eval_distract']


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
    return fill(mod.TEXT, endowment=f'{ENDOWMENT:,}', currency=CURRENCY, fee=f'{FEE:,}', check_amount=f'{CHECK_GIVE:,}', step='1')


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def olist(items):
    """Qualtrics のテーマでは <ol> の番号が表示されないことがあるので、番号を文字で入れる。"""
    return '<ol>' + ''.join(f'<li>{i + 1}. {esc(o)}</li>' for i, o in enumerate(items)) + '</ol>'


def paras(lines, cls=''):
    attr = f' class="{cls}"' if cls else ''
    return ''.join(f'<p{attr}>{esc(p)}</p>' for p in lines)


# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, T, full=False):
        self.T = T
        self.full = full
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
        if js and not self.full and tag == 'dg_give':
            p['QuestionText'] += '<p class="small">入力した額が相手の受け取る額、1,000 円から引いた残りがあなたの取り分になります。</p>'
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
    def block(self, key, description, qids, fixed_order=None, randomize=None):
        bid = f'BL_{key}'
        qids = [q for q in qids if q]              # Timing を入れない版では None が混じる
        if fixed_order:
            fixed_order = [q for q in fixed_order if q]
        elems = [{'Type': 'Question', 'QuestionID': q} for q in qids]
        opts = {'BlockLocking': 'false', 'RandomizeQuestions': 'false', 'BlockVisibility': 'Collapsed'}
        if randomize:
            opts = {
                'BlockLocking': 'false', 'RandomizeQuestions': 'Advanced',
                'Randomization': {'Advanced': {'FixedOrder': fixed_order, 'RandomizeAll': randomize, 'RandomSubSet': [], 'Undisplayed': [],
                                               'TotalRandSubset': '0', 'QuestionsPerPage': '0'}, 'EvenPresentation': False},
                'BlockVisibility': 'Collapsed',
            }
        self.blocks.append({'Type': 'Standard', 'Description': description, 'ID': bid, 'BlockElements': elems, 'Options': opts})
        self.block_ids[key] = bid
        return bid


def build(T, full=False):
    b = Builder(T, full)
    scale6 = T['likert6']
    scale5 = T['likert5']
    items = T['items']

    # ---- 1. 同意 ----
    consent_html = f'<h2>{esc(T["consent_title"])}</h2>' + paras(T['consent_body'])
    q_t = b.timing('t_consent')
    q_consent_text = b.text('consent_text', consent_html)
    q_consent = b.checkboxes('consent', '参加するには 2 つの項目にチェックを入れてください。', [T['consent_check'], T['eligible_check']], 2)
    b.block('consent', '1 同意', [q_t, q_consent_text, q_consent])

    # ---- 2. 質問紙 1/2 = FAB + 注意チェック（2 ページ） ----
    intro_fab = ('<h2>質問紙 1/2</h2>' + paras(T['fab_intro']) +
                 '<p class="small">選択肢</p>' + olist(scale6))
    fab_q = {}
    for f in FAB:
        fab_q[f] = b.likert(f, items[f], scale6)
    cq_q = {cq: b.likert(cq, items[cq], scale6) for cq in ('cq1', 'cq2')}
    # ページ 1: FAB 8 項目（ランダム）+ cq1 を中央に固定、ページ 2: FAB 7 項目 + cq2。どの FAB 項目がどのページに出るかは固定
    # （Qualtrics のブロック内ランダム化はページをまたげないため。oTree 版は 17 項目を一体でシャッフル）
    page1_items = HG + PP[:3]          # 8 項目
    page2_items = PP[3:] + MC          # 7 項目
    t1 = b.timing('t_fab1')
    intro1 = b.text('fab_intro', intro_fab)
    fixed1 = [t1, intro1] + ['{~Randomized~}'] * 4 + [cq_q['cq1']] + ['{~Randomized~}'] * 4
    b.block('fab1', '2 質問紙 1/2 FAB（1 ページ目）', [t1, intro1] + [fab_q[f] for f in page1_items] + [cq_q['cq1']],
            fixed_order=fixed1, randomize=[fab_q[f] for f in page1_items])
    t2 = b.timing('t_fab2')
    intro2 = b.text('fab_intro2', '<h2>質問紙 1/2（2 ページ目）</h2>' + paras([T['fab_intro_short']], 'small'))
    fixed2 = [t2, intro2] + ['{~Randomized~}'] * 3 + [cq_q['cq2']] + ['{~Randomized~}'] * 4
    b.block('fab2', '3 質問紙 1/2 FAB（2 ページ目）', [t2, intro2] + [fab_q[f] for f in page2_items] + [cq_q['cq2']],
            fixed_order=fixed2, randomize=[fab_q[f] for f in page2_items])

    # ---- 3. 質問紙 2/2 = HEXACO ----
    intro_hex = ('<h2>質問紙 2/2</h2>' + paras(T['hex_intro']) +
                 '<p class="small">選択肢</p>' + olist(scale5))
    t3 = b.timing('t_hex')
    intro3 = b.text('hex_intro', intro_hex)
    hex_q = [b.likert(h, items[h], scale5) for h in HEX]
    b.block('hex', '4 質問紙 2/2 HEXACO', [t3, intro3] + hex_q, fixed_order=[t3, intro3] + ['{~Randomized~}'] * 10, randomize=hex_q)

    # ---- 4. DG 説明 ----
    body = T['dg_intro_body']
    dg_html = (f'<h2>{esc(T["dg_intro_title"])}</h2><p><b>{esc(T["dg_round_name"])}</b></p>' + paras(body[:3]) +
               olist(T['dg_options']) + paras(body[3:]) +
               f'<p><b>{esc(T["dg_intro_example"])}</b></p>')
    t4 = b.timing('t_dg_intro')
    q_dg_intro = b.text('dg_intro', dg_html)
    b.block('dg_intro', '5 意思決定課題の説明', [t4, q_dg_intro])

    # ---- 5. 理解確認（1 回目） ----
    check_html = f'<h2>{esc(T["check_title"])}</h2>' + paras([T['check_lead']], 'small') + f'<p><b>{esc(T["check_question"])}</b></p><p class="small">半角数字（{CURRENCY}）</p>'
    recap = '<details><summary>' + esc(T['dg_reread']) + '</summary>' + dg_html + '</details>'
    t5 = b.timing('t_dg_check')
    q_check = b.number('dg_check', check_html + recap, 0, 100000)
    b.block('dg_check', '6 理解確認', [t5, q_check])
    # 再回答（1 回目が不正解のときだけ Survey Flow の分岐で表示）
    t5b = b.timing('t_dg_check2')
    retry_html = (f'<h2>{esc(T["check_title"])}</h2><p style="color:#b00020"><b>{esc(T["check_retry"])}</b></p>' + dg_html +
                  f'<p><b>{esc(T["check_question"])}</b></p><p class="small">半角数字（{CURRENCY}）</p>')
    q_check2 = b.number('dg_check2', retry_html, 0, 100000)
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
    decide_html = (f'<h2>{esc(T["decision_title"])}</h2>' + paras([T['decision_lead']]) + f'<p><b>{esc(T["decision_question"])}</b></p>' +
                   paras([T['decision_hint']], 'small'))
    t6 = b.timing('t_dg_decide')
    q_give = b.number('dg_give', decide_html, 0, ENDOWMENT, js=js)
    b.block('dg_decide', '7 決定', [t6, q_give])

    # ---- 7. 事後評価 ----
    t7 = b.timing('t_post')
    q_post_intro = b.text('post_intro', f'<h2>{esc(T["post_title"])}</h2>' + paras([T['post_intro']], 'small'))
    post_q = [b.likert(k, T['post_items'][k], scale6) for k in EVAL]
    q_comment = b.essay('comment_open', esc(T['post_comment']))
    b.block('post', '8 事後評価', [t7, q_post_intro] + post_q + [q_comment])

    # ---- 8. 終了 ----
    end_html = (f'<h2>{esc(T["end_title"])}</h2>' + paras(T['end_body']) + f'<p>{esc(T["end_code_label"])}</p>'
                '<p style="font-family:monospace;font-size:1.6rem;letter-spacing:.1em;background:#f1f5f9;display:inline-block;padding:.5rem 1rem;border-radius:10px">${e://Field/ResponseID}</p>'
                + paras([T['end_close']], 'small'))
    q_end = b.text('end_text', end_html)
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

    def survey_stage():
        return {'Type': 'BlockRandomizer', 'FlowID': fl(), 'SubSet': 1, 'EvenPresentation': True, 'Flow': [
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'scale_order 1: FAB → HEXACO', 'Flow': [ed(scale_order=1), blk('fab1'), blk('fab2'), blk('hex')]},
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'scale_order 2: HEXACO → FAB', 'Flow': [ed(scale_order=2), blk('hex'), blk('fab1'), blk('fab2')]},
        ]}

    def dg_stage():
        branch = {'Type': 'Branch', 'FlowID': fl(), 'Description': '理解確認が不正解なら 1 回だけ再回答',
                  'BranchLogic': {'0': {'0': {'LogicType': 'Question', 'QuestionID': q_check, 'QuestionIsInLoop': 'no',
                                              'ChoiceLocator': f'q://{q_check}/ChoiceTextEntryValue', 'Operator': 'NotEqualTo',
                                              'RightOperand': str(ENDOWMENT - CHECK_GIVE), 'LeftOperand': f'q://{q_check}/ChoiceTextEntryValue',
                                              'Type': 'Expression', 'Description': f'<span class="ConjDesc">If</span> <span class="QuestionDesc">理解確認</span> <span class="LeftOpDesc">Text Response</span> <span class="OpDesc">Is Not Equal to</span> <span class="RightOpDesc"> {ENDOWMENT - CHECK_GIVE} </span>'},
                                        'Type': 'If'}, 'Type': 'BooleanExpression'},
                  'Flow': [blk('dg_check2')]}
        return [blk('dg_intro'), blk('dg_check'), branch, blk('dg_decide')]

    root_flow = [
        ed(endowment=ENDOWMENT, participation_fee_yen=FEE, app_version='v0.5-qualtrics', task_order='', scale_order=''),
        blk('consent'),
        {'Type': 'BlockRandomizer', 'FlowID': fl(), 'SubSet': 1, 'EvenPresentation': True, 'Flow': [
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'task_order 1: 質問紙 → DG', 'Flow': [ed(task_order=1), survey_stage()] + dg_stage()},
            {'Type': 'Group', 'FlowID': fl(), 'Description': 'task_order 2: DG → 質問紙', 'Flow': [ed(task_order=2)] + dg_stage() + [survey_stage()]},
        ]},
        blk('post'),
        blk('end'),
        {'Type': 'EndSurvey', 'FlowID': fl()},
    ]
    flow = {'Type': 'Root', 'FlowID': 'FL_root', 'Flow': root_flow, 'Properties': {'Count': b.flow_id + 1, 'RemovedFieldsets': []}}

    now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    blocks_payload = {str(i): blk_ for i, blk_ in enumerate(b.blocks)}
    blocks_payload[str(len(b.blocks))] = {'Type': 'Trash', 'Description': 'Trash / Unused Questions', 'ID': 'BL_trash', 'BlockElements': []}
    elements = [
        {'SurveyID': SURVEY_ID, 'Element': 'BL', 'PrimaryAttribute': 'Survey Blocks', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': blocks_payload},
        {'SurveyID': SURVEY_ID, 'Element': 'FL', 'PrimaryAttribute': 'Survey Flow', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': flow},
        {'SurveyID': SURVEY_ID, 'Element': 'SO', 'PrimaryAttribute': 'Survey Options', 'SecondaryAttribute': None, 'TertiaryAttribute': None, 'Payload': {
            'BackButton': 'false', 'SaveAndContinue': 'true', 'SurveyProtection': 'PublicSurvey', 'BallotBoxStuffingPrevention': 'false',
            'NoIndex': 'Yes', 'SecureResponseFiles': 'true', 'SurveyExpiration': 'None', 'SurveyTermination': 'DefaultMessage',
            'Header': '', 'Footer': '', 'ProgressBarDisplay': 'VerboseText', 'PartialData': '+1 week', 'ValidationMessage': '',
            'PreviousButton': ' ← ', 'NextButton': ' 次へ ', 'SurveyTitle': T['title'], 'SkinLibrary': '', 'SkinType': 'MQ', 'Skin': 'MQ',
            'EOSMessage': '', 'ShowExportTags': 'false', 'CollectGeoLocation': 'false',
            'SurveyMetaDescription': T['title'], 'AvailableLanguages': {'JA': []}, 'ProtectSelectionIds': True,
            'SurveyLanguage': 'JA', 'PasswordProtection': 'No', 'AnonymizeResponse': 'No', 'RefererCheck': 'No', 'UseCustomSurveyLinkCompletedMessage': None,
            'SurveyLinkCompletedMessage': None, 'SurveyLinkCompletedMessageLibrary': None, 'ResponseSummary': 'No', 'EOSMessageLibrary': None,
            'EOSRedirectURL': None, 'ShowExportTags': 'false', 'EmailThankYou': 'false', 'ThankYouEmailMessageLibrary': None, 'ThankYouEmailMessage': None,
            'ValidateMessage': 'false', 'InactiveSurvey': 'DefaultMessage', 'PartialDeletion': None,
            'AutoConfirmTarget': None,
        }},
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
    return qsf, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--texts', required=True, help='a1-decision-study_v0.5/altruism_study/texts/ja.py')
    ap.add_argument('--out', default='A-1_v0.5_ja.qsf')
    ap.add_argument('--full', action='store_true', help='Timing 質問と JavaScript を入れる（有料ライセンス向け）')
    ap.add_argument('--brand', default=None, help='SurveyBrandID（既定: スクリプトの BRAND_ID）')
    args = ap.parse_args()
    global BRAND_ID
    if args.brand:
        BRAND_ID = args.brand
    T = load_texts(args.texts)
    qsf, b = build(T, full=args.full)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(qsf, f, ensure_ascii=False, indent=1)
    tags = [q['Payload']['DataExportTag'] for q in b.questions]
    print(f'wrote {args.out}: {len(b.questions)} questions, {len(b.blocks)} blocks, {b.flow_id} flow elements')
    print('export tags:', ', '.join(tags))


if __name__ == '__main__':
    main()
