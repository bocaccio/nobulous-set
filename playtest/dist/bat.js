/* BAT's playtest table: the UI half. The rules live in bat_rules.js, which
 * has no DOM in it and is tested by playtest/test_bat_rules.js under node.
 *
 * This file owns #screen-bat and nothing else. It renders state, collects
 * clicks, and rolls dice; every question about what a rule DOES is answered
 * by window.BAT_RULES, so a rule can be checked without playing the page.
 *
 * Rules source: rules/bat.html, the scavenged-Tyrant design.
 */
(() => {
  "use strict";
  const R = window.BAT_RULES;
  const $ = id => document.getElementById(id);
  const STORE = "nobulous-bat-v4";   // v2 was the printed game; v3 had a
                                   // Red die with no colour on it
  const cards = window.BAT_EXPERIMENTS || [];
  const names = R.RAT_NAMES;
  const colors = ["purple", "blue", "green", "yellow"];
  const DIE_ORDER = ["red", "purple", "blue", "green", "yellow"];
  const byColor = (a, b) =>
    DIE_ORDER.indexOf(a.color) - DIE_ORDER.indexOf(b.color);
  const faces = {
    purple: ["✦", "✦", "✦", "✦", "✷", ""],
    blue: ["✦", "✦", "✦", "✷", "", ""],
    green: ["✦", "✦", "✷", "", "", ""],
    yellow: ["✦", "✷", "", "", "", ""],
    red: ["✦", "✦", "✦", "✦", "✦", "✷"]
  };
  const faceValue = f => f === "✷" ? 2 : f === "✦" ? 1 : 0;
  const rollFace = color => faces[color][Math.floor(Math.random() * 6)];
  const escape = v => String(v).replace(/[&<>"']/g, ch =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
  const batTier = () =>
    window.NOBULOUS_TIER ? window.NOBULOUS_TIER.forGame("bat") : "0";

  let state = null;

  // ------------------------------------------------------------ the table
  function freshDice() {
    return names.map((_, i) => ({
      side: "front",
      dice: colors.map((c, k) => ({
        id: `${i}-${k}`, color: c, zone: "available", face: "", selected: false
      }))
    }));
  }

  function fresh(difficulty) {
    return {
      v: 4,
      difficulty,
      tier: batTier(),
      g: R.newGame(difficulty),
      rats: freshDice(),
      red: { color: "red", holder: Math.floor(Math.random() * 4),
             zone: "available", face: "", selected: false, aside: false },
      activeRat: null,
      rolled: false,
      successes: 0,
      notice: "",
      log: []
    };
  }

  function save() {
    try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {}
  }
  function load() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE) || "null");
      if (raw && raw.v === 4 && raw.g && raw.red && raw.red.color)
        return raw;
    } catch (e) {}
    return null;
  }

  const allDice = () => state.rats.flatMap(r => r.dice);
  const poolDice = () => allDice().filter(d => d.zone !== "banished"
    && d.zone !== "tyrant");
  const availableOf = i => state.rats[i].dice.filter(d => d.zone === "available");
  const inBattle = () => !!state.g.battle && state.g.phase === "battle";
  const over = () => state.g.phase === "won" || state.g.phase === "lost";
  const redUsable = () => !state.red.aside && state.red.zone === "available";

  function note(text) { state.notice = text; render(); }

  function logLine(text) {
    state.log.unshift(text);
    state.log = state.log.slice(0, 40);
  }

  // ------------------------------------------------------------- the lab
  function ensureExperiment() {
    const g = state.g;
    if (g.phase !== "lab" || g.current) return false;
    const c = R.revealExperiment(g);
    if (!c) { toBattle(); return true; }
    state.activeRat = null;
    state.rolled = false;
    state.successes = 0;
    allDice().forEach(d => { d.selected = false; });
    state.red.selected = false;
    save();
    return false;
  }

  const expCard = () => cards[state.g.current ? state.g.current.e : 0] || {};
  const expNumber = () => expCard().target ?? 4;
  const targetNow = () => R.target(state.g, expNumber());

  function selectedDice() {
    const picked = state.activeRat === null ? []
      : availableOf(state.activeRat).filter(d => d.selected);
    if (state.red.selected && redUsable()) picked.push(state.red);
    return picked;
  }

  function rollSelected() {
    const picked = selectedDice();
    if (!picked.length) return note("Select at least one die, or resolve a "
      + "zero-dice Experiment as a failure.");
    let total = 0;
    picked.forEach(d => { d.face = rollFace(d.color); total += faceValue(d.face); });
    state.successes = total;
    state.rolled = true;
    save();
    render();
  }

  function finishExperiment(ok, keep) {
    const g = state.g;
    const c = g.current;
    if (!c) return;
    const out = R.resolve(g, ok, keep);
    logLine(`${expCard().name}: Target ${targetNow()}, ${state.successes}`
      + ` success${state.successes === 1 ? "" : "es"} - `
      + (ok ? "SUCCESS" : "FAILURE")
      + `. Grafted ${R.partName(out.graft)} [${R.partValue(out.graft)}];`
      + ` the old Tyrant reclaimed ${R.partName(out.reclaim)}`
      + ` [${R.partValue(out.reclaim)}].`);
    // the committed dice exhaust, then this Rat recovers its REC
    if (state.activeRat !== null) {
      selectedDice().forEach(d => {
        if (d === state.red) { state.red.aside = true; }
        else { d.zone = "exhausted"; }
        d.selected = false;
      });
      const rec = R.RAT_REC[state.activeRat];
      state.rats[state.activeRat].dice
        .filter(d => d.zone === "exhausted")
        .slice(0, rec)
        .forEach(d => { d.zone = "available"; d.face = ""; });
      // Red goes to a non-active Rat, as the lab's own rule has it
      const others = names.map((_, i) => i).filter(i => i !== state.activeRat);
      state.red.holder = others[Math.floor(Math.random() * others.length)];
      state.red.aside = false;
      state.red.face = "";
    }
    g.current = null;
    state.rolled = false;
    state.successes = 0;
    state.notice = "";
    save();
    if (!ensureExperiment()) render();
  }

  // --------------------------------------------------------- the battle
  function toBattle() {
    const g = state.g;
    // The Tyrant's six come out of the Rats' own dice: there are only 17.
    const want = R.TYRANT_BAG.slice();
    want.forEach(color => {
      const die = poolDice().find(d => d.color === color && d.zone !== "tyrant");
      if (die) die.zone = "tyrant";
      else {
        const any = poolDice().find(d => d.zone !== "tyrant");
        if (any) any.zone = "tyrant";
      }
    });
    R.wakeUp(g);
    // available stays available, exhausted stays exhausted, then recover 2
    poolDice().filter(d => d.zone === "exhausted")
      .slice(0, R.OPENING_RECOVERY)
      .forEach(d => { d.zone = "available"; d.face = ""; });
    state.red.zone = "available";
    state.red.aside = false;
    logLine(`WAKE-UP after ${g.wakeUpAt} Experiments. The Prototyrant holds`
      + ` ${g.grafts.length} grafts; the old Tyrant's wall is`
      + ` ${g.battle.wall.length} Splices. ${g.rounds} rounds.`);
    openRound();
  }

  function openRound() {
    const g = state.g;
    if (g.phase !== "battle") return;
    R.openRound(g);
    state.activeRat = null;
    state.rolled = false;
    state.successes = 0;
    poolDice().forEach(d => { d.selected = false; });
    state.red.selected = false;
    save();
    render();
  }

  function battlePicked() {
    const picked = poolDice().filter(d => d.zone === "available" && d.selected);
    if (state.red.selected && redUsable()) picked.push(state.red);
    return picked;
  }

  function battleRoll() {
    const b = state.g.battle;
    if (!b.exposed && b.shown.length) return note("Choose which graft to use "
      + "and expose.");
    const picked = battlePicked();
    const cap = R.diceCap(state.g);
    if (!picked.length) return note("Select dice, or take the recovery pass.");
    if (picked.length > cap) return note(`The exposed graft caps you at ${cap}`
      + ` dice. Direct the attack is not a rule here - drop one.`);
    let total = 0;
    picked.forEach(d => { d.face = rollFace(d.color); total += faceValue(d.face); });
    state.successes = total;
    state.rolled = true;
    picked.forEach(d => {
      if (d === state.red) state.red.zone = "exhausted";   // R21: it exhausts
      else d.zone = "exhausted";
      d.selected = false;
    });
    const res = R.strike(state.g, total);
    logLine(`Round ${b.round}: ${picked.length} dice -> ${total} damage vs`
      + ` ${R.partName(b.splice)} [${R.partValue(b.splice)}] - `
      + (res.broke ? "BREAKS." : "bounces off."));
    if (res.won) { finishBattle(true); return; }
    retaliate(false);
  }

  function battlePass() {
    const b = state.g.battle;
    if (!b.exposed && b.shown.length) return note("Choose which graft to "
      + "expose first - it still defends.");
    retaliate(true);
  }

  function retaliate(passed) {
    const g = state.g, b = g.battle;
    const n = R.attackDice(g);
    const bag = R.TYRANT_BAG;
    let hits = 0;
    const rolled = [];
    for (let i = 0; i < n; i++) {
      const color = bag[Math.floor(Math.random() * bag.length)];
      const face = rollFace(color);
      rolled.push(color);
      hits += faceValue(face);
    }
    // The mechanical Attack cards. With one shared Health track the two
    // retargeting cards choose nothing, so they resolve as plain attacks -
    // their text is still printed in the log.
    const peek = b.attackDeck[0];
    let extra = "";
    if (peek === 0) { hits += 3; extra = " (+3, Overwhelming Mass)"; }
    if (peek === 3) { hits += b.wall.length; extra = ` (+${b.wall.length}, one per surviving Splice)`; }
    if (peek === 4) { hits = 0; extra = " (no damage, Terrifying Roar)"; }
    let direct = 0;
    if (peek === 5) { direct = 1; hits = Math.max(0, hits - 1); extra = " (1 straight to Health)"; }
    if (direct) { b.hp -= direct; }
    const out = R.retaliate(g, hits);
    logLine(`  ${out.name}: ${n} dice -> ${hits} incoming${extra}.`
      + (out.graftLost ? ` ${R.partName(out.graftLost)} destroyed.`
        : out.toHealth ? ` ${out.toHealth} to the Prototyrant's Health.`
          : " The graft holds."));
    if (passed) {
      const rec = state.activeRat === null ? R.PASS_RECOVERY_BONUS
        : R.recoveryPass(state.g, state.activeRat);
      const got = poolDice().filter(d => d.zone === "exhausted").slice(0, rec);
      got.forEach(d => { d.zone = "available"; d.face = ""; });
      if (state.red.zone === "exhausted" && got.length < rec) {
        state.red.zone = "available";
      }
      logLine(`  recovery pass: ${got.length} dice back.`);
    }
    if (g.phase === "lost") { finishBattle(false); return; }
    save();
    openRound();
  }

  function finishBattle(won) {
    state.g.phase = won ? "won" : "lost";
    logLine(won ? "The last Splice is down. The Rats win."
      : state.g.battle.round >= state.g.rounds
        ? "The rounds ran out with the wall standing. The Rats lose."
        : "The Prototyrant's Health is gone. The Rats lose.");
    save();
    render();
    const dlg = $("batEndDialog");
    if (dlg) {
      $("batEndTitle").textContent = won ? "The Prototyrant holds" : "Containment lost";
      $("batEndQuote").textContent = won
        ? "Nobulous will want to know how."
        : "Note the time of death and start again.";
      dlg.hidden = false;
    }
  }

  // ------------------------------------------------------------- render
  const cardArt = (label, value, sub) =>
    `<div class="suite-card portrait"><strong>${escape(label)}</strong>`
    + (value === undefined ? "" : `<span class="target-number">${value}</span>`)
    + (sub ? `<span class="tiny">${escape(sub)}</span>` : "") + "</div>";

  function renderStats() {
    const g = state.g;
    const bits = [];
    if (inBattle() || over()) {
      const b = g.battle;
      bits.push(["Round", `${b.round} / ${g.rounds}`]);
      bits.push(["Prototyrant Health", `${Math.max(0, b.hp)} / ${R.PROTO_HP}`]);
      bits.push(["Wall", `${b.wall.length} Splices`]);
      bits.push(["Grafts left", `${g.grafts.length}`]);
      bits.push(["Commit colour", b.commitColor || "free"]);
    } else {
      bits.push(["Experiments", `${g.experiments}`]);
      bits.push(["Carcass", `${g.parts.length} + ${g.discard.length} discard`]);
      bits.push(["Grafts", `${g.grafts.length}`
        + ` (Value ${g.grafts.reduce((t, c) => t + R.partValue(c), 0)})`]);
      bits.push(["Red", names[state.red.holder]]);
    }
    $("batStats").innerHTML = bits.map(([k, v]) =>
      `<div class="suite-stat"><span class="tiny">${escape(k)}</span>`
      + `<strong>${escape(v)}</strong></div>`).join("");
  }

  function renderRats() {
    $("batRats").innerHTML = state.rats.map((rat, i) => {
      const active = state.activeRat === i;
      const dice = rat.dice.slice().sort(byColor).map(d =>
        `<button class="face die-${d.color} ${d.zone}`
        + `${d.selected ? " selected" : ""}" data-bat-die="${d.id}"`
        + ` ${d.zone === "available" ? "" : "disabled"}>`
        + `${d.face || "·"}</button>`).join("");
      const red = state.red.holder === i
        ? `<button class="face die-red${state.red.selected ? " selected" : ""}"`
        + ` data-bat-die="red" ${redUsable() ? "" : "disabled"}>`
        + `${state.red.face || "R"}</button>` : "";
      return `<article class="suite-card landscape bat-rat-card`
        + `${active ? " active" : ""}" data-bat-active="${i}">`
        + `<strong>${escape(names[i])}</strong>`
        + `<span class="tiny">REC ${R.RAT_REC[i]}</span>`
        + `<div class="rat-dice-row">${dice}${red}</div></article>`;
    }).join("");
  }

  function renderLab() {
    const g = state.g, c = g.current;
    $("batPoolPanel").hidden = true;
    $("batBattlePanel").hidden = true;
    if (!c) { $("batEncounterText").textContent = ""; return; }
    const card = expCard();
    $("batEncounter").innerHTML = `<strong>${escape(card.name || "")}</strong>`
      + `<span class="target-number">${expNumber()}</span>`
      + `<span class="target-label">method</span>`;
    const t = targetNow();
    $("batEncounterText").innerHTML =
      `${escape(card.effect || "")}<br><span class="tiny">Target = `
      + `${R.partValue(c.parts[0])} + ${R.partValue(c.parts[1])} combined `
      + `&minus; ${expNumber()} = <strong>${t}</strong></span>`;
    ["A", "B"].forEach((k, idx) => {
      const p = c.parts[idx];
      $("batUpgrade" + k).innerHTML = `<strong>${escape(R.partName(p))}</strong>`
        + `<span class="target-number">${R.partValue(p)}</span>`
        + `<span class="tiny">${R.isSpecimen(p) ? "Specimen" : "Upgrade"}</span>`;
    });
    const ok = state.rolled && state.successes >= t;
    const head = $("batResolveHead");
    if (head) head.textContent = state.rolled
      ? "Assign the Splices" : "Resolve this Experiment";
    // BEFORE THE ROLL there is one action and it is ROLL. Two buttons both
    // reading Roll is what the first draft shipped, and it reads as a
    // choice the player does not have.
    $("batSuccessA").textContent = state.rolled
      ? `Success · graft ${R.partName(c.parts[0])}` : "Roll committed dice";
    $("batSuccessB").textContent = state.rolled
      ? `Success · graft ${R.partName(c.parts[1])}` : "";
    $("batSuccessA").disabled = state.rolled && !ok;
    $("batSuccessB").disabled = !ok;
    $("batSuccessB").hidden = !state.rolled;
    $("batFail").hidden = false;
    $("batFail").disabled = false;
    $("batFail").textContent = state.rolled
      ? "Failure · the old Tyrant takes the better Splice"
      : "Commit nothing · automatic failure";
    $("batEffect").innerHTML = state.notice
      ? `<strong>${escape(state.notice)}</strong>`
      : state.rolled
        ? `Rolled <strong>${state.successes}</strong> against Target `
          + `<strong>${t}</strong>. ${state.successes >= t
            ? "You choose which Splice the Prototyrant grafts."
            : "The old Tyrant takes the better Splice."}`
        : state.activeRat === null
          ? "Choose the active Rat, then commit dice."
          : "Commit dice and roll.";
  }

  function renderBattle() {
    const g = state.g, b = g.battle;
    $("batPoolPanel").hidden = false;
    $("batBattlePanel").hidden = false;
    const pool = poolDice().filter(d => d.zone !== "tyrant");
    $("batPool").innerHTML = pool.slice().sort(byColor).map(d =>
      `<button class="face die-${d.color} ${d.zone}`
      + `${d.selected ? " selected" : ""}" data-bat-die="${d.id}"`
      + ` ${d.zone === "available" ? "" : "disabled"}>${d.face || "·"}</button>`
    ).join("") + (state.red.zone !== "banished"
      ? `<button class="face die-red${state.red.selected ? " selected" : ""}"`
      + ` data-bat-die="red" ${redUsable() ? "" : "disabled"}>`
      + `${state.red.face || "R"}</button>` : "");
    const cap = R.diceCap(g);
    const shown = b.shown.length ? b.shown.map((gr, i) =>
      `<button class="bat-track-state${b.exposed === gr ? " bat-required" : ""}"`
      + ` data-bat-expose="${i}">${escape(R.partName(gr))}`
      + ` [${R.partValue(gr)}]</button>`).join("") : "";
    $("batTrack").innerHTML =
      `<div class="bat-track-name">Exposed Splice</div>`
      + (b.splice ? cardArt(R.partName(b.splice), R.partValue(b.splice),
        "meet it in one blow") : "<em>none</em>")
      + `<div class="bat-track-name">Grafts revealed — use one, set one aside</div>`
      + shown
      + `<div class="tiny">Dice cap ${cap}. `
      + `${b.exposed ? escape(R.partName(b.exposed)) + " defends at "
        + R.partValue(b.exposed) : "no graft: nothing defends"}.</div>`;
    $("batEffect").innerHTML = state.notice
      ? `<strong>${escape(state.notice)}</strong>`
      : `Round ${b.round} of ${g.rounds}. Commit up to ${cap}, or pass to `
        + `recover. ${b.wall.length} Splice${b.wall.length === 1 ? "" : "s"} left.`;
    const head = $("batResolveHead");
    if (head) head.textContent = over() ? "The fight is over"
      : `Round ${b.round} of ${g.rounds}`;
    $("batSuccessA").textContent = "Attack · roll committed dice";
    $("batSuccessA").disabled = over();
    $("batSuccessA").hidden = false;
    $("batSuccessB").textContent = "Recovery pass";
    $("batSuccessB").disabled = over();
    $("batSuccessB").hidden = false;
    // No third action in the battle, so the button goes rather than
    // sitting there dead.
    $("batFail").hidden = true;
  }

  function render() {
    if (!state) return;
    // THE NRJ MODULES ARE NOT IN THIS TABLE YET, and saying nothing would
    // be worse than saying that: the scavenged-Tyrant design changes every
    // one of their cards (batrev.py's R33, R34 and R35 - two Protocols
    // re-expressed, the Modifications' ownership text rewritten, four of
    // the six Research Notes needing new wording), so the old copies would
    // teach a playtester rules no card has. Play them off the cards until
    // they are ported.
    $("batOverlay").textContent = (window.NOBULOUS_TIER && batTier() !== "0")
      ? `NRJ Tier ${window.NOBULOUS_TIER.name(batTier())}: the module cards`
        + " are NOT dealt by this table yet - the scavenged-Tyrant design"
        + " rewrites all of them. Play them from the printed cards."
      : "";
    $("batDifficulty").value = state.difficulty;
    renderStats();
    renderRats();
    if (inBattle() || over()) renderBattle(); else renderLab();
    $("batSpliceCount").textContent = inBattle() || over()
      ? `${state.g.battle.wall.length} Splices standing`
      : `${state.g.grafts.length} grafted`;
    $("batSpliceNames").innerHTML = (inBattle() || over()
      ? state.g.battle.wall : state.g.grafts).map(c =>
      `<span class="bat-track-state">${escape(R.partName(c))}`
      + ` [${R.partValue(c)}]</span>`).join("") || "<em>nothing yet</em>";
    $("batRoller").innerHTML = state.log.length
      ? state.log.map(l => `<p class="tiny">${escape(l)}</p>`).join("")
      : `<p class="hint">The log of this game appears here.</p>`;
  }

  // -------------------------------------------------------------- clicks
  function toggleDie(id) {
    if (id === "red") {
      if (!redUsable()) return;
      state.red.selected = !state.red.selected;
    } else {
      const die = allDice().find(d => d.id === id);
      if (!die || die.zone !== "available") return;
      if (!inBattle() && state.activeRat !== null
        && !availableOf(state.activeRat).includes(die)) {
        return note("That die belongs to another Rat. Borrowing is a table "
          + "action in the lab: move it yourself.");
      }
      die.selected = !die.selected;
    }
    state.notice = "";
    save();
    render();
  }

  function handleClick(event) {
    if (!state) return;
    const el = event.target.closest?.("[data-bat-die],[data-bat-active],"
      + "[data-bat-expose],button");
    if (!el) return;
    if (el.dataset?.batDie) { event.preventDefault(); return toggleDie(el.dataset.batDie); }
    if (el.dataset?.batExpose !== undefined) {
      event.preventDefault();
      R.expose(state.g, Number(el.dataset.batExpose));
      state.notice = "";
      save();
      return render();
    }
    if (el.dataset?.batActive !== undefined && !inBattle()) {
      event.preventDefault();
      state.activeRat = Number(el.dataset.batActive);
      state.notice = "";
      save();
      return render();
    }
    if (el.id === "batSuccessA") {
      event.preventDefault();
      return inBattle() ? battleRoll()
        : state.rolled ? finishExperiment(true, 0) : rollSelected();
    }
    if (el.id === "batSuccessB") {
      event.preventDefault();
      return inBattle() ? battlePass()
        : state.rolled ? finishExperiment(true, 1) : rollSelected();
    }
    if (el.id === "batFail" && !inBattle()) {
      event.preventDefault();
      return finishExperiment(false, null);
    }
    if (el.dataset?.batActive !== undefined && inBattle()) {
      event.preventDefault();
      state.activeRat = Number(el.dataset.batActive);
      save();
      return render();
    }
  }

  document.addEventListener("click", handleClick, true);
  $("batDifficulty").onchange = e => {
    state = fresh(e.target.value);
    save();
    if (!ensureExperiment()) render();
  };
  $("batRat").onchange = e => {
    state.activeRat = e.target.selectedIndex;
    save();
    render();
  };
  window.addEventListener("nobulous-tier", () => {
    if (batTier() === (state && state.tier || "0")) return render();
    state = fresh(state.difficulty);
    save();
    if (!ensureExperiment()) render();
  });

  state = load() || fresh("Standard");
  if (!ensureExperiment()) render();
  window.BAT_LAB = { render: () => { if (!ensureExperiment()) render(); } };
})();
