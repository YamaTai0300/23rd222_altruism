"""ボットテスト（設計書 §10.1）v0.2。

実行: otree test a1_ja 20   （20 名 × 7 ケース）
ケース:
  normal          正常系（注意チェック正答、理解確認 1 回で正答、300 円を分ける、入力確認「はい」）
  cq_fail         注意チェック cq1 に誤答 → exclude_reason_in_app に 'cq'
  check_retry_ok  理解確認 1 回目誤答 → 再回答で正答 → dg_check_pass = True, attempts = 2
  check_fail      理解確認 2 回とも誤答 → dg_check_pass = False だが最後まで進める
  zero_give       0 円を分ける → dg_share = False
  revise          入力確認で「いいえ」→ 入力し直し（200 → 400）→ dg_give_1 = 200, dg_give_2 = 400, dg_give = 400
  bad_amount      範囲外・刻み違いの額は受け付けない（元手超過、負の値、dg_step の倍数でない値）
"""
from otree.api import Bot, Submission, SubmissionMustFail, expect

from . import (
    C,
    Consent,
    ParticipantCode,
    SurveyIntroA, SurveyPage1A, SurveyPage2A, DemographicsA,
    DGIntroB, DGCheckB, DGPredictB, DGDecisionB, DGConfirmB, DGDecisionAgainB,
    SurveyIntroB, SurveyPage1B, SurveyPage2B, DemographicsB,
    DGIntroA, DGCheckA, DGPredictA, DGDecisionA, DGConfirmA, DGDecisionAgainA,
    PostSurvey,
    End,
    survey_fields,
)


