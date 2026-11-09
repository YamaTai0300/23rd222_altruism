#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qualtrics 版（make_qsf.py r3 で作った調査。r2 も可）のエクスポート CSV を、oTree 版のエクスポート形式に変換する。

目的: analysis/01_clean.R（と tools/pairing.py、tools/archive_export.py）を oTree 版・Qualtrics 版で共通に使う。
      変換後の列は analysis/codebook.csv と 99_synthetic.R の列（participant.*, player.*, session.*）と同じ。

使い方:
  python qualtrics_to_otree.py <Qualtrics の CSV> --out-dir ../a1-decision-study_v0.5/raw/main [--qsf A-1_v0.5r2_ja.qsf]
      [--date YYYY-MM-DD] [--tz +09:00] [--include-preview] [--keep-unfinished] [--session SV_xxx]
  → <out-dir>/altruism_study_<date>.csv（完了者だけ）、Timing 質問（--full の QSF）があれば <out-dir>/PageTimes_<date>.csv、
    <out-dir>/convert_<date>.txt（行数・除いた行・列の対応）

Qualtrics 側のエクスポート設定: Data & Analysis → Export → CSV、「Use numeric values」、
  「Export viewing order data for randomized surveys」を ON（FAB・HEXACO の項目順 fab_item_order / hex_item_order に使う）。
  先頭 3 行がヘッダー（列名・質問文・ImportId）。

oTree 版との対応（変換で吸収する差）
- participant.code ← 埋め込みデータ exp_id（r3 の実験 ID。列がない r2 のデータでは ResponseId）、participant.label ← ResponseId、
  player.exp_id ← exp_id。session.code ← --session（既定: QSF の SurveyID、なければ 'qualtrics'）
- consent / eligible_confirm ← consent_1 / consent_2（複数選択の 2 項目）
- dg_check（最終回答）← dg_check_answer2 があればそれ、なければ dg_check_answer1。dg_check_attempts / dg_check_pass もここで作る
- cq1_pass / cq2_pass / dg_share / excluded_in_app / exclude_reason_in_app は oTree 版の __init__.py と同じ定義で作る
- t_start ← StartDate、t_end ← EndDate（Qualtrics はアカウントのタイムゾーンで出す。--tz で ISO 8601 のオフセットを付ける）。
  oTree 版の t_start は同意を送信した時刻だが、Qualtrics の StartDate は調査を開いた時刻（同意文を読む時間を含む）
- duration_sec ← Duration (in seconds)。finished ← Finished（--keep-unfinished で未完了も残す。既定は完了者だけ）
- git_commit ← 埋め込みデータ qsf_hash、otree_version ← 'qualtrics'、rand_seed ← 空（Qualtrics の割り付けは seed なし）
- user_agent / screen_width ← Meta Info 質問（--meta で入れたとき）の列。なければ空
- fab_item_order / hex_item_order ← 表示順の列（名前が _DO で終わる列。値は export tag か QID を | 区切り。QID は --qsf で tag に直す）
- Status が 0（通常の回答）以外（1 = プレビュー、2 = テスト、8 = スパム など）は除く（--include-preview でプレビューも残す）
- Page Times: Timing 質問 t_<page> の「Page Submit」秒を、参加者が通ったページ順（Consent → … → End）に積み上げて
  epoch_time_completed にする。再回答ページ t_dg_check2 は DGCheck に足す（oTree 版は同じページ）
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
from collections import OrderedDict

HG = ['hg_1', 'hg_3', 'hg_7', 'hg_10', 'hg_13']
PP = ['pp_1', 'pp_8', 'pp_12', 'pp_14', 'pp_15']
MC = ['mc_1', 'mc_3', 'mc_18', 'mc_20', 'mc_23']
FAB = HG + PP + MC
CQ = ['cq1', 'cq2']
HEX = [f'hex_{i}' for i in range(1, 11)]
EVAL = ['eval_understand', 'eval_difficult', 'eval_reflect', 'eval_distract']
CQ_EXPECTED = dict(cq1=1, cq2=6)
CHECK_GIVE = 300

# oTree 版の page_sequence（__init__.py）。PageTimes の page_index はこの位置（1 始まり）
PAGE_SEQUENCE = ['Consent', 'HexFirstA', 'FabPage1A', 'FabPage2A', 'HexLastA', 'DGIntroA', 'DGCheckA', 'DGDecisionA',
                 'DGIntroB', 'DGCheckB', 'DGDecisionB', 'HexFirstB', 'FabPage1B', 'FabPage2B', 'HexLastB', 'PostSurvey', 'End']
