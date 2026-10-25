# -*- coding: utf-8 -*-
"""English texts (v0.2). Keys mirror ja.py.

Sources (all at https://osf.io/t5mf2/)
- FAB items: Supplement.pdf S1, quoted verbatim. Keys are the original variable names (hg_1 ... mc_23).
- FAB instruction: Studies/11/11_codebook_raw.csv, QUESTION column.
- Control questions: Studies/09 and 11 codebooks (cq1 = "strongly disagree", cq2 = "strongly agree").
- Dictator Game wording: Studies/03/03_thesis_blinded.pdf appendix p.44 (German, translated) and the paper's Methods.
- Entry confirmation (dg_correct): Studies/09 codebook / preprocessing.R.
- Post-task evaluation items: Studies/11 codebook (AG11_01-06).
"""

TEXT = dict(
    title='Decision Study',

    consent_title='Invitation to take part',
    consent_body=[
        'You are invited to take part in a study on decision making and everyday behavior. It takes about 15 minutes, '
        'can be done at any time and place on your own smartphone or computer, and consists of a short decision task and a questionnaire.',
        'You will receive {fee} {currency} for taking part, plus an amount that depends on the decision task (how to receive it is explained on the final page).',
        'Participation is voluntary. Once you start, please complete the study in one sitting without interruption (about 15 minutes). '
        'If you want to stop, close this page; incomplete responses are not kept and no payment can be made.',
        'Your answers are stored under a random participant code; no names or email addresses are stored with them. '
        'Anonymized data may be shared publicly for research.',
        'Contact: [researcher name, affiliation, email]',
    ],
    consent_check='I have read the above and agree to take part.',
    age_check='I am 18 years or older.',
    student_check='I am a student at [university].',
    consent_error='To take part, please tick all three boxes.',

    code_title='Your participant code',
    code_body='Your participant code is shown below. Please write it down or take a screenshot: you will need it to receive your payment.',
    code_note='Do not close this tab until you reach the final page. If your connection drops, open the same URL again to continue where you left off.',

    survey_title='Questionnaire',
    survey_intro=[
        'The following pages show statements about how people behave and act in everyday life.',
        'Please state honestly and spontaneously how you would typically behave or act. '
        'Answers are on a six-point scale. There are no right or wrong answers.',
    ],
    survey_intro_short='Please state honestly and spontaneously how you would typically behave or act.',
    likert6=['strongly disagree', 'disagree', 'rather disagree', 'rather agree', 'agree', 'strongly agree'],
    required_error='Some items are unanswered. Please answer all items on this page.',

    items=dict(
        # Help Giving (S1)
        hg_1='When unsure, I rather stand with the weak than the strong.',
        hg_3='I would jeopardize my own well-being in order to help the sick and hungry.',
        hg_7='In an emergency I would probably spontaneously risk my own life to save complete strangers.',
        hg_10='Despite potential costs I might incur, I support people whether or not I know them personally.',
        hg_13='I often do good things for others without reservation or expectations.',
        # Peer Punishment (S1)
        pp_1='When someone demands special privileges for themselves, I look for others with whom I can try to stop them.',
        pp_8='When someone purposely takes advantage of the community, I discretely get back at them in one way or another.',
        pp_12='I pay close attention to whether someone misbehaves in a team.',
        pp_14="If someone benefits at the expense of everyone else, I secretly try to ensure that they don't succeed.",
        pp_15='Those who construe the rules to their advantage will sooner or later be held accountable by my friends and me.',
        # Moral Courage (S1)
        mc_1='I openly question the decisions of authorities or superiors.',
        mc_3='It has happened that I have affronted others due to my moral convictions.',
        mc_18='I try to carry through with policies that are important for everyone, even if the general public disagrees with them.',
        mc_20='I fight against unjust instructions from authorities, even if it costs me more than it benefits me.',
        mc_23='In a conflict, I confront the attacker.',
        # Control questions (original wording; expected cq1 = 1, cq2 = 6)
        cq1='Please tick the option "strongly disagree" for this question. This is a control question.',
        cq2='Please tick the option "strongly agree" for this question. This is a control question.',
        # HEXACO-60 Honesty-Humility (Ashton & Lee, 2009; hexaco.org, free for research use). hex_1..hex_10 = HEXACO-60 items
        # 6, 12R, 18, 24R, 30R, 36, 42R, 48R, 54, 60R (R = reverse-keyed; see codebook.csv). Transcribed from memory on 2026-10-24:
        # verify against hexaco.org before use. Note: shown on the FAB 6-point scale (original HEXACO uses 5 points).
        hex_1="I wouldn't use flattery to get a raise or promotion at work, even if I thought it would succeed.",
        hex_2="If I knew that I could never get caught, I would be willing to steal a million dollars.",
        hex_3="Having a lot of money is not especially important to me.",
        hex_4="I think that I am entitled to more respect than the average person is.",
        hex_5="If I want something from someone, I will laugh at that person's worst jokes.",
        hex_6="I would never accept a bribe, even if it were very large.",
        hex_7="I would get a lot of pleasure from owning expensive luxury goods.",
        hex_8="I want people to know that I am an important person of high status.",
        hex_9="I wouldn't pretend to like someone just to get that person to do favors for me.",
        hex_10="I'd be tempted to use counterfeit money, if I were sure I could get away with it.",
    ),

    demog_title='About you',
    demog_intro='Please tell us a little about yourself.',
    demog_age='Age',
    demog_gender='Gender',
    gender_options=[[1, 'Male'], [2, 'Female'], [3, 'Other'], [4, 'Prefer not to say']],
    demog_grade='Year',
    grade_options=[
        ['B1', '1st year undergraduate'], ['B2', '2nd year undergraduate'], ['B3', '3rd year undergraduate'],
        ['B4', '4th year undergraduate'], ['M1', "Master's 1st year"], ['M2', "Master's 2nd year"],
        ['D', 'Doctoral'], ['other', 'Other'],
    ],
    demog_game_exp='Have you ever taken part in an economic experiment or a money-splitting task like this before?',
    game_exp_options=[[True, 'Yes'], [False, 'No']],

    # Dictator Game. Original (Study 03 appendix p.44): "You are lucky! You are in our winner group ... We give you this
    # amount as a gift. 1. You can keep it. 2. You can share it with another participant who was not in the winner group and
    # received no gift. That person stays anonymous to you and you to them. How much do you give to a person in the unlucky group?"
    # Rewritten for the role-uncertainty design (everyone decides as if they were in the winner group).
    dg_intro_title='Decision Task',
    dg_round_name='"Lucky" and "unlucky"',
    dg_intro_body=[
        'In this task you will be paired with one other person who takes part in this study at some point during the study period. '
        'You never meet or interact online, and neither of you will learn who the other is.',
        'After the study closes, a computer lottery splits all participants into a "lucky group" and an "unlucky group" of equal size '
        'and pairs one person from the lucky group with one person from the unlucky group.',
        'Each person in the lucky group receives a gift of {endowment} {currency}. People in the lucky group have two options:',
        'Because the lottery has not been drawn yet, everyone now decides as if they were in the lucky group. '
        'The decisions of those who end up in the lucky group are carried out exactly: they keep what they did not give, '
        'and their partner in the unlucky group receives what was given.',
        'Payments are made later together with the participation fee of {fee} {currency}. You decide only once. There are no right or wrong answers.',
    ],
    dg_options=[
        'Keep the whole {endowment} {currency}.',
        'Share any part of it, or all of it, with the paired person in the unlucky group (who received no gift). '
        'That person stays anonymous to you, and you stay anonymous to them.',
    ],
    dg_intro_example='Example: if a person in the lucky group gives 200 {currency}, they keep 800 {currency} and their partner receives 200 {currency}.',

    check_title='Comprehension question',
    check_question='Suppose you are in the lucky group and decide to give {check_amount} {currency} to your partner. How much do you keep?',
    check_unit='{currency}',
    check_retry='That is not correct. Please read the description below again and answer once more.',

    predict_title='Before you decide',
    predict_question='Before you decide: how much do you think you will actually give to your partner?',
    predict_note='This answer does not affect any payment.',

    decision_title='Your decision',
    decision_lead='Suppose you are in the lucky group. You receive a gift of {endowment} {currency}.',
    decision_question='How much of the {endowment} {currency} do you give to your partner in the unlucky group?',
    decision_hint='Enter any amount from 0 to {endowment} ({currency}).',
    decision_keep='You keep',
    decision_other='Your partner receives',
    amount_error='Please enter an amount from 0 to {endowment} in steps of {step} {currency}.',

    confirm_title='Please check your entry',
    confirm_body='You give {give} {currency} to your partner and keep {keep} {currency}. Is this entry correct?',
    confirm_options=[[1, 'Yes, it is correct'], [2, 'No, I want to enter it again']],
    confirm_error='Please choose one option.',
    decision_again_lead='Please enter your decision again. This entry will be final.',

    post_title='Finally',
    post_intro='A few questions about this study. Please indicate how much you agree with each statement.',
    post_items=dict(
        eval_understand='Overall, the decision task was easy to understand.',
        eval_difficult='It was difficult to make a decision in the decision task.',
        eval_reflect='My decision in the decision task reflects my decisions in real-life interaction.',
        eval_distract='I was distracted while participating.',
    ),
    post_comment='If you noticed anything or have any comments about this study, please write them here (optional).',

    end_title='Thank you',
    end_body=[
        'The study is now complete. Your participant code is shown below.',
        'To receive your payment, open the contact form with the button below and enter your email address (the form already contains your code).',
        'Pairs and the lucky/unlucky lottery are drawn after the study closes. How and when you receive your payment will be sent to the email address you enter.',
        'You may now close this page.',
    ],
    end_code_label='Participant code',
    end_button='Open the contact form',
)
