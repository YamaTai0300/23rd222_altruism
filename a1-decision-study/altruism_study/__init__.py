"""A-1 追試: FAB 質問紙 × 独裁者ゲーム（一回完結・順序ランダム化・役割不確定法）v0.4

設計書: https://claude.ai/code/artifact/5f9cc974-cbb4-4fd0-840b-7836e6283d47
原資料: https://osf.io/t5mf2/（Binder et al., 2026 の補足資料。CHANGELOG.md に対応表）
- 全画面を 1 つのアプリ（1 ラウンド）に置き、順序の分岐は is_displayed で行う（§4）
- WaitPage・グループは使わない。各参加者は自分のペースで最後まで進む（FR-25）
- 文言は texts/ から引く。テンプレートに文言を書かない（§8）
- 変数名は原研究の整形済みデータ（Studies/XX/XX_data.csv）に合わせる: hg_1 … mc_23, cq1, cq2, dg_give, dg_correct
- v0.4: HEXACO 正直さ-謙虚さ 10 項目を既定で混ぜる（codebook に逆転フラグ）。cfg_fee を記録。文言から支払い方法の指定を外した
- v0.3: 各回答に来歴（app_version, git_commit, otree_version, 設定値, 乱数シード, ブラウザ, 画面幅）を記録し、
  順序割り当てと項目順のランダム化を seed 付きで再現できるようにした（実験計画書「記録・分析ノート・図表」）
"""
import hashlib
import os
import random
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
Binder et al. (2026) の Help Giving → 独裁者ゲームの関連を日本の大学生で再現する一回完結のオンライン実験。
質問紙（FAB 15 項目 + 注意チェック 2）と意思決定課題（DG, 元手は session config）の順序を参加者ごとにランダム化する。
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
    HEX_FIELDS = [f'hex_{i}' for i in range(1, 11)]
    EVAL_FIELDS = ['eval_understand', 'eval_difficult', 'eval_reflect', 'eval_distract']
    LIKERT = [1, 2, 3, 4, 5, 6]
    CHECK_GIVE = 300  # 理解確認「300 円を分けると取り分は？」
    SURVEY_PAGES = 2


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------
def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def likert_field():
    # blank=True にして必須チェックは error_message で行う。
    # こうすると未回答があっても回答済みの値を保存でき、再表示時に選択が消えない。
    return models.IntegerField(choices=C.LIKERT, blank=True)


def endowment(player):
    return player.session.config['endowment']


def step(player):
    return player.session.config['dg_step']


def amount_error(player, value):
    """DG の金額入力（dg_give, dg_predict）の検証: 0〜endowment、dg_step の倍数。"""
    if value is None or value < 0 or value > endowment(player) or value % step(player) != 0:
        return texts(player)['amount_error']


def dg_give_error_message(player, value):
    return amount_error(player, value)


def dg_predict_error_message(player, value):
    return amount_error(player, value)


def survey_fields(player, page_no):
    """質問紙の page_no（1 or 2）に表示するフィールド名。順序は creating_session で確定済み。"""
    items = list(player.participant.item_order)
    half = (len(items) + 1) // 2
    return items[:half] if page_no == 1 else items[half:]


def likert_items(player, fields, labels_src, highlight):
    T = texts(player)
    labels = T['likert6']
    items = []
    for f in fields:
        val = player.field_maybe_none(f)
        items.append(
            dict(
                name=f,
                text=labels_src[f],
                missing=highlight and val is None,
                options=[dict(v=v, label=labels[v - 1], checked=(val == v)) for v in C.LIKERT],
            )
        )
    return items


