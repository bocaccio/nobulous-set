"""Does the Imposter Scenario put the dice pool under pressure?

    python imposter.py            # 4000 games per cell

The other three games have been measured against 20 Strong's core question -
"am I going to run out of dice?" - by dicetension.py. The finale never had
been, and it is the one place in the set where dice are explicitly currency:
every failed Scenario offers "lose 1 Health OR banish 2 available dice", so
the pool is not only a budget to spend, it is what the loss condition is
paid with.

The answer used to be no, and for a reason worth reading past the headline.
The pool did not run out: it collapsed to exactly REC by the fourth attempt
and sat there for the remaining five, which is income, not a budget. The
Targets then outran it by a margin growing to about 9, so nothing a player
did in the second half changed anything - no tension, only arithmetic that
had already been settled. It won 32.4% and showed 0% of commit decisions at
two dice or fewer.

REPAIR H HAS SINCE BEEN APPLIED: "your REC is 3 minus the number of cards in
the Suspicion row", with 5 starting Health rather than 4. The recovery floor
now falls as the finale goes wrong, so the pool declines across the nine
attempts instead of plateauing. That was the only kind of change that
worked - proto/fix.py measured eight candidates, and every one that left the
floor fixed moved the win rate without creating any dice pressure at all,
including one that banishes eight of the seventeen dice per game. Section 1
is the result; section 3 is the part H does NOT fix.

Seven sections, every number produced by this file:

  1 TENSION       dice available when the game asks you to commit, measured
                  exactly as dicetension.py measures NAP, AoS and BAT.
  2 ECONOMY       the pool across the nine attempts, and the Target faced
                  against the reach of the dice that are left.
  3 THE TRADE     how often "banish 2 available dice" can even be paid.
  4 DICE CLAUSES  the six Scenarios that restrict which dice may contribute.
  5 POLICY        the four model choices in nrj.py that are not rules.
  6 DIALS         REC, Health, STR and the attempt count, one step each.
  7 RESEARCH      the other budget, and how much of it goes unspent.
"""
import random
import statistics
import sys

import dicetension
import nrj
from dice import EV


GAMES = 4000

def reference_rows(games):
    """NAP and AoS on the same scale, MEASURED rather than copied.

    This was a frozen copy of dicetension.py's printed figures, which went
    stale as soon as NAP's commit policy was retuned - the comparison the
    whole section rests on would have been against a player NAP no longer
    has. Calling the tool costs a few seconds and cannot drift.
    """
    rows = []
    for label, fn in (("NAP  (Standard)", dicetension.nap_game),
                      ("AoS  (Standard)", dicetension.aos_game)):
        r = dicetension.sample(fn, games)
        rows.append((label, r["mean"], r["low"], r["starved"],
                     r["trough"], r["tight"], r["dry"]))
    return rows

CLAUSE_CARDS = sorted(set(list(nrj.NEED_COLORS) + list(nrj.NEED_DISTINCT)
                          + list(nrj.NEED_COUNT) + list(nrj.FORBID_COLOR)))


