"""Results tables for NAP, BAT and AoS, split by difficulty and NRJ tier.

    python table.py              # 20,000 games per cell
    python table.py 4000         # quicker pass

Every cell is a modeled win rate. Tier columns are cumulative - "each tier
includes the ones before it" - and are NOT difficulty levels: Tier II is the
pressure peak and Tier III hands tools back.

Reference: the 20 Strong Community Game Stats sheet puts the published games
at 47-57%, and 53% across 955 recorded games. That is the band a finished
game in this system lands in, and it is the yardstick for the tables below.
"""
import sys
import time

import aos
import bat
import cards
import nap
import nrj

DEFAULT = 20000

# NAP difficulty is (Credit goal, Setbacks); the FINF dial is separate.
# (Credit goal, Setbacks in the deck) - see nap.LEVELS.
NAP_LEVELS = nap.LEVELS
NAP_APPS = ["Prodigy", "Slacker", "Technician", "Savant", "Opportunist", "Lab Rat"]
TIERS = ["none", "I", "II", "III"]

# 20 Strong Community Game Stats, read 2026-09-20. Published titles only.
COMMUNITY = [
    ("Solar Sentinels", 282, 49),
    ("Too Many Bones", 194, 55),
    ("Hoplomachus: Victorum", 103, 53),
    ("Tanglewoods: Red", 122, 47),
    ("Tanglewoods: White", 49, 53),
    ("Tanglewoods: Gold", 68, 57),
    ("Tanglewoods: Rose", 35, 31),
    ("all titles", 955, 53),
]


def pct(x):
    return "%.1f%%" % (100 * x)


def grid(title, subtitle, rows, runner, games, notes=()):
    print()
    print("=" * 66)
    print(title)
    print("=" * 66)
    print("  %s" % subtitle)
    print()
    print("  %-22s %9s %9s %9s %9s" % ("", "no NRJ", "Tier I", "Tier II", "Tier III"))
    for label, key in rows:
        cells = [pct(runner(key, t, games)) for t in TIERS]
        print("  %-22s %9s %9s %9s %9s" % tuple([label] + cells))
    for n in notes:
        print("  %s" % n)