class PlayerBot(Bot):
    cases = ['normal', 'cq_fail', 'check_retry_ok', 'check_fail', 'zero_give', 'revise', 'bad_amount']

    def play_round(self):
        c = self.case
        cfg = self.session.config
        correct = cfg['endowment'] - C.CHECK_GIVE

        # 同意: 未チェックでは進めない
        yield SubmissionMustFail(Consent, dict(consent=True, age_confirm='', student_confirm=True))  # '' = 未チェック
        yield Consent, dict(consent=True, age_confirm=True, student_confirm=True)
        # 来歴の hidden 項目（v0.3）。ブラウザが埋めるが、未取得でも進める
        if c == 'normal':
            yield ParticipantCode, dict(user_agent='bot/1.0 ' + 'x' * 400, screen_width=375)
        else:
            yield ParticipantCode

        if self.player.task_order == 1:
            yield from self.survey(c, SurveyIntroA, SurveyPage1A, SurveyPage2A)
            yield from self.demog(DemographicsA)
            yield from self.dg(c, correct, DGIntroA, DGCheckA, DGPredictA, DGDecisionA, DGConfirmA, DGDecisionAgainA)
        else:
            yield from self.dg(c, correct, DGIntroB, DGCheckB, DGPredictB, DGDecisionB, DGConfirmB, DGDecisionAgainB)
            yield from self.survey(c, SurveyIntroB, SurveyPage1B, SurveyPage2B)
            yield from self.demog(DemographicsB)

        # 事後評価: 評価項目は必須、自由記述は任意
        yield SubmissionMustFail(PostSurvey, dict(eval_understand=5, eval_difficult=2, eval_reflect=4))
        yield PostSurvey, dict(eval_understand=5, eval_difficult=2, eval_reflect=4, eval_distract=1, comment_open='')

        yield Submission(End, {}, check_html=False)  # 最終ページ（ボタンなし）
        p = self.player
        expect(p.finished, True)
        expect(p.field_maybe_none('t_start') is not None, True)
        expect(p.duration_sec >= 0, True)
        expect(p.dg_share, p.dg_give > 0)
        expect(p.eval_distract, 1)
        n_items = 17 + (10 if cfg['use_hexaco'] else 0)
        expect(len(p.fab_item_order.split(',')), n_items)
        # 来歴（v0.3）: 設定値・版・乱数シードが各行に残る
        expect(p.cfg_endowment, cfg['endowment'])
        expect(p.cfg_dg_step, cfg['dg_step'])
        expect(p.cfg_fee, cfg['participation_fee_yen'])
        expect(p.cfg_use_hexaco, bool(cfg['use_hexaco']))
        expect(p.app_version, cfg['app_version'])
        expect(bool(p.otree_version), True)
        expect(bool(p.git_commit), True)
        expect(p.rand_seed is not None, True)
        if c == 'normal':
            expect(p.screen_width, 375)
            expect(len(p.user_agent) <= 300, True)
            expect(p.user_agent.startswith('bot/1.0'), True)
        else:
            expect(p.field_maybe_none('screen_width'), None)
        # 原研究と同じ変数名で FAB が保存されている
        for f in C.FAB_FIELDS:
            expect(getattr(p, f), 4)
        if c == 'cq_fail':
            expect(p.cq1_pass, False)
            expect('cq' in p.exclude_reason_in_app, True)
            expect(p.excluded_in_app, True)
        else:
            expect(p.cq1_pass, True)
            expect(p.cq2_pass, True)
        if c == 'check_retry_ok':
            expect(p.dg_check_attempts, 2)
            expect(p.dg_check_pass, True)
        if c == 'check_fail':
            expect(p.dg_check_attempts, 2)
            expect(p.dg_check_pass, False)
            expect('check' in p.exclude_reason_in_app, True)
        if c in ('normal', 'zero_give', 'revise', 'bad_amount'):
            expect(p.excluded_in_app, False)
        if c == 'zero_give':
            expect(p.dg_give, 0)
            expect(p.dg_give_1, 0)
        if c == 'revise':
            expect(p.dg_correct, 2)
            expect(p.dg_give_1, 200)
            expect(p.dg_give_2, 400)
            expect(p.dg_give, 400)
        else:
            expect(p.dg_correct, 1)
            expect(p.dg_give_1, p.dg_give)
            expect(p.field_maybe_none('dg_give_2'), None)

    def survey(self, c, intro, page1, page2):
        yield intro
        for page_no, page in ((1, page1), (2, page2)):
            fields = survey_fields(self.player, page_no)
            answers = {f: 4 for f in fields}
            # 注意チェックの正答（原研究: cq1 = strongly disagree, cq2 = strongly agree）
            for cq, v in C.CQ_EXPECTED.items():
                if cq in answers:
                    answers[cq] = v
            if c == 'cq_fail' and 'cq1' in answers:
                answers['cq1'] = 4
            if page_no == 1:
                # 1 項目を未回答で送ると、そのページに留まる
                partial = dict(answers)
                partial.pop(fields[0])
                yield SubmissionMustFail(page, partial)
            yield page, answers

    def demog(self, page):
        yield SubmissionMustFail(page, dict(age=21, gender=1, grade='B3'))  # game_exp 未回答
        yield page, dict(age=21, gender=1, grade='B3', game_exp=False)

    def dg(self, c, correct, intro, check, predict, decide, confirm, again):
        cfg = self.session.config
        yield intro
        if c == 'check_retry_ok':
            yield SubmissionMustFail(check, dict(dg_check=C.CHECK_GIVE))  # 1 回目誤答 → 同じページ
            yield check, dict(dg_check=correct)
        elif c == 'check_fail':
            yield SubmissionMustFail(check, dict(dg_check=C.CHECK_GIVE))
            yield check, dict(dg_check=correct + 100)  # 2 回目も誤答だが通過する
        else:
            yield check, dict(dg_check=correct)
        if c == 'bad_amount':
            yield SubmissionMustFail(predict, dict(dg_predict=cfg['endowment'] + 1))
            yield SubmissionMustFail(predict, dict(dg_predict=-1))
            if cfg['dg_step'] > 1:
                yield SubmissionMustFail(predict, dict(dg_predict=cfg['dg_step'] // 2))
        yield predict, dict(dg_predict=300)
        if c == 'bad_amount':
            yield SubmissionMustFail(decide, dict(dg_give=cfg['endowment'] + 1))
            yield SubmissionMustFail(decide, dict(dg_give=-5))
            if cfg['dg_step'] > 1:
                yield SubmissionMustFail(decide, dict(dg_give=cfg['dg_step'] // 2))
        give = 0 if c == 'zero_give' else (200 if c == 'revise' else 300)
        yield decide, dict(dg_give=give)
        yield SubmissionMustFail(confirm, dict())  # 未選択では進めない
        if c == 'revise':
            yield confirm, dict(dg_correct=2)
            yield again, dict(dg_give=400)
        else:
            yield confirm, dict(dg_correct=1)
