/* BAT's rules engine, with no DOM in it.
 *
 * WHY THIS FILE EXISTS. The lab's BAT table used to be one 1685-line module
 * where the rules and the rendering were the same code, so the only way to
 * check a rule was to play the page. This half is pure: it takes a state
 * object and returns a new one, it never touches the document, and
 * playtest/test_bat_rules.js runs it in node. generator/check_app_sync.py
 * holds its numbers against simulation/batrev.py, which is BAT's model of
 * record, so the lab and the model cannot drift apart quietly.
 *
 * Rules source: rules/bat.html, the scavenged-Tyrant design of 2026-11-20.
 * The ruling numbers in comments (R2, R5, R13...) are batrev.py's.
 */
(function (root) {
  "use strict";

  // ---- card data. The values are generator/build_bat.py's, transcribed
  // the same way simulation/bat.py transcribes them.
  var UPGRADES = [
    ["Serrated Claws", 2], ["Reinforced Jaw", 3], ["Capacitor Muscles", 3],
    ["Piercing Horn", 4], ["Spring-Loaded Legs", 2], ["Prehensile Tail", 2],
    ["Tripwire Tendons", 3], ["Evasive Reflexes", 3], ["Thickened Hide", 2],
    ["Layered Carapace", 3], ["Chromatic Plating", 3], ["Reactive Shell", 4],
    ["Acute Hearing", 2], ["Predatory Focus", 3], ["Rapid Metabolism", 2],
    ["Neural Overclock", 4]
  ];
  var SPECIMENS = ["Titanium-Toothed Mole", "Voltaic Mantis", "Blink Hare",
    "Ghost Gecko", "Ironback Beetle", "Prismatic Tortoise", "Echo Bat",
    "Regenerator Newt"];
  var SPECIMEN_VALUE = 5;

  // ---- the ladder. Difficulty sets the Specimens in the carcass and the
  // ROUNDS the Rats get; the parts deck is 13 on every rung, because a deck
  // card is a whole Splice and so a whole attack out of ten rounds.
  var DIFFICULTY = {
    Easy: { specimens: 5, rounds: 12 },
    Standard: { specimens: 7, rounds: 10 },
    Hard: { specimens: 7, rounds: 9 },
    Nobulous: { specimens: 8, rounds: 8 }
  };
  var PARTS_DECK = 13;
  var EXPERIMENTS_DEALT = 8;
  var WAKEUP_PACKET = 3;
  var TARGET_FLOOR = 1;      // R2
  var PROTO_HP = 12;         // one shared Health track
  var OPENING_RECOVERY = 2;  // R14
  var PASS_RECOVERY_BONUS = 2;
  var NO_GRAFT_CAP = 3;
  var GRAFT_REVEAL = 2;
  var TYRANT_BAG = ["purple", "purple", "blue", "blue", "green", "yellow"];
  var RAT_NAMES = ["Rummage", "Fidget", "Whiz", "Mottle"];
  var RAT_REC = [2, 2, 1, 1];
  var ATTACK_NAMES = ["Overwhelming Mass", "Adaptive Strike",
    "Predatory Instinct", "Spliced Reflexes", "Terrifying Roar",
    "Crushing Blow", "Unstable Growth"];
  var ATTACK_DOTS = ["G", "G", "G", "Y", "Y", "Y", "B"];
  var DOT_COLOR = { G: "green", Y: "yellow", B: "blue" };

  function partValue(card) {
    return card.type === "s" ? SPECIMEN_VALUE : UPGRADES[card.i][1];
  }
  function partName(card) {
    return card.type === "s" ? SPECIMENS[card.i] : UPGRADES[card.i][0];
  }
  function isSpecimen(card) { return card.type === "s"; }

  function shuffle(list, rng) {
    var a = list.slice(), i, j, t;
    for (i = a.length - 1; i > 0; i--) {
      j = Math.floor(rng() * (i + 1));
      t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function sample(list, n, rng) { return shuffle(list, rng).slice(0, n); }

  // ---------------------------------------------------------------- setup
  function newGame(difficulty, rng) {
    rng = rng || Math.random;
    var conf = DIFFICULTY[difficulty] || DIFFICULTY.Standard;
    var pool = [], i;
    for (i = 0; i < UPGRADES.length; i++) pool.push({ type: "u", i: i });
    sample([0, 1, 2, 3, 4, 5, 6, 7], conf.specimens, rng)
      .forEach(function (k) { pool.push({ type: "s", i: k }); });

    // R3: eight Experiments dealt, then the last two shuffled with the
    // Wake-Up card and put underneath the first six. Six, seven or eight
    // resolve, at equal odds, and the Rats cannot know which.
    var all = [], packet, deck;
    for (i = 0; i < 20; i++) all.push(i);
    var dealt = sample(all, EXPERIMENTS_DEALT, rng);
    packet = shuffle(dealt.slice(EXPERIMENTS_DEALT - (WAKEUP_PACKET - 1))
      .concat([null]), rng);
    deck = dealt.slice(0, EXPERIMENTS_DEALT - (WAKEUP_PACKET - 1))
      .concat(packet);

    return {
      v: 3,
      difficulty: difficulty,
      rounds: conf.rounds,
      parts: sample(pool, PARTS_DECK, rng),
      discard: [],
      grafts: [],
      expDeck: deck,
      reserve: all.filter(function (x) { return dealt.indexOf(x) < 0; }),
      experiments: 0,
      current: null,
      phase: "lab",
      wakeUpAt: null,
      battle: null,
      log: []
    };
  }

  // R4: never fail to reveal a part - the discard recirculates.
  function drawPart(s, rng) {
    if (!s.parts.length) {
      if (!s.discard.length) return null;
      s.parts = shuffle(s.discard, rng || Math.random);
      s.discard = [];
    }
    return s.parts.pop();
  }

  function revealExperiment(s, rng) {
    rng = rng || Math.random;
    if (!s.expDeck.length) return null;
    var e = s.expDeck.shift();
    if (e === null) { s.phase = "wakeup"; s.wakeUpAt = s.experiments; return null; }
    var a = drawPart(s, rng), b = drawPart(s, rng);
    if (!a || !b) { s.phase = "wakeup"; s.wakeUpAt = s.experiments; return null; }
    s.current = {
      e: e, parts: [a, b], activeRat: null, rolled: false,
      successes: 0, resolved: false
    };
    return s.current;
  }

  // R2: Target = the two parts' combined Value minus the Experiment's
  // printed number, floored at 1. Rich parts are harder to win; a
  // high-numbered Experiment is a better method.
  function target(s, printedNumber) {
    var c = s.current;
    if (!c) return null;
    var combined = partValue(c.parts[0]) + partValue(c.parts[1]);
    return Math.max(TARGET_FLOOR, combined - printedNumber);
  }

  // R5/R6: one part grafted, one reclaimed, every time. Success only
  // decides WHO PICKS. `keep` is the index the Rats graft on a success.
  function resolve(s, ok, keep) {
    var c = s.current, order, graft, reclaim;
    if (!c || c.resolved) return null;
    order = c.parts.slice().sort(function (x, y) {
      return partValue(y) - partValue(x);
    });
    if (ok) graft = c.parts[keep === 1 ? 1 : 0];
    else graft = order[1];                      // the old Tyrant takes the best
    reclaim = c.parts[0] === graft ? c.parts[1] : c.parts[0];
    s.grafts.push(graft);
    s.discard.push(reclaim);
    c.resolved = true;
    c.graft = graft;
    c.reclaim = reclaim;
    s.experiments += 1;
    return { graft: graft, reclaim: reclaim };
  }

  // ------------------------------------------------------------- Wake-Up
  // R13/R14: the wall is what is left in the carcass - undrawn deck plus
  // discard - which is starting parts minus the grafts. Conservation is
  // checkable, and conservationOk() below is what checks it.
  function wakeUp(s, rng) {
    rng = rng || Math.random;
    var wall = shuffle(s.parts.concat(s.discard), rng);
    var attacks = [], i;
    for (i = 0; i < ATTACK_NAMES.length; i++) attacks.push(i);
    s.parts = [];
    s.discard = [];
    s.current = null;
    s.phase = "battle";
    s.battle = {
      wall: wall,
      graftPile: shuffle(s.grafts, rng),
      graftAside: [],
      shown: [],
      exposed: null,
      splice: null,
      hp: PROTO_HP,
      round: 0,
      bag: TYRANT_BAG.slice(),
      attackDeck: shuffle(attacks, rng),
      attackDiscard: [],
      commitColor: null,
      activeRat: 0,
      rolled: false,
      passed: false
    };
    return s.battle;
  }

  function conservationOk(s, startingParts) {
    var b = s.battle;
    var wall = b ? b.wall.length : s.parts.length + s.discard.length;
    return wall + s.grafts.length === (startingParts || PARTS_DECK);
  }

  // ------------------------------------------------------------- a round
  // R15: two grafts are revealed, one used and exposed and the other set
  // aside where nothing can destroy it. The exposed Splice is the top of
  // the wall, and its Value is the damage to land in ONE blow.
  function openRound(s, rng) {
    rng = rng || Math.random;
    var b = s.battle;
    if (b.graftPile.length < GRAFT_REVEAL) {
      b.graftPile = shuffle(b.graftPile.concat(b.graftAside), rng);
      b.graftAside = [];
    }
    b.shown = b.graftPile.splice(0, Math.min(GRAFT_REVEAL,
      b.graftPile.length));
    b.exposed = b.shown.length ? b.shown[0] : null;
    b.splice = b.wall.length ? b.wall[0] : null;
    b.round += 1;
    b.rolled = false;
    b.passed = false;
    return b;
  }

  function expose(s, which) {
    var b = s.battle;
    if (!b.shown.length) return null;
    b.exposed = b.shown[which] || b.shown[0];
    b.graftAside = b.graftAside.concat(b.shown.filter(function (g) {
      return g !== b.exposed;
    }));
    return b.exposed;
  }

  function diceCap(s) {
    var b = s.battle;
    return b.exposed ? partValue(b.exposed) : NO_GRAFT_CAP;
  }

  // A Splice does not chip: meet its Value in one blow or the attack is
  // wasted, and nothing carries to the next Splice.
  function strike(s, damage) {
    var b = s.battle, broke;
    if (!b.splice) return { broke: false, won: false };
    broke = damage >= partValue(b.splice);
    if (broke) {
      b.wall.shift();
      if (!b.wall.length) { s.phase = "won"; return { broke: true, won: true }; }
    }
    b.brokeThisRound = broke;
    return { broke: broke, won: false };
  }

  // R20: a destroyed Splice still sets the counterattack's dice count, and
  // its printed effect does not fire. The exposed graft defends whether or
  // not it attacked, and is destroyed when the blow meets its Value.
  function retaliate(s, rolled) {
    var b = s.battle, card = b.attackDeck.shift(), hits = rolled, out;
    if (card === undefined) {
      b.attackDeck = b.attackDiscard;
      b.attackDiscard = [];
      card = b.attackDeck.shift();
    }
    b.attackDiscard.unshift(card);
    b.commitColor = DOT_COLOR[ATTACK_DOTS[card]];
    out = { card: card, name: ATTACK_NAMES[card], hits: hits, graftLost: null,
            toHealth: 0 };
    if (b.exposed) {
      if (hits >= partValue(b.exposed)) {
        out.graftLost = b.exposed;
        s.grafts = s.grafts.filter(function (g) { return g !== b.exposed; });
      } else {
        b.graftPile.push(b.exposed);
      }
    } else {
      out.toHealth = hits;
      b.hp -= hits;
    }
    b.exposed = null;
    b.shown = [];
    if (b.hp <= 0) s.phase = "lost";
    else if (b.round >= s.rounds && b.wall.length) s.phase = "lost";
    return out;
  }

  function attackDice(s) {
    var b = s.battle;
    return b.splice ? Math.min(partValue(b.splice), b.bag.length) : 2;
  }

  function recoveryPass(s, ratIndex) {
    return RAT_REC[ratIndex] + PASS_RECOVERY_BONUS;
  }

  root.BAT_RULES = {
    UPGRADES: UPGRADES, SPECIMENS: SPECIMENS, SPECIMEN_VALUE: SPECIMEN_VALUE,
    DIFFICULTY: DIFFICULTY, PARTS_DECK: PARTS_DECK,
    EXPERIMENTS_DEALT: EXPERIMENTS_DEALT, WAKEUP_PACKET: WAKEUP_PACKET,
    TARGET_FLOOR: TARGET_FLOOR, PROTO_HP: PROTO_HP,
    OPENING_RECOVERY: OPENING_RECOVERY,
    PASS_RECOVERY_BONUS: PASS_RECOVERY_BONUS, NO_GRAFT_CAP: NO_GRAFT_CAP,
    GRAFT_REVEAL: GRAFT_REVEAL, TYRANT_BAG: TYRANT_BAG,
    RAT_NAMES: RAT_NAMES, RAT_REC: RAT_REC,
    ATTACK_NAMES: ATTACK_NAMES, ATTACK_DOTS: ATTACK_DOTS,
    DOT_COLOR: DOT_COLOR,
    partValue: partValue, partName: partName, isSpecimen: isSpecimen,
    shuffle: shuffle, newGame: newGame, drawPart: drawPart,
    revealExperiment: revealExperiment, target: target, resolve: resolve,
    wakeUp: wakeUp, conservationOk: conservationOk, openRound: openRound,
    expose: expose, diceCap: diceCap, strike: strike, retaliate: retaliate,
    attackDice: attackDice, recoveryPass: recoveryPass
  };
}(typeof window !== "undefined" ? window
  : typeof globalThis !== "undefined" ? globalThis : this));

if (typeof module !== "undefined" && module.exports) {
  module.exports = (typeof globalThis !== "undefined" ? globalThis : this)
    .BAT_RULES;
}
