"""IS A NAP COMMITMENT A ONE-TIME DEAL? Measured 2026-11-25, at Jon's ask.

The proposed rule: "anytime you attempt to complete a card with stored
progress, you must commit a die (or wild) corresponding to the color - the
commitment is not a one time deal."

THE FIRST FINDING IS THAT THIS IS ALREADY THE RULE on the main path, in all
three owners that enforce anything, so most of the proposal is a no-op:

  * rules/nap.html prints it per application - "to complete an Assignment
    or store progress on it, the successes you apply must include a die
    matching its color dot, Red, or two successful dice of another color".
  * nap.py checks it against THIS roll: commit_for leads with a matching
    die from the available pool, and the success-side check reads only
    `take` and `results`. Stored dice are never consulted.
  * suite.js checks `successful`, the dice selected for this application.

So a card holding four stored successes and needing one more cannot be
finished with an off-colour die today. Where the commitment IS bought once
and kept is three narrower places, and only the third can move a number:

  1. REWARD-ADDED DICE. rules/nap.html, on Sharpen the Surgical Implements
     and Salvage Useful Components: "Rewards that add a die still obey the
     color rule - the Assignment must already hold a legal die", and
     "Sharpen's receiving Task must already hold stored progress that
     satisfies the color rule." That is the stored die satisfying the rule
     in place of a fresh commitment, in as many words.
  2. STUDY NOBULOUS' NOTES. "If the progress already on the card meets the
     lower Request Target, the Task completes at once" - no commitment.
  3. THE SETBACK BLEED. "At the start of this Time Slot, if this Setback
     has no stored dice, exhaust 1 available die." One die parked on a
     Setback switches the bleed off for the rest of the game, and the die
     is not even spent, only locked.

3 is the one that is a difficulty dial, and SETBACK_UPKEEP prices it. The
answer is that it is worth nothing: +0.2 at Standard for "you must have
worked it this slot", and about a point for making the bleed unconditional.
The reason is that a base Setback LOCKS THE ROW - nothing else in the Time
Slot may be worked until it is cleared - so the player is clearing it
promptly whether the bleed is on or off, and the immunity buys an exhausted
die or two across a whole game. The exploit the clause looks like it allows
is not reachable while the lock is there.

THE SECOND RULE MEASURED HERE is the Final Exam setup: "place a random
final exam card face down in the first slot of every time slot". Selecting
the three at setup rather than at exam time cannot move a number by itself
- they are face down either way, and this model's exam loop has never
looked ahead - so what is priced is the two things that CAN move: whether
the card occupies an Assignment space, and whether "a random final exam
card" is the same draw as one per subject.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nap

LEVELS = ("Easy", "Standard", "Hard", "Nobulous")
APPS = ["Prodigy", "Slacker", "Technician", "Savant", "Opportunist", "Lab Rat"]
PUBLISHED = (58.1, 49.0, 37.0, 26.3)


def ladder(games=18000, **dials):
    old = {k: getattr(nap, k) for k in dials}
    for k, v in dials.items():
        setattr(nap, k, v)
    keep = (nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK)
    try:
        out = []
        for level in LEVELS:
            nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = nap.LEVELS[level]
            each = max(200, games // len(APPS))
            out.append(100.0 * sum(nap.run(a, "-1", each, tier="none")
                                   for a in APPS) / len(APPS))
        return out
    finally:
        for k, v in old.items():
            setattr(nap, k, v)
        nap.CREDITS_TO_LEAVE, nap.SETBACKS_IN_DECK = keep


def exam_draws(trials=200000, seed=3):
    """One per subject and 3 of 4, against any 3 of the 12."""
    rng = random.Random(seed)
    by_subject = {}
    for e in nap.EXAMS:
        by_subject.setdefault(e[0], []).append(e)
    out = {}
    for label in ("one per subject, 3 of 4", "any 3 of the 12"):
        dupes = 0
        seen = {s: 0 for s in by_subject}
        for _ in range(trials):
            if label.startswith("one"):
                pool = [rng.choice(v) for v in by_subject.values()]
                rng.shuffle(pool)
                pick = pool[:3]
            else:
                pick = rng.sample(nap.EXAMS, 3)
            names = [p[0] for p in pick]
            if len(set(names)) < 3:
                dupes += 1
            for s in set(names):
                seen[s] += 1
        out[label] = (100.0 * dupes / trials,
                      {s: 100.0 * n / trials for s, n in seen.items()})
    return out


def row(label, cells, base=None):
    line = "%-44s %s" % (label, " ".join("%7.1f%%" % x for x in cells))
    if base:
        line += "   " + " ".join("%+5.1f" % (cells[i] - base[i])
                                 for i in range(4))
    print(line)


def main():
    print("NAP - is the commitment a one-time deal, and what does the")
    print("Final Exam setup rule cost? Mean of the six Apprentices,")
    print("3000 games each, FINF Reduce 1, no NRJ tier.")
    print()
    print("%-44s %8s %8s %8s %8s   %s"
          % ("", *LEVELS, "vs shipped"))
    base = ladder()
    row("AS SHIPPED", base)
    row("published, 20k games", PUBLISHED)
    print()
    print("THE SETBACK BLEED - 'commit every time you want it quiet'")
    row("must have worked it THIS slot", ladder(SETBACK_UPKEEP="slot"), base)
    row("the bleed is unconditional", ladder(SETBACK_UPKEEP="always"), base)
    print("  Worth nothing, because a base Setback locks the row: you")
    print("  clear it promptly whether or not it is bleeding.")
    print()
    print("THE FINAL EXAM ON THE TIME SLOT - does it cost a space?")
    row("rows of 3, not 4", ladder(ROW_MAX=3), base)
    print("  Also near nothing, and that is worth knowing: the row is not")
    print("  the binding constraint on NAP, Strategy rolls are.")
    print()
    print("SPECIAL RECOVERY, capped. 'Recover ALL exhausted dice of the")
    print("queued color' is the largest single refill in NAP, and the")
    print("suspect for a Standard that wins on the last die and still")
    print("never asks for a hard decision.")
    for cap in (3, 2, 1):
        row("at most %d of the queued color" % cap,
            ladder(SPECIAL_RECOVERY_CAP=cap), base)
    print("  Capping the SIZE of the refill does not make NAP tense, it")
    print("  ends it. Dice are the whole economy and Special Recovery is")
    print("  most of the income.")
    print()
    print("THE TIMING INSTEAD OF THE SIZE. The real complaint was not that")
    print("the refill is big, it is that it is CERTAIN: the Primary's dot")
    print("names the next slot's colour, so once purple is queued you")
    print("spend every purple you have. Making the recovery reach only")
    print("dice that were already exhausted when the slot began takes the")
    print("certainty away and leaves the size alone.")
    row("only PREVIOUS slots' dice come back",
        ladder(SPECIAL_RECOVERY_AGE=True), base)
    row("...and capped at 3 as well",
        ladder(SPECIAL_RECOVERY_AGE=True, SPECIAL_RECOVERY_CAP=3), base)
    print("  Right in kind and still too strong in degree: -17 at Standard")
    print("  puts it under the 47-57% band, and EASY lands at 43.7%, below")
    print("  where Standard should be. The ladder would have to be")
    print("  re-pegged under it - and both its dials are already at their")
    print("  soft end on the Easy rung, 4 Credits and 1 Setback, so the")
    print("  re-peg needs a rung below the one that exists today.")
    print()
    print("AND WHICH EXAMS YOU SIT - the half of the rule that is not free.")
    for label, (dupes, seen) in exam_draws().items():
        print("  %-26s a subject repeats %5.1f%% of games" % (label, dupes))
        print("  %-26s   %s" % ("", "  ".join(
            "%s %.0f%%" % (s[:4], p) for s, p in sorted(seen.items()))))
    print("  Drawing from all 12 repeats a subject in half of all games,")
    print("  and drops each subject's appearance from 75% to 62%. Credits")
    print("  reduce the Target of THAT subject's exam, so a repeat doubles")
    print("  the value of one specialism and strands the other three. To")
    print("  keep the shipped draw, select 1 per subject, shuffle the four")
    print("  face down, deal 3 to the Time Slots and box the fourth unseen")
    print("  - that is the current rule with a new table position, and it")
    print("  moves nothing.")


if __name__ == "__main__":
    main()