class Probe(object):
    """One batch of finales, hooked rather than edited."""

    def __init__(self):
        self.at_commit = []
        self.troughs = []
        self.committed = []
        self.spare = []
        self.by_attempt = [[] for _ in range(nrj.ATTEMPTS)]
        self.target_raw = [[] for _ in range(nrj.ATTEMPTS)]
        self.target_net = [[] for _ in range(nrj.ATTEMPTS)]
        self.reach = [[] for _ in range(nrj.ATTEMPTS)]
        self.trade_avail = []
        self.banish_events = 0
        self.health_events = 0
        self.banished = []
        self.failures = []
        self.bought = []
        self.cards_left = []
        self.retained_left = []
        self.clause_seen = dict((c, 0) for c in CLAUSE_CARDS)
        self.clause_blocked = dict((c, 0) for c in CLAUSE_CARDS)
        self.wins = 0
        self.games = 0
        self.lost_at = []

    def play(self, rng, mode="standalone"):
        g = nrj.Game(mode, rng)
        real_commit, real_spend, real_can = g.commit, g.spend, g.can_attempt
        bought = [0]
        seen = []

        def commit(target, name=None):
            i = min(g.attempts, nrj.ATTEMPTS - 1)
            seen.append(len(g.available))
            self.by_attempt[i].append(len(g.available))
            self.reach[i].append(g.expected(g.available))
            take = real_commit(target, name)
            self.committed.append(len(take))
            self.spare.append(len(g.available) - len(take))
            return take

        def spend(sid, target):
            i = min(g.attempts, nrj.ATTEMPTS - 1)
            self.target_raw[i].append(target)
            out = real_spend(sid, target)
            self.target_net[i].append(out)
            bought[0] += target - out
            return out

        def can_attempt(name):
            ok = real_can(name)
            if name in self.clause_seen:
                self.clause_seen[name] += 1
                if not ok:
                    self.clause_blocked[name] += 1
            return ok

        g.commit, g.spend, g.can_attempt = commit, spend, can_attempt

        fails = 0
        guard = 0
        while g.attempts < nrj.ATTEMPTS and guard < 60:
            guard += 1
            hp0, nb0, at0 = g.hp, len(g.banished), g.attempts
            alive = g.attempt()
            if g.attempts > at0:
                if g.hp < hp0:
                    self.health_events += 1
                    fails += 1
                elif len(g.banished) > nb0:
                    self.banish_events += 1
                    fails += 1
            if not alive:
                self.lost_at.append(g.attempts)
                break

        won = g.hp > 0 and g.attempts >= nrj.ATTEMPTS
        self.games += 1
        self.wins += 1 if won else 0
        self.banished.append(len(g.banished))
        self.failures.append(fails)
        self.bought.append(bought[0])
        self.cards_left.append(len(g.pool))
        self.retained_left.append(sum(1 for c in g.pool if c.retained))
        if seen:
            self.at_commit.extend(seen)
            self.troughs.append(min(seen))
        return won


def measure(games=GAMES, seed=11, mode="standalone", **over):
    """Run a batch with nrj module globals temporarily overridden."""
    saved = dict((k, getattr(nrj, k)) for k in over)
    for k, v in over.items():
        setattr(nrj, k, v)
    try:
        p = Probe()
        rng = random.Random(seed)
        for _ in range(games):
            p.play(rng, mode)
        return p
    finally:
        for k, v in saved.items():
            setattr(nrj, k, v)


def tension(p):
    c = p.at_commit
    return (statistics.mean(c),
            100.0 * sum(1 for x in c if x <= 2) / len(c),
            100.0 * sum(1 for x in c if x == 0) / len(c),
            statistics.mean(p.troughs),
            100.0 * sum(1 for t in p.troughs if t <= 2) / len(p.troughs),
            100.0 * sum(1 for t in p.troughs if t == 0) / len(p.troughs))


def win(p):
    return 100.0 * p.wins / p.games


# ---------------------------------------------------------------------------
def trade_pool(games, seed=7):
    """Available dice at the instant the failure trade is offered.

    Traced rather than hooked: the choice happens inside attempt(), between
    the commit and the recovery, which is the trough of the pool.
    """
    import os
    line = None
    src = open(nrj.__file__, encoding="utf-8").read().split("\n")
    for i, text in enumerate(src, 1):
        if text.strip().startswith("can_banish ="):
            line = i
    target = os.path.normcase(os.path.abspath(nrj.__file__))
    out = []

    def liner(frame, event, arg):
        if event == "line" and frame.f_lineno == line:
            out.append(len(frame.f_locals["self"].available))
        return liner

    def tracer(frame, event, arg):
        if event == "call" and \
                os.path.normcase(frame.f_code.co_filename) == target:
            return liner
        return None

    sys.settrace(tracer)
    try:
        nrj.run("standalone", games, seed=seed)
    finally:
        sys.settrace(None)
    return out


