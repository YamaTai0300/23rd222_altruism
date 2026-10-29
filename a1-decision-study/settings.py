"""oTree settings for the A-1 replication (Binder et al., 2026 → HG × Dictator Game).

設計書: https://claude.ai/code/artifact/5f9cc974-cbb4-4fd0-840b-7836e6283d47 §9
環境変数（本番）: OTREE_PRODUCTION, OTREE_AUTH_LEVEL, OTREE_ADMIN_PASSWORD, OTREE_SECRET_KEY, OTREE_REST_KEY, DATABASE_URL
"""
from os import environ

# 共通の設定。言語・金額はセッション作成画面でも変更できる。
_COMMON = dict(
    app_sequence=['altruism_study'],
    num_demo_participants=4,
    endowment=1000,              # DG の元手（円）
    dg_step=1,                   # DG の入力の刻み（円）。原研究は 0〜10.70 の任意の額を数値で入力（刻みなし）なので既定 1。
                                 # 100 にすると 100 円単位に制限される（入力欄の step と検証に反映）
    participation_fee_yen=300,   # 参加謝礼（円）。v0.5 から画面には出さない（リンク配布時に案内）。データに cfg_fee として記録し、pairing.py が使う
    use_hexaco=True,             # HEXACO-60 正直さ-謙虚さ 10 項目を 2 つ目の質問紙として入れる（v0.5: 原版と同じ 5 件法、FAB とは別の段階）
    # 順序割り当てと項目順の乱数シード。0 = セッションコードから決定的に導く（既定）。
    # 整数を入れるとその値を使う。どちらでも各回答の rand_seed 列に記録される（v0.3）
    rand_seed=0,
    app_version='v0.5-pilot',
    doc='A-1 追試: FAB・HEXACO 質問紙と独裁者ゲーム（一回完結・順序ランダム化・役割不確定法）',
)

SESSION_CONFIGS = [
    dict(_COMMON, name='a1_ja', display_name='A-1 日本語版（予備実験）', lang='ja', currency_label='円'),
    dict(_COMMON, name='a1_en', display_name='A-1 English version', lang='en', currency_label='yen'),
]

# oTree 標準の支払い計算は使わない（支払いは tools/pairing.py で計算する）
SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1.00, participation_fee=0.00, doc="")

# participant に保持する一時値（CSV には出ないので、分析に使う値は Player にも書く）
PARTICIPANT_FIELDS = ['fab_order', 'hex_order', 'survey_error']
SESSION_FIELDS = []

# oTree 自身の定型文（「次へ」ボタン、エラー文など）の言語。日本語版は 'ja'
LANGUAGE_CODE = 'ja'
REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = False

# 募集用の固定 URL（/room/<name>）。participant_label_file は使わない（誰でも参加できる）
#  demo  : 開発・デモ用。run_dev.bat がセッションを自動で用意し、何度でも使える URL を開く（v0.5）
#  pilot : 予備実験、main: 本実験
ROOMS = [
    dict(name='demo', display_name='A-1 デモ（開発用・使い回し）'),
    dict(name='pilot', display_name='A-1 予備実験'),
    dict(name='main', display_name='A-1 本実験'),
]
# run_dev.bat / tools/ensure_room.py が demo ルームに作るセッションの人数（この回数まで同じ URL で参加できる。足りなくなると次回起動時に作り直す）
DEMO_ROOM_PARTICIPANTS = 100

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """
A-1 追試（FAB・HEXACO 質問紙 × 独裁者ゲーム）の試作版 v0.5（画面を最低限に、質問紙を 2 段階に、進捗表示、使い回せるデモ URL）。
"""

SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'dev-only-change-me')

INSTALLED_APPS = ['otree']
