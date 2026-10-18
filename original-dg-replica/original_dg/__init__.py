"""原研究（Binder, Schultze, Chen & Windmann, 2026, Sci Rep 16:11600）の独裁者ゲーム部分の再現。

目的: 「元の研究ではこうだった」を画面で示す（本追試 a1-decision-study との比較用）。
根拠: OSF T5MF2 — Studies/03 卒論付録 p.43–44（一般教示・DG 教示の原文）、Studies/09 codebook（dg_correct）、
      Studies/11 codebook（事後評価・属性）、論文 Methods（欺罔の有無、報酬方式）。docs/sources_ja.md に対応表。

原研究の 6 研究で異なっていた点はセッション設定で切り替える:
  deception      True  = 相手が実在すると信じさせ、最後にデブリーフィング（Study 03, 15）
                 False = 事前に「相手は架空」と告知（Study 09, 11, 12, 13）
  incentive      'none' = 架空のお金（Study 03）/ 'flat' = 決定と無関係の定額（Study 09, 11）/
                 'conversion' = 1 つの決定を 1:rate で換算して上乗せ（Study 12, 13, 15）
  confirm_entry  True = 入力後に「入力は正しいか」を確認し、いいえなら再入力（Study 09）
  post_evaluation True = 事後評価 6 項目（Study 11）
"""
from otree.api import *

from .texts import SOURCES, fill, money, texts

doc = """原研究の DG（Runde: Glück und Pech）の再現。相手は架空（原研究と同じ）、一回限り・匿名、0〜10.70 の任意額を入力。"""


class C(BaseConstants):
    NAME_IN_URL = 'orig'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    EVAL_FIELDS = [f'eval_{i}' for i in range(1, 7)]
    LIKERT = [1, 2, 3, 4, 5, 6]


def cfg(player):
    return player.session.config


def likert_field():
    return models.IntegerField(choices=C.LIKERT, blank=True)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    study_label = models.StringField(blank=True)
    lang = models.StringField(blank=True)
    consent = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
    fictive_ok = models.BooleanField(widget=widgets.CheckboxInput, blank=True)
    username = models.StringField(blank=True)
    waited_sec = models.IntegerField(blank=True)
    # DG（原研究の変数名: dg_give, dg_give_2, dg_correct, dg_total, dg_payout）
    dg_give = models.FloatField(min=0)
    dg_give_1 = models.FloatField(blank=True)
    dg_give_2 = models.FloatField(blank=True)
    dg_correct = models.IntegerField(choices=[1, 2], blank=True)
    dg_total = models.FloatField(blank=True)   # 自分の取り分（Gewinn total）
    dg_payout = models.FloatField(blank=True)  # 実際の支払額（報酬方式による）
    # 事後評価（Study 11 AG11_01〜06）
    eval_1 = likert_field()
    eval_2 = likert_field()
    eval_3 = likert_field()
    eval_4 = likert_field()
    eval_5 = likert_field()
    eval_6 = likert_field()
    eval_open = models.LongStringField(blank=True)
    # 属性（Study 11）
    gender = models.IntegerField(choices=[1, 2, 3], blank=True)
    gender_text = models.StringField(blank=True)
    age = models.IntegerField(min=18, max=99, blank=True)
    edu = models.IntegerField(blank=True)


def creating_session(subsession: Subsession):
    for p in subsession.get_players():
        p.study_label = subsession.session.config['study_label']
        p.lang = subsession.session.config['lang']
        p.participant.eval_error = False


def amount_ok(player, value):
    return value is not None and 0 <= value <= cfg(player)['endowment'] and round(value * 100) == value * 100


def dg_give_error_message(player, value):
    if not amount_ok(player, value):
        return texts(player)['dg_error']


def compute_payout(player):
    c = cfg(player)
    player.dg_total = round(c['endowment'] - player.dg_give, 2)
    if c['incentive'] == 'flat':
        player.dg_payout = c['flat_fee']
    elif c['incentive'] == 'conversion':
        player.dg_payout = round(c['conversion_rate'] * player.dg_total, 2)
    else:
        player.dg_payout = 0.0


def likert_items(player, labels_src, highlight):
    T = texts(player)
    items = []
    for f in C.EVAL_FIELDS:
        val = player.field_maybe_none(f)
        items.append(dict(name=f, text=labels_src[f], missing=highlight and val is None,
                          options=[dict(v=v, label=T['likert6'][v - 1], checked=(val == v)) for v in C.LIKERT]))
    return items


# ---------------------------------------------------------------------------
# ページ
# ---------------------------------------------------------------------------
class Consent(Page):
    form_model = 'player'
    form_fields = ['consent', 'fictive_ok']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player), fictive=cfg(player)['incentive'] == 'none')

    @staticmethod
    def error_message(player: Player, values):
        need_fictive = cfg(player)['incentive'] == 'none'
        if not values['consent'] or (need_fictive and not values['fictive_ok']):
            return texts(player)['consent_error']


class Disclosure(Page):
    """欺罔なしの研究（09, 11, 12, 13）: 相手が架空であることを事前に告知する。"""

    @staticmethod
    def is_displayed(player: Player):
        return not cfg(player)['deception']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player))


