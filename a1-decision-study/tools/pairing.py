#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ペアリング・役割抽選・支払額の計算（設計書 §12.3、FR-19）。

使い方:
  python tools/pairing.py --data raw/altruism_study_2026-11-01.csv \
      --contacts raw/contacts_2026-11-01.csv --seed 20261101 \
      [--already-paid payout/sent_2026-10-25.csv] [--dry-run]

  元手と参加謝礼は CSV に記録された設定値（player.cfg_endowment, player.cfg_fee）から読む（v0.4）。
  データ内で値が 1 通りでなければ止まる（設定の違うセッションを混ぜない）。--endowment / --fee は
  古い CSV（cfg_* 列がない v0.3 以前）のための上書き用で、CSV の値と食い違うと警告して止まる（--force で続行）。

入力:
  --data      oTree 管理画面からエクスポートした CSV（altruism_study.csv または all_apps_wide.csv）
  --contacts  参加者コード + メールアドレスの CSV（v0.5 からは実験の外で集める: 参加者が終了画面のコードを申告する）。列名は自動判定
              （「コード」/ "code" を含む列、「メール」/ "mail" を含む列）。--code-col/--email-col で指定も可
  --seed      乱数シード（必須。summary.txt に記録される）
  --already-paid  支払い済みの参加者コードを含む CSV（週次バッチ運用のとき。code 列を読む）
  --session   対象とするセッションコード（予備実験と本実験のデータが同じ CSV に混ざるのを防ぐ。省略時は全セッション）

手順:
  1. finished == 1 の参加者を支払い対象にする（注意チェック等の除外フラグは支払いでは無視）
  2. 連絡先と code で結合。同じメールアドレスが複数の code に紐づく場合は t_end が最も早い code だけを残し、
     他は dup_list.csv に出す（支払い対象外）
  3. random.Random(seed) でシャッフルし、先頭から 2 人ずつペアにする。各ペアでコイン投げ（random）で sender を決める
  4. payout: sender = fee + endowment - dg_give、receiver = fee + dg_give（dg_give は sender の決定）
  5. 奇数のときは余った 1 名を receiver とし、ランダムに選んだ sender の dg_give を受け取る（その sender の支払いは変わらない）
  6. 連絡先のない完了者もペアには入れるが unreachable.csv に分けて出す（後日連絡）

出力（payout/ 以下、日付付き）:
  pairs_<date>.csv       pair_id, code, role, dg_give_applied, payout_yen, email, reachable
  dup_list_<date>.csv    重複と判定した code
  unreachable_<date>.csv 連絡先のない完了者
  summary_<date>.txt     人数・合計額・seed
