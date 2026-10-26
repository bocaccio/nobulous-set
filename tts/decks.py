"""Deck manifest for the Nobulous Set TTS mod.

key            : sheet stem in cards/out
count          : number of cards
w, h           : grid width / height
back           : 'unique' -> <key>_TTS_back.png, else a CardBack_*.png stem
land           : landscape card
game           : BAT | NAP | AoS | NRJ | IMP
label          : shown on the deck in-game
"""

DECKS = [
    # ---- BAT -------------------------------------------------------------
    dict(key='BAT_Rats', count=4, w=4, h=1, back='unique', land=True,
         game='BAT', label='Lab Rats (A / B)'),
    dict(key='BAT_Encounters', count=20, w=10, h=2, back='CardBack_BAT_Encounter',
         land=False, game='BAT', label='Encounters'),
    dict(key='BAT_Upgrades', count=16, w=10, h=2, back='CardBack_BAT_Upgrade',
         land=False, game='BAT', label='Upgrades'),
    dict(key='BAT_Specimens', count=8, w=8, h=1, back='CardBack_BAT_Upgrade',
         land=False, game='BAT', label='Specimens'),
    dict(key='BAT_TyrantAttacks', count=7, w=7, h=1, back='CardBack_BAT_TyrantAttack',
         land=False, game='BAT', label='Tyrant Attacks'),
    dict(key='BAT_BuffHP', count=1, w=1, h=1, back='CardBack_BAT_BuffHP', land=False,
         game='BAT', label='Buff HP Track'),
    # ---- NAP -------------------------------------------------------------
    dict(key='NAP_Apprentices', count=3, w=3, h=1, back='unique', land=True,
         game='NAP', label='Apprentices'),
    dict(key='NAP_Tasks', count=26, w=10, h=3, back='CardBack_NAP_Assignment',
         land=True, game='NAP', label='Tasks'),
    dict(key='NAP_Opportunities', count=6, w=6, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NAP', label='Opportunities'),
    dict(key='NAP_Setbacks', count=6, w=6, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NAP', label='Setbacks'),
    dict(key='NAP_FinalExams', count=12, w=10, h=2, back='CardBack_NAP_FinalExam',
         land=True, game='NAP', label='Final Exams'),
    dict(key='NAP_SlotsFINF', count=4, w=4, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NAP', label='Time Slots + FINF'),
    # ---- AoS -------------------------------------------------------------
    dict(key='AoS_Technicians', count=3, w=3, h=1, back='unique', land=True,
         game='AoS', label='Technicians'),
    dict(key='AoS_Routine', count=8, w=8, h=1, back='unique', land=False,
         game='AoS', label='Routine Programs'),
    dict(key='AoS_Specialized', count=8, w=8, h=1, back='unique', land=False,
         game='AoS', label='Specialized Programs'),
    dict(key='AoS_Unstable', count=8, w=8, h=1, back='unique', land=False,
         game='AoS', label='Unstable Programs'),
    dict(key='AoS_Advanced', count=8, w=8, h=1, back='unique', land=False,
         game='AoS', label='Advanced Programs'),
    dict(key='AoS_Limitations', count=6, w=6, h=1, back='CardBack_AoS_Limitation',
         land=False, game='AoS', label='Limitations'),
    dict(key='AoS_ElementMats', count=5, w=5, h=1, back='CardBack_AoS_Limitation',
         land=False, game='AoS', label='Element Mats'),
    # ---- NRJ -------------------------------------------------------------
    dict(key='NRJ_BAT_Protocols', count=6, w=6, h=1, back='CardBack_NRJ_Protocol',
         land=False, game='NRJ', label='Experimental Protocols'),
    dict(key='NRJ_BAT_Modifications', count=6, w=6, h=1, back='CardBack_BAT_Upgrade',
         land=False, game='NRJ', label='Unauthorized Modifications'),
    dict(key='NRJ_BAT_ResearchNotes', count=6, w=6, h=1, back='CardBack_NRJ_ResearchNote',
         land=False, game='NRJ', label='Research Notes'),
    dict(key='NRJ_NAP_ImpostorTasks', count=4, w=4, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NRJ', label='Impostor Tasks'),
    dict(key='NRJ_NAP_FollowingSetbacks', count=4, w=4, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NRJ', label='Following Setbacks'),
    dict(key='NRJ_NAP_DeviousOpportunities', count=6, w=6, h=1, back='CardBack_NAP_Assignment',
         land=True, game='NRJ', label='Devious Opportunities'),
    dict(key='NRJ_AoS_Interference', count=6, w=6, h=1, back='CardBack_NRJ_Interference',
         land=False, game='NRJ', label='Nobulous Interference'),
    dict(key='NRJ_AoS_CorruptedLimitations', count=6, w=6, h=1, back='CardBack_AoS_Limitation',
         land=False, game='NRJ', label='Corrupted Limitations'),
    dict(key='NRJ_AoS_BackdoorRoutines', count=6, w=6, h=1, back='CardBack_NRJ_BackdoorRoutine',
         land=False, game='NRJ', label='Backdoor Routines'),
    dict(key='NRJ_ImposterScenarios', count=24, w=10, h=3, back='CardBack_NRJ_CouncilTest',
         land=False, game='IMP', label='Council Test Scenarios'),
]

GAME_COLOR = {'BAT': (0.17, 0.37, 0.29), 'NAP': (0.42, 0.25, 0.55),
               'AoS': (0.54, 0.24, 0.18), 'NRJ': (0.12, 0.31, 0.42),
               'IMP': (0.29, 0.23, 0.42)}
