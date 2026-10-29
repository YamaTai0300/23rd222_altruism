"""Playwright で最初から最後まで通し、スマホ幅（375px）でスクリーンショットを撮る（設計書 §10.2 の補助）v0.5。

使い方: 別ターミナルで `otree devserver 8010` を起動したうえで
  python tools/browser_walk.py shots a1_ja [--base http://localhost:8010] [--participants 4] [--pdf docs/screens_v0.5_ja.pdf]
要: pip install playwright pillow && playwright install chromium

デモページ（/demo/<config>）の参加者リンクを順に開く。順序群（task_order）と質問紙の段階順（scale_order）は
参加者ごとに違うので、既定で 4 人分を通し、画面の種類ごとに最初に出てきたものを撮る（全種類が揃う）。
--pdf を付けると撮った PNG を 1 つの PDF にまとめる（ページ順）。
"""
import argparse
import os
import re
import sys

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('out', nargs='?', default='shots')
ap.add_argument('config', nargs='?', default='a1_ja')
ap.add_argument('--base', default='http://localhost:8010')
ap.add_argument('--participants', type=int, default=4)
ap.add_argument('--pdf', default=None)
ap.add_argument('--next', default=None, help='「次へ」ボタンの文言（既定: ja → 次へ, en → Next）')
args = ap.parse_args()
OUT, CONFIG, BASE = args.out, args.config, args.base
NEXT = args.next or ('次へ' if CONFIG.endswith('ja') else 'Next')
os.makedirs(OUT, exist_ok=True)

shot_files = []
seen_types = set()


def shot(page, name, suffix=''):
    path = f'{OUT}/{len(shot_files):02d}_{name}{suffix}.png'
    page.screenshot(path=path, full_page=True)
    shot_files.append(path)
    print('   shot', path)


def page_type(name):
    """画面の種類（A/B と First/Last を無視）。同じ種類は 1 回だけ撮る。"""
    return re.sub(r'(First|Last)?[AB]$', '', name)


def walk(page, href, take_shots):
    page.goto(BASE + href if href.startswith('/') else href)
    page.wait_for_load_state('networkidle')
    seq = []
    for step in range(40):
        url = page.url
        m = re.search(r'/study/(\w+)/\d+', url)
        name = m.group(1) if m else 'unknown'
        ptype = page_type(name)
        first = take_shots and ptype not in seen_types
        if first:
            seen_types.add(ptype)
        seq.append(name)
        print(step, name, url)
        if name == 'Consent':
            if first:
                shot(page, name)
                page.click('button.otree-btn-next')  # 未チェック → エラー
                page.wait_for_load_state('networkidle')
                shot(page, name, '_error')
            for cb in page.locator('input[type=checkbox]').all():
                cb.check()
            page.click('button.otree-btn-next')
        elif name.startswith('FabPage') or name.startswith('Hex'):
            radios = page.locator('input[type=radio]')
            names = sorted(set(radios.nth(i).get_attribute('name') for i in range(radios.count())))
            value = '3'
            if first:
                shot(page, name)
                # 1 項目だけ未回答で送信 → エラー表示と自動スクロールを確認
                for n in names[1:]:
                    page.check(f'input[name="{n}"][value="{value}"]')
                page.click('button.otree-btn-next')
                page.wait_for_load_state('networkidle')
                shot(page, name, '_error')
                kept = sum(1 for n in names[1:] if page.is_checked(f'input[name="{n}"][value="{value}"]'))
                print('   kept after error:', kept, '/', len(names) - 1)
                page.check(f'input[name="{names[0]}"][value="2"]')
            else:
                for n in names:
                    page.check(f'input[name="{n}"][value="{value}"]')
            page.click('button.otree-btn-next')
        elif name.startswith('DGIntro'):
            if first:
                shot(page, name)
            page.click('button.otree-btn-next')
        elif name.startswith('DGCheck'):
            if first:
                shot(page, name)
                page.fill('input[name=dg_check]', '300')  # 誤答
                page.click('button.otree-btn-next')
                page.wait_for_load_state('networkidle')
                shot(page, name, '_retry')
            page.fill('input[name=dg_check]', '700')
            page.click('button.otree-btn-next')
        elif name.startswith('DGDecision'):
            page.fill('input[name=dg_give]', '300')
            page.wait_for_timeout(200)
            if first:
                shot(page, name)
            page.click('button.otree-btn-next')
        elif name == 'PostSurvey':
            if first:
                shot(page, name)
            radios = page.locator('input[type=radio]')
            names = sorted(set(radios.nth(i).get_attribute('name') for i in range(radios.count())))
            for n in names:
                page.check(f'input[name="{n}"][value="5"]')
            page.fill('textarea[name=comment_open]', 'テスト' if CONFIG.endswith('ja') else 'test')
            page.click('button.otree-btn-next')
        elif name == 'End':
            if first:
                shot(page, name)
            break
        else:
            shot(page, name, '_unknown')
            print('unknown page, stopping')
            break
        page.wait_for_load_state('networkidle')
    return seq


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2, is_mobile=True,
                        locale='ja-JP' if CONFIG.endswith('ja') else 'en-US')
    page = ctx.new_page()
    page.goto(f'{BASE}/demo/{CONFIG}')
    page.wait_for_load_state('networkidle')
    links = page.locator('a[href*="InitializeParticipant"]')
    hrefs = [links.nth(i).get_attribute('href') for i in range(links.count())]
    print('participant links:', len(hrefs))
    for i, href in enumerate(hrefs[:args.participants]):
        print(f'--- participant {i + 1}')
        seq = walk(page, href, take_shots=True)
        print('   sequence:', ' > '.join(seq), f'({len(seq)} pages)')
    b.close()

if args.pdf and shot_files:
    from PIL import Image

    imgs = [Image.open(f).convert('RGB') for f in shot_files]
    os.makedirs(os.path.dirname(args.pdf) or '.', exist_ok=True)
    imgs[0].save(args.pdf, save_all=True, append_images=imgs[1:], resolution=144)
    print('pdf:', args.pdf, len(imgs), 'pages')
print('done')
