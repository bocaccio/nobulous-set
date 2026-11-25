# -*- coding: utf-8 -*-
"""Which levers make NAP harder, probed at the Standard rung alone.

Candidate A shipped on 2026-11-25 and took Standard UP, not down:
49.0% -> 55.4% solo. The rule it added costs -17.1 by itself
(napcommit.txt); REC 3 and a Credit goal one lower paid for it, and
together they overpaid. So the first question is not "what new rule
makes NAP harder" but "which part of the payment can come back".

Standard only, mean of the six Apprentices, solo and Tier III.
Each lever is set from the shipped state and put back afterwards.
napladder.py then takes the survivors across all four rungs.
"""
import time

import nap

GAMES = 20004          # 3334 an Apprentice
APPS = nap.APPRENTICES


def cell(tier):
    each = GAMES // len(APPS)
    return 100.0 * sum(nap.run(a, "-1", each, tier=tier) for a in APPS) / len(APPS)


def row(label, **dials):
    old = {k: getattr(nap, k) for k in dials}
    for k, v in dials.items():
        setattr(nap, k, v)
    solo, t3 = cell("none"), cell("III")
    for k, v in old.items():
        setattr(nap, k, v)
    print("  %-46s %6.1f%% %8.1f%%" % (label, solo, t3))
    return solo, t3


def main():
    started = time.time()
    print("NAP - levers that make Standard harder. %d games a cell,"
          % GAMES)
    print("mean of the six Apprentices, FINF Reduce 1.")
    print()
    print("  %-46s %6s %9s" % ("", "no NRJ", "Tier III"))
    base = row("AS SHIPPED  (4 Cr / 2 Sb, REC 3, age rule)")
    print()
    print("  TAKING BACK THE PAYMENT FOR CANDIDATE A")
    row("Credit goal back to 5 (the pre-A ladder)", CREDITS_TO_LEAVE=5)
    row("REC back to 2", REC_START=2)
    row("Setbacks 3 instead of 2", SETBACKS_IN_DECK=3)
    print()
    print("  THE TWO EXAM DECISIONS STILL OPEN")
    row("contribute = succeed", EXAM_NEED="success")
    row("contribute = succeed, 1 Health not the card",
        EXAM_NEED="success_soft")
    row("unmeetable clause costs 1 Health (need only)",
        EXAM_WAIVER_COST=1)
    row("unmeetable clause costs 1 Health (all clauses)",
        EXAM_WAIVER_COST=1, EXAM_WAIVER_SCOPE="all")
    print()
    print("  PRINTED-CARD LEVERS")
    row("every Assignment Target +1", TARGET_DELTA=1)
    row("Setback bleed unconditional", SETBACK_UPKEEP="always")
    row("Final Exam pool weighted by Credits again",
        EXAM_POOL_BY_CREDITS=True)
    print()
    print("  COMBINATIONS worth a look")
    row("Credit goal 5 + contribute = succeed",
        CREDITS_TO_LEAVE=5, EXAM_NEED="success")
    row("Credit goal 5 + unmeetable costs 1 (need)",
        CREDITS_TO_LEAVE=5, EXAM_WAIVER_COST=1)
    row("contribute = succeed + unmeetable costs 1 (need)",
        EXAM_NEED="success", EXAM_WAIVER_COST=1)
    print()
    print("  Shipped control reads %.1f%% solo / %.1f%% Tier III;"
          % base)
    print("  napage_confirm.txt has 55.4% / 40.9% at 20,000.")
    print("  The 47-57% band is on the solo column.")
    print("  Finished in %.0fs." % (time.time() - started))


if __name__ == "__main__":
    main()
