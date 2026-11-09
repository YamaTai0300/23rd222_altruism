"""A-1 追試: FAB 質問紙 × HEXACO × 独裁者ゲーム（一回完結・順序ランダム化・役割不確定法）v0.6

設計書: https://claude.ai/code/artifact/5f9cc974-cbb4-4fd0-840b-7836e6283d47
原資料: https://osf.io/t5mf2/（Binder et al., 2026 の補足資料。CHANGELOG.md に対応表）
- 全画面を 1 つのアプリ（1 ラウンド）に置き、順序の分岐は is_displayed で行う（§4）
- WaitPage・グループは使わない。各参加者は自分のペースで最後まで進む（FR-25）
- 文言は texts/ から引く。テンプレートに文言を書かない（§8）
- 変数名は原研究の整形済みデータ（Studies/XX/XX_data.csv）に合わせる: hg_1 … mc_23, cq1, cq2, dg_give
- v0.6: CrowdWorks 募集に合わせた（研究室マニュアル）。参加資格を「18 歳以上・日本語が母語」に、終了画面に 10 桁の実験 ID
  （player.exp_id、セッション作成時に secrets で発行、セッション内で一意）を表示。参加者はそれを CW のフォームに入力し、
  tools/match_cw_ids.py で CW の承認待ち一覧と照合する。participant.code は内部用に残す
- v0.5: 画面を実験に必要な最低限にした（同意 → 質問紙 2 段階 → DG 説明・理解確認・決定 → 事後評価 → 終了。順序群で前後が入れ替わる）。
  謝礼・連絡先の案内、参加者コードの前置きページ、属性、自己予測、入力確認を外した（案内はリンク配布時に伝える）。
  質問紙を FAB（+注意チェック、6 件法、2 ページ）と HEXACO（5 件法、1 ページ）の 2 段階にし、段階の順序 scale_order も
  参加者ごとにランダム化（task_order と 2×2 でブロック）。各ページに進捗を表示
- v0.4: HEXACO 正直さ-謙虚さ 10 項目を採用。cfg_fee を記録
- v0.3: 各回答に来歴（app_version, git_commit, otree_version, 設定値, 乱数シード, ブラウザ, 画面幅）を記録し、
  順序割り当てと項目順のランダム化を seed 付きで再現できるようにした（実験計画書「記録・分析ノート・図表」）
"""
import hashlib
import os
import random
import secrets
import subprocess
from datetime import datetime, timezone

from otree.api import *

from .texts import fill, texts

try:
    import otree as _otree
    OTREE_VERSION = getattr(_otree, '__version__', 'unknown')
except Exception:  # pragma: no cover
    OTREE_VERSION = 'unknown'


def _git_commit():
    """起動時のコードの Git コミット（短縮ハッシュ）。環境変数 A1_GIT_COMMIT が優先。
    run_dev.bat は OneDrive 外にコピーして起動するので .git がない → run_dev.bat が環境変数に入れる。"""
    env = os.environ.get('A1_GIT_COMMIT')
    if env:
        return env.strip()[:40]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        out = subprocess.run(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=root, capture_output=True,
                             text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True, timeout=5)
            return out.stdout.strip() + ('-dirty' if dirty.stdout.strip() else '')
    except Exception:
        pass
    return 'unknown'


GIT_COMMIT = _git_commit()

doc = """
Binder et al. (2026) の Help Giving → 独裁者ゲームの関連を日本の CrowdWorks ワーカーで再現する一回完結のオンライン実験。
質問紙（FAB 15 項目 + 注意チェック 2、HEXACO 正直さ-謙虚さ 10 項目）と意思決定課題（DG, 元手は session config）の
順序、および 2 つの質問紙の順序を参加者ごとにランダム化する。
"""


