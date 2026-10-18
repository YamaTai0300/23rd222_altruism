# -*- coding: utf-8 -*-
"""English texts = language of Studies 09, 11, 12 (Binder et al., 2026).

Provenance (see SOURCE): the English screens of the original SoSci survey are NOT on OSF. The general instructions and
the Dictator Game text are translated from the German original (Studies/03/03_thesis_blinded.pdf, appendix pp. 43-44)
and checked against the paper's Methods ("winner", "gift of $10.70", "another unknown participant who had not been
randomly selected as winner", "keep the money or share the amount"). The evaluation items and demographics are quoted
verbatim from the Study 11 codebook (Studies/11/11_codebook_raw.csv), the entry confirmation from the Study 09 codebook.
Placeholders {endowment} {currency} {base} {fee} {rate} are filled from the session config.
"""

SOURCE = dict(
    general_body='translated from German original (verbatim DE)', username_label='translated from German original',
    dg_round='translated from German original ("Glück und Pech")', dg_body='translated; wording cross-checked with paper Methods',
    dg_options='translated', dg_question='translated',
    disclosure_body='reconstructed (paper: "disclosed beforehand and were asked to act as if there were other real participants")',
    waiting_body='reconstructed', confirm_question='Study 09 codebook: dg_correct "Korrekte Eingabe?" Yes/No (wording reconstructed)',
    result_body='reconstructed from codebook variables dg_total / dg_payout',
    eval_items='verbatim (Study 11 codebook AG11_01-06)', demog='verbatim (Study 11 codebook)',
    debrief_body='translated from German original (abridged)',
)

TEXT = dict(
    title='Study on economic behavior',

    consent_title='Welcome',
    consent_body=[
        'Thank you for your interest in our study on economic behavior among participants. In this study you will take part '
        'in decision situations in which you can win or lose money.',
        'Participation is voluntary. Your answers are stored anonymously and used for research purposes only.',
    ],
    consent_fictive_note='Please note: the money in this study is not real.',
    consent_check='I have read the information and agree to take part.',
    fictive_check='I understand that the money in this study is not real.',
    consent_error='Please confirm all statements to take part.',

    disclosure_title='Important note on the decision situations',
    disclosure_body=[
        'The other participants you will interact with in the following decision situations are not real. '
        'Their decisions and usernames were determined in advance.',
        'Please nevertheless make your decisions as if they were real other participants.',
    ],

    general_title='General instructions',
    general_body=[
        'In the following you will be asked to take part in a series of decision situations. In doing so you will interact '
        'with different people. All participants learn only a self-chosen username of the participants they interact with.',
        'In the individual situations, different roles (winner, loser, dictator, reviewer, investor, judge) are randomly '
        'assigned among the participants. These will be explained in more detail in the respective situations. If not enough '
        'participants are online, the system will wait a maximum of 10 seconds and then read from a stored list of previous '
        'decisions.',
        'Several decision situations follow one after the other, in which you can win or lose money. As a basis for your '
        'decisions you have a base payout of {base} {currency}. At the end of the study, the amount from one decision '
        'situation will be selected at random, offset against your base payout of {base} {currency}, and paid out to you.',
    ],
    username_label='Please enter a username here that does not reveal your identity.',
    username_error='Please enter a username (2 to 20 characters).',

    waiting_title='Looking for participants …',
    waiting_body='Please wait until enough participants are online. The system waits a maximum of 10 seconds.',
    waiting_found='Participants found. The round begins.',

    dg_round='Round: Luck and bad luck',
    dg_body=[
        'You are lucky! You have been placed in our winner group. You are a winner in this round.',
        'The amount currently available is {endowment} {currency}. We give you this amount as a gift.',
        'You now have the following options:',
    ],
    dg_options=[
        'You can keep {endowment} {currency}.',
        'You can share the money with another participant of this study who was not placed in our winner group and did not '
        'receive a gift of money. This person remains anonymous to you, and you remain anonymous to this person.',
    ],
    dg_question='How much of the {endowment} {currency} do you give to a person in the bad-luck group?',
    dg_unit='{currency}',
    dg_error='Please enter an amount between 0 and {endowment} {currency} (up to two decimal places).',

    confirm_title='Is your entry correct?',
    confirm_question='You entered: {give} {currency}. You keep {keep} {currency}. Is this entry correct?',
    confirm_options=[[1, 'Yes'], [2, 'No']],
    confirm_error='Please choose Yes or No.',
    again_lead='Please enter your decision again.',

    result_title='Round: Luck and bad luck – result',
    result_body=[
        'You gave {give} {currency} to a person in the bad-luck group and keep {keep} {currency}.',
    ],
    result_payout_none='Reminder: the money in this study is not real.',
    result_payout_flat='For this round you receive {fee} {currency}, regardless of your decision.',
    result_payout_conversion='If this round is selected at the end, your earnings are converted at a rate of 1:{rate}: '
                             'you then receive {bonus} {currency} in addition to your base payout.',

    eval_title='Evaluation',
    eval_intro='Please indicate how much you agree with the following statements.',
    likert6=['strongly disagree', 'disagree', 'rather disagree', 'rather agree', 'agree', 'strongly agree'],
    eval_items=dict(
        eval_1='Completing this survey took too long.',
        eval_2='It was difficult to make decisions in the interactive situations.',
        eval_3='Interactions with other fictional participants felt unrealistic.',
        eval_4='My decisions in these online situations reflect my decisions in real-life interaction.',
        eval_5='Overall, these interactive situations were easy to understand.',
        eval_6='I was distracted while participating.',
    ),
    eval_open='Did you notice anything during the study? (optional)',
    required_error='Please answer all statements.',

    demog_title='About you',
    demog_gender='What best describes your gender?',
    gender_options=[[1, 'female'], [2, 'male'], [3, 'prefer to self-describe']],
    demog_age='How old are you? I am ... years old.',
    demog_edu='What is your highest professional qualification?',
    edu_options=[
        [1, 'No professional qualifications'], [2, 'Vocational training period with diploma'],
        [3, '(Compact) vocational training program/course'], [4, 'Completed industrial or agricultural apprenticeship'],
        [5, 'Completed commercial traineeship'], [6, 'Internship, practical training'], [7, 'Specialized vocational qualification'],
        [8, 'General vocational qualification'], [9, 'Master/technical certification or equivalent vocational qualification'],
        [10, 'University/College studies ongoing'], [11, 'Vocational university/university of applied sciences degree'],
        [12, 'University degree'], [13, 'Other degree'],
    ],

    debrief_title='Debriefing',
    debrief_body=[
        'Thank you for taking part in our study! Finally, we ask you to read the following debriefing carefully.',
        'You took part in a study in which we use so-called economic games to measure decision behavior in different '
        'situations and interactions with other people. We wanted to examine the relationship between a questionnaire '
        'measuring altruism and decisions in economic situations – in this case voluntary sharing.',
        'However, the other people in this study were fictitious. We let you believe that you were interacting with real '
        'people in order to make the situations appear as realistic as possible. In research we sometimes have to weigh '
        'standardization and experimental precision against fully informing participants in advance. Our procedure was '
        'reviewed by the ethics committee of our department beforehand.',
        'With the decisions you have just made online, we do not capture your entire behavior, only individual behaviors in '
        'specific situations. We also only look at group values.',
    ],

    end_title='Thank you!',
    end_body='The study is finished. Your payout: {payout} {currency}.',
    end_body_none='The study is finished.',
)
