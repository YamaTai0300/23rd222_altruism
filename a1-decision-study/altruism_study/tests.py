"""ボットテスト（設計書 §10.1）v0.6。

実行: otree test a1_ja 24   （24 名 × 6 ケース。4 名ごとに task_order × scale_order の 4 通りが揃う）
ケース:
  normal          正常系（注意チェック正答、理解確認 1 回で正答、300 円を分ける）
  cq_fail         注意チェック cq1 に誤答 → exclude_reason_in_app に 'cq'
  check_retry_ok  理解確認 1 回目誤答 → 再回答で正答 → dg_check_pass = True, attempts = 2
  check_fail      理解確認 2 回とも誤答 → dg_check_pass = False だが最後まで進める
  zero_give       0 円を分ける → dg_share = False
  bad_amount      範囲外・刻み違いの額は受け付けない（元手超過、負の値、dg_step の倍数でない値）
v0.5 で外したもの: revise（入力確認）、属性、自己予測、参加者コードページ。
v0.6: 実験 ID（exp_id）が 10 桁の数字で、セッション内で重複しないことを検査。
"""
from otree.api import Bot, Submission, SubmissionMustFail, expect

from . import (
    C,
    Consent,
    HexFirstA, FabPage1A, FabPage2A, HexLastA, DGIntroA, DGCheckA, DGDecisionA,
    DGIntroB, DGCheckB, DGDecisionB, HexFirstB, FabPage1B, FabPage2B, HexLastB,
    PostSurvey,
    End,
    fab_fields, hex_fields,
)


class PlayerBot(Bot):
    cases = ['normal', 'cq_fail', 'check_retry_ok', 'check_fail', 'zero_give', 'bad_amount']

    def play_round(self):
        c = self.case
        cfg = self.session.config
        correct = cfg['endowment'] - C.CHECK_GIVE

        # 同意: 2 項目とも必須。hidden の来歴項目はブラウザが埋めるが、未取得でも進める
        yield SubmissionMustFail(Consent, dict(consent=True, eligible_confirm=''))  # '' = 未チェック
        if c == 'normal':
            yield Consent, dict(consent=True, eligible_confirm=True, user_agent='bot/1.0 ' + 'x' * 400, screen_width=375)
        else:
            yield Consent, dict(consent=True, eligible_confirm=True)

        if self.player.task_order == 1:
            yield from self.survey(c, HexFirstA, FabPage1A, FabPage2A, HexLastA)
            yield from self.dg(c, correct, DGIntroA, DGCheckA, DGDecisionA)
        else:
            yield from self.dg(c, correct, DGIntroB, DGCheckB, DGDecisionB)
            yield from self.survey(c, HexFirstB, FabPage1B, FabPage2B, HexLastB)

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
        expect(len(p.fab_item_order.split(',')), 17)  # FAB 15 + 注意チェック 2
        # v0.6: 実験 ID は 10 桁の数字で、同じセッションの他の参加者と重ならない
        expect(len(p.exp_id), 10)
        expect(p.exp_id.isdigit(), True)
        expect(sum(1 for q in p.subsession.get_players() if q.field_maybe_none('exp_id') == p.exp_id), 1)
        if cfg['use_hexaco']:
            expect(p.scale_order in (1, 2), True)
            expect(len(p.hex_item_order.split(',')), 10)
            expect(sorted(p.hex_item_order.split(',')), sorted(C.HEX_FIELDS))
            for f in C.HEX_FIELDS:
                expect(getattr(p, f), 3)  # 5 件法の中央
        else:
            expect(p.scale_order, 0)
            expect(p.hex_item_order, '')
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
        if c in ('normal', 'zero_give', 'bad_amount'):
            expect(p.excluded_in_app, False)
        if c == 'zero_give':
            expect(p.dg_give, 0)

    def survey(self, c, hex_first, fab1, fab2, hex_last):
        cfg = self.session.config
        hexaco = bool(cfg['use_hexaco'])
        if hexaco and self.player.scale_order == 2:
            yield from self.hex_stage(hex_first)
        for page_no, page in ((1, fab1), (2, fab2)):
            fields = fab_fields(self.player, page_no)
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
        if hexaco and self.player.scale_order == 1:
            yield from self.hex_stage(hex_last)

    def hex_stage(self, page):
        fields = hex_fields(self.player)
        expect(len(fields), 10)
        answers = {f: 3 for f in fields}
        yield SubmissionMustFail(page, {f: 6 for f in fields})   # 6 は 5 件法の範囲外
        partial = dict(answers)
        partial.pop(fields[-1])
        yield SubmissionMustFail(page, partial)                  # 未回答があれば留まる
        yield page, answers

    def dg(self, c, correct, intro, check, decide):
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
            yield SubmissionMustFail(decide, dict(dg_give=cfg['endowment'] + 1))
            yield SubmissionMustFail(decide, dict(dg_give=-5))
            if cfg['dg_step'] > 1:
                yield SubmissionMustFail(decide, dict(dg_give=cfg['dg_step'] // 2))
        give = 0 if c == 'zero_give' else 300
        yield decide, dict(dg_give=give)