"""
import argparse
import csv
import os
import random
import sys
from datetime import date


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def find_col(columns, suffix):
    """'player.dg_give' でも 'altruism_study.1.player.dg_give' でも拾う。"""
    for c in columns:
        if c == suffix or c.endswith('.' + suffix):
            return c
    raise SystemExit(f'列が見つかりません: {suffix}')


def guess_col(columns, keywords, override=None):
    if override:
        return override
    for c in columns:
        lc = c.lower()
        if any(k in lc for k in keywords):
            return c
    raise SystemExit(f'列を自動判定できません（候補: {keywords}）。--code-col / --email-col で指定してください: {columns}')


def config_value(rows, columns, suffix, override, label, force):
    """CSV の設定値列（cfg_*）から 1 つの値を取る。列がなければ override を使う。"""
    c = None
    for col in columns:
        if col == suffix or col.endswith('.' + suffix):
            c = col
            break
    vals = sorted({int(float(r[c])) for r in rows if c and r[c] not in ('', None)}) if c else []
    if len(vals) > 1:
        raise SystemExit(f'{label}: CSV の {suffix} に複数の値があります {vals}。セッションを --session で絞ってください')
    if vals:
        if override is not None and override != vals[0] and not force:
            raise SystemExit(f'{label}: 引数 {override} と CSV の記録値 {vals[0]} が食い違います（CSV の値を使うなら引数を外す。--force で引数を優先）')
        return override if (override is not None and force) else vals[0]
    if override is None:
        raise SystemExit(f'{label}: CSV に {suffix} 列がありません（v0.3 以前のデータ）。--{label} で指定してください')
    return override


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', required=True)
    ap.add_argument('--contacts', required=False, help='省略すると全員 unreachable 扱いで計算だけ行う')
    ap.add_argument('--seed', required=True, type=int)
    ap.add_argument('--endowment', type=int, default=None, help='CSV に cfg_endowment がないときだけ指定')
    ap.add_argument('--fee', type=int, default=None, help='CSV に cfg_fee がないときだけ指定')
    ap.add_argument('--force', action='store_true', help='CSV の設定値と引数が食い違っても引数の値で続行')
    ap.add_argument('--already-paid', default=None)
    ap.add_argument('--session', default=None, help='session.code で絞り込む')
    ap.add_argument('--code-col', default=None)
    ap.add_argument('--email-col', default=None)
    ap.add_argument('--out', default='payout')
    ap.add_argument('--dry-run', action='store_true', help='ファイルを書かずに summary だけ表示')
    args = ap.parse_args()

    rows = read_csv(args.data)
    if not rows:
        raise SystemExit('データが空です')
    cols = list(rows[0].keys())
    c_code = find_col(cols, 'participant.code')
    c_fin = find_col(cols, 'player.finished')
    c_give = find_col(cols, 'player.dg_give')
    c_tend = find_col(cols, 'player.t_end')

    if args.session:
        c_sess = find_col(cols, 'session.code')
        rows = [r for r in rows if r[c_sess] == args.session]
        if not rows:
            raise SystemExit(f'session.code == {args.session} の行がありません')
    completers = [r for r in rows if r[c_fin] in ('1', 'True', 'true')]
    # 元手と参加謝礼: CSV に記録された設定値を使う（v0.4）。複数の値が混ざっていたら止まる
    args.endowment = config_value(completers, cols, 'player.cfg_endowment', args.endowment, 'endowment', args.force)
    args.fee = config_value(completers, cols, 'player.cfg_fee', args.fee, 'fee', args.force)
    paid = set()
    if args.already_paid:
        for r in read_csv(args.already_paid):
            paid.add(r.get('code') or r.get('participant.code'))
    completers = [r for r in completers if r[c_code] not in paid]

    # 連絡先の結合と重複判定
    email_by_code = {}
    if args.contacts:
        crows = read_csv(args.contacts)
        ccols = list(crows[0].keys()) if crows else []
        cc = guess_col(ccols, ['code', 'コード'], args.code_col)
        ce = guess_col(ccols, ['mail', 'メール'], args.email_col)
        for r in crows:
            code = r[cc].strip()
            email = r[ce].strip().lower()
            if code and email and code not in email_by_code:
                email_by_code[code] = email
    tend = {r[c_code]: r[c_tend] for r in completers}
    by_email = {}
    for code, email in email_by_code.items():
        if code in tend:
            by_email.setdefault(email, []).append(code)
    dup = []
    for email, codes in by_email.items():
        if len(codes) > 1:
            codes.sort(key=lambda c: tend[c])
            dup.extend(codes[1:])
    dup = set(dup)
    eligible = [r for r in completers if r[c_code] not in dup]

    # ペアリング
    rng = random.Random(args.seed)
    people = [dict(code=r[c_code], give=int(r[c_give])) for r in eligible]
    rng.shuffle(people)
    pairs = []
    i = 0
    while i + 1 < len(people):
        a, b = people[i], people[i + 1]
        if rng.random() < 0.5:
            a, b = b, a
        pairs.append((a, b))  # (sender, receiver)
        i += 2
    leftover = people[i] if i < len(people) else None

    out = []
    for pid, (s, r) in enumerate(pairs, start=1):
        out.append(dict(pair_id=pid, code=s['code'], role='sender', dg_give_applied=s['give'],
                        payout_yen=args.fee + args.endowment - s['give']))
        out.append(dict(pair_id=pid, code=r['code'], role='receiver', dg_give_applied=s['give'],
                        payout_yen=args.fee + s['give']))
    if leftover is not None:
        if pairs:
            s, _ = rng.choice(pairs)
            give = s['give']
            note = f'odd: receives dg_give of sender {s["code"]}'
        else:
            give = 0
            note = 'odd: no sender available, fee only'
        out.append(dict(pair_id=len(pairs) + 1, code=leftover['code'], role='receiver',
                        dg_give_applied=give, payout_yen=args.fee + give, note=note))
    for o in out:
        o['email'] = email_by_code.get(o['code'], '')
        o['reachable'] = bool(o['email'])
        o.setdefault('note', '')

    total = sum(o['payout_yen'] for o in out)
    summary = [
        f'date: {date.today().isoformat()}',
        f'seed: {args.seed}',
        f'endowment: {args.endowment}  fee: {args.fee}',
        f'rows in data: {len(rows)}  finished: {len(completers) + len([c for c in paid])}  already paid: {len(paid)}',
        f'duplicates removed: {len(dup)}  eligible: {len(eligible)}  pairs: {len(pairs)}  leftover: {1 if leftover else 0}',
        f'senders: {sum(1 for o in out if o["role"] == "sender")}  receivers: {sum(1 for o in out if o["role"] == "receiver")}',
        f'unreachable (no email): {sum(1 for o in out if not o["reachable"])}',
        f'total payout (yen): {total}',
    ]
    print('\n'.join(summary))
    if args.dry_run:
        return

    os.makedirs(args.out, exist_ok=True)
    tag = date.today().isoformat()
    with open(os.path.join(args.out, f'pairs_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['pair_id', 'code', 'role', 'dg_give_applied', 'payout_yen', 'email', 'reachable', 'note'])
        w.writeheader()
        w.writerows(out)
    with open(os.path.join(args.out, f'dup_list_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['code', 'email'])
        for c in sorted(dup):
            w.writerow([c, email_by_code.get(c, '')])
    with open(os.path.join(args.out, f'unreachable_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['code', 'role', 'payout_yen'])
        for o in out:
            if not o['reachable']:
                w.writerow([o['code'], o['role'], o['payout_yen']])
    with open(os.path.join(args.out, f'summary_{tag}.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary) + '\n')
    print(f'written to {args.out}/')


if __name__ == '__main__':
    sys.exit(main())
