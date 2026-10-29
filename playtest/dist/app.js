(() => {
  "use strict";

  const ASSET = "assets/";
  const ASSET_VERSION = "cards-fixed-1";
  const MAX_ELEMENTS = 5; // the allocation board always shows five Element slots
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
  // Which element carries the printed overheat ring, per deck (generator/aos.py).
  const PROGRAM_MARKS = {
    Routine: [0, 1, 0, 1, 2, 1, 2, 2],
    Specialized: [1, 0, 1, 3, 0, 2, 1, 2],
    Unstable: [0, 3, 2, 1, 0, 3, 1, 1],
    Advanced: [2, 1, 3, 0, 2, 2, 1, 1],
  };
  // Difficulty is how many Programs come from each deck, not which deck you
  // pick. All three carry the same reward multiset, so mixing them changes
  // only the Targets and element counts.
  // Specialized held at 3; each step up trades one Routine Program for one
  // Unstable. Measured 45.8 / 34.0 / 24.5 / 17.5.
  const AOS_LEVELS = {
    Easy:     [5, 3, 0],
    Standard: [4, 3, 1],
    Hard:     [3, 3, 2],
    Nobulous: [2, 3, 3],
  };
  const AOS_DECK_NAMES = ["Routine", "Specialized", "Unstable"];
  // A Program knows which deck it came from, so every per-deck lookup goes
  // through here rather than through one deck name for the whole game.
  function programSource(c) {
    if (!c) return null;
    if (c.mode === "advanced") return { deck: "Advanced", pid: c.id };
    const p = (state.programs || []).find(x => x.id === c.id);
    return { deck: (p && p.src) || state.deck, pid: (p && p.pid != null) ? p.pid : c.id };
  }
  function markedElement() {
    const c = state.current;
    if (!c) return -1;
    const { deck, pid } = programSource(c);
    return PROGRAM_MARKS[deck]?.[pid] ?? -1;
  }
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
  // --- NRJ module cards ----------------------------------------------
  const AOS_INTERFERENCE = [
    ["I Don't Have Time for This","Begin all Programs Overheated. When an already-Overheated Program fails, cycle it to the bottom of its deck instead of setting it aside."],
    ["Legacy Hardware","At setup, choose and banish 1 non-Red die."],
    ["Nobulous Was Here","Randomly flip 2 Programs to their Overheated sides before play."],
    ["Undocumented Dependencies","The first element of every Program must receive at least 1 die and no more than its Target."],
    ["Works on My Machine","A Crit rolled on the second element counts as 3 successes. Crits on every other element count as basic successes."],
    ["Memory Leak","Whenever you over-allocate an element, exhaust 1 additional available die after resolving the Program."],
  ];
  // Corrupted Limitations sit in the Limitation deck. Each withholds 2 dice of
  // a randomly chosen color on top of the printed corruption.
  const AOS_CORRUPT = [
    ["Uneven Architecture","The first element must receive more dice than the last."],
    ["Memory Collision","No two adjacent elements may receive the same number of dice."],
    ["Circular Reference","The first and final elements must receive different numbers of dice."],
    ["Hard-Coded Constant","Randomly select one element. It must receive exactly its Target number of dice."],
    ["Deprecated Function","Randomly select one color. Crits rolled by that color count as basic successes for this Program."],
    ["Stack Overflow","If any element receives 5+ dice, exhaust one die committed to that element before rolling."],
  ];
  const AOS_BACKDOOR = [
    ["Diagnostic Port","Claim after completing a Program with no element over-allocated.","Later, reroll one entire Strategy roll."],
    ["Privilege Escalation","Claim after completing an Overheated Program without failing an element.","Later, ignore one Limitation."],
    ["Resource Fork","Claim after completing a Program while committing no more than Target + 1 dice in total beyond its summed Targets.","Later, recover 2 exhausted dice."],
    ["Packet Sniffer","Claim after completing a Program with Crits on at least two different elements.","Later, look at the next Limitation before selecting a Program."],
    ["Garbage Collection","Claim after completing a Program while at least 4 dice are exhausted.","Later, recover one die of each of two different colors."],
    ["Root Access","Claim after completing a Program with Optimal Implementation on at least two elements.","During Advanced Programming, treat one failed element as successful."],
  ];
  const aosTier = () => window.NOBULOUS_TIER ? window.NOBULOUS_TIER.forGame("aos") : "0";
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
    { name: "Engineer", side: "back", index: 1, ability: "Redundancy — For up to 2 elements per Program, the allocation cap is Target +2 instead of Target +1." },
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
  // AoS stores faces as "hit" / "crit" / "blank" rather than glyphs.
  const rollTally = dice => dice.reduce((t, x) => {
    if (x.face === "crit") { t.crits++; t.successes += 2; }
    else if (x.face === "hit") { t.hits++; t.successes += 1; }
    else t.misses++;
    return t;
  }, { crits: 0, hits: 0, misses: 0, successes: 0 });
  const tallyText = t => `${t.successes} success${t.successes === 1 ? "" : "es"} · `
    + `${t.crits} Crit${t.crits === 1 ? "" : "s"}, ${t.hits} hit${t.hits === 1 ? "" : "s"}, `
    + `${t.misses} miss${t.misses === 1 ? "" : "es"}`;
  const faceLabel = face => face === "crit" ? "Crit · 2 successes"
    : face === "hit" ? "Hit · 1 success" : "Miss · 0 successes";
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
  // Tier I draws one Nobulous Interference card; two of the six change setup.
  function aosDrawInterference(){
    const t=aosTier();
    return (t==="1"||t==="2"||t==="3") ? Math.floor(Math.random()*AOS_INTERFERENCE.length) : null;
  }
  function aosFreshPrograms(level){
    const comp = AOS_LEVELS[level] || AOS_LEVELS.Standard;
    const picks = [];
    AOS_DECK_NAMES.forEach((name, k) => {
      shuffle([...Array(8).keys()]).slice(0, comp[k]).forEach(pid => picks.push({ src: name, pid }));
    });
    return shuffle(picks).map((p, id) => ({ id, src: p.src, pid: p.pid, status: "stable" }));
  }
  function aosFreshBackdoors(){
    return aosTier()==="3" ? AOS_BACKDOOR.map(()=>({claimed:false,spent:false})) : [];
  }
  // Tier II shuffles the 6 Corrupted Limitations into the Limitation deck.
  function aosLimitationQueue(){
    const base=[0,1,2,3,4,5];
    const t=aosTier();
    return shuffle(t==="2"||t==="3" ? base.concat([6,7,8,9,10,11]) : base);
  }
  function aosApplyInterferenceSetup(){
    // "Begin all Programs Overheated" / "Randomly flip 2 Programs".
    if(state.interference===0)state.programs.forEach(p=>p.status="overheated");
    if(state.interference===2){
      const pick=shuffle(state.programs.map(p=>p.id)).slice(0,2);
      state.programs.forEach(p=>{if(pick.includes(p.id))p.status="overheated";});
    }
  }
  function aosClaimBackdoor(i,spend){
    state.backdoors??=[];
    const st=state.backdoors[i]||(state.backdoors[i]={claimed:false,spent:false});
    const claimedCount=state.backdoors.filter(b=>b&&b.claimed).length;
    if(spend){
      if(!st.claimed||st.spent)return;
      st.spent=true;
    }else{
      if(st.claimed)return;
      // "You may claim at most 2 per game."
      if(claimedCount>=2)return;
      st.claimed=true;
    }
    save();render();
  }
  function renderAOSModules(){
    const host=document.getElementById("aosModules");
    if(!host)return;
    const tier=state.tier||"0",backdoors=state.backdoors||[];
    const on=tier!=="0"&&(state.interference!=null||backdoors.length);
    host.classList.toggle("hidden",!on);
    if(!on)return;
    let html="";
    if(state.interference!=null){
      const card=AOS_INTERFERENCE[state.interference];
      const auto=state.interference===0||state.interference===2;
      html+=`<div class="bat-protocol"><p class="kicker">Nobulous Interference &middot; Tier I</p>`
        +`<h3>${card[0]}</h3><p>${card[1]}</p>`
        +`<p class="hint">${auto?"Applied to this game's Programs at setup.":"Apply this at the table; the lab does not enforce it."}</p></div>`;
    }
    if(backdoors.length){
      const claimed=backdoors.filter(b=>b&&b.claimed).length;
      html+=`<div class="bat-notes"><p class="kicker">Backdoor Routines &middot; Tier III</p>`
        +`<p class="hint">Claimed ${claimed} / 2.</p><div class="bat-note-grid">`
        +AOS_BACKDOOR.map((card,i)=>{
          const st=backdoors[i]||{};
          return `<article class="bat-note ${st.spent?"spent":st.claimed?"claimed":""}">`
            +`<strong>${card[0]}</strong><small><b>Claim:</b> ${card[1]}</small><small><b>Use:</b> ${card[2]}</small>`
            +`${st.spent?`<span class="bat-note-state">Spent</span>`
              :st.claimed?`<button data-aos-backdoor-spend="${i}">Use</button>`
              :`<button data-aos-backdoor-claim="${i}" ${claimed>=2?"disabled":""}>Claim</button>`}</article>`;
        }).join("")+`</div></div>`;
    }
    host.innerHTML=html;
  }
  const freshMetrics = () => ({ programs: 0, failedElements: 0, catastrophes: 0, negated: 0, rerolls: 0, diceExhausted: 0, requiredMisses: 0, fiddly: 0, unclear: 0, good: 0 });
  const freshState = (level = "Standard") => ({
    started: false, deck: level, level, tech: 0, hp: 2, str: 2, rec: 3, cycle: 1, mode: "program",
    programs: aosFreshPrograms(level), queue: [], discard: [], current: null,
    tier: aosTier(), interference: aosDrawInterference(), backdoors: aosFreshBackdoors(), corruptColor: null, corruptElement: null,
    currentFace: "front", currentCompleted: false, lastResultFailed: false, limitation: null, limitationRevealed: false, limitationResolved: false, limitationQueue: aosLimitationQueue(), banishedLimitations: [],
    advancedQueue: [], nextAdvancedOverheated: false, advancedDone: 0, dice: freshDice(), elements: [], elementCount: 3,
    rerollsUsed: 0, recoveryCredits: 0, recoverySource: "", architectUsed: false, architectMode: false, debuggerUsed: false, optimizerUsed: false, rewardApplied: false,
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
    const { deck, pid } = programSource(state.current);
    return PROGRAM_TARGETS[deck]?.[state.currentFace]?.[pid] || Array.from({ length: state.elementCount }, () => 3);
  }
  function currentReward() {
    if (!state.current || state.current.mode !== "program") return null;
    const { deck, pid } = programSource(state.current);
    const kind = PROGRAM_REWARDS[deck]?.[pid];
    return kind ? { kind, label: REWARDS[kind] } : null;
  }
  function ensureElements() { state.elements = Array.from({ length: state.elementCount }, (_, i) => state.elements[i] ? { ...elementTemplate(i), ...state.elements[i], id: i } : elementTemplate(i)); }
  function syncPrintedTargets() { currentTargets().forEach((target, i) => { if (state.elements[i]) state.elements[i].target = target; }); }
  function save() { state.notes = $("notes")?.value ?? state.notes; localStorage.setItem(STORAGE, JSON.stringify(state)); }
  function load() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE));
      if (saved && saved.dice && saved.metrics) {
        state = { ...freshState(saved.level || "Standard"), ...saved };
        // The spread above takes the saved metrics whole, so a save written
        // before a counter existed would leave it undefined and render as
        // "undefined" once incremented. Fill in any missing counter.
        state.metrics = { ...freshMetrics(), ...saved.metrics };
        state.level = state.level || (AOS_LEVELS[state.deck] ? state.deck : "Standard");
        if (!(state.programs || []).every(p => p.src)) {
          // Pre-mix save: give every Program the deck it was actually from.
          const was = AOS_DECK_NAMES.includes(saved.deck) ? saved.deck : null;
          state.programs = was
            ? (state.programs || []).map((p, id) => ({ ...p, id, src: was, pid: p.pid != null ? p.pid : id }))
            : aosFreshPrograms(state.level);
        }
      }
    } catch (_) {}
    if (state.current) {
      state.elementCount = currentElementCount();
      state.limitationRevealed = true;
      if (state.limitationResolved === undefined) state.limitationResolved = state.dice.some(d => d.zone === "allocated") || state.currentCompleted;
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
  // Misses that must be exhausted on failed elements to negate the Health
  // loss from a Catastrophic Failure. Mirrors MISSES_TO_NEGATE in
  // simulation/aos.py; 0 restores the rule as printed before 2026-10-28.
  const MISSES_TO_NEGATE = 2;
  function zoneDice(zone) { return state.dice.filter(d => d.zone === zone); }
  // Recovery (REC at the end of each Program, 2 for Optimal Implementation, 3 from the Program Reward)
  // always takes exhausted dice only. It is a gated step: select exactly the dice owed, then recover them.
  function recoveryOwed() { return Math.min(state.recoveryCredits, zoneDice("exhausted").length); }
  function recoveryPending() { return recoveryOwed() > 0; }
  function grantRecovery(n, source) {
    if (n <= 0) return;
    state.recoveryCredits += n; state.recoverySource = state.recoverySource ? `${state.recoverySource} + ${source}` : source;
    selectedDice.clear();
    if (!zoneDice("exhausted").length) { log(`${source}: no exhausted dice to recover.`); state.recoveryCredits = 0; state.recoverySource = ""; }
  }
  function recoverSelected() {
    const owed = recoveryOwed(); if (!owed) return;
    const picked = [...selectedDice].map(dieById).filter(d => d && d.zone === "exhausted");
    if (picked.length !== owed) { toast(`Select ${owed} exhausted ${owed === 1 ? "die" : "dice"} (${picked.length} selected).`); return; }
    picked.forEach(d => { d.zone = "available"; d.face = null; });
    log(`Recovered ${picked.map(d => d.color).join(", ")} (${state.recoverySource || "Recovery"}).`, "good");
    state.recoveryCredits = 0; state.recoverySource = ""; selectedDice.clear(); render();
  }
  // Once any Element has rolled, allocation is locked (Architect's Reconfigure is the only exception).
  function rollingStarted() { return state.elements.some(e => e.rolled); }
  function extraRollsLeft() { return Math.max(0, Math.max(0, state.str - 1) - state.rerollsUsed); }
  const SHORTAGE_COLORS = ["yellow", "green", "blue", "purple"];
  // Checks the withheld dice against the active Limitation. Returns an error message, or "" when resolved.
  // Limitations 0-5 are native; 6-11 are the Tier II Corrupted Limitations,
  // which withhold 2 dice of a randomly chosen color on top of their text.
  const isCorrupt = lim => lim >= 6;
  function limitationName(lim){
    return isCorrupt(lim) ? AOS_CORRUPT[lim-6][0] : LIMITATION_FLAVOR[lim].name;
  }
  function limitationText(lim){
    return isCorrupt(lim) ? AOS_CORRUPT[lim-6][1] : LIMITATION_FLAVOR[lim].text;
  }
  function corruptColor(){
    if(!state.corruptColor)state.corruptColor=shuffle(["purple","blue","green","yellow"])[0];
    return state.corruptColor;
  }
  function limitationProblem() {
    const lim = state.limitation; if (lim === null || lim === undefined) return "";
    const inPlay = state.dice.filter(d => d.zone === "available" || d.zone === "withheld");
    const held = state.dice.filter(d => d.zone === "withheld");
    const name = limitationName(lim);
    if (isCorrupt(lim)) {
      // Withhold 2 of the randomly chosen color; the printed corruption is
      // an allocation rule the table applies when placing dice.
      const c = corruptColor(), need = Math.min(2, inPlay.filter(d => d.color === c).length);
      const ofColor = held.filter(d => d.color === c).length;
      const operator = TECHS[state.tech].name === "Operator";
      if (held.length !== need) return `${name}: withhold exactly ${need} ${c} ${need === 1 ? "die" : "dice"} (${held.length} withheld).`;
      if (held.some(d => d.color === "red")) return `${name}: Red cannot be withheld in place of a ${c} die.`;
      // Workaround applies here exactly as it does to a native shortage.
      if (ofColor < need - (operator ? 1 : 0))
        return operator ? `${name}: at least ${need - 1} withheld die must be ${c} (Workaround swaps only 1).`
                        : `${name}: every withheld die must be ${c}.`;
      return "";
    }
    if (lim <= 3) {
      const c = SHORTAGE_COLORS[lim], need = Math.min(2, inPlay.filter(d => d.color === c).length);
      const ofColor = held.filter(d => d.color === c).length, operator = TECHS[state.tech].name === "Operator";
      const others = held.filter(d => d.color !== c);
      if (held.length !== need) return `${name}: withhold exactly ${need} ${c} ${need === 1 ? "die" : "dice"} (${held.length} withheld).`;
      if (others.some(d => d.color === "red")) return `${name}: Red cannot be withheld in place of a ${c} die.`;
      if (ofColor < need - (operator ? 1 : 0)) return operator ? `${name}: at least ${need - 1} withheld die must be ${c} (Workaround swaps only 1).` : `${name}: every withheld die must be ${c}.`;
      return "";
    }
    if (lim === 4) {
      const colors = new Set(inPlay.filter(d => d.color !== "red").map(d => d.color));
      const need = Math.min(2, colors.size);
      if (held.length !== need) return `${name}: withhold exactly ${need} non-Red dice (${held.length} withheld).`;
      if (held.some(d => d.color === "red")) return `${name}: Red does not count; withhold non-Red dice.`;
      if (new Set(held.map(d => d.color)).size !== held.length) return `${name}: the withheld dice must be different colors.`;
      return "";
    }
    const need = inPlay.some(d => d.color === "red") ? 1 : 0;
    if (held.length !== need || held.some(d => d.color !== "red")) return need ? `${name}: withhold the Red die, and only the Red die.` : "";
    return "";
  }
  function resolveLimitation() {
    if (!state.current || state.currentCompleted || state.limitationResolved) return;
    const problem = limitationProblem(); if (problem) { toast(problem); return; }
    state.limitationResolved = true; selectedDice.clear();
    log(`Limitation resolved: ${limitationName(state.limitation)}.`); render();
  }
  function selectedAvailable() { return [...selectedDice].map(dieById).filter(d => d && d.zone === "available"); }

  function startOrDraw() { if (state.started) drawProgram(); else startGame(); }
  function startGame() {
    const deck = $("deckSelect").value;
    const tech = Number($("techSelect").value);
    state = freshState(deck); state.started = true; state.tech = tech; aosApplyInterferenceSetup();
    state.queue = shuffle(state.programs.map(p => p.id)); ensureElements();
    log(`${deck} playtest started with ${TECHS[tech].name}.`);
    drawProgram();
  }
  function drawProgram() {
    if (!state.started || state.finished) return;
    if (state.current && !state.currentCompleted) { toast("Complete the active Program first."); return; }
    if (recoveryPending()) { toast("Recover your dice before revealing the next Program."); return; }
    if (state.mode === "program" && state.queue.length === 0) {
      const active = state.programs.filter(p => p.status !== "aside" && p.status !== "removed").map(p => p.id);
      if (state.cycle < 3 && active.length) { state.cycle += 1; state.queue = shuffle(active); state.discard=state.discard.filter(name=>name.startsWith("Limitation:")); log(`Cycle ${state.cycle} began with ${active.length} Programs.`); }
      else { beginAdvanced(); return; }
    }
    if (state.mode === "advanced" && state.advancedQueue.length === 0) { finishGame(true); return; }
    const id = state.mode === "advanced" ? state.advancedQueue.shift() : state.queue.shift();
    const program = state.mode === "advanced" ? null : state.programs[id];
    state.current = { id, mode: state.mode };
    state.currentFace = state.mode === "advanced" ? (state.nextAdvancedOverheated ? "back" : "front") : (program.status === "overheated" ? "back" : "front");
    state.currentCompleted = false; state.lastResultFailed = false; state.limitationRevealed = true; state.limitationResolved = false; state.rerollsUsed = 0; state.recoveryCredits = 0;
    state.architectUsed = false; state.architectMode = false; state.debuggerUsed = false; state.optimizerUsed = false; state.rewardApplied = false;
    if (!state.limitationQueue.length) {state.limitationQueue = shuffle([0,1,2,3,4,5].filter(x => !state.banishedLimitations.includes(x)));state.discard=state.discard.filter(name=>!name.startsWith("Limitation:"));}
    state.limitation = state.limitationQueue.pop();
    state.dice.filter(d => d.zone === "withheld" || d.zone === "allocated").forEach(d => { d.zone = "available"; d.element = null; d.face = null; });
    state.elementCount = currentElementCount();
    state.elements = currentTargets().map((target, i) => ({ ...elementTemplate(i), target }));
    selectedDice.clear(); log(`${state.mode === "advanced" ? "Advanced" : (state.programs.find(x=>x.id===id)||{}).src || state.deck} Program ${id + 1} and Limitation ${state.limitation + 1} revealed (${state.elementCount} elements).`); render();
  }
  function beginAdvanced() {
    state.mode = "advanced"; state.advancedQueue = shuffle([0,1,2,3,4,5,6,7]).slice(0,3); state.nextAdvancedOverheated = false; state.current = null;state.discard=state.discard.filter(name=>name.startsWith("Limitation:"));
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
    if (recoveryPending()) { toast("Recover your dice first."); return; }
    el.failed = el.successes < el.target;
    if (el.usedReroll || el.failed) {
      // Count the misses BEFORE exhausting, because exhausting clears d.element
      // and completeProgram can no longer tell which element a die sat on.
      // Only misses still showing after any rerolls count, per the rulebook.
      if (el.failed) el.misses = dice.filter(d => value(d.face) === 0).length;
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
    if (optimal) grantRecovery(2, `Optimal Implementation on Element ${el.id + 1}`);
    el.resolved = true; el.pendingExhaust = 0;
    log(`Element ${el.id + 1}: ${el.successes}/${el.target}${el.failed ? " failed" : " succeeded"}.`);
    render();
  }
  function rollElement(i, reroll = false) {
    const el = state.elements[i]; const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i);
    if (state.architectMode) { toast("Finish or cancel Reconfigure first."); return; }
    if (recoveryPending()) { toast("Recover your dice first."); return; }
    if (!dice.length || el.resolved) { toast("Allocate at least one die first."); return; }
    if (!reroll && (el.rolled || i !== nextElementToRoll())) { toast("Roll the Elements in order, left to right."); return; }
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
    log(`${reroll ? "Rerolled" : "Rolled"} Element ${i + 1}: ${tallyText(rollTally(dice))}.`); render();
  }
  function completeProgram(forcedFailure = false) {
    if (!state.current || state.currentCompleted) return;
    if (!forcedFailure && state.elements.some(e => !e.resolved)) { toast("Resolve every visible element first."); return; }
    if (recoveryPending()) { toast("Recover your dice first."); return; }
    const failed = forcedFailure ? 1 : state.elements.filter(e => e.failed).length;
    state.metrics.programs += 1; state.metrics.failedElements += failed;
    if (!forcedFailure && failed >= 2) {
      state.metrics.catastrophes += 1;
      // "You may exhaust 2 misses on failed elements to negate the Health
      // loss." Applied automatically: every die on a failed element was
      // exhausted at beginResolve already, so spending the misses costs
      // nothing and no player would ever decline. MISSES_TO_NEGATE in
      // simulation/aos.py is the same constant; keep the two in step.
      const missesOnFailed = state.elements.reduce((n, e) => n + (e.failed ? (e.misses || 0) : 0), 0);
      if (missesOnFailed >= MISSES_TO_NEGATE) {
        state.metrics.negated += 1;
        log(`Catastrophic Failure negated: exhausted ${MISSES_TO_NEGATE} of ${missesOnFailed} misses on failed elements. No Health lost.`, "good");
      } else {
        state.hp = Math.max(0, state.hp - 1);
        log(`Catastrophic Failure: lost 1 HP (only ${missesOnFailed} miss${missesOnFailed === 1 ? "" : "es"} on failed elements, ${MISSES_TO_NEGATE} needed to negate).`, "bad");
      }
    }
    state.dice.filter(d => d.zone === "allocated" || d.zone === "withheld").forEach(d => { d.zone = "available"; d.element = null; d.face = null; });
    grantRecovery(state.rec, `REC ${state.rec}`);
    if (state.current.mode === "program") {
      const p = state.programs[state.current.id];
      if (failed > 0) p.status = p.status === "stable" ? "overheated" : "aside";
    } else {
      state.advancedDone += 1; state.nextAdvancedOverheated = failed >= 2;
    }
    state.discard.push(`${programSource(state.current).deck}: ${PROGRAM_FLAVOR[state.current.mode === "advanced" ? "Advanced" : state.deck][state.current.id].name}`);
    if(state.limitation !== null)state.discard.push(`Limitation: ${limitationName(state.limitation)}`);
    state.currentCompleted = true; state.lastResultFailed = failed > 0;
    log(`Program completed with ${failed} failed element${failed === 1 ? "" : "s"}.`);
    if (state.hp <= 0) finishGame(false); else render();
  }
  function finishGame(won) { state.finished = true; state.currentCompleted = true; log(won ? "AoS completed — Technician survived." : "AoS ended — Technician was knocked out.", won ? "good" : "bad"); render(); toast(won ? "Playtest won" : "Playtest lost"); }

  function applyReward(kind = currentReward()?.kind) {
    if (!state.currentCompleted || state.lastResultFailed || state.current?.mode !== "program") return;
    if (!kind || kind !== currentReward()?.kind) return;
    if (kind === "hp") state.hp = Math.min(6, state.hp + 1);
    if (kind === "recover") grantRecovery(3, "Program Reward");
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
    if (!state.limitationResolved) { toast("Resolve the Limitation before committing dice."); return; }
    if (rollingStarted()) { toast("Dice are locked once the first Element rolls."); return; }
    const dice = selectedAvailable(); if (!dice.length) { toast("Select available dice first."); return; }
    dice.forEach(d => { d.zone = "allocated"; d.element = i; d.face = null; selectedDice.delete(d.id); }); render();
  }
  function returnElementDice(i) {
    const el = state.elements[i];
    if (!el || el.rolled || state.currentCompleted || rollingStarted()) return;
    state.dice.filter(d => d.zone === "allocated" && d.element === i).forEach(d => {
      d.zone = "available"; d.element = null; d.face = null; selectedDice.delete(d.id);
    });
    render();
  }
  function toggleArchitectMode() {
    if (TECHS[state.tech].name !== "Architect" || !state.current || state.currentCompleted || state.architectUsed) return;
    state.architectMode = !state.architectMode; selectedDice.clear();
    toast(state.architectMode ? "Select up to 2 allocated dice, then choose their destination." : "Reconfigure canceled.");
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
    if (recoveryPending()) {
      if (d.zone !== "exhausted") { toast("Only exhausted dice can be recovered."); return; }
      [...selectedDice].forEach(x => { if (dieById(x)?.zone !== "exhausted") selectedDice.delete(x); });
      if (!selectedDice.has(id) && selectedDice.size >= recoveryOwed()) { toast(`You may recover ${recoveryOwed()} ${recoveryOwed() === 1 ? "die" : "dice"}.`); return; }
      selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render(); return;
    }
    if (state.architectMode) {
      const el = d.zone === "allocated" ? state.elements[d.element] : null;
      if (!el || el.resolved || el.rolled) { toast("Reconfigure selects allocated dice from unresolved elements."); return; }
      if (!selectedDice.has(id) && selectedDice.size >= 2) { toast("Architect can move up to 2 dice."); return; }
      selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render(); return;
    }
    if (d.zone === "allocated") {
      const el = state.elements[d.element];
      if (el?.pendingExhaust > 0) {
        d.zone = "exhausted"; d.element = null; el.pendingExhaust -= 1; state.metrics.diceExhausted += 1;
        if (el.pendingExhaust === 0) finalizeElement(el); else render(); return;
      }
      if (!el?.rolled) { if (rollingStarted()) { toast("Dice are locked once the first Element rolls."); return; } d.zone = "available"; d.element = null; selectedDice.delete(id); render(); }
      else if ((TECHS[state.tech].name === "Compiler" || (TECHS[state.tech].name === "Debugger" && !state.debuggerUsed && el.successes === el.target - 1)) && !el.resolved) { selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render(); }
      return;
    }
    if (d.zone === "banished") return;
    if (d.zone === "withheld" && state.current && !state.currentCompleted && !state.limitationResolved) { d.zone = "available"; selectedDice.delete(id); render(); return; }
    selectedDice.has(id) ? selectedDice.delete(id) : selectedDice.add(id); render();
  }

  function dieButton(d) {
    const face = d.face ? FACE_MARK[d.face] : "";
    const eligible = d.zone === "exhausted" && recoveryPending();
    return `<button class="die ${d.color}${selectedDice.has(d.id) ? " selected" : ""}${eligible ? " eligible" : ""}" data-die="${d.id}" title="${d.color} die · ${d.face ? faceLabel(d.face) : "not rolled"}" aria-label="${d.color} die${d.face ? `, ${faceLabel(d.face)}` : ", not rolled"}"><span class="face">${face}</span><span class="tiny">${d.color[0].toUpperCase()}</span></button>`;
  }
  function renderCard() {
    const card = $("programCard");
    if (!state.current) { clearSprite(card, state.started ? "Draw the next Program." : "Start a playtest to load the deck."); $("programTitle").textContent = state.started ? "Between Programs" : "No program drawn"; $("programFlavor").textContent = ""; }
    else {
      const src = programSource(state.current); const name = src.deck; const data = DECKS[name];
      const flavor = PROGRAM_FLAVOR[name][state.current.id];
      sprite(card, state.currentFace === "front" ? data.front : data.back, state.current.id, data.count);
      $("programTitle").textContent = `${flavor.name} · ${state.currentFace === "front" ? "Stable" : "Overheated"}`;
      $("programFlavor").textContent = flavor[state.currentFace];
    }
    if (state.current) {
      const lim = state.limitation;
      if (isCorrupt(lim)) sprite($("limitationCard"), "NRJ_AoS_CorruptedLimitations_TTS.png", lim - 6, 6);
      else sprite($("limitationCard"), "AoS_Limitations_TTS.png", lim, 6);
      $("limitationFlavor").textContent = lim === null || lim === undefined ? ""
        : isCorrupt(lim) ? `${limitationText(lim)} Withhold 2 ${corruptColor()} dice.` : (LIMITATION_FLAVOR[lim]?.text || "");
    }
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
  // Elements are rolled strictly left to right: only the leftmost unresolved Element may roll.
  function nextElementToRoll() { return state.elements.findIndex(e => !e.resolved); }

  function renderElements() {
    const wrap = $("elements");
    const nextRoll = nextElementToRoll(), pend = recoveryPending();
    const readyToRoll = state.elements.every((e, n) => e.resolved || state.dice.some(d => d.zone === "allocated" && d.element === n));
    wrap.innerHTML = state.elements.map((el, i) => {
      const dice = state.dice.filter(d => d.zone === "allocated" && d.element === i).sort(byColor);
      const status = (el.resolved ? (el.failed ? "failed" : "resolved") : "")
        + (i === markedElement() ? " marked" : "");
      const score = el.rolled ? `${el.successes} success${el.successes === 1 ? "" : "es"}${el.pendingExhaust ? ` · choose ${el.pendingExhaust} to exhaust` : ""}` : "Not rolled";
      const optimizerEligible = el.rolled && !el.resolved && el.successes === el.target + 1 && !state.optimizerUsed;
      const optimizer = TECHS[state.tech].name === "Optimizer" ? `<button data-optimize="${i}" ${optimizerEligible ? "" : "disabled"}>${el.optimizerUsed ? "✓ Optimal" : "Count as optimal"}</button>` : "";
      const debuggerButton = TECHS[state.tech].name === "Debugger" ? `<button data-debug="${i}" ${el.rolled && !el.resolved && el.successes === el.target - 1 && !state.debuggerUsed ? "" : "disabled"}>Debug selected</button>` : "";
      const engineer = TECHS[state.tech].name === "Engineer" ? `<button data-safe="${i}" ${el.rolled ? "disabled" : ""}>${el.thresholdBonus === 2 ? "✓ " : ""}Safe T+2</button>` : "";
      const assignLabel = state.architectMode ? "Move selected here" : "Commit selected";
      const locked = rollingStarted();
      const canCommit = state.architectMode ? !el.rolled && !el.resolved : state.limitationResolved && !locked && !el.resolved;
      const left = extraRollsLeft();
      return `<article class="element ${status}${readyToRoll && i === nextRoll ? " next" : ""}"><div class="element-head"><h3>Element ${i + 1}</h3><div class="target" aria-label="Printed Target"><span class="target-label">Printed Target</span><strong>${el.target}</strong></div></div><div class="element-drop" data-assign="${i}">${dice.map(dieButton).join("") || "<span class='hint'>No dice assigned</span>"}</div><div class="element-actions"><button data-assign="${i}" ${canCommit ? "" : "disabled"}${state.limitationResolved || state.architectMode ? "" : ' title="Resolve the Limitation first"'}>${assignLabel}</button><button data-unassign="${i}" ${!dice.length || el.rolled || locked ? "disabled" : ""}>Return dice</button><button data-roll="${i}" ${!readyToRoll || el.rolled || i !== nextRoll || pend ? "disabled" : ""}${readyToRoll ? (i > nextRoll && !el.resolved ? ' title="Roll the Elements in order, left to right"' : "") : ' title="Allocate dice to every Element first"'}>Roll</button><button data-reroll="${i}" ${!el.rolled || el.resolved || left <= 0 || pend ? "disabled" : ""}>${left > 0 ? `Extra roll (${left} left)` : "No extra rolls"}</button><button data-resolve="${i}" ${!el.rolled || el.resolved || pend ? "disabled" : ""}>Resolve</button>${engineer}${optimizer}${debuggerButton}</div><div class="element-score">${score}</div></article>`;
    }).join("") + Array.from({ length: Math.max(0, MAX_ELEMENTS - state.elements.length) }, (_, k) =>
      // Unused slots keep the board at five Elements; they take no dice and every control stays disabled.
      `<article class="element unused" aria-disabled="true"><div class="element-head"><h3>Element ${state.elements.length + k + 1}</h3><div class="target" aria-label="Printed Target"><span class="target-label">Printed Target</span><strong>—</strong></div></div><div class="element-drop"><span class='hint'>Not used on this Program</span></div><div class="element-actions"><button disabled>Commit selected</button><button disabled>Return dice</button><button disabled>Roll</button><button disabled>Extra roll</button><button disabled>Resolve</button></div><div class="element-score">&nbsp;</div></article>`
    ).join("");
  }
  const DIE_ORDER=["red","purple","blue","green","yellow"];   // Red sits left of Purple
  const byColor=(a,b)=>DIE_ORDER.indexOf(a.color)-DIE_ORDER.indexOf(b.color);
  function renderPools() {
    for (const zone of ["available", "exhausted", "withheld", "banished"]) {
      const dice = [...zoneDice(zone)].sort(byColor); $(`${zone}Dice`).innerHTML = dice.map(dieButton).join(""); $(`${zone}Count`).textContent = `(${dice.length})`;
    }
  }
  function renderMetrics() {
    const m = state.metrics;
    const items = [["Programs",m.programs],["Failed elements",m.failedElements],["Catastrophes",m.catastrophes],["Negated",m.negated],["Extra rolls",m.rerolls],["Dice exhausted",m.diceExhausted],["Required misses",m.requiredMisses],["Fiddly / unclear",`${m.fiddly} / ${m.unclear}`],["Good decisions",m.good]];
    $("metrics").innerHTML = items.map(([k,v]) => `<div class="metric"><span>${k}</span><strong>${v}</strong></div>`).join("");
    $("eventLog").innerHTML = state.log.map(e => `<div class="log-entry"><b>${e.at}</b> · ${e.message}</div>`).join("") || "<div class='log-entry'>The playtest log will appear here.</div>";
  }
  function render() {
    renderAOSModules();
    ensureElements();
    $("deckSelect").value = state.level || state.deck; $("techSelect").value = String(state.tech); $("elementCount").textContent = String(state.elementCount);
    $("hp").textContent = state.hp; $("str").textContent = state.str; $("rec").textContent = state.rec; $("cycle").textContent = state.mode === "advanced" ? `ADV ${state.advancedDone + 1}/3` : (state.started ? `${state.cycle}/3` : "—");
    $("drawPile").textContent = state.started ? (state.mode === "advanced" ? state.advancedQueue.length : state.queue.length) : "—";
    $("programsDone").textContent = state.metrics.programs;
    $("recoveryCredits").textContent = state.recoveryCredits; $("rerolls").textContent = `${state.rerollsUsed} / ${Math.max(0,state.str-1)}`;
    $("runState").textContent = !state.started ? "Choose a deck and Technician, then draw the first Program." : state.finished ? (state.hp > 0 ? "Playtest complete: survived Advanced Programming." : "Playtest complete: Health reached 0.") : `${state.deck} · ${TECHS[state.tech].name} · ${state.programs.filter(p=>p.status==="aside").length} set aside`;
    $("drawBtn").disabled = (!!state.current && !state.currentCompleted) || state.finished; $("drawBtn").textContent = !state.started ? "Start playtest" : state.mode === "advanced" ? "Next Advanced" : "Draw program";
    $("flipBtn").disabled = !state.current || state.currentCompleted;
    $("programControls").classList.toggle("hidden", !state.current || state.currentCompleted); $("rewardBar").classList.toggle("hidden", !state.currentCompleted || state.finished || state.lastResultFailed || state.rewardApplied || state.current?.mode !== "program");
    const reward = currentReward(); $("rewardName").textContent = reward?.label || "—"; $("applyRewardBtn").disabled = !reward;
    if (state.recoveryCredits > 0 && !zoneDice("exhausted").length) { state.recoveryCredits = 0; state.recoverySource = ""; }
    const owed = recoveryOwed(), picked = [...selectedDice].filter(x => dieById(x)?.zone === "exhausted").length;
    $("recoverBar").classList.toggle("hidden", !owed);
    $("recoverText").innerHTML = owed ? `<b>${state.recoverySource || "Recovery"}:</b> recover ${owed} exhausted ${owed === 1 ? "die" : "dice"}. Select ${owed === 1 ? "it" : "them"} in the Exhausted pool.` : "";
    $("recoverSelectedBtn").textContent = `Recover Selected Dice (${picked}/${owed})`;
    $("recoverSelectedBtn").disabled = picked !== owed;
    ["exhaustSelectedBtn", "withholdSelectedBtn", "banishSelectedBtn"].forEach(b => { if (owed) $(b).disabled = true; });
    if (owed) { $("drawBtn").disabled = true; $("finishProgramBtn").disabled = true; }
    else $("finishProgramBtn").disabled = false;
    const gate = $("limitationResolveBtn"), gateOpen = !!state.current && !state.currentCompleted;
    gate.classList.toggle("hidden", !gateOpen); gate.disabled = !!state.limitationResolved;
    gate.classList.toggle("primary", !state.limitationResolved);
    gate.textContent = state.limitationResolved ? "✓ Limitation resolved" : "Resolve Limitation";
    $("limitationHint").classList.toggle("hidden", !gateOpen || !!state.limitationResolved);
    $("withholdSelectedBtn").disabled = gateOpen && !!state.limitationResolved;
    renderCard(); renderTech(); renderElements(); renderPools(); renderMetrics();
    if (document.activeElement !== $("notes")) $("notes").value = state.notes || "";
    save();
  }

  function summary() {
    const m = state.metrics;
    return `AoS playtest — ${state.level || state.deck} / ${TECHS[state.tech].name}\nResult: ${state.finished ? (state.hp > 0 ? "Win" : "Loss") : "In progress"}\nHP ${state.hp} · STR ${state.str} · REC ${state.rec}\nPrograms ${m.programs}; failed elements ${m.failedElements}; catastrophes ${m.catastrophes} (${m.negated} negated); extra rolls ${m.rerolls}; dice exhausted ${m.diceExhausted}; required-color misses ${m.requiredMisses}\nSignals: fiddly ${m.fiddly}; unclear ${m.unclear}; good decisions ${m.good}\nNotes: ${state.notes || "—"}`;
  }
  async function copySummary() { state.notes = $("notes").value; try { await navigator.clipboard.writeText(summary()); toast("Summary copied"); } catch (_) { toast("Copy unavailable; select the notes manually."); } save(); }
  function reset() { if (document.getElementById("gameNav")?.value !== "aos") return; if (!confirm("Start a new playtest? The current in-progress state will be replaced.")) return; state = freshState(state.level || "Standard"); aosApplyInterferenceSetup(); selectedDice.clear(); render(); }
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
    $("drawBtn").addEventListener("click", startOrDraw); 
    document.addEventListener("click", event => {
      const claim = event.target.closest?.("[data-aos-backdoor-claim]");
      if (claim) return aosClaimBackdoor(Number(claim.dataset.aosBackdoorClaim), false);
      const use = event.target.closest?.("[data-aos-backdoor-spend]");
      if (use) return aosClaimBackdoor(Number(use.dataset.aosBackdoorSpend), true);
    });
    window.addEventListener("nobulous-tier", () => {
      if (aosTier() === (state.tier || "0")) return render();
      state = freshState(state.level || "Standard"); aosApplyInterferenceSetup(); save(); render();
    });
    window.AOS_LAB = { render };

    $("flipBtn").addEventListener("click", () => { state.currentFace = state.currentFace === "front" ? "back" : "front"; syncPrintedTargets(); render(); });
    $("finishProgramBtn").addEventListener("click", () => completeProgram(false)); $("requiredMissBtn").addEventListener("click", markRequiredMiss);
    $("techActionBtn").addEventListener("click", toggleArchitectMode); $("applyRewardBtn").addEventListener("click", () => applyReward());
    $("resetBtn").addEventListener("click", reset); $("copySummaryBtn").addEventListener("click", copySummary);
    $("closeCardBtn").addEventListener("click", () => $("cardDialog").close());
    [$("programCard"), $("limitationCard"), $("techCard")].forEach(el => el.addEventListener("click", () => zoomCard(el)));
    $("deckSelect").addEventListener("change", e => {
      // The level IS the Program deck, so changing it rebuilds the 8 cards.
      const level = e.target.value;
      if (state.started && !confirm("Change difficulty? The current run restarts with a new Program deck.")) {
        e.target.value = state.level || "Standard";
        return;
      }
      state = freshState(level);
      aosApplyInterferenceSetup();
      selectedDice.clear();
      save();
      render();
    }); $("techSelect").addEventListener("change", e => { if(!state.started){state.tech=Number(e.target.value);renderTech();save();}else e.target.value=String(state.tech); });
    $("exhaustSelectedBtn").addEventListener("click", () => moveSelected("exhausted")); $("withholdSelectedBtn").addEventListener("click", () => moveSelected("withheld")); $("limitationResolveBtn").addEventListener("click", resolveLimitation); $("recoverSelectedBtn").addEventListener("click", recoverSelected); $("banishSelectedBtn").addEventListener("click", () => moveSelected("banished"));
    $("notes").addEventListener("input", e => { state.notes=e.target.value;save(); });
    document.addEventListener("click", e => {
      if (!e.target.closest("#screen-aos, #recordPanel")) return;
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
