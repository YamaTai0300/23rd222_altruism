"""ボットテスト: otree test <config名> 4   （各セッション設定で 4 ケース）

ケース:
  keep_all   0 を渡す（全額保持）
  share_half 5.35 を渡す
  bad_input  範囲外（10.71、-1、小数 3 桁）は拒否される
  revise     入力確認で「いいえ」→ 再入力（confirm_entry のある設定のみ。他では share_half と同じ）
"""
from otree.api import Bot, Submission, SubmissionMustFail, expect

from . import (
    C, Consent, Disclosure, GeneralInstructions, Waiting, DGDecision, DGConfirm, DGDecisionAgain, DGResult,
    Evaluation, Demographics, Debrief, End,
)


class PlayerBot(Bot):
    cases = ['keep_all', 'share_half', 'bad_input', 'revise']

    def play_round(self):
        c = self.case
        cfg = self.session.config
        fictive = cfg['incentive'] == 'none'

        if fictive:
            yield SubmissionMustFail(Consent, dict(consent=True, fictive_ok=''))
            yield Consent, dict(consent=True, fictive_ok=True)
        else:
            yield SubmissionMustFail(Consent, dict(consent=''))
            yield Consent, dict(consent=True)
        if not cfg['deception']:
            yield Disclosure
        yield SubmissionMustFail(GeneralInstructions, dict(username='x'))
        yield GeneralInstructions, dict(username='Pegasus')
        yield Submission(Waiting, {}, check_html=False, timeout_happened=True)

        if c == 'bad_input':
            yield SubmissionMustFail(DGDecision, dict(dg_give=cfg['endowment'] + 0.01))
            yield SubmissionMustFail(DGDecision, dict(dg_give=-1))
            yield SubmissionMustFail(DGDecision, dict(dg_give=1.005))
        give = {'keep_all': 0, 'share_half': 5.35, 'bad_input': 2.5, 'revise': 3.0}[c]
        yield DGDecision, dict(dg_give=give)
        if cfg['confirm_entry']:
            yield SubmissionMustFail(DGConfirm, dict())
            if c == 'revise':
                yield DGConfirm, dict(dg_correct=2)
                yield DGDecisionAgain, dict(dg_give=4.5)
                give = 4.5
            else:
                yield DGConfirm, dict(dg_correct=1)
        yield DGResult
        if cfg['post_evaluation']:
            yield SubmissionMustFail(Evaluation, dict(eval_1=2, eval_2=2, eval_3=2, eval_4=5, eval_5=5))
            yield Evaluation, dict(eval_1=2, eval_2=2, eval_3=2, eval_4=5, eval_5=5, eval_6=1, eval_open='')
        yield SubmissionMustFail(Demographics, dict(gender=1, age=30))
        yield Demographics, dict(gender=1, age=30, edu=12)
        if cfg['deception']:
            yield Debrief
        yield Submission(End, {}, check_html=False)

        p = self.player
        expect(round(p.dg_give, 2), give)
        expect(round(p.dg_total, 2), round(cfg['endowment'] - give, 2))
        if cfg['incentive'] == 'none':
            expect(p.dg_payout, 0.0)
        elif cfg['incentive'] == 'flat':
            expect(p.dg_payout, cfg['flat_fee'])
        else:
            expect(round(p.dg_payout, 2), round(cfg['conversion_rate'] * (cfg['endowment'] - give), 2))
        if cfg['confirm_entry'] and c == 'revise':
            expect(p.dg_correct, 2)
            expect(round(p.dg_give_1, 2), 3.0)
            expect(round(p.dg_give_2, 2), 4.5)
        expect(p.username, 'Pegasus')
        expect(p.waited_sec, cfg['waiting_seconds'])
