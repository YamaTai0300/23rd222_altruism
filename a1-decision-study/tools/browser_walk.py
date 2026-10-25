"""Playwright で日本語版を最初から最後まで通し、スマホ幅（375px）でスクリーンショットを撮る（設計書 §10.2 の補助）。

使い方: 別ターミナルで `otree devserver 8010` を起動したうえで
  python tools/browser_walk.py shots a1_ja
要: pip install playwright && playwright install chromium
"""
import re, sys, os
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8010'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'shots'
CONFIG = sys.argv[2] if len(sys.argv) > 2 else 'a1_ja'
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=2, is_mobile=True, locale='ja-JP')
    page = ctx.new_page()
    page.goto(f'{BASE}/demo/{CONFIG}')
    page.wait_for_load_state('networkidle')
    links = page.locator('a[href*="InitializeParticipant"]')
    hrefs = [links.nth(i).get_attribute('href') for i in range(links.count())]
    print('participant links:', len(hrefs))
    page.goto(BASE + hrefs[0] if hrefs[0].startswith('/') else hrefs[0])
    page.wait_for_load_state('networkidle')

    seen = {}
    for step in range(50):
        url = page.url
        m = re.search(r'/study/(\w+)/\d+', url)
        name = m.group(1) if m else 'unknown'
        seen[name] = seen.get(name, 0) + 1
        tag = f'{step:02d}_{name}'
        print(step, name, url)
        if name == 'Consent':
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.click('text=次へ')  # 未チェック → エラー
            page.wait_for_load_state('networkidle')
            page.screenshot(path=f'{OUT}/{tag}_error.png', full_page=True)
            for cb in page.locator('input[type=checkbox]').all():
                cb.check()
            page.click('text=次へ')
        elif name == 'ParticipantCode':
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.click('text=次へ')
        elif name in ('SurveyIntroA', 'SurveyIntroB', 'DGIntroA', 'DGIntroB'):
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.click('text=次へ')
        elif name.startswith('SurveyPage'):
            radios = page.locator('input[type=radio]')
            names = sorted(set(radios.nth(i).get_attribute('name') for i in range(radios.count())))
            if seen[name] == 1:
                page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
                # 1 項目だけ未回答で送信 → エラー表示を確認
                for n in names[1:]:
                    page.check(f'input[name="{n}"][value="4"]')
                page.click('text=次へ')
                page.wait_for_load_state('networkidle')
                page.screenshot(path=f'{OUT}/{tag}_error.png', full_page=True)
                # 再表示後も選択が残っているか
                kept = sum(1 for n in names[1:] if page.is_checked(f'input[name="{n}"][value="4"]'))
                print('   kept after error:', kept, '/', len(names) - 1)
                page.check(f'input[name="{names[0]}"][value="2"]')
                page.click('text=次へ')
            else:
                for n in names:
                    page.check(f'input[name="{n}"][value="3"]')
                page.click('text=次へ')
        elif name.startswith('Demographics'):
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.fill('input[name=age]', '21')
            page.check('input[name=gender][value="2"]')
            page.select_option('select[name=grade]', 'B3')
            page.check('input[name=game_exp][value="False"]')
            page.click('text=次へ')
        elif name.startswith('DGCheck'):
            if seen[name] == 1:
                page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
                page.fill('input[name=dg_check]', '300')  # 誤答
                page.click('text=次へ')
                page.wait_for_load_state('networkidle')
                page.screenshot(path=f'{OUT}/{tag}_retry.png', full_page=True)
                page.fill('input[name=dg_check]', '700')
                page.click('text=次へ')
            else:
                page.fill('input[name=dg_check]', '700')
                page.click('text=次へ')
        elif name.startswith('DGPredict'):
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.fill('input[name=dg_predict]', '400')
            page.click('text=次へ')
        elif name.startswith('DGDecisionAgain'):
            # 入力確認で「いいえ」を選んだ後の再入力画面（v0.2）
            page.fill('input[name=dg_give]', '350')
            page.wait_for_timeout(200)
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.click('text=次へ')
        elif name.startswith('DGDecision'):
            page.fill('input[name=dg_give]', '300')
            page.wait_for_timeout(200)
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.click('text=次へ')
        elif name.startswith('DGConfirm'):
            # 1 回目は「いいえ」で再入力画面も撮る（v0.2）
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            page.check('input[name=dg_correct][value="2"]')
            page.click('text=次へ')
        elif name == 'PostSurvey':
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            radios = page.locator('input[type=radio]')
            names = sorted(set(radios.nth(i).get_attribute('name') for i in range(radios.count())))
            for n in names:
                page.check(f'input[name="{n}"][value="5"]')
            page.fill('textarea[name=comment_open]', 'テスト')
            page.click('text=次へ')
        elif name == 'End':
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            print('   contact link:', page.locator('a.btn').get_attribute('href'))
            break
        else:
            page.screenshot(path=f'{OUT}/{tag}.png', full_page=True)
            print('unknown page, stopping'); break
        page.wait_for_load_state('networkidle')
    b.close()
print('done')