def survey_vars(player, page_no):
    T = texts(player)
    highlight = bool(player.participant.survey_error)
    player.participant.survey_error = False
    items = likert_items(player, survey_fields(player, page_no), T['items'], highlight)
    return dict(T=T, items=items, page_no=page_no, num_pages=C.SURVEY_PAGES)


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
    # 順序のブロックランダム化（2 人ずつ 1,2 をシャッフル）→ 各群がほぼ同数になる
    orders = []
    for _ in range(0, len(players), 2):
        block = [1, 2]
        rng.shuffle(block)
        orders.extend(block)
    for p, o in zip(players, orders):
        p.task_order = o
        p.lang = cfg['lang']
        p.app_version = cfg['app_version']
        # 来歴（実験計画書「記録・分析ノート・図表」）: 条件の違いを後から機械的に確認できるようにする
        p.git_commit = GIT_COMMIT
        p.otree_version = OTREE_VERSION
        p.rand_seed = seed
        p.cfg_endowment = cfg['endowment']
        p.cfg_dg_step = cfg['dg_step']
        p.cfg_fee = cfg['participation_fee_yen']
        p.cfg_use_hexaco = bool(cfg['use_hexaco'])
        # 原研究と同じく FAB 項目は常にランダム順。注意チェックと混ぜる尺度も一体でシャッフルする
        items = C.FAB_FIELDS + C.CQ_FIELDS + (C.HEX_FIELDS if cfg['use_hexaco'] else [])
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
        p.participant.item_order = items
        p.participant.survey_error = False
        p.fab_item_order = ','.join(items)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # 割り当て・メタ
    task_order = models.IntegerField()  # 1 = 質問紙→DG, 2 = DG→質問紙（oTree では order が予約語）
    lang = models.StringField()
    app_version = models.StringField()
    # 来歴（v0.3）: どのコード・設定・乱数で集めた回答かを各行に残す
    git_commit = models.StringField(blank=True)
    otree_version = models.StringField(blank=True)
    rand_seed = models.IntegerField(blank=True)
    cfg_endowment = models.IntegerField(blank=True)
    cfg_dg_step = models.IntegerField(blank=True)
    cfg_fee = models.IntegerField(blank=True)  # 参加謝礼。tools/pairing.py はこの列と cfg_endowment から支払額を計算する
    cfg_use_hexaco = models.BooleanField(blank=True)
    user_agent = models.LongStringField(blank=True)
    screen_width = models.IntegerField(blank=True)
    # 同意
    consent = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
    age_confirm = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
    student_confirm = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
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
    # 混ぜる尺度（任意）
    hex_1 = likert_field()
    hex_2 = likert_field()
    hex_3 = likert_field()
    hex_4 = likert_field()
    hex_5 = likert_field()
    hex_6 = likert_field()
    hex_7 = likert_field()
    hex_8 = likert_field()
    hex_9 = likert_field()
    hex_10 = likert_field()
    # 属性
    age = models.IntegerField(min=18, max=99, blank=True)
    gender = models.IntegerField(choices=[1, 2, 3, 4], blank=True)
    grade = models.StringField(choices=['B1', 'B2', 'B3', 'B4', 'M1', 'M2', 'D', 'other'], blank=True)
    game_exp = models.BooleanField(blank=True)
    # DG
    dg_check = models.IntegerField(min=0, max=100000)
    dg_check_answer1 = models.IntegerField(blank=True)
    dg_check_answer2 = models.IntegerField(blank=True)
    dg_check_attempts = models.IntegerField(initial=0)
    dg_check_pass = models.BooleanField(blank=True)
    dg_predict = models.IntegerField(min=0)
    dg_give = models.IntegerField(min=0)        # 最終決定（dg_correct = 2 なら 2 回目の入力）
    dg_give_1 = models.IntegerField(blank=True)  # 1 回目の入力
    dg_give_2 = models.IntegerField(blank=True)  # 2 回目の入力（入力し直したときだけ）
    dg_correct = models.IntegerField(choices=[1, 2], blank=True)  # 1 = 入力は正しい, 2 = 入力し直す（原研究 Study 09）
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
    form_model = 'player'
    form_fields = ['consent', 'age_confirm', 'student_confirm']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player))

    @staticmethod
    def error_message(player: Player, values):
        if not (values['consent'] and values['age_confirm'] and values['student_confirm']):
            return texts(player)['consent_error']