class C(BaseConstants):
    NAME_IN_URL = 'study'  # URL に課題の性質を出さない（FR-13）
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    # FAB 15 項目。原研究の変数名（Supplement S1 / analysis.Rmd の cfa_model と同じ）
    HG_FIELDS = ['hg_1', 'hg_3', 'hg_7', 'hg_10', 'hg_13']
    PP_FIELDS = ['pp_1', 'pp_8', 'pp_12', 'pp_14', 'pp_15']
    MC_FIELDS = ['mc_1', 'mc_3', 'mc_18', 'mc_20', 'mc_23']
    FAB_FIELDS = HG_FIELDS + PP_FIELDS + MC_FIELDS
    # 注意チェック（原研究の control question）。cq1 = strongly disagree (1), cq2 = strongly agree (6)
    CQ_FIELDS = ['cq1', 'cq2']
    CQ_EXPECTED = dict(cq1=1, cq2=6)
    # HEXACO-60 正直さ-謙虚さ 10 項目（v0.5: 原版と同じ 5 件法で、FAB とは別の段階として提示）
    HEX_FIELDS = [f'hex_{i}' for i in range(1, 11)]
    EVAL_FIELDS = ['eval_understand', 'eval_difficult', 'eval_reflect', 'eval_distract']
    LIKERT6 = [1, 2, 3, 4, 5, 6]
    LIKERT5 = [1, 2, 3, 4, 5]
    CHECK_GIVE = 300  # 理解確認「300 円を分けると取り分は？」
    FAB_PAGES = 2     # FAB + 注意チェック 17 項目を 2 ページに分ける


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def likert_field(choices=C.LIKERT6):
    # blank=True にして必須チェックは error_message で行う。
    # こうすると未回答があっても回答済みの値を保存でき、再表示時に選択が消えない。
    return models.IntegerField(choices=choices, blank=True)


def endowment(player):
    return player.session.config['endowment']


def step(player):
    return player.session.config['dg_step']


def use_hexaco(player):
    return bool(player.session.config['use_hexaco'])


def dg_give_error_message(player, value):
    """DG の金額入力の検証: 0〜endowment、dg_step の倍数。"""
    if value is None or value < 0 or value > endowment(player) or value % step(player) != 0:
        return texts(player)['amount_error']


def fab_fields(player, page_no):
    """FAB 段階の page_no（1 or 2）に表示するフィールド名。順序は creating_session で確定済み。"""
    items = list(player.participant.fab_order)
    half = (len(items) + 1) // 2
    return items[:half] if page_no == 1 else items[half:]


def hex_fields(player):
    return list(player.participant.hex_order)


def visible_pages(player):
    """この参加者が実際に通るページの page_sequence 上の位置（1 始まり）。進捗表示に使う。"""
    out = []
    for i, pg in enumerate(page_sequence, start=1):
        pred = pg.__dict__.get('is_displayed')  # 自分で定義した staticmethod だけを評価（基底の既定は常に表示）
        if pred is None or pred(player):
            out.append(i)
    return out


def progress(player):
    """進捗（現在のページ番号 / この参加者が通るページ数）。oTree の _index_in_pages は page_sequence 上の 1 始まりの位置。"""
    idx = player.participant._index_in_pages or 1
    vis = visible_pages(player)
    pos = vis.index(idx) + 1 if idx in vis else len(vis)
    return dict(page=pos, pages=len(vis), percent=int(round(100 * pos / max(len(vis), 1))))


def ctx(player, **extra):
    """全ページ共通のテンプレート変数（文言 T と進捗）。"""
    T = texts(player)
    pr = progress(player)
    d = dict(T=T, progress=pr, progress_text=fill(T['progress_label'], page=pr['page'], pages=pr['pages']))
    d.update(extra)
    return d


def likert_items(player, fields, labels_src, scale_labels, choices, highlight):
    items = []
    for f in fields:
        val = player.field_maybe_none(f)
        items.append(
            dict(
                name=f,
                text=labels_src[f],
                missing=highlight and val is None,
                options=[dict(v=v, label=scale_labels[v - 1], checked=(val == v)) for v in choices],
            )
        )
    return items


def stage_numbers(player):
    """FAB と HEXACO の段階番号（1 or 2）。HEXACO を使わないときは FAB だけ（段階数 1）。"""
    if not use_hexaco(player):
        return dict(fab=1, hex=None, stages=1)
    so = player.scale_order
    return dict(fab=1 if so == 1 else 2, hex=2 if so == 1 else 1, stages=2)


