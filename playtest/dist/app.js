(() => {
  "use strict";

  const ASSET = "assets/";
  const ASSET_VERSION = "aos-flavor-v2";
  const DECKS = {
    Routine: { front: "AoS_Routine_TTS.png", back: "AoS_Routine_TTS_back.png", count: 8 },
    Specialized: { front: "AoS_Specialized_TTS.png", back: "AoS_Specialized_TTS_back.png", count: 8 },
    Unstable: { front: "AoS_Unstable_TTS.png", back: "AoS_Unstable_TTS_back.png", count: 8 },
    Advanced: { front: "AoS_Advanced_TTS.png", back: "AoS_Advanced_TTS_back.png", count: 8 }
  };
  const ELEMENT_COUNTS = {
    Routine: [3, 3, 3, 3, 3, 4, 3, 4],
    Specialized: [3, 4, 3, 4, 3, 4, 4, 4],
    Unstable: [4, 4, 4, 4, 4, 4, 4, 4],
    Advanced: [5, 4, 5, 4, 5, 4, 5, 5]
  };
  const PROGRAM_TARGETS = {
    Routine: {
      front: [[2,3,2],[3,2,2],[2,2,3],[2,3,2],[3,2,2],[2,2,2,2],[2,3,2],[2,2,2,3]],
      back: [[3,3,2],[3,3,2],[3,2,3],[2,4,2],[3,2,3],[2,3,2,2],[2,3,3],[2,2,3,3]]
    },
    Specialized: {
      front: [[3,2,3],[2,3,2,2],[3,3,2],[2,3,2,3],[3,2,3],[3,2,3,2],[2,3,3,2],[3,2,2,3]],
      back: [[3,3,3],[3,3,2,2],[3,4,2],[2,3,2,4],[4,2,3],[3,2,4,2],[2,4,3,2],[3,2,3,3]]
    },
    Unstable: {
      front: [[3,2,3,2],[2,3,2,3],[3,2,3,2],[2,3,3,2],[3,2,2,3],[2,3,2,3],[3,3,2,3],[3,2,3,2]],
      back: [[4,2,3,2],[2,3,2,4],[3,2,4,2],[2,4,3,2],[4,2,2,3],[2,3,2,4],[3,4,2,3],[3,3,3,2]]
    },
    Advanced: {
      front: [[2,3,3,3,2],[3,3,3,3],[2,3,3,3,3],[3,3,3,2],[3,2,3,2,3],[3,3,3,3],[2,3,3,3,2],[3,3,3,3,3]],
      back: [[2,3,4,3,2],[3,4,3,3],[2,3,3,4,3],[4,3,3,2],[3,2,4,2,3],[3,3,4,3],[2,4,3,3,2],[3,3,4,3,3]]
    }
  };
  const PROGRAM_REWARDS = {
    Routine: ["hp", "recover", "rec", "unheat", "str", "banish", "recover", "unheat"],
    Specialized: ["hp", "str", "recover", "rec", "unheat", "banish", "recover", "unheat"],
    Unstable: ["hp", "rec", "unheat", "str", "recover", "banish", "recover", "unheat"]
  };
  const REWARDS = {
    hp: "Gain 1 HP", recover: "Recover 3 exhausted dice", rec: "+1 REC; remove this Program",
    str: "+1 STR; remove this Program", unheat: "Return 1 Overheated Program to Stable", banish: "Banish 1 Limitation"
  };
  const PROGRAM_FLAVOR = {
    Routine: [
      { name:"Maintain Balance", front:"The shale frame holds steady while Nobulous adds one unnecessary clipboard.", back:"The frame still balances, provided nobody breathes near it." },
      { name:"Lift a Heavy Object", front:"The automaton raises the test mass with reassuring precision.", back:"The test mass rises. The floor follows." },
      { name:"Climb an Incline", front:"Measured steps carry the chassis cleanly up the graded ramp.", back:"Each step lands harder than the last; the ramp files a complaint." },
      { name:"Move at Speed", front:"The timing gates agree: it is fast, controlled, and technically indoors.", back:"It clears the final gate before the first one stops shaking." },
      { name:"Navigate a Passage", front:"The frame folds through the mock corridor without touching a wall.", back:"The corridor is now wider, though not by design." },
      { name:"Cross Uneven Ground", front:"Independent joints keep the load level over broken ground.", back:"The joints correct so violently that the ground becomes the stable part." },
      { name:"Manipulate an Object", front:"Stone fingers turn the instrument exactly one calibrated notch.", back:"The instrument turns three notches and ceases to be calibrated." },
      { name:"Detect an Obstacle", front:"Its sensors mark every obstruction before contact.", back:"It detects each obstruction immediately after impact." }
    ],
    Specialized: [
      { name:"Traverse Difficult Terrain", front:"The chassis reads the terrain and places each step where the ground will hold.", back:"It reads the terrain correctly, then challenges every conclusion." },
      { name:"Move Without Detection", front:"Noise dampers reduce a stone machine to a passing draft.", back:"The dampers hold; the footprints still resemble impact craters." },
      { name:"Track a Moving Subject", front:"Sensors maintain a calm lock through every change of direction.", back:"The lock tightens until every movement looks like an escape attempt." },
      { name:"Climb a Vertical Surface", front:"Anchors bite, release, and rise in a clean mechanical rhythm.", back:"The anchors bite deeper; sections of wall begin climbing too." },
      { name:"Clear an Obstacle", front:"It measures the barrier and clears it with centimeters to spare.", back:"It clears the barrier. The barrier does not clear it." },
      { name:"Operate in Low Light", front:"Passive sensors map the dark without announcing their presence.", back:"The map is perfect; the glowing heat signature is less subtle." },
      { name:"Maintain a Pursuit", front:"It matches the subject's pace without closing too quickly.", back:"Pursuit logic discards 'too quickly' as an unnecessary constraint." },
      { name:"Carry a Moving Load", front:"Compensators cradle the shifting load through every turn.", back:"The load remains secure while everything beneath it shifts." }
    ],
    Unstable: [
      { name:"Navigate Without Guidance", front:"The automaton builds a route from landmarks and quiet inference.", back:"It builds several routes and attempts all of them at once." },
      { name:"Evade Observation", front:"Timing and cover reduce a stone chassis to a rumor.", back:"It avoids every observer except the ones staring at the new hole." },
      { name:"Overcome a Barrier", front:"The frame tests the obstruction, then applies exactly enough force.", back:"It applies exactly enough force to redefine the obstruction." },
      { name:"Intercept a Moving Subject", front:"Prediction places the automaton precisely in the subject's path.", back:"Prediction becomes certainty; the path has no remaining alternatives." },
      { name:"Maintain Control of a Load", front:"Micro-corrections keep unstable cargo centered and intact.", back:"Corrections accelerate until the cargo is the calmest thing in motion." },
      { name:"Adapt to Changing Terrain", front:"The gait rewrites itself as the ground changes.", back:"The gait keeps rewriting after the ground stops." },
      { name:"Execute a Complex Route", front:"Every turn arrives on time, in sequence, and without hesitation.", back:"The sequence remains flawless; the surrounding architecture does not." },
      { name:"Operate Autonomously", front:"It completes the objective without instruction or improvisation.", back:"It completes a different objective with alarming confidence." }
    ],
    Advanced: [
      { name:"Rapid Approach", front:"It reaches the target before the warning can become an alarm.", back:"It reaches the target before the warning—and most of the doorway." },
      { name:"Unobserved Entry", front:"Locks open, cameras loop, and the corridor never learns it was occupied.", back:"Locks open, cameras loop, and the corridor becomes difficult to explain." },
      { name:"Subject Acquisition", front:"It identifies, isolates, and secures the designated subject without disturbing the room.", back:"It secures the subject, several bystanders, and the room's structural supports." },
      { name:"Difficult Extraction", front:"It carries the subject through the least impossible route.", back:"The route becomes less impossible as walls become optional." },
      { name:"Autonomous Infiltration", front:"It enters, adapts, and advances without a single transmitted instruction.", back:"Silence is maintained because it has stopped accepting instructions." },
      { name:"Controlled Restraint", front:"Force sensors hold the subject firmly below the injury threshold.", back:"The threshold remains documented, if no longer especially relevant." },
      { name:"Adaptive Pursuit", front:"It learns each evasion and closes the next escape before it begins.", back:"It learns too quickly; every movement becomes evidence of escape." },
      { name:"Council Extraction Protocol", front:"The automaton escorts the Councilor out beneath a veil of perfect procedure.", back:"The Councilor is extracted. The Council chamber is now an open-plan space." }
    ]
  };
  const LIMITATION_FLAVOR = [
    { name:"Yellow Shortage", text:"The precision components are on another bench. Nobulous has misplaced the bench." },
    { name:"Green Shortage", text:"Mobility actuators have been reassigned to a 'more urgent' prototype." },
    { name:"Blue Shortage", text:"Sensor stock is low; confidence remains inexplicably high." },
    { name:"Purple Shortage", text:"Load-bearing modules are delayed. The load is not." },
    { name:"Diversity Protocol", text:"Nobulous demands cross-functional resilience with fewer functions." },
    { name:"Red Quarantine", text:"The emergency die is perfectly safe inside the locked cabinet." }
  ];
  const TECHS = [
    { name: "Architect", side: "front", index: 0, ability: "Reconfigure — Once per Program, before rolling an element, move up to 2 allocated dice between unresolved elements." },
    { name: "Debugger", side: "back", index: 0, ability: "Debug — Once per Program, after failing by exactly 1 success, reroll 1 allocated die. If it still fails, exhaust that die." },
    { name: "Optimizer", side: "front", index: 1, ability: "Optimize — Once per Program, Target +1 successes may count as Optimal Implementation." },
    { name: "Engineer", side: "back", index: 1, ability: "Redundancy — For up to 2 elements per Program, the safe allocation threshold is Target +2 instead of Target +1." },
    { name: "Operator", side: "front", index: 2, ability: "Workaround — When a non-Red Limitation would withhold 2 dice, you may withhold 1 of those dice as another non-Red color instead." },
    { name: "Compiler", side: "back", index: 2, ability: "Compile — When spending an additional STR roll, reroll any number of dice on that element while keeping the others." }
  ];
  const COLORS = ["purple", "blue", "green", "yellow"];
  const FACES = {
    purple: ["hit", "hit", "hit", "crit", "hit", "blank"],
    blue: ["hit", "hit", "blank", "crit", "hit", "blank"],
    green: ["hit", "blank", "blank", "crit", "hit", "blank"],
    yellow: ["hit", "blank", "blank", "crit", "blank", "blank"],
    red: ["hit", "hit", "hit", "crit", "hit", "hit"]
  };
  const FACE_MARK = { hit: "✦", crit: "✷", blank: "" };
  const STORAGE = "nobulous-aos-playtest-v1";
  let selectedDice = new Set();
  let toastTimer;

  const $ = (id) => document.getElementById(id);
  const shuffle = (items) => {
    const a = [...items];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  const freshDice = () => [...COLORS.flatMap(color => Array.from({ length: 4 }, (_, i) => ({ id: `${color}-${i}`, color, zone: "available", element: null, face: null }))), { id: "red-0", color: "red", zone: "available", element: null, face: null }];
  const freshMetrics = () => ({ programs: 0, failedElements: 0, catastrophes: 0, rerolls: 0, diceExhausted: 0, requiredMisses: 0, fiddly: 0, unclear: 0, good: 0 });
  const freshState = () => ({
    started: false, deck: "Specialized", tech: 0, hp: 2, str: 2, rec: 3, cycle: 1, mode: "program",
    programs: Array.from({ length: 8 }, (_, id) => ({ id, status: "stable" })), queue: [], current: null,
    currentFace: "front", currentCompleted: false, lastResultFailed: false, limitation: null, limitationRevealed: false, limitationQueue: shuffle([0,1,2,3,4,5]), banishedLimitations: [],
    advancedQueue: [], nextAdvancedOverheated: false, advancedDone: 0, dice: freshDice(), elements: [], elementCount: 3,
    rerollsUsed: 0, recoveryCredits: 0, architectUsed: false, architectMode: false, debuggerUsed: false, optimizerUsed: false, rewardApplied: false,
    targetsVersion: 1, metrics: freshMetrics(), notes: "", log: [], finished: false
  });
  let state = freshState();

  function elementTemplate(i) { return { id: i, target: 3, thresholdBonus: 1, optimizerUsed: false, rolled: false, usedReroll: false, resolved: false, failed: false, pendingExhaust: 0, successes: 0 }; }
  function currentElementCount() {
    if (!state.current) return state.elementCount || 3;
    const deck = state.current.mode === "advanced" ? "Advanced" : state.deck;
    return ELEMENT_COUNTS[deck]?.[state.current.id] || 3;
  }
  function currentTargets() {
    if (!state.current) return Array.from({ length: state.elementCount }, () => 3);
    const deck = state.current.mode === "advanced" ? "Advanced" : state.deck;
    return PROGRAM_TARGETS[deck]?.[state.currentFace]?.[state.current.id] || Array.from({ length: state.elementCount }, () => 3);
  }
  function currentReward() {
    if (!state.current || state.current.mode !== "program") return null;
    const kind = PROGRAM_REWARDS[state.deck]?.[state.current.id];
    return kind ? { kind, label: REWARDS[kind] } : null;
  }
  function ensureElements() { state.elements = Array.from({ length: state.elementCount }, (_, i) => state.elements[i] ? { ...elementTemplate(i), ...state.elements[i], id: i } : elementTemplate(i)); }
  function syncPrintedTargets() { currentTargets().forEach((target, i) => { if (state.elements[i]) state.elements[i].target = target; }); }
  function save() { state.notes = $("notes")?.value ?? state.notes; localStorage.setItem(STORAGE, JSON.stringify(state)); }
  function load() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE));
      if (saved && saved.dice && saved.metrics) state = { ...freshState(), ...saved };
    } catch (_) {}
    if (state.current) {
      state.elementCount = currentElementCount();
      state.limitationRevealed = true;
    }
    ensureElements();
    if (state.current) { syncPrintedTargets(); state.targetsVersion = 1; }
  }
  function log(message, kind = "") {
    state.log.unshift({ at: new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }), message, kind });
    state.log = state.log.slice(0, 80);
  }
  function toast(message) {
    const el = $("toast"); el.textContent = message; el.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove("show"), 2200);
  }
  function sprite(el, file, index, count, landscape = false) {
    el.classList.remove("placeholder-card"); el.innerHTML = "";
    el.style.backgroundImage = `url('${ASSET}${file}?v=${ASSET_VERSION}')`;
    el.style.backgroundSize = landscape ? `100% ${count * 100}%` : `${count * 100}% 100%`;
    const pct = count === 1 ? 0 : (index / (count - 1)) * 100;
    el.style.backgroundPosition = landscape ? `0 ${pct}%` : `${pct}% 0`;
  }
  function clearSprite(el, text) { el.removeAttribute("style"); el.classList.add("placeholder-card"); el.innerHTML = `<span>${text}</span>`; }
  function dieById(id) { return state.dice.find(d => d.id === id); }
  function value(face) { return face === "crit" ? 2 : face === "hit" ? 1 : 0; }
  function zoneDice(zone) { return state.dice.filter(d => d.zone === zone); }
  function selectedAvailable() { return [...selectedDice].map(dieById).filter(d => d && d.zone === "available"); }

  function startGame() {
    const deck = $("deckSelect").value;
    const tech = Number($("techSelect").value);
    state = freshState(); state.started = true; state.deck = deck; state.tech = tech;
    state.queue = shuffle(state.programs.map(p => p.id)); ensureElements();
    log(`${deck} playtest started with ${TECHS[tech].name}.`);
    drawProgram();
  }
  function drawProgram() {
    if (!state.started || state.finished) return;
    if (state.current && !state.currentCompleted) { toast("Complete the active Program first."); return; }
    if (state.mode === "program" && state.queue.length === 0) {
      const active = state.programs.filter(p => p.status !== "aside" && p.status !== "removed").map(p => p.id);
      if (state.cycle < 3 && active.length) { state.cycle += 1; state.queue = shuffle(active); log(`Cycle ${state.cycle} began with ${active.length} Programs.`); }
      else { beginAdvanced(); return; }
    }
    if (state.mode === "advanced" && state.advancedQueue.length === 0) { finishGame(true); return; }
    const id = state.mode === "advanced" ? state.advancedQueue.shift() : state.queue.shift();
    const program = state.mode === "advanced" ? null : state.programs[id];
    state.current = { id, mode: state.mode };
    state.currentFace = state.mode === "advanced" ? (state.nextAdvancedOverheated ? "back" : "front") : (program.status === "overheated" ? "back" : "front");
    state.currentCompleted = false; state.lastResultFailed = false; state.limitationRevealed = true; state.rerollsUsed = 0; state.recoveryCredits = 0;
    state.architectUsed = false; state.architectMode = false; state.debuggerUsed = false; state.optimizerUsed = false; state.rewardApplied = false;
    if (!state.limitationQueue.length) state.limitationQueue = shuffle([0,1,2,3,4,5].filter(x => !state.banishedLimitations.includes(x)));
    state.limitation = state.limitationQueue.pop();
    state.dice.filter(d => d.zone === "withheld" || d.zone === "allocated").forEach(d => { d.zone = "available"; d.element = null; d.face = null; });
    state.elementCount = currentElementCount();
    state.elements = currentTargets().map((target, i) => ({ ...elementTemplate(i), target }));
    selectedDice.clear(); log(`${state.mode === "advanced" ? "Advanced" : state.deck} Program ${id + 1} and Limitation ${state.limitation + 1} revealed (${state.elementCount} elements).`); render();
  }
  function beginAdvanced() {
    state.mode = "advanced"; state.advancedQueue = shuffle([0,1,2,3,4,5,6,7]).slice(0,3); state.nextAdvancedOverheated = false; state.current = null;
    log("Advanced Programming began."); toast("Advanced Programming"); drawProgram();
  }
  function markRequiredMiss() {
    if (!state.current || state.currentCompleted) return;
    state.hp = Math.max(0, state.hp - 1); state.metrics.requiredMisses += 1;
    log("Required color could not be supplied; lost 1 HP.", "bad");
    completeProgram(true);
  }
  function beginResolve(i) {
    const el = state.elements[i]; const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i);
    if (!el.rolled || el.resolved) return;
    el.failed = el.successes < el.target;
    if (el.usedReroll || el.failed) {
      dice.forEach(d => { d.zone = "exhausted"; d.element = null; }); state.metrics.diceExhausted += dice.length;
      finalizeElement(el); return;
    }
    const excessDice = Math.max(0, dice.length - (el.target + el.thresholdBonus));
    const overkill = el.successes >= el.target + 2 ? 1 : 0;
    el.pendingExhaust = Math.min(dice.length, excessDice + overkill);
    if (el.pendingExhaust > 0) { toast(`Choose ${el.pendingExhaust} die${el.pendingExhaust === 1 ? "" : "s"} to exhaust.`); render(); return; }
    finalizeElement(el);
  }
  function finalizeElement(el) {
    state.dice.filter(d => d.zone === "allocated" && d.element === el.id).forEach(d => { d.zone = "available"; d.element = null; });
    const optimal = !el.failed && (el.successes === el.target || (TECHS[state.tech].name === "Optimizer" && el.optimizerUsed && el.successes === el.target + 1));
    if (optimal) state.recoveryCredits += 2;
    el.resolved = true; el.pendingExhaust = 0;
    log(`Element ${el.id + 1}: ${el.successes}/${el.target}${el.failed ? " failed" : " succeeded"}.`);
    render();
  }
  function rollElement(i, reroll = false) {
    const el = state.elements[i]; const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i);
    if (state.architectMode) { toast("Finish or cancel Reconfigure first."); return; }
    if (!dice.length || el.resolved) { toast("Allocate at least one die first."); return; }
    if (reroll) {
      const limit = Math.max(0, state.str - 1);
      if (!el.rolled || state.rerollsUsed >= limit) { toast("No extra STR roll is available."); return; }
      state.rerollsUsed += 1; state.metrics.rerolls += 1; el.usedReroll = true;
    }
    let rolling = dice;
    if (reroll && TECHS[state.tech].name === "Compiler") {
      const chosen = dice.filter(d => selectedDice.has(d.id));
      if (chosen.length) rolling = chosen;
    }
    rolling.forEach(d => { d.face = FACES[d.color][Math.floor(Math.random() * 6)]; selectedDice.delete(d.id); });
    el.successes = dice.reduce((sum, d) => sum + value(d.face), 0); el.rolled = true;
    log(`${reroll ? "Rerolled" : "Rolled"} Element ${i + 1}: ${el.successes} successes.`); render();
  }
  function completeProgram(forcedFailure = false) {
    if (!state.current || state.currentCompleted) return;
    if (!forcedFailure && state.elements.some(e => !e.resolved)) { toast("Resolve every visible element first."); return; }
    const failed = forcedFailure ? 1 : state.elements.filter(e => e.failed).length;
    state.metrics.programs += 1; state.metrics.failedElements += failed;
    if (!forcedFailure && failed >= 2) { state.hp = Math.max(0, state.hp - 1); state.metrics.catastrophes += 1; log("Catastrophic Failure: lost 1 HP.", "bad"); }
    state.dice.filter(d => d.zone === "allocated" || d.zone === "withheld").forEach(d => { d.zone = "available"; d.element = null; d.face = null; });
    state.recoveryCredits += state.rec;
    if (state.current.mode === "program") {
      const p = state.programs[state.current.id];
      if (failed > 0) p.status = p.status === "stable" ? "overheated" : "aside";
    } else {
      state.advancedDone += 1; state.nextAdvancedOverheated = failed >= 2;
    }
    state.currentCompleted = true; state.lastResultFailed = failed > 0;
    log(`Program completed with ${failed} failed element${failed === 1 ? "" : "s"}.`);
    if (state.hp <= 0) finishGame(false); else render();
  }
  function finishGame(won) { state.finished = true; state.currentCompleted = true; log(won ? "AoS completed — Technician survived." : "AoS ended — Technician was knocked out.", won ? "good" : "bad"); render(); toast(won ? "Playtest won" : "Playtest lost"); }

  function applyReward(kind = currentReward()?.kind) {
    if (!state.currentCompleted || state.lastResultFailed || state.current?.mode !== "program") return;
    if (!kind || kind !== currentReward()?.kind) return;
    if (kind === "hp") state.hp = Math.min(6, state.hp + 1);
    if (kind === "recover") state.recoveryCredits += 3;
    if (kind === "rec") { state.rec = Math.min(6, state.rec + 1); markCurrentRemoved(); }
    if (kind === "str") { state.str = Math.min(6, state.str + 1); markCurrentRemoved(); }
    if (kind === "unheat") { const p = state.programs.find(x => x.status === "overheated"); if (p) p.status = "stable"; }
    if (kind === "banish") { if (!state.banishedLimitations.includes(state.limitation)) state.banishedLimitations.push(state.limitation); state.limitationQueue = state.limitationQueue.filter(x => x !== state.limitation); }
    state.rewardApplied = true; log(`Program Reward applied: ${REWARDS[kind]}.`); render();
  }
  function markCurrentRemoved() { if (state.current?.mode === "program") state.programs[state.current.id].status = "removed"; }
  function adjustStat(stat, delta) { state[stat] = Math.max(stat === "hp" ? 0 : 1, Math.min(6, state[stat] + delta)); render(); }
  function assignSelected(i) {
    if (state.architectMode) { moveArchitectDice(i); return; }
    const dice = selectedAvailable(); if (!dice.length) { toast("Select available dice first."); return; }
    dice.forEach(d => { d.zone = "allocated"; d.element = i; d.face = null; selectedDice.delete(d.id); }); render();
  }
  function returnElementDice(i) {
    const el = state.elements[i];
    if (!el || el.rolled || state.currentCompleted) return;
    state.dice.filter(d => d.zone === "allocated" && d.element === i).forEach(d => {
      d.zone = "available"; d.element = null; d.face = null; selectedDice.delete(d.id);
    });
    render();
  }
  function toggleArchitectMode() {
    if (TECHS[state.tech].name !== "Architect" || !state.current || state.currentCompleted || state.architectUsed) return;
    state.architectMode = !state.architectMode; selectedDice.clear();
    toast(state.architectMode ? "Select up to 2 allocated dice, then choose their destination." : "Reconfigure cancelled.");
    render();
  }
  function moveArchitectDice(destination) {
    if (!state.architectMode || state.architectUsed) return;
    const dest = state.elements[destination];
    if (!dest || dest.resolved || dest.rolled) { toast("Choose an unresolved element that has not been rolled."); return; }
    const dice = [...selectedDice].map(dieById).filter(d => d?.zone === "allocated" && d.element !== destination && !state.elements[d.element]?.resolved && !state.elements[d.element]?.rolled);
    if (!dice.length || dice.length > 2) { toast("Select 1 or 2 allocated dice from another unresolved element."); return; }
    dice.forEach(d => { d.element = destination; selectedDice.delete(d.id); });
    state.architectUsed = true; state.architectMode = false; log(`Architect moved ${dice.length} allocated die${dice.length === 1 ? "" : "s"} to Element ${destination + 1}.`); render();
  }
  function debugElement(i) {
    const el = state.elements[i];
    if (TECHS[state.tech].name !== "Debugger" || state.debuggerUsed || !el?.rolled || el.resolved || el.successes !== el.target - 1) return;
    const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i && selectedDice.has(d.id));
    if (dice.length !== 1) { toast("Select exactly 1 die from this element to Debug."); return; }
    const die = dice[0]; const before = value(die.face);
    die.face = FACES[die.color][Math.floor(Math.random() * 6)]; selectedDice.delete(die.id);
    el.successes += value(die.face) - before; state.debuggerUsed = true;
    if (el.successes < el.target) { die.zone = "exhausted"; die.element = null; state.metrics.diceExhausted += 1; log(`Debugger rerolled 1 die; Element ${i + 1} still failed, so that die was exhausted.`); }
    else log(`Debugger rerolled 1 die; Element ${i + 1} reached its Target.`);
    render();
  }
  function moveSelected(zone) {
    const dice = [...selectedDice].map(dieById).filter(Boolean);
    if (!dice.length) { toast("Select dice first."); return; }
    dice.forEach(d => { d.zone = zone; d.element = null; d.face = null; }); selectedDice.clear(); render();
  }
  function clickDie(id) {
    const d = dieById(id); if (!d) return;
    if (state.architectMode) {
      const el = d.zone === "allocated" ? state.elements[d.element] : null;
      if (!el || el.resolved || el.rolled) { toast("Reconfigure selects allocated dice from unresolved elements."); return; }
      if (!selectedDice.has(id) && selectedDice.size >= 2) { toast("Architect can move up to 2 dice."); return; }
      selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render(); return;
    }
    if (d.zone === "exhausted" && state.recoveryCredits > 0) { d.zone = "available"; state.recoveryCredits -= 1; log(`${d.color} die recovered.`); render(); return; }
    if (d.zone === "allocated") {
      const el = state.elements[d.element];
      if (el?.pendingExhaust > 0) {
        d.zone = "exhausted"; d.element = null; el.pendingExhaust -= 1; state.metrics.diceExhausted += 1;
        if (el.pendingExhaust === 0) finalizeElement(el); else render(); return;
      }
      if (!el?.rolled) { d.zone = "available"; d.element = null; selectedDice.delete(id); render(); }
      else if ((TECHS[state.tech].name === "Compiler" || (TECHS[state.tech].name === "Debugger" && !state.debuggerUsed && el.successes === el.target - 1)) && !el.resolved) { selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render(); }
      return;
    }
    if (d.zone === "banished") return;
    selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render();
  }

  function dieButton(d) {
    const face = d.face ? FACE_MARK[d.face] : "";
    return `<button class="die ${d.color}${selectedDice.has(d.id) ? " selected" : ""}" data-die="${d.id}" aria-label="${d.color} die${d.face ? `, ${d.face}` : ", not rolled"}"><span class="face">${face}</span><span class="tiny">${d.color[0].toUpperCase()}</span></button>`;
  }
  function renderCard() {
    const card = $("programCard");
    if (!state.current) { clearSprite(card, state.started ? "Draw the next Program." : "Start a playtest to load the deck."); $("programTitle").textContent = state.started ? "Between Programs" : "No program drawn"; $("programFlavor").textContent = ""; }
    else {
      const name = state.current.mode === "advanced" ? "Advanced" : state.deck; const data = DECKS[name];
      const flavor = PROGRAM_FLAVOR[name][state.current.id];
      sprite(card, state.currentFace === "front" ? data.front : data.back, state.current.id, data.count);
      $("programTitle").textContent = `${flavor.name} · ${state.currentFace === "front" ? "Stable" : "Overheated"}`;
      $("programFlavor").textContent = flavor[state.currentFace];
    }
    if (state.current) { sprite($("limitationCard"), "AoS_Limitations_TTS.png", state.limitation, 6); $("limitationFlavor").textContent = LIMITATION_FLAVOR[state.limitation]?.text || ""; }
    else { clearSprite($("limitationCard"), "Revealed with the active Program."); $("limitationFlavor").textContent = ""; }
  }
  function renderTech() {
    const tech = TECHS[state.tech]; $("techName").textContent = tech.name; $("techAbility").textContent = tech.ability;
    sprite($("techCard"), tech.side === "front" ? "AoS_Technicians_TTS.png" : "AoS_Technicians_TTS_back.png", tech.index, 3);
    const hints = {
      Architect: "Use Reconfigure, select up to 2 allocated dice from unresolved elements, then tap Move selected here on their destination.",
      Debugger: "After missing a Target by exactly 1, tap one die in that element and choose Debug selected.",
      Optimizer: "After rolling Target +1, choose Count as optimal on that element. Usable once per Program.",
      Engineer: "Choose Safe T+2 before rolling on up to 2 elements per Program.",
      Operator: "Apply Workaround manually by selecting the substitute non-Red die and using Withhold.",
      Compiler: "After a roll, tap the dice you want to reroll, then choose Extra roll. With none selected, all dice reroll."
    };
    $("techHint").textContent = hints[tech.name];
    const architect = tech.name === "Architect";
    $("techAction").classList.toggle("hidden", !state.started);
    $("techActionBtn").classList.toggle("hidden", !architect);
    if (architect) {
      $("techActionBtn").textContent = state.architectMode ? "Cancel Reconfigure" : (state.architectUsed ? "Reconfigure used" : "Use Reconfigure");
      $("techActionBtn").disabled = !state.current || state.currentCompleted || (state.architectUsed && !state.architectMode);
    }
  }
  function zoomCard(source) {
    if (!source.style.backgroundImage) return;
    const zoom = $("cardZoom");
    zoom.style.backgroundImage = source.style.backgroundImage;
    zoom.style.backgroundSize = source.style.backgroundSize;
    zoom.style.backgroundPosition = source.style.backgroundPosition;
    zoom.style.aspectRatio = source === $("techCard") ? "7/5" : "5/7";
    $("cardDialog").showModal();
  }
  function renderElements() {
    const wrap = $("elements"); wrap.innerHTML = state.elements.map((el, i) => {
      const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i);
      const status = el.resolved ? (el.failed ? "failed" : "resolved") : "";
      const score = el.rolled ? `${el.successes} success${el.successes === 1 ? "" : "es"}${el.pendingExhaust ? ` · choose ${el.pendingExhaust} to exhaust` : ""}` : "Not rolled";
      const optimizerEligible = el.rolled && !el.resolved && el.successes === el.target + 1 && !state.optimizerUsed;
      const optimizer = TECHS[state.tech].name === "Optimizer" ? `<button data-optimize="${i}" ${optimizerEligible ? "" : "disabled"}>${el.optimizerUsed ? "✓ Optimal" : "Count as optimal"}</button>` : "";
      const debuggerButton = TECHS[state.tech].name === "Debugger" ? `<button data-debug="${i}" ${el.rolled && !el.resolved && el.successes === el.target - 1 && !state.debuggerUsed ? "" : "disabled"}>Debug selected</button>` : "";
      const engineer = TECHS[state.tech].name === "Engineer" ? `<button data-safe="${i}" ${el.rolled ? "disabled" : ""}>${el.thresholdBonus === 2 ? "✓ " : ""}Safe T+2</button>` : "";
      const assignLabel = state.architectMode ? "Move selected here" : "Assign selected";
      return `<article class="element ${status}"><div class="element-head"><h3>Element ${i + 1}</h3><div class="target" aria-label="Printed Target"><span class="target-label">Printed Target</span><strong>${el.target}</strong></div></div><div class="element-drop" data-assign="${i}">${dice.map(dieButton).join("") || "<span class='hint'>No dice assigned</span>"}</div><div class="element-actions"><button data-assign="${i}" ${el.resolved || el.rolled ? "disabled" : ""}>${assignLabel}</button><button data-unassign="${i}" ${!dice.length || el.rolled ? "disabled" : ""}>Return dice</button><button data-roll="${i}" ${el.resolved ? "disabled" : ""}>Roll</button><button data-reroll="${i}" ${!el.rolled || el.resolved ? "disabled" : ""}>Extra roll</button><button data-resolve="${i}" ${!el.rolled || el.resolved ? "disabled" : ""}>Resolve</button>${engineer}${optimizer}${debuggerButton}</div><div class="element-score">${score}</div></article>`;
    }).join("");
  }
  function renderPools() {
    for (const zone of ["available", "exhausted", "withheld", "banished"]) {
      const dice = zoneDice(zone); $(`${zone}Dice`).innerHTML = dice.map(dieButton).join(""); $(`${zone}Count`).textContent = `(${dice.length})`;
    }
  }
  function renderMetrics() {
    const m = state.metrics;
    const items = [["Programs",m.programs],["Failed elements",m.failedElements],["Catastrophes",m.catastrophes],["Extra rolls",m.rerolls],["Dice exhausted",m.diceExhausted],["Required misses",m.requiredMisses],["Fiddly / unclear",`${m.fiddly} / ${m.unclear}`],["Good decisions",m.good]];
    $("metrics").innerHTML = items.map(([k,v]) => `<div class="metric"><span>${k}</span><strong>${v}</strong></div>`).join("");
    $("eventLog").innerHTML = state.log.map(e => `<div class="log-entry"><b>${e.at}</b> · ${e.message}</div>`).join("") || "<div class='log-entry'>The playtest log will appear here.</div>";
  }
  function render() {
    ensureElements();
    $("deckSelect").value = state.deck; $("techSelect").value = String(state.tech); $("elementCount").textContent = String(state.elementCount);
    $("hp").textContent = state.hp; $("str").textContent = state.str; $("rec").textContent = state.rec; $("cycle").textContent = state.mode === "advanced" ? `ADV ${state.advancedDone + 1}/3` : (state.started ? `${state.cycle}/3` : "—");
    $("recoveryCredits").textContent = state.recoveryCredits; $("rerolls").textContent = `${state.rerollsUsed} / ${Math.max(0,state.str-1)}`;
    $("runState").textContent = !state.started ? "Choose a deck and Technician." : state.finished ? (state.hp > 0 ? "Playtest complete: survived Advanced Programming." : "Playtest complete: Health reached 0.") : `${state.deck} · ${TECHS[state.tech].name} · ${state.programs.filter(p=>p.status==="aside").length} set aside`;
    $("drawBtn").disabled = !state.started || (!!state.current && !state.currentCompleted) || state.finished; $("drawBtn").textContent = state.mode === "advanced" ? "Next Advanced" : "Draw program";
    $("flipBtn").disabled = !state.current || state.currentCompleted;
    $("programControls").classList.toggle("hidden", !state.current || state.currentCompleted); $("rewardBar").classList.toggle("hidden", !state.currentCompleted || state.finished || state.lastResultFailed || state.rewardApplied || state.current?.mode !== "program");
    const reward = currentReward(); $("rewardName").textContent = reward?.label || "—"; $("applyRewardBtn").disabled = !reward;
    renderCard(); renderTech(); renderElements(); renderPools(); renderMetrics();
    if (document.activeElement !== $("notes")) $("notes").value = state.notes || "";
    save();
  }

  function summary() {
    const m = state.metrics;
    return `AoS playtest — ${state.deck} / ${TECHS[state.tech].name}\nResult: ${state.finished ? (state.hp > 0 ? "Win" : "Loss") : "In progress"}\nHP ${state.hp} · STR ${state.str} · REC ${state.rec}\nPrograms ${m.programs}; failed elements ${m.failedElements}; catastrophes ${m.catastrophes}; extra rolls ${m.rerolls}; dice exhausted ${m.diceExhausted}; required-color misses ${m.requiredMisses}\nSignals: fiddly ${m.fiddly}; unclear ${m.unclear}; good decisions ${m.good}\nNotes: ${state.notes || "—"}`;
  }
  async function copySummary() { state.notes = $("notes").value; try { await navigator.clipboard.writeText(summary()); toast("Summary copied"); } catch (_) { toast("Copy unavailable; select the notes manually."); } save(); }
  function reset() { if (!confirm("Start a new playtest? The current in-progress state will be replaced.")) return; state = freshState(); selectedDice.clear(); render(); }
  function registerWebMCP() {
    const context = document.modelContext; if (!context?.registerTool) return;
    const tools = [
      { name:"read_playtest_state", title:"Read playtest state", description:"Read the current AoS playtest setup, progress, stats, and metrics.", inputSchema:{type:"object",properties:{},additionalProperties:false}, annotations:{readOnlyHint:true,untrustedContentHint:false}, execute:()=>({deck:state.deck,technician:TECHS[state.tech].name,hp:state.hp,str:state.str,rec:state.rec,cycle:state.cycle,mode:state.mode,metrics:state.metrics,notes:state.notes}) },
      { name:"record_playtest_signal", title:"Record playtest signal", description:"Record a fiddly step, unclear rule, or good decision in the visible playtest log.", inputSchema:{type:"object",properties:{signal:{type:"string",enum:["fiddly","unclear","good"]},note:{type:"string"}},required:["signal"],additionalProperties:false}, annotations:{readOnlyHint:false,untrustedContentHint:false}, execute:({signal,note})=>{ if(!["fiddly","unclear","good"].includes(signal)) throw new Error("Invalid signal"); state.metrics[signal]+=1; log(note||`Signal recorded: ${signal}.`); render(); return {recorded:true,signal,count:state.metrics[signal]}; } }
    ];
    tools.forEach(tool => { try { void Promise.resolve(context.registerTool(tool)).catch(()=>{}); } catch (_) {} });
  }

  function bind() {
    TECHS.forEach((t,i) => $("techSelect").insertAdjacentHTML("beforeend", `<option value="${i}">${t.name}</option>`));
    $("startBtn").addEventListener("click", startGame); $("drawBtn").addEventListener("click", drawProgram);
    $("flipBtn").addEventListener("click", () => { state.currentFace = state.currentFace === "front" ? "back" : "front"; syncPrintedTargets(); render(); });
    $("finishProgramBtn").addEventListener("click", () => completeProgram(false)); $("requiredMissBtn").addEventListener("click", markRequiredMiss);
    $("techActionBtn").addEventListener("click", toggleArchitectMode); $("applyRewardBtn").addEventListener("click", () => applyReward());
    $("resetBtn").addEventListener("click", reset); $("copySummaryBtn").addEventListener("click", copySummary);
    $("rulesBtn").addEventListener("click", () => $("rulesDialog").showModal()); $("closeRulesBtn").addEventListener("click", () => $("rulesDialog").close());
    $("closeCardBtn").addEventListener("click", () => $("cardDialog").close());
    [$("programCard"), $("limitationCard"), $("techCard")].forEach(el => el.addEventListener("click", () => zoomCard(el)));
    $("deckSelect").addEventListener("change", e => { if(!state.started){state.deck=e.target.value;render();}else e.target.value=state.deck; }); $("techSelect").addEventListener("change", e => { if(!state.started){state.tech=Number(e.target.value);renderTech();save();}else e.target.value=String(state.tech); });
    $("exhaustSelectedBtn").addEventListener("click", () => moveSelected("exhausted")); $("withholdSelectedBtn").addEventListener("click", () => moveSelected("withheld")); $("banishSelectedBtn").addEventListener("click", () => moveSelected("banished"));
    $("notes").addEventListener("input", e => { state.notes=e.target.value;save(); });
    document.addEventListener("click", e => {
      const die=e.target.closest("[data-die]"); if(die){clickDie(die.dataset.die);return;}
      const assign=e.target.closest("[data-assign]"); if(assign){assignSelected(Number(assign.dataset.assign));return;}
      const unassign=e.target.closest("[data-unassign]"); if(unassign){returnElementDice(Number(unassign.dataset.unassign));return;}
      const roll=e.target.closest("[data-roll]"); if(roll){rollElement(Number(roll.dataset.roll));return;}
      const reroll=e.target.closest("[data-reroll]"); if(reroll){rollElement(Number(reroll.dataset.reroll),true);return;}
      const resolve=e.target.closest("[data-resolve]"); if(resolve){beginResolve(Number(resolve.dataset.resolve));return;}
      const safe=e.target.closest("[data-safe]"); if(safe){const el=state.elements[Number(safe.dataset.safe)];if(el.thresholdBonus===2){el.thresholdBonus=1;}else if(state.elements.filter(x=>x.thresholdBonus===2).length<2){el.thresholdBonus=2;}else{toast("Engineer can use Redundancy on up to 2 elements.");}render();return;}
      const optimize=e.target.closest("[data-optimize]"); if(optimize){const el=state.elements[Number(optimize.dataset.optimize)];if(!state.optimizerUsed&&el.rolled&&!el.resolved&&el.successes===el.target+1){el.optimizerUsed=true;state.optimizerUsed=true;log(`Optimizer counted Element ${el.id+1} at Target +1 as optimal.`);render();}return;}
      const debug=e.target.closest("[data-debug]"); if(debug){debugElement(Number(debug.dataset.debug));return;}
      const stat=e.target.closest("[data-stat]"); if(stat){adjustStat(stat.dataset.stat,Number(stat.dataset.delta));return;}
      const signal=e.target.closest("[data-signal]"); if(signal){state.metrics[signal.dataset.signal]+=1;log(`Signal recorded: ${signal.dataset.signal}.`);render();}
    });
  }

  load(); bind(); render(); registerWebMCP();
})();