class ParticipantCode(Page):
    # ブラウザの種類と画面幅を hidden input（JS で埋める）から受け取る。未取得でも進める（blank=True）
    form_model = 'player'
    form_fields = ['user_agent', 'screen_width']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player), code=player.participant.code)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if not player.field_maybe_none('t_start'):
            player.t_start = now_iso()
        ua = player.field_maybe_none('user_agent')
        if ua:
            player.user_agent = ua[:300]


class SurveyIntroBase(Page):
    template_name = 'altruism_study/SurveyIntro.html'

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player))


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


class DemographicsBase(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'grade', 'game_exp']
    template_name = 'altruism_study/Demographics.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        g = player.field_maybe_none('gender')
        gr = player.field_maybe_none('grade')
        ge = player.field_maybe_none('game_exp')
        return dict(
            T=T,
            gender_options=[dict(v=v, label=lbl, checked=(g == v)) for v, lbl in T['gender_options']],
            grade_options=[dict(v=v, label=lbl, checked=(gr == v)) for v, lbl in T['grade_options']],
            game_exp_options=[dict(v=v, label=lbl, checked=(ge == v)) for v, lbl in T['game_exp_options']],
        )

    @staticmethod
    def error_message(player: Player, values):
        return survey_error_message(player, values)


class DGIntroBase(Page):
    template_name = 'altruism_study/DGIntro.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        return dict(T=T, intro_blocks=intro_blocks(T))


class DGCheckBase(Page):
    form_model = 'player'
    form_fields = ['dg_check']
    template_name = 'altruism_study/DGCheck.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        return dict(T=T, intro_blocks=intro_blocks(T), retry=player.dg_check_attempts >= 1)

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


def amount_vars(player, field):
    cfg = player.session.config
    return dict(
        T=texts(player),
        field=field,
        value=player.field_maybe_none(field),
        has_value=player.field_maybe_none(field) is not None,
        endowment=cfg['endowment'],
        step=cfg['dg_step'],
        unit=cfg['currency_label'],
    )


class DGPredictBase(Page):
    form_model = 'player'
    form_fields = ['dg_predict']
    template_name = 'altruism_study/DGPredict.html'

    @staticmethod
    def vars_for_template(player: Player):
        return amount_vars(player, 'dg_predict')


