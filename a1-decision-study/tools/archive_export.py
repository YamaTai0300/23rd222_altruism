#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""エクスポート CSV を「完了した回答だけ」にして raw/<purpose>/ に保存する（v0.4）。

方針（実験計画書「参加者」）: 一度始めた参加者には最後まで一度に回答してもらい、未完了の回答は保存しない。
oTree はページを進むたびに DB に書くので、未完了の行は管理画面のエクスポートには含まれる。
このスクリプトで finished == 1 の行だけを残した CSV を保存し、以降の解析・支払い・公開はその CSV だけを使う。
Page Times（管理画面 Data → Page Times）も同じ参加者だけに絞って保存する。

使い方:
  python tools/archive_export.py <altruism_study.csv> [--page-times <PageTimes-YYYY-MM-DD.csv>] [--purpose main|pilot] [--date YYYY-MM-DD]
出力:
  raw/<purpose>/altruism_study_<date>.csv     完了者のみ
  raw/<purpose>/PageTimes_<date>.csv          完了者のみ（--page-times を渡したとき）
  raw/<purpose>/archive_<date>.sha256         両ファイルの SHA-256 と行数
  標準出力に 行数（全体 / 完了 / 未完了）を表示。未完了の行は保存しない。
"""
import argparse
import csv
import hashlib
import os
import sys
from datetime import date


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        return list(r), r.fieldnames


def col(columns, suffix):
    for c in columns:
        if c == suffix or c.endswith('.' + suffix):
            return c
    raise SystemExit(f'列が見つかりません: {suffix}')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path, rows, fields):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv')
    ap.add_argument('--page-times', default=None)
    ap.add_argument('--purpose', default='main', choices=['main', 'pilot'])
    ap.add_argument('--date', default=date.today().isoformat())
    ap.add_argument('--out-root', default='raw')
    args = ap.parse_args()

    rows, fields = read_csv(args.csv)
    if not rows:
        raise SystemExit('データが空です')
    c_fin = col(fields, 'player.finished')
    c_code = col(fields, 'participant.code')
    finished = [r for r in rows if r[c_fin] in ('1', 'True', 'true')]
    codes = {r[c_code] for r in finished}
    out_dir = os.path.join(args.out_root, args.purpose)
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, f'altruism_study_{args.date}.csv')
    if os.path.exists(out_csv):
        raise SystemExit(f'既にあります: {out_csv}（上書きしない。--date を変えるか既存ファイルを確認）')
    write_csv(out_csv, finished, fields)
    lines = [f'{sha256(out_csv)}  {os.path.basename(out_csv)}  rows={len(finished)}']
    print(f'rows: all {len(rows)} / finished {len(finished)} / unfinished (not saved) {len(rows) - len(finished)}')
    print(f'written: {out_csv}')

    if args.page_times:
        prow, pfields = read_csv(args.page_times)
        c_pcode = col(pfields, 'participant_code')
        kept = [r for r in prow if r[c_pcode] in codes]
        out_pt = os.path.join(out_dir, f'PageTimes_{args.date}.csv')
        write_csv(out_pt, kept, pfields)
        lines.append(f'{sha256(out_pt)}  {os.path.basename(out_pt)}  rows={len(kept)}')
        print(f'page times: all {len(prow)} / kept {len(kept)}')
        print(f'written: {out_pt}')

    with open(os.path.join(out_dir, f'archive_{args.date}.sha256'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
