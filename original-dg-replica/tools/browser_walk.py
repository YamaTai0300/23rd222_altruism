"""Playwright で 1 設定を最初から最後まで通し、スマホ幅（375px）のスクリーンショットを撮る。

使い方: 別ターミナルで `otree devserver 8020` を起動したうえで
  python tools/browser_walk.py <出力フォルダー> <config名> [next_button_text]
例:   python tools/browser_walk.py shots orig_ja_demo 次へ
      OTREE_LANGUAGE_CODE=de otree devserver 8020 → python tools/browser_walk.py shots_de orig_study03_de Weiter
要: pip install playwright && playwright install chromium
"""
import os, re, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get('OTREE_BASE', 'http://localhost:8020')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'shots'
CONFIG = sys.argv[2] if len(sys.argv) > 2 else 'orig_ja_demo'
NEXT = sys.argv[3] if len(sys.argv) > 3 else '次へ'
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or None)
    ctx = b.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2, is_mobile=True)
    page = ctx.new_page()
    page.goto(f'{BASE}/demo/{CONFIG}')
    page.wait_for_load_state('networkidle')
    links = page.locator('a[href*="InitializeParticipant"]')
    href = links.nth(0).get_attribute('href')
    page.goto(BASE + href if href.startswith('/') else href)
    page.wait_for_load_state('networkidle')
    seen = {}
    for step in range(40):
        m = re.search(r'/orig/(\w+)/\d+', page.url)
        name = m.group(1) if m else 'unknown'
        seen[name] = seen.get(name, 0) + 1
        tag = f'{step:02d}_{name}' + ('_again' if seen[name] > 1 else '')
        print(step, name, page.url)
        page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
        if name == 'Consent':
            for cb in page.locator('input[type=checkbox]').all():
                cb.check()
            page.click(f'text={NEXT}')
        elif name in ('Disclosure', 'DGResult', 'Debrief'):
            page.click(f'text={NEXT}')
        elif name == 'GeneralInstructions':
            page.fill('input[name=username]', 'Pegasus')
            page.click(f'text={NEXT}')
        elif name == 'Waiting':
            page.wait_for_url(re.compile(r'/orig/DGDecision/'), timeout=20000)
            continue
        elif name == 'DGDecision':
            page.fill('input[name=dg_give]', '3.50')
            page.screenshot(path=f'{OUT}/{tag}_filled.png', full_page=True)
            page.click(f'text={NEXT}')
        elif name == 'DGConfirm':
            page.check('input[name=dg_correct][value="2"]' if seen[name] == 1 else 'input[name=dg_correct][value="1"]')
            page.click(f'text={NEXT}')
        elif name == 'DGDecisionAgain':
            page.fill('input[name=dg_give]', '4.00')
            page.click(f'text={NEXT}')
        elif name == 'Evaluation':
            radios = page.locator('input[type=radio]')
            names = sorted(set(radios.nth(i).get_attribute('name') for i in range(radios.count())))
            for n in names:
                page.check(f'input[name="{n}"][value="5"]')
            page.click(f'text={NEXT}')
        elif name == 'Demographics':
            page.check('input[name=gender][value="2"]')
            page.fill('input[name=age]', '30')
            page.select_option('select[name=edu]', '12')
            page.click(f'text={NEXT}')
        elif name == 'End':
            break
        else:
            print('unknown page, stopping'); break
        page.wait_for_load_state('networkidle')
    b.close()
print('done')
