# -*- coding: utf-8 -*-
"""Deutsche Texte = Originalsprache der Studien 03, 13, 15 (Binder et al., 2026).

Herkunft (siehe SOURCE unten):
  verbatim      wörtlich aus Studies/03/03_thesis_blinded.pdf, Anhang S. 43–44 (Allgemeine Instruktionen, Dictator Game)
                bzw. S. 49 (Aufklärung) – OSF T5MF2
  reconstructed aus der Beschreibung im Paper (Methods) bzw. den Codebooks (Studies/09, 11) rekonstruiert; der genaue
                Wortlaut der SoSci-Survey-Seiten ist auf OSF nicht enthalten
Platzhalter: {endowment} {currency} {base} {fee} {rate} werden aus der Session-Config gefüllt.
"""

SOURCE = dict(
    general_title='verbatim', general_body='verbatim', username_label='verbatim',
    dg_round='verbatim', dg_body='verbatim', dg_options='verbatim', dg_question='verbatim', dg_unit='verbatim',
    debrief_title='verbatim', debrief_body='verbatim (gekürzt)',
    consent_body='reconstructed', disclosure_body='reconstructed (Paper: "disclosed beforehand and asked to act as if")',
    waiting_body='reconstructed (Allgemeine Instruktionen: "maximal 10 Sekunden warten")',
    confirm_question='reconstructed (Codebook Studie 09: dg_correct "Korrekte Eingabe?" Ja/Nein)',
    result_body='reconstructed (Codebook: dg_total "Gewinn total", dg_payout "Auszahlung")',
    eval_items='reconstructed (Codebook Studie 11, AG11_01–06, dort englisch)',
    demog='reconstructed (Codebook Studie 11)',
)

