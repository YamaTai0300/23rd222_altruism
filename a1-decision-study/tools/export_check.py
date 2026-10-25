#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""エクスポート CSV の列名と値の範囲を analysis/codebook.csv と突合する（設計書 §13）。

使い方: python tools/export_check.py raw/altruism_study_2026-11-01.csv [--codebook analysis/codebook.csv]
終了コード 0 = 問題なし、1 = 問題あり（内容を表示）
"""
import argparse
import csv
import sys


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--codebook', default='analysis/codebook.csv')
    args = ap.parse_args()

    rows = read_csv(args.csv)
    cols = set(rows[0].keys()) if rows else set()
    # 'player.x' でも 'altruism_study.1.player.x'（all_apps_wide）でも x で引けるようにする
    short = {}
    for c in cols:
        if 'player.' in c:
            short[c.split('player.')[-1]] = c
    BUILTIN = {'id_in_group', 'payoff', 'role'}
    book = read_csv(args.codebook)
    problems = []

    for v in book:
        name = v['variable']
        if v.get('in_export', '1') != '1':
            continue
        col = short.get(name) or short.get(f'player.{name}')
        if col is None:
            problems.append(f'列がありません: {name}')
            continue
        lo, hi = v.get('min', ''), v.get('max', '')
        allowed = v.get('values', '')
        for i, r in enumerate(rows, start=2):
            val = r[col]
            if val == '':
                continue
            if lo != '' and hi != '':
                try:
                    x = float(val)
                except ValueError:
                    problems.append(f'{name} 行{i}: 数値でない値 {val!r}')
                    continue
                if not (float(lo) <= x <= float(hi)):
                    problems.append(f'{name} 行{i}: 範囲外 {val}')
                step = v.get('step', '')
                if step and x % float(step) != 0:
                    problems.append(f'{name} 行{i}: 刻み {step} でない値 {val}')
            elif allowed:
                if val not in allowed.split('|'):
                    problems.append(f'{name} 行{i}: 許容値以外 {val!r}（許容: {allowed}）')

    known = {v['variable'] for v in book}
    extra = sorted(c for c in cols if 'player.' in c and c.split('player.')[-1] not in known | BUILTIN)
    if extra:
        problems.append('コードブックにない player.* 列: ' + ', '.join(extra))

    print(f'rows: {len(rows)}  columns: {len(cols)}  codebook variables: {len(book)}')
    if problems:
        print('\n'.join(problems[:200]))
        if len(problems) > 200:
            print(f'... ほか {len(problems) - 200} 件')
        return 1
    print('OK: 列名と値の範囲はコードブックと一致しています')
    return 0


if __name__ == '__main__':
    sys.exit(main())
