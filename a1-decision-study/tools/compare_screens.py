"""v0.4 と v0.5 のスクリーンショットを左右に並べた比較 PDF を作る（研究室内の確認用）。"""
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OLD = sys.argv[1]   # v0.4 shots dir
NEW = sys.argv[2]   # v0.5 shots dir
OUT = sys.argv[3]   # output pdf

FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if not os.path.exists(FONT):
    FONT = glob.glob('/usr/share/fonts/opentype/noto/NotoSansCJK*.ttc')[0]
f_title = ImageFont.truetype(FONT, 34)
f_sub = ImageFont.truetype(FONT, 24)
f_note = ImageFont.truetype(FONT, 22)

W, H = 1700, 1900          # 1 ページのキャンバス（横長）
COL_W, COL_H = 760, 1660   # 画面の表示領域
TOP = 200


def find(d, pat):
    m = sorted(glob.glob(os.path.join(d, pat)))
    return m[0] if m else None


def place(canvas, path, x, note):
    draw = ImageDraw.Draw(canvas)
    if path is None:
        draw.rounded_rectangle([x, TOP, x + COL_W, TOP + 300], radius=16, outline='#999', width=3, fill='#f3f4f6')
        lines = note.split('\n')
        for i, ln in enumerate(lines):
            draw.text((x + 30, TOP + 40 + i * 40), ln, fill='#333', font=f_sub)
        return
    im = Image.open(path).convert('RGB')
    scale = COL_W / im.width
    nh = int(im.height * scale)
    im = im.resize((COL_W, nh))
    cropped = False
    if nh > COL_H:
        im = im.crop((0, 0, COL_W, COL_H))
        cropped = True
    canvas.paste(im, (x, TOP))
    draw.rectangle([x, TOP, x + COL_W, TOP + im.height], outline='#bbb', width=2)
    if cropped:
        draw.rectangle([x, TOP + COL_H - 44, x + COL_W, TOP + COL_H], fill='#fff3cd')
        draw.text((x + 16, TOP + COL_H - 40), '…（下に続く。全体は screens_v0.5_ja.pdf / screens_v0.2_ja.pdf を参照）', fill='#664d03', font=f_note)


ROWS = [
    ('1. 同意', find(OLD, '*_Consent.png'), find(NEW, '*_Consent.png'),
     '謝礼・連絡先の段落と「お問い合わせ」を削除。チェックは 2 つ（同意／18 歳以上かつ在籍）。所要時間 約 10 分。来歴の hidden 項目をここに移動'),
    ('2. 参加者コード（開始時）', find(OLD, '*_ParticipantCode.png'), None,
     'v0.5: 削除\nコードは終了画面にだけ表示'),
    ('3. 質問紙の教示ページ', find(OLD, '*_SurveyIntroA.png'), None,
     'v0.5: 削除\n各段階の 1 ページ目の上部に教示と選択肢の説明を統合'),
    ('4. 質問紙 1 ページ目（FAB + 注意チェック）', find(OLD, '*_SurveyPage1A.png'), find(NEW, '*_FabPage1A.png'),
     'v0.4 は FAB・注意チェック・HEXACO を一体で 27 項目（2 ページ）。v0.5 は FAB + 注意チェックの 17 項目を 2 ページ。進捗表示、行全体をタップ、回答済みの印'),
    ('5. 質問紙 1 ページ目（未回答エラー）', find(OLD, '*_SurveyPage1A_error.png'), find(NEW, '*_FabPage1A_error.png'),
     'v0.5: 未回答の項目まで自動スクロールし、回答済みの選択は残る（v0.4 と同じ）'),
    ('6. 質問紙 2 ページ目', find(OLD, '*_SurveyPage2A.png'), find(NEW, '*_FabPage2A.png'),
     'v0.5: 2 ページ目は短い教示だけ'),
    ('7. HEXACO 正直さ-謙虚さ（質問紙 2/2）', None, find(NEW, '*_Hex*A.png'),
     'v0.4: FAB と混ぜて 6 件法\nv0.5: 別の段階として 1 ページ、原版と同じ 5 件法。FAB との前後は参加者ごとにランダム'),
    ('8. 属性（年齢・性別・学年・経験）', find(OLD, '*_DemographicsA.png'), None,
     'v0.5: 削除'),
    ('9. 意思決定課題の説明', find(OLD, '*_DGIntroA.png'), find(NEW, '*_DGIntroA.png'),
     '「参加謝礼 {fee} 円と合わせて後日お支払い」の文を削除（謝礼の案内はリンク配布時）'),
    ('10. 理解確認', find(OLD, '*_DGCheckA.png'), find(NEW, '*_DGCheckA.png'),
     'v0.5: 説明を折りたたみでいつでも読み直せる。入力欄を大きく、自動フォーカス'),
    ('11. 理解確認（再回答）', find(OLD, '*_DGCheckA_retry.png'), find(NEW, '*_DGCheckA_retry.png'),
     'v0.5: 再回答時は説明を開いた状態で表示（v0.4 と同じ）'),
    ('12. 自己予測（決める前に）', find(OLD, '*_DGPredictA.png'), None,
     'v0.5: 削除'),
    ('13. 決定', find(OLD, '*_DGDecisionA.png'), find(NEW, '*_DGDecisionA.png'),
     'v0.5: 「次へ」で確定することを明記、自動フォーカス。取り分の即時表示は同じ'),
    ('14. 入力の確認', find(OLD, '*_DGConfirmA.png'), None,
     'v0.5: 削除（入力は 1 回で確定）'),
    ('15. 入力し直し', find(OLD, '*_DGDecisionAgainA.png'), None,
     'v0.5: 削除'),
    ('16. 事後評価', find(OLD, '*_PostSurvey.png'), find(NEW, '*_PostSurvey.png'),
     '項目は同じ。行全体をタップ、回答済みの印、自由記述欄を 3 行に'),
    ('17. 終了', find(OLD, '*_End.png'), find(NEW, '*_End.png'),
     'v0.5: 連絡先フォームのボタンと謝礼の説明を削除。参加者コードだけ表示'),
]