TEXT = dict(
    title='Studie zu wirtschaftlichem Verhalten',  # Cover-Story lt. Thesis S. 13: "Untersuchung wirtschaftlichen Verhaltens"

    # ---- Einverständnis ----
    consent_title='Herzlich willkommen',
    consent_body=[
        'Vielen Dank für Ihr Interesse an unserer Studie zu wirtschaftlichem Verhalten unter Teilnehmenden. '
        'Sie nehmen in dieser Studie an Entscheidungssituationen teil, in denen Sie Geld gewinnen oder verlieren können.',
        'Ihre Teilnahme ist freiwillig. Ihre Angaben werden anonym gespeichert und ausschließlich zu Forschungszwecken verwendet.',
    ],
    consent_fictive_note='Bitte beachten Sie: Es handelt sich in dieser Studie nicht um reales Geld.',  # Studie 03 (Thesis S. 14)
    consent_check='Ich habe die Informationen gelesen und bin mit der Teilnahme einverstanden.',
    fictive_check='Ich habe verstanden, dass es sich nicht um reales Geld handelt.',
    consent_error='Bitte bestätigen Sie alle Angaben, um teilzunehmen.',

    # ---- Offenlegung vorab (nur ohne Täuschung: Studien 09, 11, 12, 13) ----
    disclosure_title='Wichtiger Hinweis zu den Entscheidungssituationen',
    disclosure_body=[
        'Die anderen Teilnehmenden, mit denen Sie in den folgenden Entscheidungssituationen interagieren, sind nicht real. '
        'Ihre Entscheidungen und Benutzernamen wurden im Voraus festgelegt.',
        'Bitte treffen Sie Ihre Entscheidungen trotzdem so, als ob es sich um echte andere Teilnehmende handeln würde.',
    ],

    # ---- Allgemeine Instruktionen (Thesis Anhang S. 43, wörtlich) ----
    general_title='Allgemeine Instruktionen',
    general_body=[
        'Sie werden im Folgenden gebeten, an einer Reihe von Entscheidungssituationen teilzunehmen. Dabei werden Sie mit '
        'unterschiedlichen Personen in Interaktion treten. Alle Teilnehmende erfahren von den Teilnehmenden, mit denen sie '
        'interagieren, nur einen selbst ausgewählten Benutzernamen.',
        'In den einzelnen Situationen werden unter den Teilnehmenden verschiedene Funktionen (Gewinner*in, Verlierer*in, '
        'Diktator*in, Gutachter*in, Investor*in, Richter*in) zufällig verteilt. Diese werden in den jeweiligen Situationen '
        'näher erklärt. Wenn nicht genügend Teilnehmende online sind, wird das System maximal 10 Sekunden warten und dann '
        'aus einer gespeicherten Liste von früheren Entscheidungen auslesen.',
        'Es folgen mehrere Entscheidungssituationen aufeinander, in denen Sie Geld gewinnen oder verlieren können. '
        'Als Grundlage für Ihre Entscheidungen steht Ihnen eine Grundauszahlung von {base} {currency} zur Verfügung. '
        'Am Ende der Studie wird der Betrag einer Entscheidungssituation per Zufall ausgewählt, mit Ihrer Grundauszahlung '
        'von {base} {currency} verrechnet und Ihnen ausgezahlt.',
    ],
    username_label='Geben Sie hier bitte einen Benutzernamen ein, der nicht auf Ihre Identität schließen lässt.',
    username_error='Bitte geben Sie einen Benutzernamen ein (2 bis 20 Zeichen).',

    # ---- Warten auf Teilnehmende (rekonstruiert) ----
    waiting_title='Teilnehmende werden gesucht …',
    waiting_body='Bitte warten Sie, bis genügend Teilnehmende online sind. Das System wartet maximal 10 Sekunden.',
    waiting_found='Teilnehmende gefunden. Die Runde beginnt.',

    # ---- Dictator Game (Thesis Anhang S. 44, wörtlich) ----
    dg_round='Runde: Glück und Pech',
    dg_body=[
        'Sie haben Glück! Sie sind in unsere Gewinn-Gruppe geraten. Sie sind in dieser Runde ein*e Gewinner*in.',
        'Die derzeit zur Verfügung stehende Summe beträgt {endowment} {currency}. Wir schenken Ihnen diesen Betrag.',
        'Sie haben nun folgende Möglichkeiten:',
    ],
    dg_options=[
        'Sie können {endowment} {currency} behalten.',
        'Sie können das Geld mit einer anderen teilnehmenden Person dieser Studie teilen, die nicht in unsere Gewinn-Gruppe '
        'geraten ist und kein Geldgeschenk erhalten hat. Diese Person bleibt für Sie anonym und auch Sie bleiben für die '
        'Person anonym.',
    ],
    dg_question='Wieviel von den {endowment} {currency} geben Sie an eine Person in der Pech-Gruppe ab?',
    dg_unit='{currency}',
    dg_error='Bitte geben Sie einen Betrag zwischen 0 und {endowment} {currency} ein (bis zu zwei Nachkommastellen).',

    # ---- Korrekte Eingabe? (Studie 09) ----
    confirm_title='Korrekte Eingabe?',
    confirm_question='Sie haben eingegeben: {give} {currency}. Sie behalten {keep} {currency}. Ist diese Eingabe korrekt?',
    confirm_options=[[1, 'Ja'], [2, 'Nein']],
    confirm_error='Bitte wählen Sie Ja oder Nein.',
    again_lead='Bitte geben Sie Ihre Entscheidung erneut ein.',

    # ---- Ergebnis (rekonstruiert aus dg_total / dg_payout) ----
    result_title='Runde: Glück und Pech – Ergebnis',
    result_body=[
        'Sie haben {give} {currency} an eine Person in der Pech-Gruppe abgegeben und behalten {keep} {currency}.',
    ],
    result_payout_none='Zur Erinnerung: In dieser Studie handelt es sich nicht um reales Geld.',
    result_payout_flat='Für diese Runde erhalten Sie unabhängig von Ihrer Entscheidung {fee} {currency}.',
    result_payout_conversion='Wird diese Runde am Ende ausgewählt, wird Ihr Gewinn im Verhältnis 1:{rate} umgerechnet: '
                             'Sie erhalten dann {bonus} {currency} zusätzlich zu Ihrer Grundauszahlung.',

    # ---- Nachbefragung (Studie 11, AG11; englische Originalitems, hier übersetzt) ----
    eval_title='Nachbefragung',
    eval_intro='Bitte geben Sie an, inwieweit Sie den folgenden Aussagen zustimmen.',
    likert6=['stimme überhaupt nicht zu', 'stimme nicht zu', 'stimme eher nicht zu', 'stimme eher zu', 'stimme zu', 'stimme voll und ganz zu'],
    eval_items=dict(
        eval_1='Die Bearbeitung dieser Studie hat zu lange gedauert.',
        eval_2='Es war schwierig, in den interaktiven Situationen Entscheidungen zu treffen.',
        eval_3='Die Interaktionen mit den anderen (fiktiven) Teilnehmenden wirkten unrealistisch.',
        eval_4='Meine Entscheidungen in diesen Online-Situationen spiegeln meine Entscheidungen in realen Interaktionen wider.',
        eval_5='Insgesamt waren die interaktiven Situationen leicht zu verstehen.',
        eval_6='Ich war während der Teilnahme abgelenkt.',
    ),
    eval_open='Ist Ihnen während der Studie etwas aufgefallen? (optional)',
    required_error='Bitte beantworten Sie alle Aussagen.',

    # ---- Demografie (Studie 11) ----
    demog_title='Angaben zur Person',
    demog_gender='Was beschreibt Ihr Geschlecht am besten?',
    gender_options=[[1, 'weiblich'], [2, 'männlich'], [3, 'divers / selbst beschreiben']],
    demog_age='Wie alt sind Sie? Ich bin ... Jahre alt.',
    demog_edu='Was ist Ihr höchster beruflicher Abschluss?',
    edu_options=[
        [1, 'Kein beruflicher Abschluss'], [2, 'Berufsausbildung mit Abschluss'], [3, 'Berufsfachschule / Kurs'],
        [4, 'Gewerbliche oder landwirtschaftliche Lehre'], [5, 'Kaufmännische Lehre'], [6, 'Praktikum / Volontariat'],
        [7, 'Fachschulabschluss'], [8, 'Allgemeiner beruflicher Abschluss'], [9, 'Meister / Techniker oder gleichwertig'],
        [10, 'Studium laufend'], [11, 'Fachhochschulabschluss'], [12, 'Universitätsabschluss'], [13, 'Anderer Abschluss'],
    ],

    # ---- Aufklärung (nur mit Täuschung; Thesis Anhang S. 49, gekürzt) ----
    debrief_title='Aufklärung',
    debrief_body=[
        'Vielen Dank für Ihre Teilnahme an unserer Studie! Als letztes möchten wir Sie bitten, die folgende Aufklärung '
        'gründlich durchzulesen.',
        'Sie haben an einer Studie teilgenommen, in der wir sogenannte Ökonomische Spiele einsetzen, um Entscheidungsverhalten '
        'in unterschiedlichen Situationen und Interaktionen mit anderen Personen zu erfassen. Dabei wollten wir den Zusammenhang '
        'zwischen einem Fragebogen zur Erfassung von Altruismus und Entscheidungen in wirtschaftlichen Situationen – in diesem '
        'Fall freiwilliges Teilen – untersuchen.',
        'Allerdings waren die Personen in dieser Studie fiktiv. Wir haben Sie in dem Glauben gelassen, dass Sie mit realen '
        'Personen interagieren, um die Situationen so realitätsnah wie möglich erscheinen zu lassen. In der Forschung müssen '
        'wir manchmal zwischen Standardisierung bzw. experimenteller Präzision einerseits und vollständiger Vorab-Informierung '
        'der Teilnehmenden andererseits abwägen. Unser Vorgehen wurde von der Ethikkommission unseres Fachbereichs im Vorfeld '
        'überprüft.',
        'Mit den Entscheidungen, die Sie gerade online getroffen haben, erfassen wir nicht Ihr gesamtes Verhalten, sondern '
        'lediglich einzelne Verhaltensweisen in spezifischen Situationen. Wir betrachten auch nur Gruppenwerte.',
    ],

    # ---- Ende ----
    end_title='Vielen Dank!',
    end_body='Die Studie ist beendet. Ihre Auszahlung: {payout} {currency}.',
    end_body_none='Die Studie ist beendet.',
)