def main(games=DEFAULT):
    started = time.time()
    print()
    print("THE NOBULOUS SET - results by difficulty and NRJ tier")
    print("%d games per cell" % games)

    # ---------------------------------------------------------------- NAP
    def nap_level(level, tier, g):
        """Mean of the six Apprentices at one Credit goal."""
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = NAP_LEVELS[level]
        each = max(200, g // len(NAP_APPS))
        return sum(nap.run(a, "-1", each, tier=tier) for a in NAP_APPS) / len(NAP_APPS)

    grid(
        "NAP  Nobulous' Apprenticeship Program",
        "difficulty = Credit goal / Setbacks in the deck; FINF at Reduce 1",
        [(("%s (%d Cr, %d Sb)" % (k, NAP_LEVELS[k][0], NAP_LEVELS[k][1]))
          + (" *" if k == "Standard" else ""), k)
         for k in ("Easy", "Standard", "Hard", "Nobulous")],
        nap_level,
        games,
        notes=("",
               "  * Standard difficulty. Mean of the six Apprentices.",
               "  Tier I   3 of 4 Following Setbacks replace 3 base Setbacks",
               "  Tier II  4 Impostor Tasks - Mandatory, and grant no Credits",
               "  Tier III 6 Devious Opportunities replace the 6 base ones"),
    )
    nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = NAP_LEVELS["Standard"]

    # ---------------------------------------------------------------- BAT
    grid(
        "BAT  Build-a-Tyrant",
        "difficulty = Specimens added / Tyrant Health; random Rat sides",
        [(d, d) for d in ("Easy", "Standard", "Hard", "Nobulous")],
        lambda d, t, g: bat.run(d, g, tier=t, card_effects=True, sides="random"),
        games,
        notes=("",
               "  Tier I   1 of 6 Experimental Protocols drawn at setup",
               "  Tier II  6 Unauthorized Modifications in the Upgrade deck",
               "  Tier III 6 Research Notes claimable for one-shot rewards",
               "",
               "  Tier II is the trough, as intended; see the BAT caveat below."),
    )


    # ---------------------------------------------------------------- AoS
    def aos_level(level, tier, g):
        """Mean of the six Technicians at one Program-deck mix."""
        each = max(200, g // len(aos.TECHS))
        return sum(aos.run(level, each, tier=tier, tech=k)
                   for k in aos.TECHS) / len(aos.TECHS)

    grid(
        "AoS  Automaton of Shale",
        "difficulty = the Routine/Specialized/Unstable mix",
        [("%s  %d/%d/%d" % ((k,) + aos.LEVELS[k]), k) for k in aos.LEVEL_NAMES],
        aos_level,
        games,
        notes=("",
               "  Mean of the six Technicians.",
               "  Tier I   1 of 6 Nobulous Interference cards drawn at setup",
               "  Tier II  6 Corrupted Limitations in the Limitation deck",
               "  Tier III 6 Backdoor Routines, at most 2 claimed per game"),
    )

    # ---------------------------------------------------------------- NRJ
    print()
    print("=" * 66)
    print("NRJ  Imposter Scenario (the campaign finale)")
    print("=" * 66)
    print("  The tiers apply to the three games above, not to the finale, and")
    print("  the finale has no difficulty dial. Its variable is the Research")
    print("  Pool.")
    print()
    for mode in nrj.POOL_MODES:
        print("  %-14s %9s" % (mode, pct(nrj.run(mode, games))))

    # ---------------------------------------------------------------- refs
    print()
    print("=" * 66)
    print("CALIBRATION - published 20 Strong titles, community-recorded")
    print("=" * 66)
    print("  %-24s %7s %9s" % ("title", "games", "win rate"))
    for name, n, rate in COMMUNITY:
        print("  %-24s %7d %8d%%" % (name, n, rate))
    print()
    print("  Source: 20 Strong Community Game Stats, read 2026-09-20.")
    print("  A finished game in this system sits near 50%. Against that:")
    print("    AoS  near band at Easy, below it from Standard down.")
    print("    NAP  in band at Easy, below it from Standard down.")
    print("    BAT  in band at Easy, below it from Standard down.")
    print("  BAT's Health dial was tuned against this model, so the model")
    print("  agreeing with the shipped ladder is construction, not")
    print("  corroboration. The rulebooks no longer print win rates at all -")
    print("  this file is the only place they live.")

    # ---------------------------------------------------------------- caveats
    print()
    print("=" * 66)
    print("CAVEATS")
    print("=" * 66)
    print("""
  THE BAT TIER COLUMNS USED TO RUN THE WRONG WAY, and the reason is worth
  keeping. The tier modules made BAT EASIER - Tier II +6.1 and Tier III
  +7.2 against no-NRJ - which contradicted the intent that Tier II is the
  pressure peak. The caveat here blamed content the model omits. That was
  wrong.

  BAT's Tier II was the only tier in the set that ADDED cards to a deck.
  NAP replaces at every tier; BAT shuffled 6 Unauthorized Modifications
  INTO a 22-card Upgrade deck, so the Rats simply drew more Upgrades, and
  every Upgrade absorbs one Tyrant attack before it is spent. The tier was
  handing out armor as a side effect of its own delivery mechanism.

  Two card-design changes fixed it, with no difficulty dial touched:
    * the Modifications REPLACE 6 ordinary Upgrades (MODS_REPLACE)
    * their Values rose by 1, to 4/4/5/4/5/4

  The second is the counter-intuitive one. Splices come out of the Upgrade
  deck, so under threshold damage a card's Value is the height of a wall the
  Rats must clear in ONE blow - it matters more to the Tyrant than to the
  Rat holding it. LOWERING the Modification bodies made Tier II easier;
  raising them gave it teeth.

  THE EXPERIMENTAL PROTOCOLS WERE REBALANCED, and how they were broken is
  worth keeping. Tier I used to measure about -1.0, and an earlier caveat
  blamed unmodeled content. That was wrong - all seven Tyrant Attack cards
  are handled individually, and borrowing is implemented including the
  banishment check and both Protocols that hook it. Forcing each Protocol in
  turn showed the real problem: the six cards disagreed violently, three
  making BAT HARDER and three EASIER, spanning 29 points. Tier I averaged to
  nothing because they cancelled.

    protocol                    before   retuned     now
    Cross-Contamination          +3.4     -6.0     -7.3
    Shared Equipment Budget     -18.8     -6.0     -7.2
    Accelerated Trials           +6.3     -6.9     -0.8   <-- out of band
    Questionable Methodology    +10.7     -4.1     -2.8
    Questionable Procurement     -3.1     -3.2     -4.8
    Independent Funding          -0.2     -5.1     -4.4

  Tier I now sits at -4.1 at Standard, against NAP's -3.1, and the six
  average -4.5. The "now" column is 8,000 forced games a card against a
  46.8% no-tier baseline, measured after the Upgrade-leak fixes.

  TWO OF THEM GATE ON THE PRINTED TARGET, SO ZEROING TARGET_DELTA RE-AIMED
  THEM. Accelerated Trials fires at printed Target 5+ and Independent
  Funding at 4 or less. With the model's +1 still on top, the deck read
  4/4/5x13/6x5, so Accelerated Trials covered 18 of the 20 Experiments and
  Independent Funding 2. The printed deck is 3/3/4x13/5x5, which is 5 and
  15 - very nearly swapped. Accelerated Trials fell from -6.9 to -0.8 and
  is now the one card outside the -3 to -6 band, not because its text
  changed but because the Targets under it did. Raise it as a design
  question before touching the dial: ACCEL_FLOOR = 4 measures -9.9, which
  is as far outside the band on the other side.

  WHICH DIE DOES "EXHAUST AN AVAILABLE DIE" TAKE? It used to take the best
  one, in all three games, by accident. BAT walked rat.dice, which is COLORS
  order - purple, blue, green, yellow - and took the first available, so it
  handed over the PURPLE every time. NAP and AoS held one flat list ending
  in red and popped from the end, so they handed over the RED die first, the
  strongest in the game. AoS did it twice: allocate() sorts the pool
  strongest-first, so an element's dice run best-to-worst and dice[:burn]
  burned the best ones allocated to it.

  A player hands over the yellow, which makes those clauses nearly free -
  Accelerated Trials measured +4.5 once the model stopped overcharging it.
  So the three cards that exhaust dice as a cost now NAME a colour (Purple
  for Accelerated Trials and Hypermetabolism, Blue for Independent Funding),
  and NAP's Demand penalties name the Assignment's own recovery dot. Holding
  none of that colour is not a free pass: the weakest die goes instead.
  AoS's exhaust clauses carry no colour, so there the weakest simply goes.

  Correcting this moved NAP by +0.1 and AoS by +1.0; BAT's Protocols were
  retuned against it. If a cost clause seems inert, check WHICH die it takes
  before making it bigger.

  TWO OF THOSE TURNED ON TIMING, NOT SIZE. Accelerated Trials billed the
  active Rat's dice AFTER the attempt, when it has already spent them -
  raising the charge from 2 dice to 4 changed the win rate by nothing at
  all, because there was nothing left to take. Billing ONE die before the
  attempt was worth -5.0 when most of the deck was Target 5+. If a cost
  clause seems inert, check when it fires before making it bigger - and
  check what its trigger is gated on before trusting the figure later.

  BAT'S TIER III RECOVERS WEAKLY, AND THE REASON MOVED. Tier II is the
  trough as intended and Tier III gains +5.4 back at Standard, against
  NAP's +8.0 and AoS's +11.0. The first diagnosis was the claim side:
  two of the six Research Notes were nearly dead paper, and the rest
  averaged 2.0 claims a game. Loosening two conditions and rewriting the
  dead one - Cross-Species Compatibility now claims on completing an
  Experiment with a BORROWED die, which is what the card is about - took
  that to 4.3 claims a game, with each of the five modelled Notes claimed
  in 73-96% of games and only 0.1% of games claiming none. The sixth,
  Controlled Failure, needs a deliberate zero-dice turn the policy never
  takes.

  It barely moved the column, because the limit is the REWARD side. bat.py
  pools every claim into one counter, `self.notes`, and spends it on two of
  the six printed rewards: recovering a Rat's dice in the battle, and
  ignoring the +1 Target a revealed Specimen adds. The other four printed
  rewards do nothing at all - choosing which Upgrade is Spliced after a
  failure, tapping another Rat's Upgrade in the battle, discarding a
  revealed Experiment, and placing Red directly on a Rat. Six separate
  once-per-game cards are modelled as one fungible token spent on two of
  them. Giving each claimed Note its own printed reward is the next lever
  on this column, and it is a structural change to the module, not a
  number.

  INDEPENDENT FUNDING NEEDED A NEW TRIGGER, not a new number. The old card
  paid the LENDER a die, and the lender's dice are not the binding resource,
  so it was worth +0.1 despite firing 2.7 times a game. Eight triggers were
  measured: anything at resolve time was worth 0.0 (the active Rat has
  already spent its dice), anything keyed to Upgrades held was dodged for
  free (the Rat-selection policy already prefers the least-loaded Rat), and
  anything undodgeable was far too big - a setup banish -11.0, taxing the Red
  holder -10.5, with nothing in between, because a Rat owns only 4 dice.

  It now taxes 1 die BEFORE each Experiment with printed Target 4 or lower -
  the complement of Accelerated Trials' Target 5+, so the two gate on
  opposite halves of the deck - and keeps the lender payout as its upside.
  Worth -5.4.

  WHAT THE CARD AUDIT FOUND. simulation/audit.py counts, per card, how
  often it reaches the table and how often its text does anything. Run it
  rather than trusting any coverage claim here - several in this file have
  been wrong, including one in this paragraph until the audit caught it.

    healthy   all 7 Tyrant Attacks appear in 89-96% of games and all are
              modelled individually; the 8 Lab Rat sides come up evenly;
              all 6 AoS Limitations appear in 94-96% of games; NAP's
              Setbacks and Opportunities are evenly drawn.
    omitted   BAT's 20 Experiment effects were not modelled at all - only
              the printed Target was read. Nineteen are now implemented and
              every one of them fires. The exception, named in UNMODELLED_EXP
              in bat.py, is Diagnostic Trial: committing Blue buys a look at
              the next Experiment, and the policy has no lookahead to spend
              it on. The three optional cards each got a stated policy -
              Containment Failure takes its -2 when the Rat's own dice look
              short, Methodological Optimization takes Target 0 when the
              Target is out of reach, Field Retrofit swaps when the card on
              offer beats the Rat's worst. Over the 16 cells the whole deck
              is worth +1.6 points, so it roughly balances, which is what a
              well-made deck should do. NRJ now omits 1 of its 24
              Scenario effects, down from 18: see the Imposter section
              below, and imposter.py.
    desync    the model carried its own table of Experiment Targets and added
              TARGET_DELTA = 1 on top. That +1 was adopted and PRINTED onto
              the cards at commit b57eedd, so seven of the twenty Experiments
              were charged the rise twice, and Containment Failure was being
              charged 4 against a printed 5. bat.py now reads the printed
              numbers with TARGET_DELTA back at 0, which is worth +11.3
              points over the 16 cells - re-measured after the leak fixes,
              against +4.2 when it was first found. Read card data off generator/build_*.py; a
              dial that gets adopted has to be zeroed when it is.
    thin      Field Retrofit Trial is modelled and all but inert. Its
              Experiment is completed 54 times in 400 games, and in 94% of
              those the Rat is nowhere near its 3-Upgrade limit, so it takes
              the better revealed card as usual and the swap is offered only
              the weaker one. The card pays at the limit, where completing an
              Experiment otherwise gives a Rat nothing - and Rats hold 1.1
              Upgrades when the battle begins. Same shape as Cross-Species Compatibility:
              a clause written for a board state Upgrade scarcity never
              reaches. A design question, not a model one.
    policy    NAP's Primary choice took the cheaper of the two revealed
              Assignments and ignored what the card paid - so it would take a
              cheap no-Credit Task over a slightly dearer Credit one, working
              against the win condition, and declined Task 23's permanent
              +1 STR in 92% of games. It now scores the reward too, which is
              worth +4.0 / +3.6 / +2.3 / -0.1 across the ladder. Weighting
              permanent upgrades HEAVILY made it play worse at Hard and
              Nobulous, so those weights are deliberately small.

  TWO AUDIT FINDINGS THAT WERE NOT REAL, recorded so nobody re-raises them.
  The 6 Unauthorized Modifications reach play 3.0 times a game of 6 (1.4 to
  a Rat, 1.6 spliced), which reads thin until you notice the per-card order
  tracks Value exactly - the two Value-5 cards lead at 29% each, and the
  Value-4s trail at 19-21%. Those are cards TAKEN: audit.py reports what is
  still HELD when the game ends, which is 2-9%, because a knocked-out Rat
  discards its Upgrades. That is `best = max(options, key=splice_value)`
  working, over ~13 picks from a 22-card deck. And NAP's 6 Setbacks share
  ONE printed rule (SB_TEXT in build_nap.py), which IS modelled - the row
  blocking and the per-slot die cost. They have no per-card text to omit.
  Modeled in the later passes, and no longer omissions: the six Apprentice
  abilities and the 26 Request rewards, the six Technician abilities and the
  six base Limitations, the Opportunity coupons, and both sides of the
  Unauthorized Modifications.

  Heroes move numbers a long way, and every bit of it is ability text. The
  printed statlines really are identical - Technicians 2/2/3, Apprentices
  2/2/2, both sides of each Lab Rat the same - so the spread comes entirely
  from the abilities, which are now modeled: about 17 points between the
  best and worst Technician (43.4% to 26.0% at Standard), about 8 between
  Apprentices (46.1% to 38.6%). This cross-tab
  reports their mean; the per-hero tables are in RESULTS.txt, and cards.py
  lists all twenty.

  Policy sensitivity is large. NRJ moved from 3.4% to 9.2% on how it spends
  the Research Pool, and from 12.6% to 33.1% on which exhausted dice REC
  hands back - neither a rules change. Prefer the shape of a column to the
  level of any single cell.

  THE IMPOSTER SCENARIO HAD NO DICE TENSION, AND IT HAS BEEN REPAIRED.
  Run simulation/imposter.py; the full output is in imposter.txt, and
  proto/fix.py holds the candidates that were measured and rejected.

  As printed it won 32.4%, and on dicetension.py's own scale it read 6.6
  mean with 0% of commit decisions at two dice or fewer and 0.0% empty. The
  pool collapsed from 17 to exactly REC by the fourth attempt and sat there
  for the remaining five - one notch above the <=2 threshold - so it was
  income rather than a budget. It could not run out, so running out was
  never a worry, and 57% of commit decisions put the whole pool in because
  there was nothing to choose between.

  THE REPAIR IS ONE LINE: "your REC is 3 minus the number of cards in the
  Suspicion row", with 5 starting Health rather than 4. No new components -
  the Suspicion row is already face-up and already drives the Target climb,
  so it does double duty. The recovery floor now falls as the finale goes
  wrong:

                        mean    <=2   empty  |  trough   <=2   empty
    Imposter, printed    6.6     0%    0.0%  |     3.0    0%    0.0%   32.4%
    Imposter, repaired   5.8    35%   13.5%  |     0.6   97%   62.9%   50.3%
    NAP (Standard)       4.3    32%    3.2%  |     0.9   92%   47.9%
    AoS (Standard)       6.2    22%    0.9%  |     1.2   86%   22.0%

  The pool now runs 17.0, 11.5, 5.5, 3.8, 3.3, 2.8, 2.0, 1.2, 0.7 across the
  nine attempts, and the win rate sits at the middle of the 47-57% community
  band. The finale leads the set on five of those six columns: NAP's mean
  pool is 4.3 against the finale's 5.8, so on the mean alone NAP is tighter.
  Every column that measures RUNNING OUT - at two dice or fewer, empty, and
  all three trough columns - is the finale's.

  WHAT DID NOT WORK IS THE MORE USEFUL HALF. Twenty-one candidates and
  combinations were measured; proto/fix.txt has them all.
  Every one that left the recovery floor fixed moved the win rate without
  creating any dice pressure whatever - including one that banishes eight of
  the seventeen dice per game and still reads 0% and 0.0%. "Recover up to
  REC exhausted dice" refills the pool to a fixed floor every attempt
  regardless of what happened, so while that holds, the pool cannot trend
  toward zero. Making failure destroy dice is the obvious fix and it does
  nothing. Letting the printed banish trade pay from the exhausted pile is
  worse than nothing: it wins 100%, because at 2 dice per Health with 17
  dice and 4 Health, dice are four times the cheaper currency and the trade
  is only balanced while it stays unpayable.

  THE ONE CLAUSE THAT WOULD MAKE DICE CURRENCY CANNOT BE PAID. The failure
  choice is resolved between the commit and the recovery - rules/nrj.html
  steps 4, 5, 6 - which is the trough. At that instant the Imposter holds
  0.35 dice on average, NONE AT ALL in 92% of failures, and can pay in dice
  in 6.1%. The printed rule anticipates it ("if you cannot banish 2 available
  dice, Health loss is mandatory"), so the finale is a Health race with a
  dice floor. Same shape as BAT's Accelerated Trials: a cost billed after
  the spend finds an empty pool. Resolving the choice after recovery, or
  banishing from the exhausted pile, would make the trade real - both are
  rules changes and neither has been made.

  SIX SCENARIOS RESTRICT THE DICE, AND ARE WORTH -1.9 POINTS. "Commit at
  least 6 dice", "commit at least 3 different colors", the two color
  minimums and "Yellow cannot contribute" were never modelled; they are now,
  and so is every other Scenario effect bar one. Three of them block the
  MAJORITY of the attempts they appear in - 69%, 58%, 56% - and the whole
  set moves the finale 52.2% to 50.3%, because by the time they bite the
  attempt was already lost, and being blocked saves the dice and the
  Research cards it would have wasted.

  The three color clauses used to block 0% of their attempts, because
  recovering the best dice leaves a pool of Purple and Blue. Repair H gave
  two of them teeth: with the pool down to two or three dice, An Old Injury
  now blocks 39% of its attempts and The Ceremonial Seal 27%, because the
  pool may simply not hold the Purple the card asks for. The Darkened
  Corridor still blocks 0% - it bars YELLOW, and a pool recovered
  strongest-first holds no Yellow to bar. That one is inert as printed. They are a tax on the recovery decision - recover the strongest
  dice and you keep the Purple but lose the spread - which is a decision the
  finale did not previously contain.

  THE CAMPAIGN HAND-OFF WORKS, AND STANDALONE IS A FAIR STAND-IN FOR IT.
  simulation/supply.py runs the three games and reads what each one banks,
  then feeds those hands to the finale. Full output in supply.txt.

    standalone, as printed        50.2%
    campaign hand-off, Easy       52.1%     Standard  51.6%
    campaign hand-off, Hard       51.8%     Nobulous  50.4%

  Supply is sufficient everywhere. NAP faces exactly 3 Final Exams out of 12
  printed, so its 3 retained and 3 Candidates are never in doubt. AoS faces
  exactly 3 Advanced Programs out of 8. BAT retains "up to 3 of the Upgrade
  cards the Rats earned - the ones they held when the battle began", and the
  Rats hold 4.2 to 4.4 of them on a win, 3 or more in 94-96% of wins.

  TWO THINGS THE MEASUREMENT CORRECTED IN build_pool. It assumed a 50%
  chance that one retained BAT card is a Specimen; a Specimen is actually on
  the table in 86-96% of wins, and at -5 against an Upgrade's -3 it is
  always the one you keep. It also assumed each retained AoS card is 50%
  Stable; the first Advanced Program is Stable BY RULE, and across the three
  the Overheated share is 34-38%, so the real hand reduces more and avoids
  less. And build_pool added a flat 3 Candidates per game, which handed BAT
  a 5-card contribution whenever it banked fewer than 3 - the printed rule
  fills to 6 from Tyrant Splices.

THE RULE WAS RIGHT IN ONE PLACE AND STALE IN TWO. bat.html was rewritten so
  that retention counts the Upgrades the Rats held when the battle began,
  survival irrelevant. Two copies of the old rule survived it: nrj.html's
  Research Pool table ("Up to 3 Upgrades held by SURVIVING Rats", with
  knocked-out Rats' Upgrades as Candidates) and bat.html's OWN knockout step
  ("for the campaign its Upgrades become candidates rather than retained
  cards"), three paragraphs from the rule it contradicted. Both corrected.
  supply.py now greps every document that says where a knocked-out Rat's
  Upgrades go, because checking only the obvious one is what let the second
  copy sit undetected.

  WHERE THE MARGIN WAS ZERO. BAT's Candidate supply is the Tyrant's 5
  Splices, and the track holds exactly 5. With 1 retained Upgrade that is 5
  needed against 5 available; a win with NO retained Upgrade needs 6 and
  comes up one short. It did not happen in any win measured, but the rules
  permit it and were silent on it. rules/bat.html now fills from unused
  Upgrade cards when the Splices do not cover it - the same source Splicing
  Machine Malfunction uses to top the Tyrant up to 5.

  The "at most 1 Specimen" cap is what binds, not supply: a second Specimen
  is on the table in 46-68% of wins and has to be left behind.

  EVERY DIAL IS STILL A CLIFF, AND THAT IS NOT FIXED. One point of starting
  Health is worth about 21 points of win rate and one point on all 24
  Targets about 18, against roughly 4 for a point of Tyrant Health in BAT.
  Nine pass/fail attempts against a small failure budget amplify any dial
  about ninefold. Flattening that means grading each attempt instead of
  passing or failing it, which is a larger change than H.

  The upside is that one number now serves as the difficulty ladder the
  finale has never had - 3/4/5/6 starting Health gives 9.3%, 29.4%, 50.8%,
  71.0%, with dice pressure rising along it. Wider rungs than the other
  three games, but a ladder where there was none. Not applied: H ships at
  5 Health, which is the Standard rung.
""")
    print("finished in %.1fs" % (time.time() - started))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)