pages = []
for title, old, new, note in ROWS:
    c = Image.new('RGB', (W, H), 'white')
    d = ImageDraw.Draw(c)
    d.text((40, 30), title, fill='#111', font=f_title)
    d.text((40, 90), note, fill='#444', font=f_note)
    d.text((60, TOP - 40), 'v0.4（修正前）', fill='#555', font=f_sub)
    d.text((60 + COL_W + 80, TOP - 40), 'v0.5（修正後）', fill='#0b5ed7', font=f_sub)
    place(c, old, 60, 'v0.4: この画面はない')
    place(c, new, 60 + COL_W + 80, note if new is None else '')
    pages.append(c)

cover = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(cover)
d.text((60, 80), 'A-1 実験プログラム 画面の比較: v0.4 → v0.5', fill='#111', font=ImageFont.truetype(FONT, 44))
lines = [
    '左 = v0.4（修正前、a1-decision-study/）、右 = v0.5（修正後、a1-decision-study_v0.5/）。日本語版、スマホ幅 375px。',
    '長い画面は上部だけを表示（全体は docs/screens_v0.5_ja.pdf と a1-decision-study/docs/screens_v0.2_ja.pdf）。',
    '',
    '参加者が通るページ数: v0.4 = 13（入力し直しを含めて 14）→ v0.5 = 9',
    '  v0.4: 同意 → コード → 質問紙教示 → 質問紙 1 → 質問紙 2 → 属性 → DG 説明 → 理解確認 → 自己予測',
    '        → 決定 → 入力確認 →(入力し直し)→ 事後評価 → 終了',
    '  v0.5: 同意 → 質問紙 1/2（2 ページ）+ 質問紙 2/2（1 ページ。FAB と HEXACO の順はランダム）',
    '        → DG 説明 → 理解確認 → 決定 → 事後評価 → 終了（順序群 2 では DG が質問紙の前）',
    '',
    '主な変更: 謝礼・連絡先の案内の削除、参加者コードは終了画面のみ、属性・自己予測・入力確認の削除、',
    '  FAB と HEXACO の 2 段階化（HEXACO は 5 件法、段階順ランダム）、進捗表示、未回答項目への自動スクロール、',
    '  選択肢の行全体をタップ、回答済みの印、教示ページの統合、理解確認で説明を読み直せる折りたたみ、',
    '  使い回せるデモ用リンク（run_dev.bat）。',
    '',
    '文言とコードの差分一覧: docs/compare_v0.4_v0.5.md',
]
for i, ln in enumerate(lines):
    d.text((60, 180 + i * 46), ln, fill='#333', font=f_sub)
pages.insert(0, cover)
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=120)
print('wrote', OUT, len(pages), 'pages')