def survey_vars(player, kind, page_no):
    """質問紙ページ（kind = 'fab' / 'hex'）のテンプレート変数。
    段階の最初のページには教示文と選択肢の説明を出し、2 ページ目以降は短い教示だけにする（v0.5）。"""
    T = texts(player)
    highlight = bool(player.participant.survey_error)
    player.participant.survey_error = False
    st = stage_numbers(player)
    if kind == 'fab':
        fields, labels, choices = fab_fields(player, page_no), T['likert6'], C.LIKERT6
        intro, intro_short, num_pages, stage = T['fab_intro'], T['fab_intro_short'], C.FAB_PAGES, st['fab']
    else:
        fields, labels, choices = hex_fields(player), T['likert5'], C.LIKERT5
        intro, intro_short, num_pages, stage = T['hex_intro'], T['hex_intro_short'], 1, st['hex']
    items = likert_items(player, fields, T['items'], labels, choices, highlight)
    title = fill(T['survey_stage_title'], stage=stage, stages=st['stages']) if st['stages'] > 1 else T['survey_title']
    page_note = fill(T['survey_page_note'], page=page_no, pages=num_pages) if num_pages > 1 else ''
    return ctx(
        player,
        items=items,
        stage_title=title,
        page_note=page_note,
        first_page=(page_no == 1),
        intro=intro,
        intro_short=intro_short,
        scale_labels=[dict(v=v, label=labels[v - 1]) for v in choices],
    )


def survey_error_message(player, values):
    """未回答チェック。回答済みの値は保存してから、未回答フィールドにエラーを付ける。"""
    missing = {}
    for f, v in values.items():
        if v is None:
            missing[f] = texts(player)['required_error']
        else:
            setattr(player, f, v)
    if missing:
        player.participant.survey_error = True
        return missing


def intro_blocks(T):
    """DG 説明の段落。3 段落目の直後に 2 つの選択肢（原研究の「1. 全額保持 2. 分ける」）を箇条書きで入れる。"""
    return [dict(text=p, options=(T['dg_options'] if i == 2 else None)) for i, p in enumerate(T['dg_intro_body'])]


# ---------------------------------------------------------------------------
# モデル
# ---------------------------------------------------------------------------
class Subsession(BaseSubsession):
    pass


def session_seed(session):
    """順序割り当てと項目順のランダム化に使う乱数シード。
    session config の rand_seed が 0 以外ならその値、0 ならセッションコードから決定的に導く。
    どちらでも各回答の rand_seed 列に残るので、割り当てを後から再現できる。"""
    cfg = session.config
    s = int(cfg.get('rand_seed', 0) or 0)
    if s:
        return s
    return int(hashlib.sha256(session.code.encode()).hexdigest()[:8], 16)


