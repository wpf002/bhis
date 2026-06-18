"""
BHIS Doctrinal Integrity Questions — Watermark Foundation
----------------------------------------------------------
All 10 Pillar 1 questions are anchored to specific sections of
Watermark Community Church's Full Doctrinal Statement.

Each question tests a core doctrine from the statement. Wrong answers
correspond to real theological errors that exist in evangelical churches —
not strawmen. The scoring reflects how far each error is from orthodoxy.

Section references:
  S1 = The Bible        S7 = Salvation
  S2 = The Trinity      S8 = Sanctification
  S3 = Jesus Christ     S9 = The Church
  S4 = Holy Spirit      S10 = Ordinances
  S6 = Man / Sin        S11 = End Times
"""

DOC = "doctrinal_integrity"
MC  = "mc"
L   = "likert"
SC  = "scenario"
FP  = "forced_prioritization"
OE  = "open_ended"

# Format:
# (q_num, pillar, q_type, question_text, is_cc, cc_pair, church_sig, indiv_sig,
#  qual_only, options: [(letter, text, score, is_correct, is_drift)])

PILLAR_1_QUESTIONS = [

    # Q1 — Salvation mechanism (S7)
    # Tests: grace through faith alone vs. moralism, sacramentalism, sincerity religion
    (1, DOC, MC,
     "According to Scripture, how is a person made right with God?",
     False, None, True, True, False, [
         ("a", "By living a moral life, treating others well, and genuinely trying to be good",
          20, False, False),
         ("b", "By trusting personally in Jesus Christ's death and resurrection as the complete "
               "payment for sin — not by anything we do",
          100, True, False),
         ("c", "By sincerely believing in God and doing your best to follow his teaching",
          30, False, False),
         ("d", "By participating in church, receiving baptism, and living as a committed Christian",
          25, False, False),
     ]),

    # Q2 — Scripture authority (S1) — contradiction pair with Q11
    # Tests: verbal inspiration, inerrancy, Scripture as supreme authority
    (2, DOC, L,
     "The Bible is the verbally inspired, inerrant Word of God and the supreme authority "
     "over what I believe and how I live.",
     True, 11, True, True, False, []),

    # Q3 — Exclusivity of Christ / universalism check (S3, S7, S11)
    # Tests: John 14:6, Acts 4:12 — also catches universalism (S11 error)
    (3, DOC, MC,
     "Which statement most honestly reflects your view of how people are saved?",
     False, None, True, True, False, [
         ("a", "There are many paths to God and Christianity is one sincere and valid option",
          10, False, True),
         ("b", "Jesus Christ is the only way to be forgiven and reconciled to God — no one comes "
               "to the Father except through him",
          100, True, False),
         ("c", "God ultimately saves all people because his love is greater than human sin",
          10, False, True),
         ("d", "Sincere faith in any conception of God is sufficient — what matters is the "
               "genuineness of belief, not the specific object",
          15, False, True),
     ]),

    # Q4 — Nature of sin (S6)
    # Tests: total depravity, sin as rebellion against God (not just harm to others or social failure)
    (4, DOC, MC,
     "What does the Bible primarily teach about the nature of sin?",
     False, None, False, True, False, [
         ("a", "Sin is mainly about harming other people — it's measured by the damage it causes",
          20, False, False),
         ("b", "Sin is the failure to reach your personal potential or live your best life",
          10, False, False),
         ("c", "Sin is rebellion against God that is universal, leaves us unable to save ourselves, "
               "and requires God's forgiveness through Christ",
          100, True, False),
         ("d", "Sin is largely a product of environment, trauma, and circumstance — people sin "
               "because of what was done to them",
          15, False, False),
     ]),

    # Q5 — Gospel confidence (S7) — contradiction pair with Q33
    # Tests gospel clarity — are members equipped to articulate it?
    (5, DOC, L,
     "I am confident I could clearly explain to someone how they can be forgiven and "
     "reconciled to God through Jesus Christ.",
     True, 33, False, True, False, []),

    # Q6 — The Trinity (S2)
    # Tests: one God, three distinct persons — distinguishes from Modalism, Tritheism, Arianism
    (6, DOC, MC,
     "Which statement best describes what the Bible teaches about God?",
     False, None, False, True, False, [
         ("a", "God is one person who reveals himself in three different ways depending on the situation "
               "(as Father, then as Son, then as Spirit)",
          20, False, False),
         ("b", "There is one God who exists as three distinct persons — Father, Son, and Holy Spirit — "
               "each fully God, and each a distinct person",
          100, True, False),
         ("c", "The Father, Son, and Holy Spirit are three separate gods who work together in unity",
          15, False, False),
         ("d", "Jesus was the greatest being God created, but he is not himself fully and eternally God",
          10, False, False),
     ]),

    # Q7 — Sanctification understanding (S8)
    # Tests: positional + progressive model, not perfectionism, not passive
    (7, DOC, MC,
     "Which statement best describes what the Bible means by 'sanctification'?",
     False, None, False, True, False, [
         ("a", "Sanctification means achieving a state of sinless perfection during this lifetime "
               "through disciplined effort",
          15, False, False),
         ("b", "Sanctification means the believer is set apart in Christ (completely and permanently) "
               "and is also progressively growing in holiness by the Spirit's power, still in "
               "conflict with sin",
          100, True, False),
         ("c", "Sanctification is the same as justification — it refers to being forgiven at the "
               "moment of salvation",
          20, False, False),
         ("d", "Sanctification is optional spiritual growth for Christians who want to go deeper — "
               "most believers will stay at the basic level",
          10, False, False),
     ]),

    # Q8 — The Holy Spirit's role (S4)
    # Tests: Spirit as divine person who regenerates, indwells all believers — not a force
    (8, DOC, MC,
     "According to Scripture, what is the role of the Holy Spirit in the life of a believer?",
     False, None, False, True, False, [
         ("a", "The Spirit is a divine force or energy that God sends to assist believers in "
               "difficult moments",
          15, False, False),
         ("b", "The Spirit is given only to especially devoted or mature believers as a reward "
               "for spiritual growth",
          10, False, False),
         ("c", "The Spirit is a divine person who, from the moment of belief in Christ, indwells "
               "every believer, seals them for salvation, regenerates them, and empowers ongoing "
               "growth in holiness",
          100, True, False),
         ("d", "The Spirit's primary work is giving miraculous gifts — speaking in tongues and "
               "healing are signs of his presence in every believer's life",
          30, False, False),
     ]),

    # Q9 — End times / eternal state (S11)
    # Tests: personal return of Christ, bodily resurrection, final judgment, eternal punishment
    (9, DOC, MC,
     "Which statement most accurately reflects what Scripture teaches about what happens "
     "after death and at the end of history?",
     False, None, False, True, False, [
         ("a", "All people will eventually be reconciled to God — his love ensures that no one "
               "is lost forever",
          10, False, True),
         ("b", "After death, people get additional opportunities to accept Christ before final judgment",
          15, False, False),
         ("c", "Jesus Christ will personally and visibly return, the dead will be raised bodily, "
               "and God will judge all people — the righteous to eternal life with him, the "
               "unrighteous to eternal punishment",
          100, True, False),
         ("d", "Heaven and Hell are primarily spiritual states of experience in this life, not "
               "literal future realities",
          10, False, True),
     ]),

    # Q10 — Forced prioritization (S1, S3, S7, S9)
    # Reveals what members actually think matters most — analyzed at church level only
    (10, DOC, FP,
     "Rank these four things from most to least important in your understanding of what "
     "Christian maturity actually looks like.",
     False, None, True, False, False, [
         ("a", "Holding sound doctrine — knowing what the Bible actually teaches", 0, False, False),
         ("b", "Living a transformed, holy life that reflects genuine change", 0, False, False),
         ("c", "Serving others and demonstrating Christlike love in relationships", 0, False, False),
         ("d", "Sharing the gospel and helping others become disciples", 0, False, False),
     ]),
]
