#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CrowdWorks の承認待ち一覧と調査データの実験 ID を照合し、承認・非承認・要確認の表を作る（v0.6、計画書「募集と実施の運用」）。

研究室の 2025 年 6 月の事例（存在しない実験 ID が 37 件、同じ ID が 23 回入力）への対策。手作業の照合（「青木方式」）を置き換える。

使い方:
  python tools/match_cw_ids.py --cw <CW の承認待ち一覧（CSV / TSV / HTML）> --data <調査データ CSV> [--out payout] [--id-len 10]
      [--id-col 列名] [--user-col 列名] [--url-col 列名] [--work-col 列名] [--date YYYY-MM-DD]

  --cw    CrowdWorks の作業一覧。承認前なら「承認待ち作業一覧」のページを HTML で保存したもの、承認後は CSV（作業ID・作業者・作業者ページURL・
          承認日時・フォームの入力値）。列は自動判定（実験 ID = 値の多くが数字だけで作業ID でない列、作業者 = 見出しに「作業者」を含み URL でない列）。
          判定が外れたら --id-col などで指定する。文字コードは UTF-8 → CP932 の順に試す
  --data  Qualtrics のエクスポート CSV（先頭 3 行がヘッダー、exp_id・Finished・Status 列）か、oTree 形式の CSV（player.exp_id・player.finished）

判定（decision / reason）:
  approve  実験 ID が調査の完了回答に 1 対 1 で存在する（ok）
  check    調査に回答はあるが未完了（unfinished）、同じ ID の最初の入力（duplicate_first: ファイルの並びが入力順と仮定）、
           桁違い・1 文字違いで未申告の完了回答に近い（near: 入力ミスの可能性。手で確認）
  reject   調査に存在しない ID（not_found）、形式が違い近い ID もない（bad_format）、同じ ID の 2 件目以降（duplicate）
  承認の方針（計画書）: 微妙なときは承認する。注意チェック等の不合格は解析で除外するが承認はする。
  CW の規約では非承認にできる件数に上限がある（3 件か総数の 30% の大きいほう）→ 超えそうなら警告を出す

出力（--out 以下、日付付き）:
  match_<date>.csv       work_id, cw_user, cw_profile_url, entered_id, normalized_id, decision, reason, data_finished, response_id
  unclaimed_<date>.csv   調査には完了回答があるが CW に入力されていない実験 ID（時間切れ・申告漏れの候補。連絡があれば個別に発注）
  contacts_<date>.csv    承認した参加者の code（= 実験 ID）, cw_user, cw_profile_url, work_id → tools/pairing.py の --contacts に渡す
  summary_match_<date>.txt