def creating_session(subsession: Subsession):
    session = subsession.session
    cfg = session.config
    players = subsession.get_players()
    seed = session_seed(session)
    rng = random.Random(seed)
    hexaco = bool(cfg['use_hexaco'])
    # 2×2 のブロックランダム化（4 人ずつ、task_order × scale_order の 4 通りをシャッフル）→ 各セルがほぼ同数になる。
    # task_order: 1 = 質問紙→DG, 2 = DG→質問紙。scale_order: 1 = FAB→HEXACO, 2 = HEXACO→FAB（HEXACO を使わないときは 0）
    combos = []
    for _ in range(0, len(players), 4):
        block = [(1, 1), (1, 2), (2, 1), (2, 2)]
        rng.shuffle(block)
        combos.extend(block)
    # 実験 ID（v0.6）: 10 桁の数字、セッション内で一意。乱数シードとは独立（secrets）なので割り当てからは推測できない。
    # 終了画面に表示し、参加者が CrowdWorks の作業ページに入力する（研究室マニュアル: 10 桁程度、重複を認めない）
    used_ids = set()
    for p, (to, so) in zip(players, combos):
        while True:
            eid = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
            if eid not in used_ids:
                used_ids.add(eid)
                break
        p.exp_id = eid
        p.task_order = to
        p.scale_order = so if hexaco else 0
        p.lang = cfg['lang']
        p.app_version = cfg['app_version']
        # 来歴（実験計画書「記録・分析ノート・図表」）: 条件の違いを後から機械的に確認できるようにする
        p.git_commit = GIT_COMMIT
        p.otree_version = OTREE_VERSION
        p.rand_seed = seed
        p.cfg_endowment = cfg['endowment']
        p.cfg_dg_step = cfg['dg_step']
        p.cfg_fee = cfg['participation_fee_yen']
        p.cfg_use_hexaco = hexaco
        # 原研究と同じく FAB 項目は常にランダム順。注意チェックは FAB と一体でシャッフルする
        items = C.FAB_FIELDS + C.CQ_FIELDS
        rng.shuffle(items)
        # 注意チェックをページの先頭・末尾に置かない（各ページ内で中央寄りに動かす）
        half = (len(items) + 1) // 2
        pages = [items[:half], items[half:]]
        for page in pages:
            for cq in C.CQ_FIELDS:
                if cq in page and page.index(cq) in (0, len(page) - 1) and len(page) > 2:
                    page.remove(cq)
                    page.insert(len(page) // 2, cq)
        items = pages[0] + pages[1]
        p.participant.fab_order = items
        p.fab_item_order = ','.join(items)
        # HEXACO は別の段階として、段階内でランダム順
        hex_items = list(C.HEX_FIELDS)
        rng.shuffle(hex_items)
        p.participant.hex_order = hex_items if hexaco else []
        p.hex_item_order = ','.join(hex_items) if hexaco else ''
        p.participant.survey_error = False


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # 割り当て・メタ
    task_order = models.IntegerField()   # 1 = 質問紙→DG, 2 = DG→質問紙（oTree では order が予約語）
    scale_order = models.IntegerField()  # 1 = FAB→HEXACO, 2 = HEXACO→FAB, 0 = HEXACO なし（v0.5）
    lang = models.StringField()
    app_version = models.StringField()
    # 来歴（v0.3）: どのコード・設定・乱数で集めた回答かを各行に残す
    git_commit = models.StringField(blank=True)
    otree_version = models.StringField(blank=True)
    rand_seed = models.IntegerField(blank=True)
    cfg_endowment = models.IntegerField(blank=True)
    cfg_dg_step = models.IntegerField(blank=True)
    cfg_fee = models.IntegerField(blank=True)  # 参加謝礼（画面には出さない）。tools/pairing.py はこの列と cfg_endowment から支払額を計算する
    cfg_use_hexaco = models.BooleanField(blank=True)
    user_agent = models.LongStringField(blank=True)
    screen_width = models.IntegerField(blank=True)
    # 実験 ID（v0.6）: 終了画面に表示し CrowdWorks に入力してもらう 10 桁の数字。creating_session で発行
    exp_id = models.StringField(blank=True)
    # 同意（v0.5: 同意 + 参加資格の 2 項目。v0.6: 参加資格 = 18 歳以上・日本語が母語）
    consent = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
    eligible_confirm = models.BooleanField(widget=widgets.CheckboxInput, blank=True)  # 18 歳以上かつ日本語が母語（v0.6）
    # FAB（原研究の変数名。1〜6、逆転項目なし）
    hg_1 = likert_field()
    hg_3 = likert_field()
    hg_7 = likert_field()
    hg_10 = likert_field()
    hg_13 = likert_field()
    pp_1 = likert_field()
    pp_8 = likert_field()
    pp_12 = likert_field()
    pp_14 = likert_field()
    pp_15 = likert_field()
    mc_1 = likert_field()
    mc_3 = likert_field()
    mc_18 = likert_field()
    mc_20 = likert_field()
    mc_23 = likert_field()
    # 注意チェック（control question）
    cq1 = likert_field()
    cq2 = likert_field()
    cq1_pass = models.BooleanField(blank=True)
    cq2_pass = models.BooleanField(blank=True)
    fab_item_order = models.LongStringField(blank=True)
    # HEXACO-60 正直さ-謙虚さ（1〜5。逆転は codebook の reverse 列、解析側で 6 − x）
    hex_1 = likert_field(C.LIKERT5)
    hex_2 = likert_field(C.LIKERT5)
    hex_3 = likert_field(C.LIKERT5)
    hex_4 = likert_field(C.LIKERT5)
    hex_5 = likert_field(C.LIKERT5)
    hex_6 = likert_field(C.LIKERT5)
    hex_7 = likert_field(C.LIKERT5)
    hex_8 = likert_field(C.LIKERT5)
    hex_9 = likert_field(C.LIKERT5)
    hex_10 = likert_field(C.LIKERT5)
    hex_item_order = models.LongStringField(blank=True)
    # DG
    dg_check = models.IntegerField(min=0, max=100000)
    dg_check_answer1 = models.IntegerField(blank=True)
    dg_check_answer2 = models.IntegerField(blank=True)
    dg_check_attempts = models.IntegerField(initial=0)
    dg_check_pass = models.BooleanField(blank=True)
    dg_give = models.IntegerField(min=0)  # 分配額（v0.5: 入力は 1 回、確認画面なし）
    dg_share = models.BooleanField(blank=True)
    # 事後評価（原研究 Study 11 の AG11 項目）
    eval_understand = likert_field()
    eval_difficult = likert_field()
    eval_reflect = likert_field()
    eval_distract = likert_field()
    comment_open = models.LongStringField(blank=True)
    # 時間・完了・除外
    t_start = models.StringField(blank=True)
    t_end = models.StringField(blank=True)
    duration_sec = models.IntegerField(blank=True)
    finished = models.BooleanField(initial=False)
    excluded_in_app = models.BooleanField(initial=False)
    exclude_reason_in_app = models.StringField(blank=True)


# ---------------------------------------------------------------------------
# ページ（共通部分）
# ---------------------------------------------------------------------------
class Consent(Page):
    # ブラウザの種類と画面幅を hidden input（JS で埋める）から受け取る。未取得でも進める（blank=True）
    form_model = 'player'
    form_fields = ['consent', 'eligible_confirm', 'user_agent', 'screen_width']

    @staticmethod
    def vars_for_template(player: Player):
        return ctx(player)

    @staticmethod
    def error_message(player: Player, values):
        if not (values['consent'] and values['eligible_confirm']):
            return texts(player)['consent_error']

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if not player.field_maybe_none('t_start'):
            player.t_start = now_iso()
        ua = player.field_maybe_none('user_agent')
        if ua:
            player.user_agent = ua[:300]


class SurveyPageBase(Page):
    form_model = 'player'
    template_name = 'altruism_study/SurveyPage.html'

    @staticmethod
    def error_message(player: Player, values):
        return survey_error_message(player, values)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        for cq in C.CQ_FIELDS:
            v = player.field_maybe_none(cq)
            if v is not None:
                setattr(player, f'{cq}_pass', v == C.CQ_EXPECTED[cq])


class FabPage1Base(SurveyPageBase):
    @staticmethod
    def get_form_fields(player: Player):
        return fab_fields(player, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 'fab', 1)


class FabPage2Base(SurveyPageBase):
    @staticmethod
    def get_form_fields(player: Player):
        return fab_fields(player, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 'fab', 2)


class HexPageBase(SurveyPageBase):
    @staticmethod
    def get_form_fields(player: Player):
        return hex_fields(player)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 'hex', 1)