# Timing 質問の tag → oTree のページ（順序群の A/B は後で付ける）
TIMING_PAGE = dict(t_consent='Consent', t_fab1='FabPage1', t_fab2='FabPage2', t_hex='Hex', t_dg_intro='DGIntro',
                   t_dg_check='DGCheck', t_dg_check2='DGCheck', t_dg_decide='DGDecision', t_post='PostSurvey')


def read_qualtrics_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        raise SystemExit('Qualtrics の CSV は先頭 3 行がヘッダー（列名・質問文・ImportId）です: ' + path)
    header = rows[0]
    body = rows[3:] if rows[2] and rows[2][0].startswith('{"ImportId"') else rows[1:]
    return header, [dict(zip(header, r)) for r in body if any(c.strip() for c in r)]


def qid_to_tag_map(qsf_path):
    with open(qsf_path, encoding='utf-8') as f:
        qsf = json.load(f)
    m, survey_id = {}, qsf.get('SurveyEntry', {}).get('SurveyID')
    for e in qsf['SurveyElements']:
        if e.get('Element') == 'SQ':
            m[e['PrimaryAttribute']] = e['Payload'].get('DataExportTag')
    return m, survey_id


def to_int(v):
    if v is None:
        return None
    v = str(v).strip()
    if v == '':
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def to_bool01(v):
    s = str(v or '').strip().lower()
    if s in ('1', 'true', 'yes'):
        return 1
    if s in ('0', 'false', 'no', ''):
        return 0
    return to_int(s) or 0


def iso(ts, tz):
    """'2026-11-06 10:12:34' → '2026-11-06T10:12:34+09:00'（Qualtrics の日時はアカウントのタイムゾーン）。"""
    ts = (ts or '').strip()
    if not ts:
        return ''
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S'):
        try:
            d = dt.datetime.strptime(ts, fmt)
            return d.strftime('%Y-%m-%dT%H:%M:%S') + tz
        except ValueError:
            continue
    return ts


def epoch(ts, tz):
    s = iso(ts, tz)
    try:
        return int(dt.datetime.fromisoformat(s).timestamp())
    except ValueError:
        return None


def item_order(row, header, qid_map, wanted):
    """表示順の列（_DO で終わる列）から wanted の項目をこの参加者の提示順で返す。"""
    for col in header:
        if not col.endswith('_DO'):
            continue
        raw = (row.get(col) or '').strip()
        if not raw:
            continue
        toks = [qid_map.get(t.strip(), t.strip()) for t in raw.split('|')]
        got = [t for t in toks if t in wanted]
        if len(got) >= min(3, len(wanted)):
            return got
    return []