"""
import argparse
import csv
import html as html_mod
import io
import os
import re
import sys
import unicodedata
from datetime import date


# ---------------------------------------------------------------------------
def read_text(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp932', 'utf-8'):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace'), 'utf-8(replace)'


def read_table(path):
    """CSV / TSV / HTML → (header, rows[list[str]])."""
    text, enc = read_text(path)
    if path.lower().endswith(('.html', '.htm')) or re.search(r'<table', text, re.I):
        return parse_html_table(text), enc
    delim = '\t' if path.lower().endswith('.tsv') or (text.count('\t') > text.count(',')) else ','
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise SystemExit(f'{path}: 空です')
    return (rows[0], rows[1:]), enc


def parse_html_table(text):
    """最初の <table> を読む（承認待ち一覧のページ）。<th> を見出し、<tr> の <td> を行にする。"""
    tables = re.findall(r'<table.*?</table>', text, re.S | re.I)
    if not tables:
        raise SystemExit('HTML に <table> がありません')
    best = max(tables, key=lambda t: len(re.findall(r'<tr', t, re.I)))
    header, rows = [], []
    for tr in re.findall(r'<tr.*?</tr>', best, re.S | re.I):
        ths = re.findall(r'<th.*?>(.*?)</th>', tr, re.S | re.I)
        tds = re.findall(r'<td.*?>(.*?)</td>', tr, re.S | re.I)
        if ths and not header:
            header = [clean_cell(c) for c in ths]
        elif tds:
            cells = []
            for c in tds:
                m = re.search(r'href="([^"]+employees/\d+[^"]*)"', c)
                cells.append(m.group(1) if m and not clean_cell(c) else clean_cell(c))
            rows.append(cells)
    if not header and rows:
        header = [f'col{i + 1}' for i in range(len(rows[0]))]
    return header, rows


def clean_cell(c):
    c = re.sub(r'<[^>]+>', '', c)
    return html_mod.unescape(c).strip()


def normalize_id(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[\s\-‐−–—_.:：、,，]', '', s)
    return s


def pick_col(header, rows, override, kind, id_len):
    """kind: 'id' | 'user' | 'url' | 'work'。見出しと値から列を推定する。"""
    if override:
        if override in header:
            return header.index(override)
        raise SystemExit(f'--{kind}-col {override!r} が見出しにありません: {header}')
    idx = None
    if kind == 'work':
        for i, h in enumerate(header):
            if re.search(r'作業\s*ID|work.?id', h, re.I):
                idx = i
                break
    elif kind == 'url':
        for i, h in enumerate(header):
            if re.search(r'URL|url', h) or any('employees/' in (r[i] if i < len(r) else '') for r in rows[:20]):
                idx = i
                break
    elif kind == 'user':
        for i, h in enumerate(header):
            if re.search(r'作業者|ユーザー|user|worker', h, re.I) and not re.search(r'URL|url|ID', h):
                idx = i
                break
    elif kind == 'id':
        # 作業ID 以外で、値の多くが数字だけ（長さが id_len に近い）の列
        best, best_score = None, 0
        for i, h in enumerate(header):
            if re.search(r'作業\s*ID|work.?id|URL|url|日時|date', h, re.I):
                continue
            vals = [normalize_id(r[i]) for r in rows if i < len(r) and (r[i] or '').strip()]
            if not vals:
                continue
            score = sum(1 for v in vals if v.isdigit() and abs(len(v) - id_len) <= 2) / len(vals)
            if re.search(r'ID|コード|code', h, re.I):
                score += 0.1
            if score > best_score:
                best, best_score = i, score
        idx = best if best_score >= 0.5 else None
    return idx


# ---------------------------------------------------------------------------
def read_data(path):
    """調査データ → dict exp_id → dict(finished=bool, response_id=str, status=str)。Qualtrics の生 CSV と oTree 形式の両方。"""
    text, enc = read_text(path)
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise SystemExit(f'{path}: 空です')
    header = rows[0]
    is_qualtrics = len(rows) > 2 and any('ImportId' in c for c in rows[2])
    body = rows[3:] if is_qualtrics else rows[1:]
    col = {h: i for i, h in enumerate(header)}

    def find(suffixes):
        for s in suffixes:
            for h, i in col.items():
                if h == s or h.endswith(s):
                    return i
        return None

    c_id = find(['exp_id', 'player.exp_id'])
    c_fin = find(['Finished', 'player.finished'])
    c_rid = find(['ResponseId', 'participant.code'])
    c_status = find(['Status']) if is_qualtrics else None
    if c_id is None:
        raise SystemExit(f'{path}: exp_id / player.exp_id 列がありません（v0.6 の調査データが必要）: {header[:10]}...')
    data = {}
    dup_in_data = []
    for r in body:
        if c_id >= len(r):
            continue
        eid = normalize_id(r[c_id])
        if not eid:
            continue
        if c_status is not None and c_status < len(r) and (r[c_status] or '0').strip() not in ('0', 'IP Address', ''):
            continue  # プレビュー・テスト・スパムの行は除く
        fin = (r[c_fin] or '').strip().lower() in ('1', 'true') if c_fin is not None and c_fin < len(r) else True
        rid = r[c_rid].strip() if c_rid is not None and c_rid < len(r) else ''
        if eid in data:
            dup_in_data.append(eid)
            data[eid]['finished'] = data[eid]['finished'] or fin
            continue
        data[eid] = dict(finished=fin, response_id=rid)
    return data, dup_in_data, enc, 'qualtrics' if is_qualtrics else 'otree'


def near(a, b):
    """1 文字の置換・挿入・削除の範囲か。"""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    for i in range(len(l)):
        if l[:i] + l[i + 1:] == s:
            return True
    return False


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cw', required=True, help='CrowdWorks の作業一覧（CSV / TSV / HTML）')
    ap.add_argument('--data', required=True, help='Qualtrics のエクスポート CSV か oTree 形式の CSV')
    ap.add_argument('--out', default='payout')
    ap.add_argument('--id-len', type=int, default=10, help='実験 ID の桁数（既定 10）')
    ap.add_argument('--id-col', default=None)
    ap.add_argument('--user-col', default=None)
    ap.add_argument('--url-col', default=None)
    ap.add_argument('--work-col', default=None)
    ap.add_argument('--date', default=date.today().isoformat())
    ap.add_argument('--dry-run', action='store_true', help='ファイルを書かずに summary だけ表示')
    args = ap.parse_args()

    (header, rows), enc_cw = read_table(args.cw)
    c_id = pick_col(header, rows, args.id_col, 'id', args.id_len)
    if c_id is None:
        raise SystemExit(f'実験 ID の列を判定できません。--id-col で指定してください: {header}')
    c_user = pick_col(header, rows, args.user_col, 'user', args.id_len)
    c_url = pick_col(header, rows, args.url_col, 'url', args.id_len)
    c_work = pick_col(header, rows, args.work_col, 'work', args.id_len)
    data, dup_in_data, enc_data, kind = read_data(args.data)

    def cell(r, i):
        return (r[i] if i is not None and i < len(r) else '').strip()

    entries = []
    for r in rows:
        entries.append(dict(work_id=cell(r, c_work), cw_user=cell(r, c_user), cw_profile_url=cell(r, c_url),
                            entered_id=cell(r, c_id), normalized_id=normalize_id(cell(r, c_id))))

    counts = {}
    for e in entries:
        counts[e['normalized_id']] = counts.get(e['normalized_id'], 0) + 1
    seen = set()
    claimed = set()
    for e in entries:
        nid = e['normalized_id']
        e['data_finished'] = ''
        e['response_id'] = ''
        if nid in data:
            e['data_finished'] = int(data[nid]['finished'])
            e['response_id'] = data[nid]['response_id']
        if counts[nid] > 1:
            if nid in data:
                claimed.add(nid)   # 誰かが申告した ID は未申告には数えない
            if nid in seen:
                e['decision'], e['reason'] = 'reject', f'duplicate ({counts[nid]} entries of the same ID)'
            else:
                e['decision'], e['reason'] = 'check', f'duplicate_first ({counts[nid]} entries; file order assumed = submission order)'
            seen.add(nid)
            continue
        if nid in data:
            claimed.add(nid)
            if data[nid]['finished']:
                e['decision'], e['reason'] = 'approve', 'ok'
            else:
                e['decision'], e['reason'] = 'check', 'unfinished (response exists but not finished; time-out?)'
            continue
        e['decision'], e['reason'] = 'reject', ('not_found' if nid.isdigit() and len(nid) == args.id_len else 'bad_format')

    # 近い ID（入力ミスの可能性）: 未申告の完了回答と 1 文字違いなら要確認にする
    unclaimed = [eid for eid, d in data.items() if eid not in claimed and d['finished']]
    for e in entries:
        if e['decision'] == 'reject' and e['reason'] in ('not_found', 'bad_format'):
            cands = [u for u in unclaimed if near(e['normalized_id'], u)]
            if len(cands) == 1:
                e['decision'], e['reason'] = 'check', f'near: {cands[0]} (1 character off; confirm by hand)'

    n = len(entries)
    n_app = sum(1 for e in entries if e['decision'] == 'approve')
    n_chk = sum(1 for e in entries if e['decision'] == 'check')
    n_rej = sum(1 for e in entries if e['decision'] == 'reject')
    cap = max(3, int(n * 0.3))
    summary = [
        f'date: {args.date}',
        f'cw file: {args.cw} ({enc_cw}; id column = {header[c_id]!r}, user = {header[c_user] if c_user is not None else "-"!r}, '
        f'url = {header[c_url] if c_url is not None else "-"!r}, work id = {header[c_work] if c_work is not None else "-"!r})',
        f'data file: {args.data} ({enc_data}, {kind}; responses with exp_id: {len(data)}, finished: {sum(1 for d in data.values() if d["finished"])})',
        f'CW entries: {n}  approve: {n_app}  check: {n_chk}  reject: {n_rej}',
        f'unclaimed finished responses (no CW entry): {len(unclaimed)}',
        f'duplicate exp_id inside the data file: {len(dup_in_data)}' + (f' {sorted(set(dup_in_data))}' if dup_in_data else ''),
        f'non-approval cap by CW terms (max(3, 30% of {n}) = {cap}): ' + ('OK' if n_rej <= cap else f'WARNING reject {n_rej} > {cap}'),
    ]
    print('\n'.join(summary))
    if args.dry_run:
        return 0

    os.makedirs(args.out, exist_ok=True)
    tag = args.date
    fields = ['work_id', 'cw_user', 'cw_profile_url', 'entered_id', 'normalized_id', 'decision', 'reason', 'data_finished', 'response_id']
    with open(os.path.join(args.out, f'match_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows([{k: e.get(k, '') for k in fields} for e in entries])
    with open(os.path.join(args.out, f'unclaimed_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['exp_id', 'response_id'])
        for u in sorted(unclaimed):
            w.writerow([u, data[u]['response_id']])
    with open(os.path.join(args.out, f'contacts_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['code', 'cw_user', 'cw_profile_url', 'work_id'])
        for e in entries:
            if e['decision'] == 'approve':
                w.writerow([e['normalized_id'], e['cw_user'], e['cw_profile_url'], e['work_id']])
    with open(os.path.join(args.out, f'summary_match_{tag}.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary) + '\n')
    print(f'written to {args.out}/ (match_{tag}.csv, unclaimed_{tag}.csv, contacts_{tag}.csv, summary_match_{tag}.txt)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