class DGDecisionBase(Page):
    """DG の決定。原研究と同じく 0〜元手の任意の額を数値で入力する（刻みは session config の dg_step）。"""
    form_model = 'player'
    form_fields = ['dg_give']
    template_name = 'altruism_study/DGDecision.html'

    @staticmethod
    def vars_for_template(player: Player):
        v = amount_vars(player, 'dg_give')
        v['again'] = False
        return v

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        return dict(endowment=cfg['endowment'], unit=cfg['currency_label'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dg_give_1 = player.dg_give
        player.dg_share = player.dg_give > 0


class DGConfirmBase(Page):
    """入力の確認（原研究 Study 09 の dg_correct「Korrekte Eingabe?」）。「いいえ」なら 1 回だけ入力し直せる。"""
    form_model = 'player'
    form_fields = ['dg_correct']
    template_name = 'altruism_study/DGConfirm.html'

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        give = player.dg_give
        keep = endowment(player) - give
        sel = player.field_maybe_none('dg_correct')
        return dict(
            T=T,
            body=fill(T['confirm_body'], give=f'{give:,}', keep=f'{keep:,}'),
            options=[dict(v=v, label=lbl, checked=(sel == v)) for v, lbl in T['confirm_options']],
        )

    @staticmethod
    def error_message(player: Player, values):
        if values['dg_correct'] is None:
            return texts(player)['confirm_error']


class DGDecisionAgainBase(Page):
    """dg_correct = 2（入力し直す）のときだけ表示。ここでの入力が最終決定（dg_give）になる。"""
    form_model = 'player'
    form_fields = ['dg_give']
    template_name = 'altruism_study/DGDecision.html'

    @staticmethod
    def vars_for_template(player: Player):
        v = amount_vars(player, 'dg_give')
        v['again'] = True
        return v

    @staticmethod
    def js_vars(player: Player):
        cfg = player.session.config
        return dict(endowment=cfg['endowment'], unit=cfg['currency_label'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dg_give_2 = player.dg_give
        player.dg_share = player.dg_give > 0


class PostSurvey(Page):
    form_model = 'player'
    form_fields = C.EVAL_FIELDS + ['comment_open']

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        highlight = bool(player.participant.survey_error)
        player.participant.survey_error = False
        items = likert_items(player, C.EVAL_FIELDS, T['post_items'], highlight)
        return dict(T=T, items=items, comment_text=player.field_maybe_none('comment_open') or '')

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
        return dict(
            T=texts(player),
            code=player.participant.code,
            contact_url=player.session.config['contact_form_url'] + player.participant.code,
        )


# ---------------------------------------------------------------------------
# 順序群ごとのページ（A = order 1: 質問紙→DG, B = order 2: DG→質問紙）
# ---------------------------------------------------------------------------
def shown_if_order(n, revise=False):
    def is_displayed(player: Player):
        if player.task_order != n:
            return False
        if revise:
            return player.field_maybe_none('dg_correct') == 2
        return True

    return staticmethod(is_displayed)


class SurveyIntroA(SurveyIntroBase):
    is_displayed = shown_if_order(1)


class SurveyPage1A(SurveyPageBase):
    is_displayed = shown_if_order(1)

    @staticmethod
    def get_form_fields(player: Player):
        return survey_fields(player, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 1)


class SurveyPage2A(SurveyPageBase):
    is_displayed = shown_if_order(1)

    @staticmethod
    def get_form_fields(player: Player):
        return survey_fields(player, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 2)


class DemographicsA(DemographicsBase):
    is_displayed = shown_if_order(1)


class DGIntroB(DGIntroBase):
    is_displayed = shown_if_order(2)


class DGCheckB(DGCheckBase):
    is_displayed = shown_if_order(2)


class DGPredictB(DGPredictBase):
    is_displayed = shown_if_order(2)


class DGDecisionB(DGDecisionBase):
    is_displayed = shown_if_order(2)


class DGConfirmB(DGConfirmBase):
    is_displayed = shown_if_order(2)


class DGDecisionAgainB(DGDecisionAgainBase):
    is_displayed = shown_if_order(2, revise=True)


class SurveyIntroB(SurveyIntroBase):
    is_displayed = shown_if_order(2)


class SurveyPage1B(SurveyPageBase):
    is_displayed = shown_if_order(2)

    @staticmethod
    def get_form_fields(player: Player):
        return survey_fields(player, 1)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 1)


class SurveyPage2B(SurveyPageBase):
    is_displayed = shown_if_order(2)

    @staticmethod
    def get_form_fields(player: Player):
        return survey_fields(player, 2)

    @staticmethod
    def vars_for_template(player: Player):
        return survey_vars(player, 2)


class DemographicsB(DemographicsBase):
    is_displayed = shown_if_order(2)


class DGIntroA(DGIntroBase):
    is_displayed = shown_if_order(1)


class DGCheckA(DGCheckBase):
    is_displayed = shown_if_order(1)


class DGPredictA(DGPredictBase):
    is_displayed = shown_if_order(1)


class DGDecisionA(DGDecisionBase):
    is_displayed = shown_if_order(1)


class DGConfirmA(DGConfirmBase):
    is_displayed = shown_if_order(1)


class DGDecisionAgainA(DGDecisionAgainBase):
    is_displayed = shown_if_order(1, revise=True)


page_sequence = [
    Consent,
    ParticipantCode,
    # order 1: 質問紙 → 属性 → DG
    SurveyIntroA, SurveyPage1A, SurveyPage2A, DemographicsA,
    # order 2: DG → 質問紙 → 属性
    DGIntroB, DGCheckB, DGPredictB, DGDecisionB, DGConfirmB, DGDecisionAgainB,
    SurveyIntroB, SurveyPage1B, SurveyPage2B, DemographicsB,
    # order 1 の DG
    DGIntroA, DGCheckA, DGPredictA, DGDecisionA, DGConfirmA, DGDecisionAgainA,
    # 共通: 事後評価 → 終了
    PostSurvey,
    End,
]