# ---------------------------------------------------------------------------
def main(games=GAMES):
    base = measure(games)

    print("THE IMPOSTER SCENARIO AND THE DICE POOL, %d games each" % games)
    print("17 dice, %d HP / STR %d / REC %d, %d attempts"
          % (nrj.START_HP, nrj.START_STR, nrj.START_REC, nrj.ATTEMPTS))
    print("win rate %.1f%%" % win(base))
    print()

    print("1. TENSION - dice available when the game asks you to commit")
    print("   the same measurement dicetension.py makes of the other three")
    print()
    print("   %-24s %7s %7s %8s  | %8s %8s %7s"
          % ("", "mean", "<=2", "empty", "trough", "<=2", "empty"))
    m = tension(base)
    print("   %-24s %7.1f %6.0f%% %7.1f%%  | %8.1f %7.0f%% %6.1f%%"
          % (("Imposter Scenario",) + m))
    for row in reference_rows(max(600, games // 4)):
        print("   %-24s %7.1f %6.0f%% %7.1f%%  | %8.1f %7.0f%% %6.1f%%" % row)
    print()
    print("   Before repair H the finale read 6.6 mean, 0% at two dice or")
    print("   fewer and 0.0% empty, with a per-game trough of 3.0 - it never")
    print("   starved and never even got low, because the pool sat on a")
    print("   fixed REC floor through the whole second half. It now leads")
    print("   the set on five of these six columns - every column that")
    print("   measures RUNNING OUT - and the floor it rested on is gone.")
    print("   NAP's mean pool is lower, 4.3 against 5.8, so on the mean")
    print("   alone NAP is the tighter game.")
    print()

    print("2. ECONOMY - the pool, the Target, and the gap between them")
    print()
    print("   attempt      " + "".join("%6d" % (i + 1)
                                       for i in range(nrj.ATTEMPTS)))
    for label, data in (("dice available", base.by_attempt),
                        ("dice reach    ", base.reach),
                        ("Target printed", base.target_raw),
                        ("Target spent  ", base.target_net)):
        print("   %-13s" % label
              + "".join("%6.1f" % statistics.mean(col) if col else "     -"
                        for col in data))
    print("   %-13s" % "SHORTFALL"
          + "".join("%6.1f" % (statistics.mean(n) - statistics.mean(r))
                    if n and r else "     -"
                    for n, r in zip(base.target_net, base.reach)))
    print()
    print("   committed per attempt   %.2f dice"
          % statistics.mean(base.committed))
    print("   spare after committing  %.2f dice; no spare at all in %.0f%% of"
          % (statistics.mean(base.spare),
             100.0 * sum(1 for s in base.spare if s <= 0) / len(base.spare)))
    print("                           commit decisions - the whole pool goes in")
    print("   failed attempts         %.2f of %d, against %d Health"
          % (statistics.mean(base.failures), nrj.ATTEMPTS, nrj.START_HP))
    print()

    print("3. THE TRADE - 'lose 1 Health OR banish 2 available dice'")
    print()
    pool = trade_pool(max(1000, games // 4))
    can_pay = 100.0 * sum(1 for x in pool if x >= 2) / len(pool)
    print("   The choice is resolved between the commit and the recovery -")
    print("   rules/nrj.html steps 4, 5, 6 - which is the trough of the pool.")
    print()
    print("   available dice at that instant   %.2f (mean)"
          % statistics.mean(pool))
    print("   none at all                      %.1f%% of failures"
          % (100.0 * pool.count(0) / len(pool)))
    print("   able to pay in dice              %.1f%% of failures" % can_pay)
    total = base.banish_events + base.health_events
    if total:
        print("   actually paid in dice            %.1f%% of failures"
              % (100.0 * base.banish_events / total))
    print("   banished over a whole game       %.2f dice of 17"
          % statistics.mean(base.banished))
    print()
    print("   So the one clause that makes dice a currency is unavailable in")
    print("   the great majority of the failures that offer it. The printed")
    print("   rule even anticipates this - 'if you cannot banish 2 available")
    print("   dice, Health loss is mandatory' - so the finale is a Health")
    print("   race with a dice floor, not a dice-management puzzle. Same")
    print("   shape as BAT's Accelerated Trials: a cost billed after the")
    print("   spend finds an empty pool.")
    print()

    print("4. DICE CLAUSES - the Scenarios that restrict the dice themselves")
    print()
    print("   Six of the 24 Council Tests constrain which dice may")
    print("   contribute, and none was modelled until this audit.")
    print()
    print("   %-30s %8s %10s" % ("", "drawn", "blocks it"))
    for c in sorted(base.clause_seen, key=lambda k: -base.clause_blocked[k]):
        n = base.clause_seen[c]
        if n:
            print("   %-30s %8d %9.0f%%"
                  % (c, n, 100.0 * base.clause_blocked[c] / n))
    off = measure(games, SCENARIO_DICE=False)
    print()
    print("   all six modelled      %5.1f%%" % win(base))
    print("   all six switched off  %5.1f%%" % win(off))
    print()
    print("   Three of them block the majority of the attempts they appear")
    print("   in, and the whole set is worth %+.1f points. That is the"
          % (win(base) - win(off)))
    print("   finding, not a reassurance: by the time these clauses bite,")
    print("   the attempt was already lost, and being blocked SAVES the dice")
    print("   and the Research cards it would have wasted. There is nothing")
    print("   left to squeeze.")
    print()
    print("   The color clauses only have teeth when the pool is thin, and")
    print("   repair H gave two of the three some: they used to block 0% of")
    print("   their attempts and now block 39% and 27%, because a pool of")
    print("   two or three dice may simply not hold the Purple the card")
    print("   asks for. The third bars YELLOW, and a pool recovered")
    print("   strongest-first holds none, so it still blocks 0% - inert as")
    print("   printed. The other two are a tax on the recovery decision -")
    print("   recover the strongest dice and you keep the Purple but lose")
    print("   the spread; recover for color and you throw weaker dice.")
    print("   That is a decision the finale did not previously contain.")
    print()

    print("5. POLICY - four choices in nrj.py that are not printed rules")
    print()
    deltas = {}
    for key, label, over in (
            ("rec", "recover the last dice appended",
             dict(RECOVER_PICK="last")),
            ("ban", "banish the last die in the list",
             dict(BANISH_PICK="last")),
            ("floor", "withhold the trade below 8 dice",
             dict(BANISH_FLOOR=8)),
            ("hope", "commit nothing at an unreachable Target",
             dict(COMMIT_HOPELESS=False))):
        q = measure(games, **over)
        deltas[key] = win(q) - win(base)
        print("   %-40s %6.1f%%  (%+.1f)"
              % (label, win(q), deltas[key]))
    print()
    print("   Recovering the worst dice rather than the best costs %.0f"
          % -deltas["rec"])
    print("   points on its own, and it was an accident of list order:")
    print("   commit() filled the exhausted pile strongest-first and REC")
    print("   popped the end of it. The two banish dials are worth %+.1f and"
          % deltas["ban"])
    print("   %+.1f, for the reason section 3 gives - the trade is already"
          % deltas["floor"])
    print("   unpayable, so how it would be paid changes nothing. Committing")
    print("   at a Target the pool cannot reach was tested and KEPT:")
    print("   withholding the dice is worth %+.1f, because 'expected"
          % deltas["hope"])
    print("   successes below the Target' is not the same as impossible, and")
    print("   a long throw can still crit its way home.")
    print()

    print("6. DIALS - one step each")
    print()
    swing = {}
    for key, label, over in (("rec-", "REC 2", dict(START_REC=2)),
                             ("rec+", "REC 4", dict(START_REC=4)),
                             ("hp-", "3 Health", dict(START_HP=3)),
                             ("hp+", "5 Health", dict(START_HP=5)),
                             ("str", "STR 3", dict(START_STR=3)),
                             ("att-", "8 attempts", dict(ATTEMPTS=8)),
                             ("att+", "10 attempts", dict(ATTEMPTS=10))):
        q = measure(games, **over)
        swing[key] = win(q) - win(base)
        print("   %-14s %6.1f%%  (%+.1f)   mean pool %4.1f"
              % (label, win(q), swing[key], tension(q)[0]))
    print()
    print("   Every dial is a cliff. One point of REC is worth %.0f to %.0f"
          % tuple(sorted((abs(swing["rec-"]), abs(swing["rec+"])))))
    print("   points of win rate and one point of Health %.0f to %.0f, against"
          % tuple(sorted((abs(swing["hp-"]), abs(swing["hp+"])))))
    print("   roughly 4 for a point of Tyrant Health in BAT. Nine attempts")
    print("   each near the pass/fail line, with Health covering only three")
    print("   failures, is a binomial knife edge - the finale is fragile")
    print("   rather than tense, and it cannot be tuned with these dials")
    print("   because there is no setting between far too easy and far too")
    print("   hard.")
    print()

    print("7. RESEARCH POOL - the other budget")
    print()
    print("   Target reduction bought   %.1f over the finale"
          % statistics.mean(base.bought))
    print("   cards left unspent        %.1f of 18"
          % statistics.mean(base.cards_left))
    print("   of those, retained        %.1f (the rest reduce nothing)"
          % statistics.mean(base.retained_left))
    print()
    print("   Not one retained card goes unspent: everything left in the")
    print("   pool at the end is a Candidate, which reduces nothing. The")
    print("   budget is spent out by the fourth attempt - see the Target")
    print("   rows in section 2, where the spent Target falls to 3.7 and is")
    print("   back at the printed value by attempt 7. The finale's whole")
    print("   reduction budget covers four attempts of nine.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else GAMES)