class DGIntroBase(Page):
    template_name = 'altruism_study/DGIntro.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        return ctx(player, intro_blocks=intro_blocks(T))


class DGCheckBase(Page):
    form_model = 'player'
    form_fields = ['dg_check']
    template_name = 'altruism_study/DGCheck.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        # 説明は折りたたみで常に読み直せるようにし、再回答のときは開いた状態にする（v0.5）
        return ctx(player, intro_blocks=intro_blocks(T), retry=player.dg_check_attempts >= 1)

    @staticmethod
    def error_message(player: Player, values):
        correct = endowment(player) - C.CHECK_GIVE
        player.dg_check_attempts += 1
        if player.dg_check_attempts == 1:
            player.dg_check_answer1 = values['dg_check']
            if values['dg_check'] != correct:
                return texts(player)['check_retry']  # 正解は示さず 1 度だけ再回答
        else:
            player.dg_check_answer2 = values['dg_check']
        return None

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        correct = endowment(player) - C.CHECK_GIVE
        last = player.dg_check_answer2 if player.dg_check_attempts >= 2 else player.dg_check_answer1
        player.dg_check_pass = last == correct


class DGDecisionBase(Page):
    """DG の決定。原研究と同じく 0〜元手の任意の額を数値で入力する（刻みは session config の dg_step）。"""
    form_model = 'player'
    form_fields = ['dg_give']
    template_name = 'altruism_study/DGDecision.html'

    @staticmethod
    def vars_for_template(player: Player):
        cfg = player.session.config
        return ctx(
            player,
            value=player.field_maybe_none('dg_give'),
            has_value=player.field_maybe_none('dg_give') is not None,
            endowment=cfg['endowment'],
            step=cfg['dg_step'],
            unit=cfg['currency_label'],
        )

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        return dict(endowment=cfg['endowment'], unit=cfg['currency_label'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dg_share = player.dg_give > 0


class PostSurvey(Page):
    form_model = 'player'
    form_fields = C.EVAL_FIELDS + ['comment_open']

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        highlight = bool(player.participant.survey_error)
        player.participant.survey_error = False
        items = likert_items(player, C.EVAL_FIELDS, T['post_items'], T['likert6'], C.LIKERT6, highlight)
        return ctx(player, items=items, comment_text=player.field_maybe_none('comment_open') or '')

    @staticmethod
    def error_message(player: Player, values):
        vals = {k: v for k, v in values.items() if k != 'comment_open'}
        return survey_error_message(player, vals)


class End(Page):
    @staticmethod
    def vars_for_template(player: Player):
        if not player.finished:
            player.t_end = now_iso()
            if player.field_maybe_none('t_start'):
                t0 = datetime.fromisoformat(player.t_start)
                t1 = datetime.fromisoformat(player.t_end)
                player.duration_sec = int((t1 - t0).total_seconds())
            reasons = []
            if not (player.field_maybe_none('cq1_pass') and player.field_maybe_none('cq2_pass')):
                reasons.append('cq')
            if not player.field_maybe_none('dg_check_pass'):
                reasons.append('check')
            player.excluded_in_app = bool(reasons)
            player.exclude_reason_in_app = ','.join(reasons)
            player.finished = True
        # v0.6: 終了画面には実験 ID（exp_id）を出す。participant.code は管理画面・エクスポートに残る
        return ctx(player, code=player.field_maybe_none('exp_id') or player.participant.code)


# ---------------------------------------------------------------------------
# 順序群ごとのページ（A = task_order 1: 質問紙→DG, B = task_order 2: DG→質問紙）
# HEXACO の段階は scale_order で FAB の前（First）か後（Last）に出る
# ---------------------------------------------------------------------------
def shown_if(task_order, scale_order=None):
    def is_displayed(player: Player):
        if player.task_order != task_order:
            return False
        if scale_order is not None:
            return use_hexaco(player) and player.scale_order == scale_order
        return True

    return staticmethod(is_displayed)


# --- task_order 1: 質問紙 → DG ---
class HexFirstA(HexPageBase):
    is_displayed = shown_if(1, scale_order=2)


class FabPage1A(FabPage1Base):
    is_displayed = shown_if(1)


class FabPage2A(FabPage2Base):
    is_displayed = shown_if(1)


class HexLastA(HexPageBase):
    is_displayed = shown_if(1, scale_order=1)


class DGIntroA(DGIntroBase):
    is_displayed = shown_if(1)


class DGCheckA(DGCheckBase):
    is_displayed = shown_if(1)


class DGDecisionA(DGDecisionBase):
    is_displayed = shown_if(1)


# --- task_order 2: DG → 質問紙 ---
class DGIntroB(DGIntroBase):
    is_displayed = shown_if(2)


class DGCheckB(DGCheckBase):
    is_displayed = shown_if(2)


class DGDecisionB(DGDecisionBase):
    is_displayed = shown_if(2)


class HexFirstB(HexPageBase):
    is_displayed = shown_if(2, scale_order=2)


class FabPage1B(FabPage1Base):
    is_displayed = shown_if(2)


class FabPage2B(FabPage2Base):
    is_displayed = shown_if(2)


class HexLastB(HexPageBase):
    is_displayed = shown_if(2, scale_order=1)


page_sequence = [
    Consent,
    # task_order 1: 質問紙（HEXACO → FAB または FAB → HEXACO）→ DG
    HexFirstA, FabPage1A, FabPage2A, HexLastA,
    DGIntroA, DGCheckA, DGDecisionA,
    # task_order 2: DG → 質問紙
    DGIntroB, DGCheckB, DGDecisionB,
    HexFirstB, FabPage1B, FabPage2B, HexLastB,
    # 共通: 事後評価 → 終了
    PostSurvey,
    End,
]
