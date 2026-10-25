#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run ログ: エクスポート CSV からセッションごとの要約を docs/run_log.csv に追記・更新する（v0.3）。

実験計画書「記録・分析ノート・図表」の run ログ。収集した「すべての run（セッション）」を機械可読で残し、
設定（元手・刻み・HEXACO）や版（app_version・Git コミット・oTree）の違うデータが本分析に混ざるのを防ぐ。

使い方:
  python tools/run_log.py raw/final/altruism_study_2026-11-01.csv --purpose main
  python tools/run_log.py __temp_bots/altruism_study.csv --purpose bot-test --note "v0.3 のボットテスト"
  python tools/run_log.py raw/pilot/altruism_study_2026-10-28.csv --purpose pilot --session abc12345

  --purpose  pilot / main / bot-test / demo のいずれか（必須）
  --session  特定のセッションコードだけを記録（省略時は CSV 内の全セッション）
  --log      ログファイル（既定 docs/run_log.csv）
同じセッションコードの行があれば上書きする（最新のエクスポートの値で更新）。
"""
import argparse
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone

FIELDS = [
    'logged_at', 'session_code', 'purpose', 'lang', 'app_version', 'git_commit', 'otree_version', 'rand_seed',
    'endowment', 'dg_step', 'use_hexaco', 'n_rows', 'n_started', 'n_finished', 'n_excluded_in_app',
    'n_finished_order1', 'n_finished_order2', 'first_start_utc', 'last_end_utc', 'export_file', 'export_md5', 'note',
]
PURPOSES = ['pilot', 'main', 'bot-test', 'demo']


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def col(columns, suffix):
    """'player.dg_give' でも 'altruism_study.1.player.dg_give' でも拾う。"""
    for c in columns:
        if c == suffix or c.endswith('.' + suffix):
            return c
    return None


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def truthy(v):
    return str(v).strip() in ('1', 'True', 'true')


def first_value(rows, c):
    for r in rows:
        if c and r.get(c, '') != '':
            return r[c]
    return ''


def summarise(rows, cols, session_code, args, export_file, export_md5):
    g = lambda s: col(cols, s)  # noqa: E731
    c_fin, c_ts, c_te, c_exc, c_ord = g('player.finished'), g('player.t_start'), g('player.t_end'), g('player.excluded_in_app'), g('player.task_order')
    finished = [r for r in rows if c_fin and truthy(r[c_fin])]
    starts = sorted(r[c_ts] for r in rows if c_ts and r[c_ts])
    ends = sorted(r[c_te] for r in finished if c_te and r[c_te])
    return dict(
        logged_at=datetime.now(timezone.utc).isoformat(timespec='seconds'),
        session_code=session_code,
        purpose=args.purpose,
        lang=first_value(rows, g('player.lang')),
        app_version=first_value(rows, g('player.app_version')),
        git_commit=first_value(rows, g('player.git_commit')),
        otree_version=first_value(rows, g('player.otree_version')),
        rand_seed=first_value(rows, g('player.rand_seed')),
        endowment=first_value(rows, g('player.cfg_endowment')),
        dg_step=first_value(rows, g('player.cfg_dg_step')),
        use_hexaco=first_value(rows, g('player.cfg_use_hexaco')),
        n_rows=len(rows),
        n_started=len(starts),
        n_finished=len(finished),
        n_excluded_in_app=sum(1 for r in finished if c_exc and truthy(r[c_exc])),
        n_finished_order1=sum(1 for r in finished if c_ord and r[c_ord] == '1'),
        n_finished_order2=sum(1 for r in finished if c_ord and r[c_ord] == '2'),
        first_start_utc=starts[0] if starts else '',
        last_end_utc=ends[-1] if ends else '',
        export_file=os.path.basename(export_file),
        export_md5=export_md5,
        note=args.note,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--purpose', required=True, choices=PURPOSES)
    ap.add_argument('--session', default=None)
    ap.add_argument('--note', default='')
    ap.add_argument('--log', default='docs/run_log.csv')
    args = ap.parse_args()

    rows = read_csv(args.csv)
    if not rows:
        raise SystemExit('データが空です')
    cols = list(rows[0].keys())
    c_sess = col(cols, 'session.code')
    if c_sess is None:
        raise SystemExit('session.code 列がありません（oTree のエクスポート CSV を指定してください）')
    sessions = sorted({r[c_sess] for r in rows})
    if args.session:
        if args.session not in sessions:
            raise SystemExit(f'session.code == {args.session} の行がありません（含まれるもの: {sessions}）')
        sessions = [args.session]
    file_md5 = md5(args.csv)

    existing = read_csv(args.log) if os.path.exists(args.log) else []
    by_code = {r['session_code']: r for r in existing}
    for s in sessions:
        srows = [r for r in rows if r[c_sess] == s]
        rec = summarise(srows, cols, s, args, args.csv, file_md5)
        action = 'update' if s in by_code else 'add'
        by_code[s] = rec
        print(f'{action}: session {s}  purpose={rec["purpose"]}  app={rec["app_version"]}  git={rec["git_commit"]}  '
              f'seed={rec["rand_seed"]}  endowment={rec["endowment"]}  step={rec["dg_step"]}  '
              f'finished={rec["n_finished"]}/{rec["n_rows"]}  excluded_in_app={rec["n_excluded_in_app"]}')

    os.makedirs(os.path.dirname(args.log) or '.', exist_ok=True)
    with open(args.log, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator='\n')
        w.writeheader()
        for r in sorted(by_code.values(), key=lambda r: (r.get('first_start_utc', ''), r['session_code'])):
            w.writerow({k: r.get(k, '') for k in FIELDS})
    print(f'written: {args.log} ({len(by_code)} sessions)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
