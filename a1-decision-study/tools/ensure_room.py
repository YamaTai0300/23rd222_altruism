"""何度でも使えるデモ用リンクを用意する（v0.5）。

oTree の Room（settings.py の ROOMS、既定 'demo'）にセッションを作り、2 種類のリンクを表示する:

  (1) 使い回しリンク  http://localhost:<port>/join/<code>
      開くたびに新しい参加者として最初から始まる。デモ・動作確認はこれを使う。
      セッションの人数（settings.DEMO_ROOM_PARTICIPANTS、既定 100）だけ使える。
  (2) 固定リンク      http://localhost:<port>/room/demo
      本実験と同じ URL の形。同じブラウザで開き直すと続きから再開する（別のブラウザ・シークレットウィンドウ・
      スマホからは新しい参加者）。サーバーを再起動して新しいセッションを作ると、同じブラウザでも最初からになる。

使い方（run_dev.bat が自動で呼ぶ。手動なら devserver を起動したうえで）:
  python tools/ensure_room.py --port 8000 --open            # 新しいセッションを作って (1) をブラウザで開く
  python tools/ensure_room.py --port 8000 --reuse           # Room に既にセッションがあればそれを使う
  python tools/ensure_room.py --port 8000 --config a1_en    # 英語版

REST API を使う。本番（OTREE_AUTH_LEVEL を設定）では環境変数 OTREE_REST_KEY が必要。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_participants():
    try:
        sys.path.insert(0, ROOT)
        import settings  # noqa: E402

        return int(getattr(settings, 'DEMO_ROOM_PARTICIPANTS', 100))
    except Exception:
        return 100


def api(base, path, payload=None):
    headers = {'Content-Type': 'application/json'}
    key = os.environ.get('OTREE_REST_KEY')
    if key:
        headers['otree-rest-key'] = key
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, headers=headers, method='POST' if data else 'GET')
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode() or 'null')


def wait_for_server(base, seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            api(base, '/api/otree_version')
            return True
        except Exception:
            time.sleep(2)
    return False


def localhost(url, port):
    # REST は 127.0.0.1 で返すので、表示・ブラウザ用に localhost に揃える
    return url.replace(f'127.0.0.1:{port}', f'localhost:{port}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--room', default='demo')
    ap.add_argument('--config', default='a1_ja', help='session config name (a1_ja / a1_en)')
    ap.add_argument('--participants', type=int, default=None, help='既定は settings.DEMO_ROOM_PARTICIPANTS')
    ap.add_argument('--reuse', action='store_true', help='Room に既にセッションがあればそれを使う（既定: 毎回新しく作る）')
    ap.add_argument('--open', action='store_true', help='使い回しリンクをブラウザで開く')
    ap.add_argument('--wait', type=int, default=300, help='サーバーの起動を待つ秒数')
    ap.add_argument('--log', default=None, help='リンクを書き出すテキストファイル')
    args = ap.parse_args()

    base = f'http://127.0.0.1:{args.port}'
    if not wait_for_server(base, args.wait):
        print(f'[ensure_room] server did not answer on port {args.port} within {args.wait} s', file=sys.stderr)
        sys.exit(1)

    n = args.participants or default_participants()
    session = None
    if args.reuse:
        rooms = {r['name']: r for r in api(base, '/api/rooms')}
        code = rooms.get(args.room, {}).get('session_code')
        if code:
            for s in api(base, '/api/sessions'):
                if s['code'] == code:
                    session = s
                    break
    if session is None:
        session = api(base, '/api/sessions', dict(session_config_name=args.config, num_participants=n, room_name=args.room))
        session['config_name'] = args.config
        session['num_participants'] = n
        made = 'created'
    else:
        made = 'reused'

    join = localhost(session['session_wide_url'], args.port)
    room = localhost(session.get('room_url', f'{base}/room/{args.room}'), args.port)
    admin = localhost(session['admin_url'], args.port)
    lines = [
        f"[ensure_room] {made} session {session['code']} ({session.get('config_name')}, {session.get('num_participants')} participants) in room '{args.room}'",
        f'  (1) reusable link  (new participant every time it is opened): {join}',
        f'  (2) fixed link     (same URL as the real study; same browser resumes):   {room}',
        f'  admin (links / data):                                                 {admin}',
    ]
    text = '\n'.join(lines)
    print(text)
    if args.log:
        with open(args.log, 'w', encoding='utf-8') as f:
            f.write(text + '\n')
    if args.open:
        webbrowser.open(join)


if __name__ == '__main__':
    main()