class GeneralInstructions(Page):
    form_model = 'player'
    form_fields = ['username']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player))

    @staticmethod
    def error_message(player: Player, values):
        u = (values['username'] or '').strip()
        if not (2 <= len(u) <= 20):
            return texts(player)['username_error']


class Waiting(Page):
    """「オンラインの参加者が足りない場合、システムは最大 10 秒待つ」の再現。一定秒で自動的に進む。"""

    @staticmethod
    def get_timeout_seconds(player: Player):
        return cfg(player)['waiting_seconds']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player), seconds=cfg(player)['waiting_seconds'])

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.waited_sec = cfg(player)['waiting_seconds'] if timeout_happened else 0


class DGDecision(Page):
    form_model = 'player'
    form_fields = ['dg_give']

    @staticmethod
    def vars_for_template(player: Player):
        c = cfg(player)
        v = player.field_maybe_none('dg_give')
        return dict(T=texts(player), again=False, endowment=c['endowment'], unit=c['currency_label'],
                    has_value=v is not None, value=('' if v is None else f'{v:.2f}'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dg_give_1 = player.dg_give
        compute_payout(player)


class DGConfirm(Page):
    """Study 09 の「Korrekte Eingabe?」。"""
    form_model = 'player'
    form_fields = ['dg_correct']

    @staticmethod
    def is_displayed(player: Player):
        return cfg(player)['confirm_entry']

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        c = cfg(player)
        sel = player.field_maybe_none('dg_correct')
        return dict(T=T,
                    question=fill(T['confirm_question'], give=money(c, player.dg_give), keep=money(c, c['endowment'] - player.dg_give)),
                    options=[dict(v=v, label=l, checked=(sel == v)) for v, l in T['confirm_options']])

    @staticmethod
    def error_message(player: Player, values):
        if values['dg_correct'] is None:
            return texts(player)['confirm_error']


class DGDecisionAgain(Page):
    form_model = 'player'
    form_fields = ['dg_give']
    template_name = 'original_dg/DGDecision.html'

    @staticmethod
    def is_displayed(player: Player):
        return cfg(player)['confirm_entry'] and player.field_maybe_none('dg_correct') == 2

    @staticmethod
    def vars_for_template(player: Player):
        c = cfg(player)
        v = player.field_maybe_none('dg_give')
        return dict(T=texts(player), again=True, endowment=c['endowment'], unit=c['currency_label'],
                    has_value=v is not None, value=('' if v is None else f'{v:.2f}'))

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.dg_give_2 = player.dg_give
        compute_payout(player)


class DGResult(Page):
    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        c = cfg(player)
        give, keep = money(c, player.dg_give), money(c, player.dg_total)
        payout_key = {'none': 'result_payout_none', 'flat': 'result_payout_flat', 'conversion': 'result_payout_conversion'}[c['incentive']]
        return dict(T=T, body=fill(T['result_body'], give=give, keep=keep),
                    payout_note=fill(T[payout_key], bonus=money(c, player.dg_payout)))


class Evaluation(Page):
    form_model = 'player'
    form_fields = C.EVAL_FIELDS + ['eval_open']

    @staticmethod
    def is_displayed(player: Player):
        return cfg(player)['post_evaluation']

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        highlight = bool(player.participant.eval_error)
        player.participant.eval_error = False
        return dict(T=T, items=likert_items(player, T['eval_items'], highlight),
                    open_text=player.field_maybe_none('eval_open') or '')

    @staticmethod
    def error_message(player: Player, values):
        missing = {}
        for f in C.EVAL_FIELDS:
            if values[f] is None:
                missing[f] = texts(player)['required_error']
            else:
                setattr(player, f, values[f])
        if missing:
            player.participant.eval_error = True
            return missing


class Demographics(Page):
    form_model = 'player'
    form_fields = ['gender', 'gender_text', 'age', 'edu']

    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        g, e = player.field_maybe_none('gender'), player.field_maybe_none('edu')
        return dict(T=T,
                    gender_options=[dict(v=v, label=l, checked=(g == v)) for v, l in T['gender_options']],
                    edu_options=[dict(v=v, label=l, checked=(e == v)) for v, l in T['edu_options']])

    @staticmethod
    def error_message(player: Player, values):
        if values['gender'] is None or values['age'] is None or values['edu'] is None:
            return texts(player)['required_error']


class Debrief(Page):
    """欺罔ありの研究（03, 15）: 事後に相手が架空だったことを説明する。"""

    @staticmethod
    def is_displayed(player: Player):
        return cfg(player)['deception']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(T=texts(player))


class End(Page):
    @staticmethod
    def vars_for_template(player: Player):
        T = texts(player)
        c = cfg(player)
        if c['incentive'] == 'none':
            body = T['end_body_none']
        else:
            total = c['base_payout'] + player.dg_payout if c['incentive'] == 'conversion' else player.dg_payout
            body = fill(T['end_body'], payout=money(c, total))
        return dict(T=T, body=body)


page_sequence = [
    Consent, Disclosure, GeneralInstructions, Waiting,
    DGDecision, DGConfirm, DGDecisionAgain, DGResult,
    Evaluation, Demographics, Debrief, End,
]