def convert(args):
    header, rows = read_qualtrics_csv(args.csv)
    qid_map, survey_id = ({}, None)
    if args.qsf:
        qid_map, survey_id = qid_to_tag_map(args.qsf)
    session_code = args.session or survey_id or 'qualtrics'
    date = args.date or dt.date.today().isoformat()
    os.makedirs(args.out_dir, exist_ok=True)

    missing = [c for c in ['ResponseId', 'Finished'] + FAB + CQ + HEX + ['dg_check_answer1', 'dg_give'] + EVAL if c not in header]
    if missing:
        raise SystemExit('列が足りません（export tag が違う QSF か、文字列エクスポートの可能性）: ' + ', '.join(missing))
    has_meta = any(c.startswith('meta_') for c in header)
    timing_cols = {t: f'{t}_Page Submit' for t in TIMING_PAGE if f'{t}_Page Submit' in header}

    out, dropped, page_rows = [], OrderedDict(status=0, unfinished=0), []
    for i, r in enumerate(rows, start=1):
        status = to_int(r.get('Status', '0'))
        if status not in (0, None) and not (args.include_preview and status == 1):
            dropped['status'] += 1
            continue
        finished = to_bool01(r.get('Finished'))
        if not finished and not args.keep_unfinished:
            dropped['unfinished'] += 1
            continue
        response_id = r['ResponseId'].strip()
        exp_id = (r.get('exp_id') or '').strip()
        code = exp_id or response_id   # r3: 実験 ID を participant.code にする（CW の照合・pairing.py と同じ ID）
        task_order, scale_order = to_int(r.get('task_order')), to_int(r.get('scale_order'))
        endow = to_int(r.get('cfg_endowment')) or args.endowment
        cq = {c: to_int(r.get(c)) for c in CQ}
        a1, a2 = to_int(r.get('dg_check_answer1')), to_int(r.get('dg_check_answer2'))
        attempts = 2 if a2 is not None else (1 if a1 is not None else 0)
        dg_check = a2 if a2 is not None else a1
        correct = endow - CHECK_GIVE
        check_pass = int(dg_check == correct) if dg_check is not None else ''
        cq_pass = {c: int(cq[c] == CQ_EXPECTED[c]) if cq[c] is not None else '' for c in CQ}
        dg_give = to_int(r.get('dg_give'))
        reasons = []
        if not (cq_pass['cq1'] == 1 and cq_pass['cq2'] == 1):
            reasons.append('cq')
        if check_pass != 1:
            reasons.append('check')
        fab_order = item_order(r, header, qid_map, set(FAB + CQ))
        hex_order = item_order(r, header, qid_map, set(HEX))
        ua, sw = '', ''
        if has_meta:
            ua = (r.get('meta_User Agent') or ' '.join(x for x in [r.get('meta_Browser', ''), r.get('meta_Version', ''), r.get('meta_Operating System', '')] if x)).strip()[:300]
            res = (r.get('meta_Resolution') or r.get('meta_Screen Resolution') or '').strip()
            m = re.match(r'(\d+)\s*[xX×]\s*\d+', res)
            sw = int(m.group(1)) if m else ''
        t_start, t_end = iso(r.get('StartDate'), args.tz), iso(r.get('EndDate'), args.tz)
        duration = to_int(r.get('Duration (in seconds)'))
        rec = OrderedDict()
        rec['participant.id_in_session'] = len(out) + 1
        rec['participant.code'] = code
        rec['participant.label'] = response_id
        rec['participant._is_bot'] = 0
        rec['participant._index_in_pages'] = len(PAGE_SEQUENCE) if finished else ''
        rec['participant._max_page_index'] = len(PAGE_SEQUENCE)
        rec['participant._current_app_name'] = 'altruism_study'
        rec['participant._current_page_name'] = 'End' if finished else ''
        rec['participant.time_started_utc'] = (r.get('StartDate') or '').strip()
        rec['participant.visited'] = 1
        rec['participant.mturk_worker_id'] = ''
        rec['participant.mturk_assignment_id'] = ''
        rec['participant.payoff'] = 0
        rec['player.id_in_group'] = 1
        rec['player.role'] = ''
        rec['player.payoff'] = 0
        rec['player.task_order'] = task_order if task_order is not None else ''
        rec['player.scale_order'] = scale_order if scale_order is not None else ''
        rec['player.lang'] = (r.get('lang') or 'ja').strip()
        rec['player.app_version'] = (r.get('app_version') or 'qualtrics').strip()
        rec['player.git_commit'] = (r.get('qsf_hash') or '').strip()
        rec['player.otree_version'] = 'qualtrics'
        rec['player.rand_seed'] = ''
        rec['player.cfg_endowment'] = endow
        rec['player.cfg_dg_step'] = to_int(r.get('cfg_dg_step')) if to_int(r.get('cfg_dg_step')) is not None else 1
        rec['player.cfg_fee'] = to_int(r.get('cfg_fee')) if to_int(r.get('cfg_fee')) is not None else args.fee
        rec['player.cfg_use_hexaco'] = to_int(r.get('cfg_use_hexaco')) if to_int(r.get('cfg_use_hexaco')) is not None else 1
        rec['player.user_agent'] = ua
        rec['player.screen_width'] = sw
        rec['player.exp_id'] = exp_id
        rec['player.consent'] = to_bool01(r.get('consent_1'))
        rec['player.eligible_confirm'] = to_bool01(r.get('consent_2'))
        for f in FAB:
            rec[f'player.{f}'] = to_int(r.get(f)) if to_int(r.get(f)) is not None else ''
        rec['player.cq1'] = cq['cq1'] if cq['cq1'] is not None else ''
        rec['player.cq2'] = cq['cq2'] if cq['cq2'] is not None else ''
        rec['player.cq1_pass'] = cq_pass['cq1']
        rec['player.cq2_pass'] = cq_pass['cq2']
        rec['player.fab_item_order'] = ','.join(fab_order)
        rec['player.hex_item_order'] = ','.join(hex_order)
        for h in HEX:
            rec[f'player.{h}'] = to_int(r.get(h)) if to_int(r.get(h)) is not None else ''
        rec['player.dg_check'] = dg_check if dg_check is not None else ''
        rec['player.dg_check_answer1'] = a1 if a1 is not None else ''
        rec['player.dg_check_answer2'] = a2 if a2 is not None else ''
        rec['player.dg_check_attempts'] = attempts
        rec['player.dg_check_pass'] = check_pass
        rec['player.dg_give'] = dg_give if dg_give is not None else ''
        rec['player.dg_share'] = int(dg_give > 0) if dg_give is not None else ''
        for k in EVAL:
            rec[f'player.{k}'] = to_int(r.get(k)) if to_int(r.get(k)) is not None else ''
        rec['player.comment_open'] = (r.get('comment_open') or '').strip()
        rec['player.t_start'] = t_start
        rec['player.t_end'] = t_end
        rec['player.duration_sec'] = duration if duration is not None else ''
        rec['player.finished'] = finished
        rec['player.excluded_in_app'] = int(bool(reasons))
        rec['player.exclude_reason_in_app'] = ','.join(reasons)
        rec['group.id_in_subsession'] = len(out) + 1
        rec['subsession.round_number'] = 1
        rec['session.code'] = session_code
        rec['session.label'] = ''
        rec['session.mturk_HITId'] = ''
        rec['session.mturk_HITGroupId'] = ''
        rec['session.comment'] = ''
        rec['session.is_demo'] = 0
        out.append(rec)

        # ---- Page Times（Timing 質問があるとき）----
        if timing_cols and task_order in (1, 2):
            sfx = 'A' if task_order == 1 else 'B'
            survey = (['Hex', 'FabPage1', 'FabPage2'] if scale_order == 2 else ['FabPage1', 'FabPage2', 'Hex'])
            survey = [(('HexFirst' if scale_order == 2 else 'HexLast') if p == 'Hex' else p) + sfx for p in survey]
            dg = [p + sfx for p in ['DGIntro', 'DGCheck', 'DGDecision']]
            pages = ['Consent'] + (survey + dg if task_order == 1 else dg + survey) + ['PostSurvey', 'End']
            secs = {}
            for tag, col in timing_cols.items():
                v = r.get(col, '')
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                base = TIMING_PAGE[tag]
                key = next((p for p in pages if p.startswith(base) or (base == 'Hex' and p.startswith('Hex'))), None)
                if key:
                    secs[key] = secs.get(key, 0.0) + v
            t0 = epoch(r.get('StartDate'), args.tz)
            if t0 is not None:
                acc = t0
                for p in pages:
                    acc += int(round(secs.get(p, 0.0)))
                    page_rows.append(OrderedDict(session_code=session_code, participant_id_in_session=len(out), participant_code=code,
                                                 page_index=PAGE_SEQUENCE.index(p) + 1, app_name='altruism_study', page_name=p,
                                                 epoch_time_completed=acc, round_number=1, timeout_happened=0, is_wait_page=0))

    if not out:
        raise SystemExit('変換後の行が 0 件です（Status / Finished で全部除かれた可能性）')
    out_path = os.path.join(args.out_dir, f'altruism_study_{date}.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    pt_path = None
    if page_rows:
        pt_path = os.path.join(args.out_dir, f'PageTimes_{date}.csv')
        with open(pt_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(page_rows[0].keys()))
            w.writeheader()
            w.writerows(page_rows)
    note_path = os.path.join(args.out_dir, f'convert_{date}.txt')
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(f'input: {args.csv}\nrows: {len(rows)}  kept: {len(out)}  dropped(status): {dropped["status"]}  dropped(unfinished): {dropped["unfinished"]}\n')
        f.write(f'session.code: {session_code}  tz: {args.tz}  meta: {has_meta}  timing: {sorted(timing_cols)}\n')
        f.write(f'item order columns: {[c for c in header if c.endswith("_DO")]}\n')
        f.write('note: t_start = StartDate (survey opened), not consent submitted; rand_seed empty; git_commit = qsf_hash\n')
    print(f'wrote {out_path}: {len(out)} rows (dropped status {dropped["status"]}, unfinished {dropped["unfinished"]})')
    if pt_path:
        print(f'wrote {pt_path}: {len(page_rows)} rows')
    print(f'wrote {note_path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv', help='Qualtrics のエクスポート CSV（数値、表示順データ入り）')
    ap.add_argument('--out-dir', default='raw/main')
    ap.add_argument('--qsf', default=None, help='取り込んだ QSF（表示順の値が QID のとき tag に直す。session.code にも使う）')
    ap.add_argument('--date', default=None, help='出力ファイル名の日付（既定: 今日）')
    ap.add_argument('--tz', default='+09:00', help='Qualtrics アカウントのタイムゾーンのオフセット（既定 +09:00）')
    ap.add_argument('--session', default=None, help='session.code に入れる値（既定: QSF の SurveyID か qualtrics）')
    ap.add_argument('--include-preview', action='store_true', help='Status = 1（プレビュー）の行も残す（動作確認用）')
    ap.add_argument('--keep-unfinished', action='store_true', help='Finished = 0 の行も残す（既定は完了者だけ。方針: 未完了は保存しない）')
    ap.add_argument('--endowment', type=int, default=1000, help='cfg_endowment 列がないときの元手')
    ap.add_argument('--fee', type=int, default=300, help='cfg_fee 列がないときの参加謝礼')
    convert(ap.parse_args())


if __name__ == '__main__':
    main()
