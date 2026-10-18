"""原研究（Binder et al., 2026）の独裁者ゲーム部分の再現 — oTree settings。

SESSION_CONFIGS は原研究の各研究の条件を表す。デモ画面で選んで「元の研究ではこうだった」を見せる。
金額は原研究のまま（10.70、基本支払い 5.00、定額 0.50 / 1.00、換算率 0.1）。
"""
from os import environ

_COMMON = dict(
    app_sequence=['original_dg'],
    num_demo_participants=3,
    endowment=10.70,        # DG の元手（原研究: $10.70 / €10.70 の「プレゼント」）
    base_payout=5.00,       # 一般教示の「基本支払い 5 ユーロ」（Study 03 付録 p.43）
    flat_fee=0.50,          # incentive = 'flat' のときのゲームごとの定額（Study 09: $0.50、Study 11: $1）
    conversion_rate=0.1,    # incentive = 'conversion' のときの換算率（Study 12, 13, 15: 1 決定を 1:0.1）
    waiting_seconds=6,      # 「最大 10 秒待つ」の再現（デモでは短め）
    post_evaluation=True,   # Study 11 の事後評価 6 項目
)

SESSION_CONFIGS = [
    dict(_COMMON, name='orig_study03_de', display_name='原研究 Study 03（独語原文・欺罔あり・架空のお金）',
         study_label='03', lang='de', currency_label='Euro', deception=True, incentive='none', confirm_entry=False),
    dict(_COMMON, name='orig_study09_en', display_name='原研究 Study 09（英語・欺罔なし・定額 $0.50・入力確認あり）',
         study_label='09', lang='en', currency_label='$', deception=False, incentive='flat', flat_fee=0.50, confirm_entry=True),
    dict(_COMMON, name='orig_study11_en', display_name='原研究 Study 11（英語・欺罔なし・定額 $1）',
         study_label='11', lang='en', currency_label='$', deception=False, incentive='flat', flat_fee=1.00, confirm_entry=False),
    dict(_COMMON, name='orig_study13_de', display_name='原研究 Study 13（独語・欺罔なし・1:0.1 換算）',
         study_label='13', lang='de', currency_label='Euro', deception=False, incentive='conversion', confirm_entry=False),
    dict(_COMMON, name='orig_study15_de', display_name='原研究 Study 15（独語・欺罔あり・1:0.1 換算）',
         study_label='15', lang='de', currency_label='Euro', deception=True, incentive='conversion', confirm_entry=False),
    dict(_COMMON, name='orig_ja_demo', display_name='原研究の和訳（説明用・Study 09 の条件）',
         study_label='09ja', lang='ja', currency_label='ドル', deception=False, incentive='flat', flat_fee=0.50, confirm_entry=True),
]

SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1.00, participation_fee=0.00, doc="")
PARTICIPANT_FIELDS = ['eval_error']
SESSION_FIELDS = []

LANGUAGE_CODE = environ.get('OTREE_LANGUAGE_CODE', 'ja')   # oTree の定型文（「次へ」など）。独語・英語で見せるときは環境変数で 'de' / 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ROOMS = []
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')
DEMO_PAGE_INTRO_HTML = """原研究（Binder et al., 2026）の独裁者ゲーム部分の再現。各設定は原研究の研究 03 / 09 / 11 / 13 / 15 の条件に対応。"""
SECRET_KEY = environ.get('OTREE_SECRET_KEY', 'dev-only-change-me')
INSTALLED_APPS = ['otree']
