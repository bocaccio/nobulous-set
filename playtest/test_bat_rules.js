/* Runs the lab's BAT rules engine in node, with no browser in the way.
 *
 *     node playtest/test_bat_rules.js
 *
 * The point is that a rule can be checked without playing the page. Every
 * assertion here is about the SCAVENGED-TYRANT design in rules/bat.html,
 * and the numbers are simulation/batrev.py's - which is BAT's model of
 * record, and what generator/check_app_sync.py holds this file against.
 */
"use strict";
var R = require("./dist/bat_rules.js");

var fails = 0, checks = 0;

function ok(label, cond, detail) {
  checks += 1;
  if (!cond) {
    fails += 1;
    console.log("  FAIL  " + label + (detail === undefined ? ""
      : "  [" + detail + "]"));
  }
}

// A seeded generator, so a failure is reproducible.
function lcg(seed) {
  var s = seed >>> 0;
  return function () {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// ---------------------------------------------------------------- setup
(function () {
  var rng = lcg(7), s = R.newGame("Standard", rng);
  ok("the carcass is 13 parts", s.parts.length === 13, s.parts.length);
  ok("the Experiment deck is 8 cards plus the Wake-Up",
    s.expDeck.length === 9, s.expDeck.length);
  ok("the Wake-Up is somewhere in the last three",
    s.expDeck.slice(6).indexOf(null) >= 0
    && s.expDeck.slice(0, 6).indexOf(null) < 0,
    JSON.stringify(s.expDeck));
  // AND THE WINDOW IS THREE WIDE, which the position alone does not prove:
  // a one-card packet puts the Wake-Up last every time and still passes the
  // check above, while the game it makes always runs eight Experiments.
  // Mutation-tested - WAKEUP_PACKET = 1 slipped past the check above.
  var seen = {};
  for (var k = 0; k < 400; k++) {
    var r2 = lcg(1000 + k), g = R.newGame("Standard", r2);
    seen[g.expDeck.indexOf(null)] = true;
  }
  ok("...and the Wake-Up really falls at six, seven OR eight",
    seen[6] && seen[7] && seen[8] && !seen[5],
    Object.keys(seen).join(","));
  ok("Standard deals 7 Specimens into the pool it samples from",
    R.DIFFICULTY.Standard.specimens === 7);
  ok("and gives ten rounds", s.rounds === 10, s.rounds);
  ok("every rung gets the same 13-card deck", R.PARTS_DECK === 13);
}());

// ------------------------------------------------------------ the Target
(function () {
  var rng = lcg(11), s = R.newGame("Standard", rng);
  R.revealExperiment(s, rng);
  var combined = R.partValue(s.current.parts[0])
    + R.partValue(s.current.parts[1]);
  ok("Target is combined Value minus the printed number",
    R.target(s, 4) === Math.max(1, combined - 4),
    R.target(s, 4) + " vs " + (combined - 4));
  ok("...and is floored at 1, never 0 or less",
    R.target(s, 99) === 1, R.target(s, 99));
}());

// ------------------------------------------- one part each, every time
(function () {
  var rng = lcg(3), s = R.newGame("Standard", rng), i, before, r;
  for (i = 0; i < 4; i++) {
    if (!R.revealExperiment(s, rng)) break;
    before = s.grafts.length;
    // fail it: the old Tyrant must take the HIGHER-Value part
    r = R.resolve(s, false, null);
    ok("a failure still grafts a part", s.grafts.length === before + 1);
    ok("...and the old Tyrant takes the better one",
      R.partValue(r.reclaim) >= R.partValue(r.graft),
      R.partValue(r.reclaim) + " vs " + R.partValue(r.graft));
  }
  ok("the Rats pick on a success", (function () {
    var rng2 = lcg(5), t = R.newGame("Standard", rng2), res;
    R.revealExperiment(t, rng2);
    var want = R.partValue(t.current.parts[0])
      >= R.partValue(t.current.parts[1]) ? 0 : 1;
    res = R.resolve(t, true, want);
    return res.graft === t.current.parts[want];
  }()));
}());

// ------------------------------------------------- conservation holds
(function () {
  var rng = lcg(21), s = R.newGame("Standard", rng), guard = 0;
  while (s.phase === "lab" && guard++ < 40) {
    if (!R.revealExperiment(s, rng)) break;
    R.resolve(s, guard % 2 === 0, 0);
  }
  ok("six, seven or eight Experiments resolve",
    s.experiments >= 6 && s.experiments <= 8, s.experiments);
  ok("conservation holds before Wake-Up", R.conservationOk(s, 13),
    s.parts.length + s.discard.length + s.grafts.length);
  R.wakeUp(s, rng);
  ok("conservation holds after Wake-Up", R.conservationOk(s, 13),
    s.battle.wall.length + " + " + s.grafts.length);
  ok("the wall is 13 minus the grafts",
    s.battle.wall.length === 13 - s.grafts.length);
  ok("the Prototyrant starts on 12", s.battle.hp === 12, s.battle.hp);
}());

// ------------------------------------------------------------ the battle
(function () {
  var rng = lcg(33), s = R.newGame("Easy", rng), guard = 0, b, cap;
  while (s.phase === "lab" && guard++ < 40) {
    if (!R.revealExperiment(s, rng)) break;
    R.resolve(s, true, 0);
  }
  R.wakeUp(s, rng);
  b = R.openRound(s, rng);
  ok("two grafts are revealed", b.shown.length === 2, b.shown.length);
  ok("a Splice is exposed", !!b.splice);
  R.expose(s, 1);
  ok("the graft not used is set aside", b.graftAside.length === 1,
    b.graftAside.length);
  // AND THE ASIDE PILE ACCUMULATES until the next reshuffle, which one
  // round cannot show: an expose() that threw the earlier cards away
  // passed the single-round check. Mutation-tested.
  if (b.graftPile.length >= 2) {
    R.openRound(s, rng);
    R.expose(s, 1);
    ok("...and a second round adds to it rather than replacing it",
      b.graftAside.length === 2, b.graftAside.length);
  }
  cap = R.diceCap(s);
  ok("the cap is the exposed graft's Value",
    cap === R.partValue(b.exposed), cap);
  ok("the Tyrant's dice are the exposed Splice's Value",
    R.attackDice(s) === Math.min(R.partValue(b.splice), 6), R.attackDice(s));
  // PINNED TO A VALUE THAT IS NOT THE DEFAULT. The check above passed a
  // mutation that returned a flat 2, because the seeded game happened to
  // expose a Value-2 Splice. A Specimen is always 5, so this one cannot.
  var keep = b.splice;
  b.splice = { type: "s", i: 0 };
  ok("...read off the card, not a constant - a Specimen draws 5",
    R.attackDice(s) === 5, R.attackDice(s));
  b.splice = { type: "u", i: 0 };            // Serrated Claws, Value 2
  ok("...and a Value-2 Splice draws 2", R.attackDice(s) === 2,
    R.attackDice(s));
  b.splice = keep;

  // a blow one short of the Target does nothing at all
  var wall = b.wall.length;
  var res = R.strike(s, R.partValue(b.splice) - 1);
  ok("a blow that falls short breaks nothing",
    !res.broke && b.wall.length === wall);
  res = R.strike(s, R.partValue(b.splice));
  ok("a blow that meets the Value breaks it",
    res.broke && b.wall.length === wall - 1);
}());

// ---------------------------------------------- the clock is a loss
(function () {
  var rng = lcg(44), s = R.newGame("Nobulous", rng), guard = 0;
  while (s.phase === "lab" && guard++ < 40) {
    if (!R.revealExperiment(s, rng)) break;
    R.resolve(s, false, null);
  }
  R.wakeUp(s, rng);
  ok("Nobulous gets eight rounds", s.rounds === 8, s.rounds);
  var i;
  for (i = 0; i < 8; i++) {
    R.openRound(s, rng);
    R.expose(s, 0);
    R.retaliate(s, 0);        // never attack, never take damage
  }
  ok("the Rats lose when the rounds run out with a wall standing",
    s.phase === "lost", s.phase + " round " + s.battle.round);
}());

// ------------------------------------- breaking the last Splice wins
(function () {
  var rng = lcg(55), s = R.newGame("Easy", rng), guard = 0;
  while (s.phase === "lab" && guard++ < 40) {
    if (!R.revealExperiment(s, rng)) break;
    R.resolve(s, true, 0);
  }
  R.wakeUp(s, rng);
  var guard2 = 0;
  while (s.battle.wall.length && guard2++ < 20) {
    R.openRound(s, rng);
    R.expose(s, 0);
    R.strike(s, 99);
  }
  ok("the last Splice ends it immediately", s.phase === "won",
    s.phase + " wall " + s.battle.wall.length);
}());

console.log((fails ? "" : "all ") + (checks - fails) + " of " + checks
  + " rules checks pass" + (fails ? ", " + fails + " FAILED" : ""));
process.exit(fails ? 1 : 0);
