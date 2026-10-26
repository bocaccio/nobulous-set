(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const STORE = "nobulous-bat-v2";
  const cards = window.BAT_EXPERIMENTS;
  const names = ["Rummage", "Fidget", "Whiz", "Mottle"];
  const colors = ["purple", "blue", "green", "yellow"];
  const DIE_ORDER=["red","purple","blue","green","yellow"];   // Red sits left of Purple
  const byColor=(a,b)=>DIE_ORDER.indexOf(a.color)-DIE_ORDER.indexOf(b.color);
  const faces = {
    purple: ["✦", "✦", "✦", "✦", "✷", ""],
    blue: ["✦", "✦", "✦", "✷", "", ""],
    green: ["✦", "✦", "✷", "", "", ""],
    yellow: ["✦", "✷", "", "", "", ""],
    red: ["✦", "✦", "✦", "✦", "✦", "✷"]
  };
  const upgrades = [
    ["Serrated Claws",2],["Reinforced Jaw",3],["Capacitor Muscles",3],["Piercing Horn",4],
    ["Spring-Loaded Legs",2],["Prehensile Tail",2],["Tripwire Tendons",3],["Evasive Reflexes",3],
    ["Thickened Hide",2],["Layered Carapace",3],["Chromatic Plating",3],["Reactive Shell",4],
    ["Acute Hearing",2],["Predatory Focus",3],["Rapid Metabolism",2],["Neural Overclock",4]
  ];
  const specimens = ["Titanium-Toothed Mole","Voltaic Mantis","Blink Hare","Ghost Gecko","Ironback Beetle","Prismatic Tortoise","Echo Bat","Regenerator Newt"];
  const shuffle = input => { const a = [...input]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; };
  const escape = value => String(value).replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"})[ch]);
  const rollTally = dice => dice.reduce((t,x)=>{
    if(x.face==="✷"){t.crits++;t.successes+=2;}
    else if(x.face==="✦"){t.hits++;t.successes+=1;}
    else t.misses++;
    return t;
  },{crits:0,hits:0,misses:0,successes:0});
  const tallyText = t => `${t.successes} success${t.successes===1?"":"es"} · `
    +`${t.crits} Crit${t.crits===1?"":"s"}, ${t.hits} hit${t.hits===1?"":"s"}, `
    +`${t.misses} miss${t.misses===1?"":"es"}`;
  const faceLabel = face => face==="✷" ? "Crit · 2 successes"
    : face==="✦" ? "Hit · 1 success" : "Miss · 0 successes";
  const faceValue = face => face === "✷" ? 2 : face === "✦" ? 1 : 0;
  const rollFace = color => faces[color][Math.floor(Math.random()*6)];
  const RAT_REC=[2,2,1,1];
  const RAT_STR=2;   // every Lab Rat prints STR 2: one roll plus one reroll
  // Upgrades that grant an extra Strategy roll when tapped.
  const isCard=(c,type,i)=>c&&c.type===type&&c.i===i;
  const STR_NOW=c=>isCard(c,"u",13)||isCard(c,"s",6);   // Predatory Focus, Echo Bat
  const STR_NEXT=c=>isCard(c,"u",12);                   // Acute Hearing: next turn
  // What is granting extra Strategy rolls this turn, by name.
  // Lab Rat abilities, one per side (generator/build_bat.py is the source).
  // The rules silence them during the Tyrant battle, so every use is gated on
  // the Splice Phase.
  const RAT_ABILITIES=[
    [{name:"Careful Borrower",text:"When checking whether a die Rummage borrowed is banished, you may reroll the check once."},
     {name:"Tool Keeper",text:"When another Rat borrows one of Rummage's dice and it is not banished, return it available instead of exhausted."}],
    [{name:"Jury-Rig",text:"Once per Experiment, after Fidget rolls, reroll one miss. This does not use a Strategy phase."},
     {name:"Fine Tuning",text:"Once per Experiment, reroll one of Fidget's basic hits. If the reroll misses, retain the original basic hit."}],
    [{name:"Self-Sufficient",text:"If Whiz commits no borrowed die and does not use the Red die this Experiment, reduce the Experiment's Target by 1."},
     {name:"Prepared",text:"If a different Rat was active on the previous turn, recover 1 of Whiz's exhausted dice after selecting Whiz and before committing dice."}],
    [{name:"Experimental Subject",text:"If at least one Specimen is revealed, Mottle has +1 STR for that Experiment and recovers 1 additional die this turn."},
     {name:"Specimen Adaptation",text:"After Mottle completes an Experiment, recover 1 additional die for each Specimen Mottle holds."}],
  ];
  const ratAbility=i=>RAT_ABILITIES[i]?.[state.rats[i]?.side==="back"?1:0];
  const ratHas=(i,name)=>!inBattle()&&ratAbility(i)?.name===name;
  const specimenShown=c=>!!c&&c.options.some(x=>x.type==="s");
  const ratUses=c=>(c.ratUses??={});
  function recBonusFor(i){const b=state.recBonus;return b&&b.rat===i?b.n:0;}
  function strSources(rat){
    if(!rat) return [];
    const out=[];
    if(rat.strNext) out.push("Acute Hearing (tapped last turn)");
    rat.upgrades.filter(c=>c.tapped&&STR_NOW(c)).forEach(c=>out.push(cardName(c)));
    return out;
  }
  function strFor(rat){
    if(!rat) return RAT_STR;
    return RAT_STR+(rat.strNext||0)+rat.upgrades.filter(c=>c.tapped&&STR_NOW(c)).length;
  }
  const inBattle = () => state.splices>=5;
  const maxPhase = c => (c.e===16?1:2)
    + (specimenShown(c)&&ratHas(state.activeRat,"Experimental Subject")?1:0);
  // The Red die is communal. Once it has been rolled it is set aside, and at
  // the start of the next turn it must be placed on a Rat other than the
  // active one - that is what stops it being used every turn. Until it is
  // placed, nobody may commit.
  const redPending = () => state.red.zone === "setaside";
  // Where a set-aside Red may legally go: normally any standing Rat other than
  // the active one, but Restricted Materials (Experiment 10) keeps it on the
  // active Rat. An empty list means there is nothing to wait for, so Red must
  // not block the turn - otherwise the Experiment can never be rolled.
  const redTakers = () => state.current?.e === 10
    ? (state.rats[state.activeRat].down ? [] : [state.activeRat])
    : state.rats.map((r,i)=>i).filter(i => i !== state.activeRat && !state.rats[i].down);
  const redBlocks = () => redPending() && redTakers().length > 0;
  const canTakeRed = i => redPending() && !state.turnLocked && redTakers().includes(i);
  // Borrowing is a decision, not a side effect of selecting a die, so the
  // rules that govern it live in one place and are reported in one place.
  // Modifications are held as ordinary Upgrades; Extra Limbs is BAT_MODS[0].
  const holdsMod = (i,idx) => state.rats[i].upgrades.some(c=>c.type==="m"&&c.i===idx);
  const borrowAllowedColors = () =>
    [colors,colors.slice(1),colors.slice(2),colors.slice(3)][Math.min(active().upgrades.length,3)];
  function borrowProblem(i, die){
    const c=state.current;
    if(!c) return "Reveal an Experiment first.";
    if(i===state.activeRat) return "A Rat cannot borrow from itself.";
    if(state.rats[i].down) return `${state.rats[i].name} is knocked out.`;
    if(c.e===11) return "Borrowing is prohibited by this Experiment.";
    if(holdsMod(state.activeRat,0)) return `${active().name} may not borrow while holding Extra Limbs.`;
    if(c.borrowedId&&c.borrowedId!==die?.id) return "Only one die may be borrowed for the whole Experiment.";
    if(!die) return "Select one available die on this Rat first.";
    if(die.zone!=="available") return "Only an available die may be lent.";
    // Cross-Contamination waives the colour limit on a Rat's first borrow.
    const free=state.protocol===0&&!(state.freeBorrow||[]).includes(state.activeRat);
    if(!free&&!borrowAllowedColors().includes(die.color))
      return `${active().name} holds ${active().upgrades.length} Upgrade${active().upgrades.length===1?"":"s"}, so ${die.color} may not be borrowed.`;
    return "";
  }
  function lendDie(i){
    const rat=state.rats[i];
    const picked=rat.dice.filter(x=>x.selected&&x.zone==="available");
    const die=picked.length===1?picked[0]:null;
    const problem=borrowProblem(i,die);
    if(problem) return setNotice(picked.length>1?"Select exactly one die to lend.":problem);
    const c=state.current;
    if(state.protocol===0&&!(state.freeBorrow||[]).includes(state.activeRat)
       &&!borrowAllowedColors().includes(die.color)){
      state.freeBorrow=[...(state.freeBorrow||[]),state.activeRat];
    }
    c.borrowedId=die.id;
    die.selected=true;
    setNotice(`${active().name} borrows ${rat.name}'s ${die.color} die for this Experiment.`);
  }
  // Undo the turn's setup - Red, the borrowed die, and every selection - so
  // a different Rat can be chosen. Only reachable before the first roll.
  function resetTurn(){
    if(state.turnLocked) return setNotice("The dice are already rolled — this turn cannot be reset.");
    const c=state.current, undone=[];
    if(state.turnRedPlaced){
      state.red.holder=null;state.red.zone="setaside";state.red.selected=false;state.red.face="";
      state.turnRedPlaced=false;undone.push("Red is set aside again");
    }
    if(c&&c.borrowedId){
      const die=personalDice().find(x=>x.id===c.borrowedId);
      if(die) die.selected=false;
      c.borrowedId=null;undone.push("the borrowed die went back");
    }
    personalDice().forEach(d=>{d.selected=false;});
    state.red.selected=false;
    setNotice(`Turn reset — choose a Rat again${undone.length?" ("+undone.join(", ")+")":""}.`);
  }
  function returnBorrowed(){
    const c=state.current;
    if(!c||!c.borrowedId) return;
    const die=personalDice().find(x=>x.id===c.borrowedId);
    // Once thrown it is committed to the Experiment and only the banished-die
    // check can send it home.
    if(die&&die.zone!=="available")
      return setNotice("That die has been rolled \u2014 it can only come back through the return check.");
    if(die) die.selected=false;
    c.borrowedId=null;
    setNotice("Borrowed die returned.");
  }
  function swapUpgrades(){
    const c=state.current;
    if(!c||c.e!==3||c.swapped) return;
    if(state.upgradeDeck.length<2){
      reshuffleUpgrades();
      if(state.upgradeDeck.length<2) return setNotice("The Upgrade deck is empty.");
    }
    state.discard.push(...c.options.map(card=>cardName(card)));
    c.options=[state.upgradeDeck.pop(),state.upgradeDeck.pop()];
    c.swapped=true;
    setNotice("Both Upgrades were discarded and replaced.");
  }
  // "The borrowed die is rolled again by itself; a miss banishes it." This is
  // a step the player takes, not something that happens while they look away.
  // Step 8, so it has to outlive the Experiment that created it: resolving
  // clears state.current, and the borrowed die still has to be rolled.
  const borrowCheckDue = () => !!state.returnCheck;
  function borrowCheck(){
    const rc=state.returnCheck;
    if(!rc) return;
    const die=personalDice().find(x=>x.id===rc.dieId);
    state.returnCheck=null;
    if(!die) return setNotice("The borrowed die is no longer on the table.");
    const owner=Number(die.id.split("-")[1]);
    let safe=!!faceValue(rollFace(die.color));
    let note=`Return check for ${state.rats[owner].name}'s ${die.color} die: ${safe?"hit":"miss"}.`;
    if(!safe&&ratHas(rc.borrower,"Careful Borrower")){
      safe=!!faceValue(rollFace(die.color));
      note+=safe?" Careful Borrower: the reroll saved it.":" Careful Borrower: the reroll missed too.";
    }
    if(!safe){
      die.zone="banished";die.face="";die.selected=false;
      note+=" It is banished.";
      if(state.protocol===0&&state.upgradeDeck.length){
        const extra=state.upgradeDeck.pop();
        recordSplice(extra);
        note+=` Cross-Contamination: ${cardName(extra)} was Spliced into the Prototyrant.`;
      }
    }else if(ratHas(owner,"Tool Keeper")){
      die.zone="available";die.face="";die.selected=false;
      note+=` Tool Keeper: ${state.rats[owner].name} takes it back available.`;
    }else{
      die.zone="exhausted";die.face="";die.selected=false;
      note+=` It returns to ${state.rats[owner].name} exhausted.`;
    }
    setNotice(note);
  }
  // Rolled dice sit unbanked until they are added to the Experiment. Whatever
  // is left unbanked is what a further Strategy roll may reroll.
  const isPending = id => (state.current?.pending||[]).includes(id);
  const pendingDie = id => id==="red" ? state.red : personalDice().find(x=>x.id===id);
  const unbankedScoring = () =>
    (state.current?.pending||[]).filter(id=>faceValue(pendingDie(id)?.face)>0);
  // Rolled successes count whether or not they have been banked - banking is
  // about protecting dice from the next throw, not about scoring them.
  const unbankedValue = () =>
    unbankedScoring().reduce((n,id)=>n+faceValue(pendingDie(id)?.face),0);
  const totalSuccesses = () =>
    (state.current?.successes||0)+unbankedValue();
  function allocateSelected(){
    const c=state.current;
    if(!c) return;
    // The pending list is this Experiment's own, so a die on it may be added
    // whatever zone it has ended up in - that rescues dice an early resolve
    // exhausted before the guard was moved ahead of it.
    const dice=personalDice().filter(x=>x.selected&&isPending(x.id));
    const red=state.red.selected&&isPending("red")?state.red:null;
    if(!dice.length&&!red) return setNotice("Select rolled dice to add to the Experiment.");
    const all=red?dice.concat([red]):dice;
    const gained=all.reduce((n,x)=>n+faceValue(x.face),0);
    c.successes+=gained;
    c.pending=(c.pending||[]).filter(id=>!all.some(x=>(x===red?"red":x.id)===id));
    // Snapshot colour and face now: these dice get exhausted at the end of
    // the Experiment, and Red's face is wiped when it is set aside.
    c.banked=(c.banked||[]).concat(all.map(x=>({
      id:x===red?"red":x.id, color:x===red?"red":x.color, face:x.face})));
    all.forEach(x=>{x.selected=false;});
    setNotice(`Added ${tallyText(rollTally(all))} to the Experiment. Banked ${c.successes} / ${target()}.`);
  }
  function exhaustRolled(keepId){personalDice().forEach(d=>{if(d.zone==="rolled"&&d.id!==keepId){d.zone="exhausted";d.selected=false;}});
    if(state.red.zone==="rolled"){state.red.zone="setaside";state.red.holder=null;state.red.selected=false;state.red.face="";}}
  const cardName = card => card.type === "s" ? specimens[card.i] : card.type === "u" ? upgrades[card.i][0] : card.type === "m" ? BAT_MODS[card.i][0] : "Untracked Upgrade";
  // --- NRJ module cards ---------------------------------------------
  const BAT_PROTOCOLS = [
    ["Cross-Contamination","The first time each Rat borrows a die, it may borrow any color regardless of Upgrade count. If that die is banished, reveal the top Upgrade and Splice it into the Tyrant."],
    ["Shared Equipment Budget","At setup, randomly select 2 personal dice from different Rats and place them in a common Equipment pool. After completing an Experiment, the active Rat may exchange one personal die with one Equipment die."],
    ["Accelerated Trials","Experiments with printed Target 5+ have -1 Target. Exhaust 2 of the active Rat's available dice after every such attempt, whether or not it is completed."],
    ["Questionable Procurement","Shuffle 1 additional random Specimen into the Upgrade deck. The first Specimen acquired by each Rat does not count against its 3-Upgrade limit until that Rat gains another Upgrade."],
    ["Independent Funding","After the borrowed die's banishment check, when a Rat has lent a die to a Rat holding fewer Upgrades, the lender recovers 1 die - but only if that Experiment was completed."],
    ["Questionable Methodology","After revealing the two Upgrades for an Experiment, you may Splice the stronger one into the Tyrant and reveal a replacement. If you do, reduce the Experiment's Target by 1."],
  ];
  // name, slot and value, printed text, value
  const BAT_MODS = [
    ["Extra Limbs","Mobility \u00b7 Value 3","Tap: roll 1 exhausted Green or Yellow die. While held, the holder may not borrow dice.",3],
    ["Secondary Brain","Senses \u00b7 Value 3","Tap before rolling: +1 STR for this Experiment/attack. While held, the holder may not use the Red die.",3],
    ["Adrenal Gland","Power \u00b7 Value 4","Tap: +3 damage. While held, the holder has 1 less Health, minimum 1.",4],
    ["Bone Plating","Defense \u00b7 Value 3","Reduce incoming damage by 2. While held, the holder has -1 REC, minimum 1.",3],
    ["Redundant Organs","Defense \u00b7 Value 4","The first time the holder would be knocked out, discard this card instead; the holder remains at 1 Health. While held, the holder cannot be selected as active on consecutive turns.",4],
    ["Hypermetabolism","Senses \u00b7 Value 3","Tap: recover +2 dice. While held, exhaust 1 available die at the end of each Experiment the holder attempts.",3],
  ];
  const BAT_NOTES = [
    ["Unexpected Resilience","Claim after a Rat completes an Experiment without committing Purple or Red.","Once per game, recover all of that Rat's dice."],
    ["Successful Integration","Claim when a single Rat holds 2 Specimens.","Once per game, ignore the +1 Target from revealing a Specimen."],
    ["Acceptable Losses","Claim after failing 3 Experiments within the same four-Rat rotation.","Once per game after another failure, choose which revealed Upgrade is Spliced."],
    ["Cross-Species Compatibility","Claim when all four Rats hold at least 2 Upgrades.","Once during the Tyrant battle, the active Rat may tap an Upgrade held by another surviving Rat."],
    ["Controlled Failure","Claim after deliberately committing zero dice to an Experiment.","Once later, after revealing an Experiment, discard it and reveal the next one instead."],
    ["Red Means Go","Claim after Red provides the success that completes an Experiment and at least one die belonging to another Rat also contributed.","Once per game after using Red, place it directly on any non-active Rat rather than setting it aside."],
  ];
  const batTier = () => window.NOBULOUS_TIER ? window.NOBULOUS_TIER.forGame("bat") : "0";
  const cardValue = card => card.type === "s" ? 5 : card.type === "u" ? upgrades[card.i][1] : card.type === "m" ? BAT_MODS[card.i][3] : 0;
  const save = () => localStorage.setItem(STORE, JSON.stringify(state));
  const personalDice = () => state.rats.flatMap(rat => rat.dice);
  const active = () => state.rats[state.activeRat];
  const selected = () => personalDice().filter(die => die.selected);
  // What the player can usefully press right now. Every button in the
  // Experiment flow reads this, so the guidance cannot contradict itself.
  // The Battle box runs its own numbered steps and is left alone.
  function dueActions(){
    const out=new Set(), c=state.current;
    if(inBattle()) return out;
    // A turn that has rolled is not over until its Rat recovers, and after
    // the Experiment resolves a fresh one is already on the table - so a
    // locked turn sitting at phase 0 is waiting for Recover and nothing else.
    // Step 8 before step 9: the borrowed die goes home before the turn ends.
    if(state.returnCheck){ out.add("retcheck"); return out; }
    if(state.turnLocked&&(!c||!c.phase)){ out.add("recover"); return out; }
    if(!c) return out;
    // Red has to be placed before anyone commits.
    if(redBlocks()){ if(!state.turnLocked) out.add("movered"); return out; }
    if(c.phase<maxPhase(c)&&(!c.phase||selected().length||state.red.selected))
      out.add("roll");
    // Banking only protects dice from the next throw, so it is worth
    // prompting only while a throw remains.
    if(unbankedScoring().length&&out.has("roll")) out.add("allocate");
    // Resolving no longer waits on banking - loose successes count - so it
    // is due as soon as there is no roll left to make.
    if(c.phase&&!out.has("roll")) out.add("resolve");
    return out;
  }
  const due = key => dueActions().has(key) ? " bat-rec-due" : "";
  // Red is for "the turn does not go on until you press this".
  const dueRed = key => dueActions().has(key) ? " bat-required" : "";
  const canCommitColor = color => active().dice.some(d=>d.color===color&&d.zone==="available") ||
    (state.current?.e!==11 && state.rats.some((rat,i)=>i!==state.activeRat&&rat.dice.some(d=>d.color===color&&d.zone==="available")) &&
     [colors,colors.slice(1),colors.slice(2),colors.slice(3)][Math.min(active().upgrades.length,3)].includes(color));

  function fresh(difficulty="Standard") {
    const tier = batTier();
    let specimenCount = {Easy:5,Standard:6,Hard:7,Nobulous:8}[difficulty];
    // Tier I draws one Experimental Protocol at setup.
    const protocol = tier==="1"||tier==="2"||tier==="3" ? Math.floor(Math.random()*BAT_PROTOCOLS.length) : null;
    // "Questionable Procurement" shuffles in one extra Specimen.
    if(protocol===3) specimenCount = Math.min(specimens.length, specimenCount+1);
    // Tier II shuffles the 6 Unauthorized Modifications into the Upgrade deck.
    const mods = (tier==="2"||tier==="3") ? [...BAT_MODS.keys()].map(i=>({type:"m",i})) : [];
    // Tier III lays the 6 Research Notes face-up, unclaimed.
    const notes = tier==="3" ? BAT_NOTES.map(()=>({claimed:false,spent:false})) : [];
    return {
      difficulty, tier, protocol, notes, deck:shuffle([...cards.keys()]),
      upgradeDeck:shuffle([...upgrades.keys()].map(i=>({type:"u",i})).concat(mods,shuffle([...specimens.keys()]).slice(0,specimenCount).map(i=>({type:"s",i})))),
      current:null, discard:[], splices:0, spliceCards:[], rounds:0, health:20, notice:"", activeRat:0, battle:null,
      red:{holder:Math.floor(Math.random()*4),zone:"available",selected:false,face:""},
      lastRat:null,recBonus:null,
      rats:names.map((name,i)=>({name,hp:[1,1,2,2][i],side:"front",upgrades:[],dice:colors.map((color,j)=>({id:`rat-${i}-${j}`,color,zone:"available",selected:false,face:""}))}))
    };
  }

  function migrate() {
    try {
      const old = JSON.parse(localStorage.getItem("nobulous-suite-v1"))?.bat;
      if(!old || !Array.isArray(old.encounters)) return fresh();
      const next = fresh(old.difficulty || "Standard");
      next.deck = old.encounters;
      next.upgradeDeck = old.upgrades || next.upgradeDeck;
      next.splices = old.splices || 0;
      next.rounds = old.round || 0;
      next.activeRat = old.activeRat || 0;
      next.red = {holder:old.redHolder || 0,zone:old.redZone || "available",selected:false,face:old.redFace || ""};
      old.rats?.forEach((rat,i) => {
        if(!next.rats[i]) return;
        next.rats[i].hp = rat.hp;
        next.rats[i].side = rat.side;
        next.rats[i].dice = rat.dice;
        next.rats[i].upgrades = Array.from({length:rat.u || 0},()=>({type:"legacy",i:0}));
      });
      if(old.current) next.current = {e:old.current.e,options:[old.current.a,old.current.b],delta:0,phase:0,successes:0,committed:[],rolled:[],blocked:null,usedFallback:false,flipped:false,peeked:false,reduced:false,swap:null};
      next.notice = "Existing BAT progress was carried over. Previously earned Upgrades have unknown identities.";
      return next;
    } catch (_) { return fresh(); }
  }

  let state;
  try { state = JSON.parse(localStorage.getItem(STORE)) || migrate(); } catch (_) { state = migrate(); }
  if(!state?.rats || !Array.isArray(state.deck)) state = fresh();
  state.discard ??= [];
  if(!Array.isArray(state.spliceCards)) state.spliceCards=Array.from({length:state.splices||0},()=>({type:"legacy",i:0}));
  save();

  // The discard holds NAMES - every push into it goes through cardName() or
  // cards[i].name - so putting a card back means looking the name up again.
  const cardByName=(()=>{
    const m=new Map();
    upgrades.forEach((u,i)=>m.set(u[0],{type:"u",i}));
    specimens.forEach((n,i)=>m.set(n,{type:"s",i}));
    BAT_MODS.forEach((c,i)=>m.set(c[0],{type:"m",i}));
    return m;
  })();
  // "Running out of Upgrade cards is not a malfunction - reshuffle the
  // Upgrade discard instead." Experiment names share the pile, match nothing
  // here, and stay put.
  function reshuffleUpgrades(){
    const back=[],keep=[];
    for(const entry of state.discard){
      const card=typeof entry==="string"?cardByName.get(entry):entry;
      if(card) back.push(card); else keep.push(entry);
    }
    if(!back.length) return false;
    state.discard=keep;
    state.upgradeDeck=shuffle(state.upgradeDeck.concat(back));
    return true;
  }
  // "Splicing Machine Malfunction. If the Experiment deck runs out first,
  // randomly select enough unused Upgrade cards to bring the Tyrant to
  // exactly 5 Splices, apply them, and begin the battle."
  function machineMalfunction(){
    const spliced=[];
    while(state.splices<5){
      let pick;
      if(state.upgradeDeck.length||reshuffleUpgrades()){
        pick=state.upgradeDeck.splice(Math.floor(Math.random()*state.upgradeDeck.length),1)[0];
      }else{
        // Nothing unused is left anywhere. The Tyrant track is five Splices
        // wide and cannot be built with fewer, so take any Upgrade rather
        // than strand the game one short. simulation/bat.py does the same.
        pick={type:"u",i:Math.floor(Math.random()*upgrades.length)};
      }
      recordSplice(pick);
      spliced.push(cardName(pick));
    }
    state.notice="Splicing Machine Malfunction \u2014 the Experiment deck ran out. "
      +(spliced.length?`${spliced.join(", ")} ${spliced.length===1?"was":"were"} Spliced into the Prototyrant. `:"")
      +"The Prototyrant is awake — begin the battle.";
    save();render();
  }
  function recordSplice(card) {
    state.splices++;
    state.spliceCards.push(card);
  }

  function target() {
    const c=state.current;
    if(!c) return null;
    const solo=ratHas(state.activeRat,"Self-Sufficient")&&!c.borrowedId&&!c.committed.includes("red");
    const printed=cards[c.e].target;
    const accelerated=state.protocol===2&&printed>=5?-1:0;   // "Accelerated Trials"
    return Math.max(0,printed + accelerated + (c.options.some(x=>x.type==="s")?1:0) + c.delta - (solo?1:0));
  }
  // The notice panel sits at the top of the page, which is nowhere near the
  // Rat boxes most clicks happen in. #toast is fixed to the viewport, so a
  // refusal reaches the player wherever they are scrolled.
  let toastTimer=null;
  function toast(message){
    const el=document.getElementById("toast");
    if(!el||!message) return;
    el.textContent=message; el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer=setTimeout(()=>el.classList.remove("show"),2600);
  }
  function setNotice(message) { state.notice=message; toast(message); save(); render(); }
  function draw() {
    if(state.current) return setNotice("Resolve the current Experiment first.");
    if(state.splices>=5) return setNotice("The Prototyrant is awake. Begin the battle.");
    // An empty Upgrade deck is just a reshuffle; an empty Experiment deck
    // is the malfunction, and it ends the Experiment phase.
    if(state.upgradeDeck.length<2) reshuffleUpgrades();
    if(!state.deck.length) return machineMalfunction();
    if(state.upgradeDeck.length<2) return setNotice("The Upgrade deck and its discard are both empty.");
    const e=state.deck.pop(), options=[state.upgradeDeck.pop(),state.upgradeDeck.pop()];
    const c={e,options,delta:0,phase:0,successes:0,committed:[],rolled:[],blocked:null,usedFallback:false,flipped:false,peeked:false,reduced:false,swap:null};
    state.current=c;
    if(e===2 && state.upgradeDeck.length) options.push(state.upgradeDeck.pop());

    if(e===4) state.discard.push(...state.deck.splice(Math.max(0,state.deck.length-2),2).map(i=>cards[i].name));
    if(e===10) {state.red.holder=state.activeRat;state.red.zone="available";state.red.selected=false;}
    state.notice = e===3 ? "Contaminated Tissue: discard both Upgrades and reveal two new ones." : e===4 ? "Two Experiments were discarded unseen." : "Choose the active Rat, then apply any effect shown below.";
    save(); render();
  }

  // A knocked-out Rat "cannot be chosen as the attacker again", so the
  // attacking seat always has to land on a Rat that is still standing.
  function liveRatFrom(i){
    for(let step=0;step<state.rats.length;step++){
      const k=(i+step)%state.rats.length;
      if(!state.rats[k].down) return k;
    }
    return -1;
  }
  // Move the selection off a knocked-out Rat. Returns the new seat, or -1
  // when no Rat is left standing.
  function keepAttackerStanding(){
    if(!state.rats[state.activeRat]?.down) return state.activeRat;
    const k=liveRatFrom(state.activeRat);
    if(k>=0) state.activeRat=k;
    return k;
  }

  function changeRat(index) {
    if(state.rats[index]?.down) return setNotice(`${state.rats[index].name} is knocked out.`);
    if(!inBattle()&&state.turnLocked&&index!==state.activeRat) return setNotice("This Rat’s turn is underway — finish it with Recover selected.");
    // Red is placed on a Rat other than the active one, so being able to
    // switch afterwards would make that placement a free look.
    if(!inBattle()&&state.turnRedPlaced&&index!==state.activeRat)
      return setNotice("Red has been placed for this turn — press Reset turn to choose a different Rat.");
    state.activeRat=index;
    if(state.current?.e===10) {state.red.holder=index;state.red.zone="available";state.red.selected=false;}
    save();render();
  }
  function strongerIndex(options) {
    const top=Math.max(...options.map(cardValue));
    const tied=options.map((card,i)=>cardValue(card)===top?i:-1).filter(i=>i>=0);
    return tied[Math.floor(Math.random()*tied.length)];
  }

  function effectAction(action) {
    const c=state.current;
    if(!c) return;
    const rat=active();
    if(action==="flip" && c.e===0 && !c.flipped) {rat.side=rat.side==="front"?"back":"front";c.flipped=true;state.notice=`${rat.name} flipped to Side ${rat.side==="front"?"A":"B"}.`;}
    if(action==="fine-fallback" && c.e===1 && !c.phase && !c.usedFallback) {if(canCommitColor("yellow"))return setNotice("A Yellow die is available to commit.");c.usedFallback=true;c.delta++;state.notice="Yellow was unavailable. Target increased by 1.";}
    if(action==="load-redraw" && c.e===5 && !c.phase) {if(canCommitColor("purple"))return setNotice("A Purple die is available to commit.");state.discard.push(cards[c.e].name,...c.options.map(cardName));state.current=null;state.notice="Load-Bearing Trial discarded. Revealed Upgrades were replaced.";save();draw();return;}
    if(action==="rapid-fallback" && c.e===7 && !c.phase && !c.usedFallback && c.options.length>1) {if(canCommitColor("green"))return setNotice("A Green die is available to commit.");const discarded=c.options.splice(strongerIndex(c.options),1)[0];state.discard.push(cardName(discarded));c.usedFallback=true;state.notice=`${cardName(discarded)} was discarded. Continue with the remaining Upgrade.`;}
    if(action==="exclude" && c.e===14 && !c.phase && !c.blocked) {const available=rat.dice.filter(d=>d.zone==="available");if(!available.length)return setNotice("No personal die is available to exclude.");const die=available[Math.floor(Math.random()*available.length)];c.blocked=die.id;die.selected=false;state.notice=`${rat.name}'s ${die.color} die was randomly excluded.`;}
    if(action==="peek" && c.e===6 && !c.peeked && c.committed.includes("blue")) {c.peeked=true;state.notice=state.deck.length?`Next Experiment: ${cards[state.deck[state.deck.length-1]].name} · Target ${cards[state.deck[state.deck.length-1]].target}. It remains on top.`:"The Experiment deck is empty.";}
    if(action==="contain" && c.e===15 && !c.phase && !c.reduced) {
      const yellow=rat.dice.find(d=>d.color==="yellow"&&d.zone==="available");
      if(!yellow) return setNotice("The active Rat needs an available Yellow die for this option.");
      c.reduced=true;c.delta=-2;
      if(faceValue(rollFace("yellow"))) {
        const blue=rat.dice.find(d=>d.color==="blue"&&d.zone==="available") || personalDice().find(d=>d.color==="blue"&&d.zone==="available");
        if(blue) {blue.zone="banished";blue.selected=false;state.notice=`Target reduced by 2; ${state.rats[Number(blue.id.split("-")[1])].name}'s Blue die was banished.`;}
        else state.notice="Target reduced by 2; the Yellow roll hit, but no available Blue die could be banished.";
      } else {yellow.zone="banished";yellow.selected=false;state.notice="Target reduced by 2; the Yellow roll missed, so that Yellow die was banished.";}
    }
    if(action==="method" && c.e===18 && !c.phase && !c.reduced) {c.reduced=true;c.delta=-cards[c.e].target;state.notice="Target reduced to 0. Success will keep the weaker Upgrade and Splice the stronger one.";}
    if(action==="swap" && c.e===17 && canSucceed()) {
      const from=Number($("batSwapFrom")?.value),to=Number($("batSwapTo")?.value);
      if(Number.isInteger(from)&&Number.isInteger(to)&&rat.upgrades[from]&&c.options[to]?.type==="u") {c.swap={from,to};state.notice=`On success, ${cardName(rat.upgrades[from])} will be swapped for ${cardName(c.options[to])}. Keep a different revealed Upgrade as the normal reward.`;}
    }
    save();render();
  }

  function chooseDie(id) {
    const c=state.current;
    const die=personalDice().find(d=>d.id===id);
    if(!die) return;
    if(c?.blocked===id) return setNotice("That die is excluded by Reagent Exclusion Trial.");
    if(die.zone==="available"||die.zone==="rolled"){
      const owner=Number(die.id.split("-")[1]);
      // A Rat may lend only one die per Experiment, so a pick in someone
      // else's pool replaces the previous pick rather than adding to it.
      if(!die.selected&&die.zone==="available"&&!inBattle()&&owner!==state.activeRat){
        state.rats[owner].dice.forEach(d=>{
          if(d!==die&&d.selected&&d.zone==="available"){
            d.selected=false;
            // Dropping the die that was actually lent releases the lend too,
            // but only while it is still in hand - once thrown it is committed.
            if(c&&c.borrowedId===d.id) c.borrowedId=null;
          }
        });
      }
      die.selected=!die.selected;
    }
    else if(c?.phase===1 && c.rolled.includes(id) && die.face==="" && c.e!==16) die.selected=!die.selected;
    else if(die.zone==="exhausted"){
      // Only REC-worth of dice can come back, so do not let the player
      // select more than that - the extras used to be silently ignored.
      if(!die.selected){
        const owner=Number(die.id.split("-")[1]), inB=inBattle();
        if(inB||owner===state.activeRat){
          // The battle pool is shared; in an Experiment a Rat recovers only
          // its own dice, and Mottle's Specimen bonus may be in play.
          const bonus=inB?2:recBonusFor(state.activeRat);
          const cap=RAT_REC[state.activeRat]+bonus;
          const pool=inB?personalDice():state.rats[owner].dice;
          const chosen=pool.filter(d=>d.selected&&d.zone==="exhausted").length;
          if(chosen>=cap) return setNotice(`Only ${cap} ${cap===1?"die":"dice"} can be recovered (REC ${RAT_REC[state.activeRat]}${bonus?` + ${bonus}`:""}). Deselect one first.`);
        }
      }
      die.selected=!die.selected;
    }
    save();render();
  }

  function validateRoll(dice,redSelected) {
    const c=state.current;
    if(!c) return "Reveal an Experiment first.";
    if(c.phase>=maxPhase(c)) return "No Strategy phase remains for this Experiment.";
    if(c.e===0&&!c.flipped) return "Flip the active Lab Rat first.";
    if(redBlocks()) return "Place the Red die on a Rat other than the active one before committing.";
    if(c.e===14&&!c.blocked) return "Randomly exclude an available die first.";
    if(c.e===10&&redSelected) return "Red cannot be used for this Experiment.";
    if(redSelected&&state.red.holder!==state.activeRat) return "Only the active Rat holding Red can commit it.";
    if(c.e===12&&c.phase===1&&dice.some(d=>d.zone==="available")) return "No additional dice may be committed in the second Strategy phase.";
    const borrowed=dice.filter(d=>!d.id.startsWith(`rat-${state.activeRat}-`));
    if(borrowed.some(d=>d.id!==c.borrowedId)) return "Use the Lend button on that Rat to borrow its die.";
    if(borrowed.length>1) return "Borrow at most one die from another Rat for the whole Experiment.";
    if(c.e===11&&borrowed.length) return "Borrowing is prohibited by this Experiment.";
    const allowed=[colors,colors.slice(1),colors.slice(2),colors.slice(3)][Math.min(active().upgrades.length,3)];
    if(borrowed.some(d=>!allowed.includes(d.color))) return "That borrowed color is not allowed with this Rat's Upgrade count.";
    if(c.e===9&&c.committed.length+dice.filter(d=>d.zone==="available").length+(redSelected?1:0)>2) return "Only two dice may be committed to this Experiment.";
    return "";
  }

  function roll() {
    const c=state.current;
    const dice=selected().filter(d=>d.zone!=="exhausted");
    // A reroll replaces the face of an unbanked die rather than adding a new one.
    if(c&&c.phase>0) c.pending=(c.pending||[]).filter(id=>!dice.some(x=>x.id===id));
    const redSelected=state.red.selected&&state.red.zone==="available";
    // Red is a committed die, so a later Strategy roll may rethrow it.
    const redAgain=state.red.selected&&state.red.zone==="rolled";
    const error=validateRoll(dice,redSelected);
    if(error) return setNotice(error);
    if(!dice.length&&!redSelected&&!redAgain) {if(!c.phase){c.phase=1;state.notice="No dice committed. You may resolve this as a failure.";save();render();}return;}
    let gained=0, forced=0;
    for(const die of dice) {
      const isNew=die.zone==="available";
      die.face=rollFace(die.color);
      if(c.e===13&&c.phase===0&&["purple","blue"].includes(die.color)&&faceValue(die.face)) {die.face=rollFace(die.color);forced++;}
      gained+=faceValue(die.face);
      die.zone="rolled";die.selected=false;
      if(isNew) {c.committed.push(die.color);c.rolled.push(die.id);if(!die.id.startsWith(`rat-${state.activeRat}-`))c.borrowedId=die.id;}
    }
    if(redSelected){state.red.face=rollFace("red");state.red.zone="rolled";state.red.selected=false;c.committed.push("red");gained+=faceValue(state.red.face);}
    else if(redAgain){state.red.face=rollFace("red");state.red.selected=false;gained+=faceValue(state.red.face);}
    c.pending=(c.pending||[]).concat(dice.map(x=>x.id)).concat(redSelected?["red"]:[]);
    c.phase++;state.turnLocked=true;
    const tally=rollTally(redSelected||redAgain?dice.concat([state.red]):dice);
    state.notice=`Strategy phase ${c.phase}: ${tallyText(tally)}${forced?`; ${forced} Purple/Blue hit${forced===1?"":"s"} rerolled by Reliability Trial`:""}. Banked ${c.successes} / ${target()} \u2014 add the dice you want to keep.`;
    save();render();
  }

  function useRatAbility(index,kind){
    const c=state.current;
    if(!c) return setNotice("Reveal an Experiment first.");
    if(index!==state.activeRat) return setNotice("Only the active Rat may use its ability.");
    const uses=ratUses(c),rat=state.rats[index];
    if(uses[kind]) return setNotice(`${ratAbility(index).name} has already been used this Experiment.`);
    if(kind==="prepared"){
      if(state.lastRat===index) return setNotice("Prepared needs a different Rat to have been active last turn.");
      if(c.phase>0) return setNotice("Prepared is used before committing dice.");
      const die=rat.dice.find(d=>d.selected&&d.zone==="exhausted")||rat.dice.find(d=>d.zone==="exhausted");
      if(!die) return setNotice(`${rat.name} has no exhausted die to recover.`);
      die.zone="available";die.face="";die.selected=false;uses.prepared=true;
      return setNotice(`Prepared: ${rat.name} recovered 1 ${die.color} die before committing.`);
    }
    const want=kind==="juryRig"?0:1;
    const die=rat.dice.find(d=>d.selected&&d.zone==="rolled"&&faceValue(d.face)===want)
      ||rat.dice.find(d=>d.zone==="rolled"&&faceValue(d.face)===want);
    if(!die) return setNotice(kind==="juryRig"?"Select a rolled miss to reroll.":"Select a rolled basic hit to reroll.");
    const before=faceValue(die.face),old=die.face,face=rollFace(die.color),after=faceValue(face);
    if(kind==="fineTuning"&&after<before){
      uses.fineTuning=true;
      return setNotice(`Fine Tuning: the reroll missed, so ${rat.name} keeps the original hit.`);
    }
    die.face=face;c.successes+=after-before;uses[kind]=true;
    setNotice(`${ratAbility(index).name}: rerolled a ${old?"hit":"miss"} into ${after?`${after} success${after===1?"":"es"}`:"a miss"}. Total ${c.successes} / ${target()}.`);
  }
  function rollZero(index){
    const c=state.current;
    if(!c) return setNotice("Reveal an Experiment first.");
    state.activeRat=index;
    const error=validateRoll([],false);
    if(error) return setNotice(error);
    personalDice().forEach(d=>{d.selected=false;});state.red.selected=false;
    c.phase++;state.turnLocked=true;
    state.notice=`${state.rats[index].name} rolled zero dice. Strategy phase ${c.phase}.`;
    save();render();
  }

  function canSucceed() {
    const c=state.current;
    if(!c||!c.phase||totalSuccesses()<target()) return false;
    if(c.e===1&&!c.usedFallback&&!c.committed.includes("yellow")) return false;
    if(c.e===5&&!c.committed.includes("purple")) return false;
    if(c.e===7&&!c.usedFallback&&!c.committed.includes("green")) return false;
    if(c.e===8&&new Set(c.committed).size<3) return false;
    return true;
  }

  function resolve(choice) {
    const c=state.current;
    if(!c) return;
    // Anything still loose is applied now. A player who did not press Add
    // selected dice has not thrown those successes away - the printed rule
    // counts the roll, not the bookkeeping.
    if(unbankedScoring().length){
      const loose=unbankedScoring().map(id=>({id,die:pendingDie(id)}));
      c.successes+=loose.reduce((n,x)=>n+faceValue(x.die?.face),0);
      c.banked=(c.banked||[]).concat(loose.map(x=>({
        id:x.id, color:x.id==="red"?"red":x.die?.color, face:x.die?.face})));
      c.pending=(c.pending||[]).filter(id=>!loose.some(x=>x.id===id));
    }
    if(choice!==null&&!canSucceed()) return setNotice("The roll has not met this Experiment's Target and commitment requirements.");
    if(choice!==null&&!c.options[choice]) return;
    if(choice!==null) {
      state.notice="";
      let kept=c.options[choice];
      if(c.e===18&&c.reduced) {
        const values=c.options.map(cardValue), high=Math.max(...values), low=Math.min(...values);
        if(high!==low) kept=c.options[values.indexOf(low)];
        else kept=c.options[choice];
        const spliced=c.options[high!==low?values.indexOf(high):(choice===0?1:0)];
        recordSplice(spliced);
        state.notice=`${cardName(spliced)} was Spliced into the Prototyrant. `;
      }
      if(c.e===17&&c.swap) {
        if(c.swap.to===choice) return setNotice("Choose a different Upgrade for the normal success reward, or clear the swap.");
        const old=active().upgrades[c.swap.from];
        active().upgrades[c.swap.from]=c.options[c.swap.to];
        c.options[c.swap.to]=old;
      }
      if(active().upgrades.length<3) active().upgrades.push(kept);
      if(c.e===19) state.health=Math.max(0,state.health-2);
      state.notice+=`Success: ${active().name} ${active().upgrades.includes(kept)?"kept":"could not keep"} ${cardName(kept)}.${c.e===19?" Prototyrant Health reduced by 2.":""}`;
    } else {
      const spliced=c.options[strongerIndex(c.options)];
      recordSplice(spliced);
      state.notice=`Failure: ${cardName(spliced)} was Spliced into the Prototyrant.`;
    }
    // Step 8. Now that the Experiment is resolved the rolled dice exhaust -
    // except a borrowed die, which stays in the active Rat's rolled area
    // until its return check is rolled.
    exhaustRolled(c.borrowedId);
    if(c.borrowedId) state.returnCheck={dieId:c.borrowedId,borrower:state.activeRat};
    // Recovery bonuses are spent on this turn's Recover selected.
    let bonus=0;
    if(specimenShown(c)&&ratHas(state.activeRat,"Experimental Subject"))bonus+=1;
    if(choice!==null&&ratHas(state.activeRat,"Specimen Adaptation"))
      bonus+=active().upgrades.filter(card=>card.type==="s").length;
    state.recBonus=bonus?{rat:state.activeRat,n:bonus}:null;
    state.lastRat=state.activeRat;
    state.discard.push(cards[c.e].name,...c.options.filter(card=>!state.rats.some(rat=>rat.upgrades.includes(card))&&!state.spliceCards.includes(card)).map(cardName));
    state.rounds++;state.current=null;
    personalDice().forEach(d=>d.selected=false);state.red.selected=false;
    const outcome=state.notice;
    if(state.splices<5&&state.deck.length&&state.upgradeDeck.length>=2){draw();state.notice=`${outcome} ${state.notice}`;}
    save();render();
  }

  function previewCard(button) {
    if(button.dataset.batHeld){const [r,c]=button.dataset.batHeld.split(":").map(Number);return state.rats[r]?.upgrades[c];}
    if(button.dataset.batSplice!==undefined)return state.spliceCards[Number(button.dataset.batSplice)];
    return null;
  }
  let heldPreview=null;
  function showHeldPreview(target) {
    const button=target.closest?.("[data-bat-held],[data-bat-splice]");if(!button)return;
    const card=previewCard(button);if(!card)return;
    if(!heldPreview){heldPreview=document.createElement("div");heldPreview.className="suite-card portrait bat-hover-preview";heldPreview.setAttribute("role","img");document.body.append(heldPreview);}
    setSprite(heldPreview,card);
    heldPreview.setAttribute("aria-label",`${cardName(card)} card face`);
    heldPreview.hidden=false;
    const rect=button.getBoundingClientRect(),width=heldPreview.getBoundingClientRect().width,height=width*7/5;
    let left=rect.right+12;if(left+width>innerWidth-12)left=Math.max(12,rect.left-width-12);
    heldPreview.style.left=`${left}px`;
    heldPreview.style.top=`${Math.max(12,Math.min(rect.top,innerHeight-height-12))}px`;
  }
  function hideHeldPreview(){if(heldPreview)heldPreview.hidden=true;}

  function setSprite(el,card) {
    if(!card||card.type==="legacy"){el.removeAttribute("style");el.classList.add("placeholder-card");el.innerHTML=`<span>${card?"Unknown Upgrade":"Upgrade"}</span>`;return;}
    const specimen=card.type==="s",cols=specimen?8:10,rows=specimen?1:2;
    const col=card.i%cols,row=Math.floor(card.i/cols);
    el.classList.remove("placeholder-card");el.innerHTML="";
    el.style.backgroundImage=`url('assets/${specimen?"BAT_Specimens_TTS.png":"BAT_Upgrades_TTS.png"}?v=fonts-1')`;
    el.style.backgroundSize=`${cols*100}% ${rows*100}%`;
    el.style.backgroundPosition=`${cols===1?0:col/(cols-1)*100}% ${rows===1?0:row/(rows-1)*100}%`;
  }

  function ratAbilityBlock(i){
    const ability=ratAbility(i);if(!ability)return "";
    const c=state.current,uses=c?ratUses(c):{},mine=state.activeRat===i&&!!c;
    const button=(kind,label,ready)=>mine&&ready&&!uses[kind]
      ? `<button data-rat-ability="${i}:${kind}">${label}</button>` : "";
    const actions=button("juryRig","Reroll a miss",ability.name==="Jury-Rig")
      +button("fineTuning","Reroll a basic hit",ability.name==="Fine Tuning")
      +button("prepared","Recover 1 die",ability.name==="Prepared"&&state.lastRat!==i&&c?.phase===0);
    const spent=mine&&(uses.juryRig&&ability.name==="Jury-Rig"||uses.fineTuning&&ability.name==="Fine Tuning"||uses.prepared&&ability.name==="Prepared");
    return `<div class="bat-rat-ability"><h4>${ability.name}${spent?" · used":""}</h4><p>${ability.text}</p>`
      +(actions?`<div class="bat-rat-ability-actions">${actions}</div>`:"")+`</div>`;
  }
  function renderRats() {
    const host=$("batRats");host.innerHTML="";
    state.rats.forEach((rat,i)=>{
      const c=state.current;
      const dieButton=die=>`<button class="rat-die ${die.color} ${die.zone} ${die.selected?"selected":""} ${c?.blocked===die.id?"blocked":""} ${c&&c.phase>0&&isPending(die.id)?"eligible-reroll":""} ${c?.borrowedId===die.id||(die.selected&&!die.id.startsWith(`rat-${state.activeRat}-`))?"borrowed":""}" data-bat-die="${die.id}" title="${die.color} · ${die.zone}${c?.borrowedId===die.id?" · borrowed by "+active().name:""}${die.zone==="rolled"||die.face?` · ${faceLabel(die.face)}`:""}"><span class="face">${die.face||""}</span><span class="tiny">${die.color[0].toUpperCase()}</span></button>`;
      const available=rat.dice.filter(d=>d.zone==="available").sort(byColor).map(dieButton).join("");
      const isActive=state.activeRat===i;
      const exhausted=rat.dice.filter(d=>d.zone==="exhausted").sort(byColor).map(dieButton).join("");
      // A borrowed die is shown with the Rat that rolled it, not its owner.
      // Still the borrowed die after the Experiment resolves, while its
      // return check is outstanding.
      const borrowedId=c?.borrowedId||state.returnCheck?.dieId||null;
      const borrowedDie=borrowedId?personalDice().find(x=>x.id===borrowedId):null;
      const isBanked=id=>(c?.banked||[]).some(b=>b.id===id);
      const mineRolled=rat.dice.filter(d=>d.zone==="rolled"&&d.id!==borrowedId&&!isBanked(d.id));
      if(isActive&&borrowedDie&&borrowedDie.zone==="rolled"&&!isBanked(borrowedDie.id)) mineRolled.push(borrowedDie);
      const rolled=mineRolled.sort(byColor).map(dieButton).join("");
      const redRolled=state.red.zone==="rolled"&&!isBanked("red")?`<button class="rat-die red rolled ${state.red.selected?"selected":""} ${c&&c.phase>0&&isPending("red")?"eligible-reroll":""}" data-bat-red="1" title="Communal Red die · rolled · ${faceLabel(state.red.face)}"><span class="face">${state.red.face||""}</span><span class="tiny">R</span></button>`:"";
      const red=state.red.holder===i&&state.red.zone==="available"?`<button class="rat-die red ${state.red.selected?"selected":""} ${c?.e===10?"blocked":""}" data-bat-red="1" title="Communal Red die"><span class="face">${state.red.face||""}</span><span class="tiny">R</span></button>`:"";
      const held=rat.upgrades.map((card,j)=>{
        const targetable=inBattle()&&!card.tapped;
        const targetBtn=targetable?`<button class="bat-owned-target ${state.battle&&state.battle.hitTarget===String(j)?"on":""}" data-hit-target="${j}" title="Send the Tyrant’s hits here">⊕</button>`:"";
        // In battle the active Rat taps an Upgrade to use its printed effect for the round.
        const useBtn=inBattle()&&isActive?`<button class="bat-owned-use ${card.tapped?"used":""}" data-bat-held="${i}:${j}">${card.tapped?"Used":"Use"}</button>`:"";
        return `<div class="bat-owned-item ${card.tapped?"tapped":""}">`
          +`<button class="bat-owned-name" data-bat-held="${i}:${j}" aria-pressed="${!!card.tapped}" title="${escape(cardName(card))} · Value ${cardValue(card)}${inBattle()?"":`: tap to mark ${card.tapped?"ready":"used"}`}">${escape(cardName(card))}</button>`
          +useBtn+targetBtn
          +`<button class="bat-owned-drop" data-bat-drop="${i}:${j}" aria-label="Destroy ${escape(cardName(card))}" title="Destroy ${escape(cardName(card))}">×</button></div>`;
      }).join("");
      const b=state.battle;
      const tgtIdx=b&&b.attackRat!=null?b.attackRat:state.activeRat;
      const hitsPrompt=inBattle()&&b&&b.tyrantHits>0&&tgtIdx===i
        ? `<button class="bat-apply-hits" data-apply-hits="1">Apply ${b.tyrantHits} ${b.tyrantHits===1?"hit":"hits"} to ${escape(b.hitTarget!=null&&rat.upgrades[Number(b.hitTarget)]?cardName(rat.upgrades[Number(b.hitTarget)]):rat.name)}</button>` : "";
      const box=document.createElement("article");box.className=`bat-rat ${state.activeRat===i?"active":"idle"} ${rat.down?"down":""} ${rat.hp===1&&inBattle()?"wounded":""}`;box.dataset.batActive=i;
      const takeRed=canTakeRed(i);
      box.innerHTML=`<div class="bat-rat-head"><h3>${rat.name}${isActive&&!inBattle()?` <span class="bat-active-tag">(Active)</span>`:""}</h3>${inBattle()?"":`<button data-move-red="${i}" class="bat-move-red${takeRed?due("movered"):""}" ${takeRed?"":"disabled"}>Move Red here</button>`}<button data-rat-side="${i}">Side ${rat.side==="front"?"A":"B"}</button>${inBattle()?"":`<button data-rat-rollzero="${i}" ${isActive?"":"disabled"}>Roll zero dice</button>`}</div><div class="bat-rat-card-wrap"><div class="suite-card landscape bat-rat-card"></div>${hitsPrompt}</div>${inBattle()?"":ratAbilityBlock(i)}<div class="bat-held-section"><h4>Earned Upgrades <span>${rat.upgrades.length} / 3</span></h4><div class="bat-owned-row">${held||'<span class="bat-empty-cards">No Upgrades yet</span>'}</div></div><div class="bat-dice-summary"><span class="bat-hp-edit"><button data-rat-hp="${i}" data-delta="-1" ${rat.hp<=0?"disabled":""} aria-label="Lower ${escape(rat.name)}'s Health">\u2212</button><strong>${rat.hp} HP</strong><button data-rat-hp="${i}" data-delta="1" aria-label="Raise ${escape(rat.name)}'s Health">+</button>${rat.down?`<em class="bat-down-tag">knocked out</em>`:""}</span><span>${rat.dice.filter(d=>d.zone==="banished").length} Banished</span></div>${inBattle()?"":`<div class="rat-rolled-zone"><h4>Rolled · held until the Experiment ends</h4><div class="rat-dice-row">${state.activeRat===i?redRolled:""}${rolled}${rolled||(state.activeRat===i&&redRolled)?"":'<span class="rat-zone-empty">No dice rolled</span>'}${borrowCheckBlock(i)}</div></div><div class="rat-dice-zones"><div class="rat-dice-zone"><h4>Available</h4><div class="rat-dice-row">${red}${available}</div></div><div class="rat-dice-zone"><h4>Exhausted${isActive?(()=>{const bonus=recBonusFor(i),cap=RAT_REC[i]+bonus,n=rat.dice.filter(d=>d.selected&&d.zone==="exhausted").length;return ` · ${n} of ${cap} selected to recover`;})():""}</h4><div class="rat-dice-row">${exhausted}</div></div></div>`}${inBattle()?"":`<div class="bat-rat-actions"><button data-rat-roll="${i}" class="primary${isActive?due("roll"):""}" ${isActive?"":"disabled"}>Roll selected</button><button data-bat-allocate="1" class="${isActive?due("allocate").trim():""}" ${isActive&&(state.current?.pending||[]).length?"":"disabled"}>Add selected dice to the Experiment</button><button data-rat-recover="${i}" class="${isActive?dueRed("recover").trim():""}" ${isActive?"":"disabled"}>Recover selected</button>${isActive&&redBlocks()?`<span class="bat-blocked-why">Place the Red die first</span>`:""}</div>`}${inBattle()||isActive?"":(()=>{
        const c=state.current;
        const lentDie=c&&c.borrowedId?rat.dice.find(x=>x.id===c.borrowedId):null;
        // Returnable until it is thrown - which is not the same as phase 0,
        // now that a die may be borrowed between Strategy rolls.
        if(lentDie)return `<div class="bat-borrow-row"><span class="bat-borrow-note">Lent to ${active().name}</span>${lentDie.zone==="available"?`<button data-bat-return="1">Return die</button>`:`<span class="bat-borrow-note">Rolled \u2014 it can only come back through the return check.</span>`}</div>`;
        const picked=rat.dice.filter(x=>x.selected&&x.zone==="available");
        const blocked=borrowProblem(i,picked.length===1?picked[0]:null);
        return `<div class="bat-borrow-row"><button data-bat-borrow="${i}" ${blocked?"disabled":""}>Lend selected die to ${active().name}</button>${blocked?`<span class="bat-borrow-note">${blocked}</span>`:""}</div>`;
      })()}`;
      const sprite=box.querySelector(".bat-rat-card"),col=i;
      sprite.style.backgroundImage=`url('assets/${rat.side==="front"?"BAT_Rats_TTS.png":"BAT_Rats_TTS_back.png"}?v=fonts-1')`;
      sprite.style.backgroundSize="400% 100%";sprite.style.backgroundPosition=`${col/3*100}% 0`;
      
      host.appendChild(box);
    });
  }

  // Buff HP no longer equals the Specimen count; it is tuned separately.
  const BUFF_BY_DIFFICULTY={Easy:3,Standard:4,Hard:7,Nobulous:11};
  const TYRANT_NEED=[["purple",2],["blue",2],["green",1],["yellow",1]];
  const tyrantDice = () => personalDice().filter(d=>d.zone==="tyrant").sort(byColor);
  // Damage is whatever is showing in the Rolled area right now, so rerolls cannot double-count.
  function rolledDamage(){
    let n=personalDice().filter(d=>d.zone==="rolled").reduce((sum,d)=>sum+faceValue(d.face),0);
    if(state.red.zone==="rolled") n+=faceValue(state.red.face);
    return n;
  }

  // Prefer surviving dice; fall back to the banished pile when a color has run out.
  function drawTyrantDice(){
    TYRANT_NEED.forEach(([color,n])=>{
      const held=personalDice().filter(d=>d.color===color&&d.zone==="tyrant").length;
      const alive=personalDice().filter(d=>d.color===color&&d.zone!=="banished"&&d.zone!=="tyrant");
      const gone=personalDice().filter(d=>d.color===color&&d.zone==="banished");
      for(let k=held;k<n;k++){const die=alive.shift()||gone.shift();if(die){die.zone="tyrant";die.selected=false;die.face="";}}
    });
  }

  // The 7 Tyrant Attack cards, in BAT_TyrantAttacks_TTS.png order (7 x 1).
  const ATTACK_NAMES=["Overwhelming Mass","Adaptive Strike","Predatory Instinct",
    "Spliced Reflexes","Terrifying Roar","Crushing Blow","Unstable Growth"];
  const ATTACK_TEXT=["+3 damage",
    "hits the next Rat clockwise",
    "hits the Rat holding the most Upgrade Value",
    "+1 damage per surviving Splice",
    "no damage; exhaust 1 die from the pool",
    "1 damage goes straight to Health",
    "if the target survives, attacks again with 2 dice"];
  // The color dot on each Attack card. The top card of the Attack discard
  // sets the color the attacking Rat must commit.
  const ATTACK_COLORS=["green","blue","yellow","green","yellow","green","yellow"];
  // The commit color now in force: the last card revealed, or the card
  // flipped at the start of the battle before the Tyrant has attacked.
  function commitColor(b){
    if(!b) return null;
    const top=(b.attack!=null)?b.attack:b.startFlip;
    return top!=null?ATTACK_COLORS[top]:null;
  }
  // Does this set of committed dice satisfy the commit color? One die of it,
  // or - when none of that color is available at all - two dice of one other
  // color. Red never counts.
  function colorCheck(b,dice){
    const need=commitColor(b);
    if(!need) return {ok:true};
    if(dice.some(d=>d.color===need)) return {ok:true,need};
    const haveAny=personalDice().some(d=>d.zone==="available"&&d.color===need);
    if(haveAny) return {ok:false,need,why:`commit at least one ${need} die`};
    const counts={};dice.forEach(d=>{counts[d.color]=(counts[d.color]||0)+1;});
    if(Object.values(counts).some(n=>n>=2)) return {ok:true,need,pair:true};
    return {ok:false,need,why:`no ${need} die is available, so commit two dice of one other color`};
  }
  // Which Rat this attack lands on, honoring the retargeting cards.
  function attackTarget(b){
    const live=state.rats.filter(r=>!r.down);
    if(!live.length) return active();
    if(b&&b.attack===1){                       // Adaptive Strike
      for(let step=1;step<=state.rats.length;step++){
        const nxt=state.rats[(state.activeRat+step)%state.rats.length];
        if(!nxt.down) return nxt;
      }
    }
    if(b&&b.attack===2){                       // Predatory Instinct
      return live.reduce((best,r)=>
        r.upgrades.reduce((t,c)=>t+cardValue(c),0) > best.upgrades.reduce((t,c)=>t+cardValue(c),0) ? r : best, live[0]);
    }
    // "Unless the card says otherwise the attack lands on the attacking Rat"
    // - and that is never a Rat that has already been knocked out.
    const k=liveRatFrom(state.activeRat);
    return k>=0?state.rats[k]:active();
  }

  function ensureBattle() {
    if(state.splices<5){state.battle=null;return null;}
    if(state.battle&&tyrantDice().length<6){drawTyrantDice();save();}
    if(state.battle){
      keepAttackerStanding();
      const t=state.battle.attackRat;
      if(t!=null&&state.rats[t]?.down){
        const k=liveRatFrom(t);state.battle.attackRat=k>=0?k:null;
      }
    }
    if(state.battle&&!Array.isArray(state.battle.attackDeck)){
      state.battle.attackDeck=shuffle([...Array(ATTACK_NAMES.length).keys()]);
      state.battle.attackDiscard=[];state.battle.attack=null;save();}
    if(state.battle&&state.battle.startFlip==null&&state.battle.attack==null&&Array.isArray(state.battle.attackDeck)&&state.battle.attackDeck.length){
      state.battle.startFlip=state.battle.attackDeck.pop();state.battle.attackDiscard.push(state.battle.startFlip);save();}
    if(!state.battle){
      const buff=BUFF_BY_DIFFICULTY[state.difficulty]??5;
      const order=shuffle([...Array(5).keys()]);
      state.battle={turn:"rats",buffHp:buff,buffMax:buff,order,hp:order.map(i=>cardValue(state.spliceCards[i])),max:order.map(i=>cardValue(state.spliceCards[i])),
        attackDeck:shuffle([...Array(ATTACK_NAMES.length).keys()]),attackDiscard:[],attack:null};
      // The Experiment phase's turn flags end here. The battle runs its own
      // turn structure (battle.turn / battle.needRec), and leaving turnLocked
      // set stranded the attacker choice behind a Recover button that the
      // battle layout does not even have.
      state.turnLocked=false;state.turnRedPlaced=false;
      // Flip the top Attack card to start the discard and supply the first color.
      state.battle.startFlip=state.battle.attackDeck.pop();
      state.battle.attackDiscard.push(state.battle.startFlip);
      drawTyrantDice();
      save();
    }
    // "Sweep every personal die still in the game - from all four Rats,
    // available AND exhausted - into one shared battle pool, all available.
    // Banished dice stay gone." The Tyrant's six are out of the supply by
    // now and are left alone.
    // Flagged rather than done inline above, so a battle that began before
    // this existed still gets its sweep - otherwise those games keep the
    // dice the Experiment phase left exhausted, for good.
    if(!state.battle.swept){
      personalDice().forEach(d=>{
        if(d.zone!=="banished"&&d.zone!=="tyrant"){d.zone="available";d.face="";d.selected=false;}
      });
      state.battle.swept=true;
      save();
    }
    return state.battle;
  }

  // The Health die sits on the leftmost card still standing.
  function frontSlot(b) {
    if(b.buffHp>0) return "buff";
    const i=b.hp.findIndex(v=>v>0);
    return i<0?"tyrant":i;
  }

  // One die runs the whole Tyrant: it sits on the card being damaged and
  // shows what that card has left, then moves right and is set to the next
  // card's Value.
  const healthDie = n =>
    `<span class="bat-buff-die" title="Health die \u00b7 ${n} left on this card">${n}</span>`;
  // The Buff HP card is a 15-space track with the Health die sitting on the
  // current value - 3 across and 5 down, counting DOWN from 15 at the
  // top-left, exactly as generator/build_bat.py prints it. The four gold
  // spaces are the difficulty starts.
  const BUFF_GOLD = new Set([11, 7, 4, 3]);
  function buffTrack(hp){
    let out="";
    for(let n=15;n>=1;n--){
      const here=n===hp;
      out+=`<span class="bat-buff-space${BUFF_GOLD.has(n)?" gold":""}${here?" marked":""}">`
        +(here?healthDie(n):n)
        +`</span>`;
    }
    return `<div class="bat-buff-track" role="img" aria-label="Buff HP ${hp} of 15">${out}</div>`;
  }
  function trackCell(slot,card,hp,max,front,editable) {
    const dead=hp<=0;
    return `<div class="bat-track-cell ${dead?"destroyed":""} ${front===slot?"front":""}">`
      +(slot==="buff"
        ? buffTrack(hp)
        : `<div class="suite-card portrait bat-track-art" data-track-art="${slot}"></div>`
          +(front===slot&&hp>0?`<div class="bat-track-die">${healthDie(hp)}</div>`:""))
      +`<div class="bat-track-name">${escape(card?cardName(card):"Buff HP")}</div>`
      +`<div class="bat-hp-selector"><button data-track-hp="${slot}" data-delta="-1" ${!editable||hp<=0?"disabled":""} aria-label="Reduce">−</button>`
      +`<strong>${hp} / ${max}</strong>`
      +`<button data-track-hp="${slot}" data-delta="1" ${!editable||hp>=max?"disabled":""} aria-label="Increase">+</button></div>`
      +`<div class="bat-track-state">${dead?"Destroyed":front===slot?"Taking damage":"Intact"}</div></div>`;
  }

  // Damage runs Buff HP, then each Splice in order, then Health.
  function applyTyrantDamage(n){
    const b=state.battle;if(!b)return 0;
    let left=n;
    if(b.buffHp>0){const hit=Math.min(b.buffHp,left);b.buffHp-=hit;left-=hit;}
    for(let i=0;i<b.hp.length&&left>0;i++){if(b.hp[i]>0){const hit=Math.min(b.hp[i],left);b.hp[i]-=hit;left-=hit;}}
    if(left>0){state.health=Math.max(0,state.health-left);}
    return n;
  }

  // The attacking Rat's turn as three steps in the pool header, mirroring the
  // Tyrant's: roll (and reroll misses), resolve the damage, then recover.
  function renderRatSteps(b,committed,rat){
    const host=$("batRatSteps");if(!host)return;
    if(!b||b.turn!=="rats"){host.innerHTML=`<span class="bat-track-state">The Tyrant is acting — the Rats' steps unlock on their turn.</span>`;return;}
    const anyRolled=personalDice().some(d=>d.zone==="rolled")||state.red.zone==="rolled";
    const rerollPick=personalDice().filter(d=>d.zone==="rolled"&&d.selected).length
      +(state.red.zone==="rolled"&&state.red.selected?1:0);
    const dmg=rolledDamage();
    const step=b.needRec?3:anyRolled?2:1;
    // Step 1 stays live (not dimmed) while rerolls remain after the first roll.
    const cls=n=>`bat-step ${step===n?"now":(n===1&&step===2&&!spent)?"":step>n?"done":""}`;
    // Step 1 doubles as the reroll: select misses among the rolled dice.
    const max=strFor(rat),used=b.ratRolls||0,spent=used>=max;
    const rollLabel=b.needRec
      ? `Roll Committed Dice for ${escape(rat.name)} · STR ${max}`
      : spent
        ? `No Rerolls Left · STR ${max}/${max}`
        : anyRolled
          ? `Reroll ${rerollPick||""} Selected ${rerollPick===1?"Die":"Dice"} for ${escape(rat.name)} · STR ${used+1}/${max}`.replace("  "," ")
          : `Roll Committed Dice for ${escape(rat.name)} · STR 1/${max}`;
    const rollOK=!b.needRec&&!spent&&(anyRolled?rerollPick>0:committed>0);
    const second=!anyRolled||b.needRec
      ? `<button disabled>Apply Damage to the Tyrant</button>`
      : dmg>0
        ? `<button data-pool-apply class="primary bat-rec-due">Apply ${dmg} Damage to the Tyrant</button>`
        : `<button data-pool-apply class="primary bat-rec-due">No Damage — Exhaust Rolled Dice</button>`;
    const cap=RAT_REC[state.activeRat]+2;
    const picked=personalDice().filter(d=>d.selected&&d.zone==="exhausted").length;
    host.innerHTML=
      `<div class="${cls(1)}"><span class="bat-step-num">1</span><div class="bat-step-stack">`
      +`<button data-pool-roll class="${step===1||(step===2&&rerollPick)?"primary":""} ${step===1&&rollOK?"bat-rec-due":""}" ${rollOK?"":"disabled"}>${rollLabel}</button>`
      +(()=>{const need=commitColor(b);if(!need||anyRolled||b.needRec)return "";
        const chk=colorCheck(b,selected().filter(d=>d.zone==="available"));
        return `<span class="bat-commit-color ${chk.ok?"ok":"due"}"><span class="bat-dot ${need}"></span>`
          +`Commit color: ${need}${chk.ok?(chk.pair?" (pair used)":" ✓"):" — required"}</span>`;})()
      +(()=>{const src=strSources(rat);return src.length
        ?`<span class="bat-str-bonus">+${src.length} STR this turn · ${src.map(escape).join(", ")}</span>`:"";})()
      +`</div></div>`
      +`<div class="${cls(2)}"><span class="bat-step-num">2</span>${second}</div>`
      +`<div class="${cls(3)}"><span class="bat-step-num">3</span>`
      +`<button data-pool-recover class="${step===3?"primary bat-rec-due":""}" ${step===3?"":"disabled"}>Recover ${picked}/${cap} Selected (REC ${RAT_REC[state.activeRat]} + 2)</button></div>`;
  }

  function renderPool() {
    const panel=$("batPoolPanel");panel.hidden=!inBattle();
    if(!inBattle())return;
    const b=state.battle;
    const die=d=>`<button class="rat-die ${d.color} ${d.zone} ${d.selected?"selected":""}" data-bat-die="${d.id}" title="${d.color} · ${d.zone}"><span class="face">${d.face||""}</span><span class="tiny">${d.color[0].toUpperCase()}</span></button>`;
    const zone=name=>personalDice().filter(d=>d.zone===name).sort(byColor).map(die).join("")||'<span class="rat-zone-empty">None</span>';
    const red=state.red.zone==="available"?`<button class="rat-die red ${state.red.selected?"selected":""}" data-bat-red="1" title="Communal Red die"><span class="face">${state.red.face||""}</span><span class="tiny">R</span></button>`:"";
    const committed=selected().filter(d=>d.zone!=="exhausted").length+(state.red.selected?1:0);
    const rat=active();
    $("batPool").innerHTML=`<div class="bat-pool-grid">`
      +`<div class="rat-dice-zone"><h4>Available · ${committed} committed of 6</h4><div class="rat-dice-row">${zone("available")}${red}</div></div>`
      +`<div class="rat-dice-zone"><h4>Rolled</h4><div class="rat-dice-row">${personalDice().filter(d=>d.zone==="rolled").sort(byColor).map(die).join("")}${state.red.zone==="rolled"?`<button class="rat-die red rolled ${state.red.selected?"selected":""}" data-bat-red="1" title="Communal Red die · rolled · ${faceLabel(state.red.face)}"><span class="face">${state.red.face||""}</span><span class="tiny">R</span></button>`:""}</div></div>`
      +`<div class="rat-dice-zone"><h4>Exhausted${(()=>{const cap=RAT_REC[state.activeRat]+2,n=personalDice().filter(d=>d.selected&&d.zone==="exhausted").length;return ` · ${n} of ${cap} selected to recover`;})()}</h4><div class="rat-dice-row">${zone("exhausted")}</div></div></div>`
      ;
    renderRatSteps(b,committed,rat);
  }

  // The Tyrant's turn as three explicit steps in the panel header. Each is
  // highlighted in turn and the next stays locked until the one before is
  // done: reveal the Attack card, draw and roll, then resolve the damage.
  function renderTyrantSteps(b,draws,bag,drawn,tyrantDie,tyrantTurn){
    const host=$("batTyrantSteps");if(!host)return;
    if(!tyrantTurn){
      // The bag is a component on the table; show what is in it. Read-only
      // spans, not buttons - the die handler toggles the bag/rolled split.
      const inBag=tyrantDice();
      const chip=d=>`<span class="rat-die ${d.color}" title="${d.color} · one of the Tyrant's six"><span class="face"></span><span class="tiny">${d.color[0].toUpperCase()}</span></span>`;
      host.innerHTML=`<span class="bat-track-state">The Rats are acting — the Tyrant's steps unlock on its turn.</span>`
        +`<div class="rat-dice-zone"><h4>Tyrant's bag · ${inBag.length} dice</h4>`
        +`<div class="bat-tyrant-dice-row">${inBag.map(chip).join("")||'<span class="rat-zone-empty">Empty</span>'}</div></div>`;
      return;
    }
    const step=!b.revealed?1:!b.rolled?2:3;
    const cls=n=>`bat-step ${step===n?"now":step>n?"done":""}`;
    const tgt=state.rats[b.attackRat!=null?b.attackRat:state.activeRat]||active();
    let third;
    if(step<3) third=`<button disabled>Apply Damage</button>`;
    else if(b.roarPending){
      const n=personalDice().filter(d=>d.selected&&d.zone==="available").length;
      third=`<button data-roar-exhaust class="primary bat-rec-due">${n===1?"Exhaust Selected Die":"Choose 1 Die to Exhaust"}</button>`;
    } else if(b.tyrantHits>0){
      third=`<button data-goto-target class="primary bat-rec-due">Apply ${b.tyrantHits} Damage to ${escape(tgt.name)}</button>`;
    } else {
      third=`<button data-apply-hits="1" class="primary bat-rec-due">No Damage — End the Tyrant's Turn</button>`;
    }
    host.innerHTML=
      `<div class="${cls(1)}"><span class="bat-step-num">1</span>`
      +`<button data-tyrant-attack class="${step===1?"primary bat-rec-due":""}" ${step===1?"":"disabled"}>Reveal Next Attack Card</button></div>`
      +`<div class="${cls(2)}"><span class="bat-step-num">2</span>`
      +`<button data-tyrant-draw="${draws}" class="${step===2?"primary bat-rec-due":""}" ${step===2?"":"disabled"}>Draw ${draws} Dice and Roll</button>`
      +`<div class="bat-step-dice">`
      +`<div class="rat-dice-zone"><h4>Bag</h4><div class="bat-tyrant-dice-row">${bag.map(tyrantDie).join("")||'<span class="rat-zone-empty">Empty</span>'}</div></div>`
      +`<div class="rat-dice-zone"><h4>Rolled</h4><div class="bat-tyrant-dice-row">${drawn.map(tyrantDie).join("")||'<span class="rat-zone-empty">—</span>'}</div></div>`
      +`</div></div>`
      +`<div class="${cls(3)}"><span class="bat-step-num">3</span>${third}</div>`;
  }

  function renderBattle() {
    const b=ensureBattle(),panel=$("batBattlePanel"),top=document.querySelector("#screen-bat .bat-table-top");
    panel.hidden=!b;if(top)top.hidden=!!b;
    if(!b) return;
    const front=frontSlot(b);
    // A card is only adjustable once everything to its left is destroyed.
    const cells=[trackCell("buff",null,b.buffHp,b.buffMax,front,front==="buff")]
      .concat(b.order.map((cardIndex,pos)=>trackCell(pos,state.spliceCards[cardIndex],b.hp[pos],b.max[pos],front,front===pos)));
    const draws=Math.min(6,Math.max(2,...b.order.map((cardIndex,pos)=>b.hp[pos]>0?cardValue(state.spliceCards[cardIndex]):0)));
    const drawn=tyrantDice().filter(d=>d.selected),bag=tyrantDice().filter(d=>!d.selected);
    const tyrantDie=d=>`<button class="rat-die ${d.color} ${d.selected?"selected":""} ${d.face?"rolled":""}" data-tyrant-die="${d.id}" title="${d.color}"><span class="face">${d.face||""}</span><span class="tiny">${d.color[0].toUpperCase()}</span></button>`;
    // 21 positions round the face: 20 at the top, counting down clockwise.
    const STEP=360/21,angleFor=v=>(20-v)*STEP;
    const numbers=[];
    for(let v=0;v<=20;v++){
      const rad=(angleFor(v)-90)*Math.PI/180;
      numbers.push(`<text class="dial-num ${v===state.health?"on":""}" x="${(60+46*Math.cos(rad)).toFixed(1)}" y="${(60+46*Math.sin(rad)).toFixed(1)}">${v}</text>`);
    }
    const tyrantTurn=b.turn==="tyrant";
    const dial=`<div class="bat-tyrant ${front==="tyrant"?"front":""} ${tyrantTurn?"acting":""}">`
      +`<div class="bat-track-name">Tyrant Health${tyrantTurn?' <span class="bat-turn-flag">its turn</span>':""}</div>`
      +`<div class="bat-dial">`
      +`<svg viewBox="0 0 120 120" role="img" aria-label="Tyrant Health ${state.health} of 20">`
      +`<circle class="dial-ring" cx="60" cy="60" r="56"></circle>`
      +numbers.join("")
      +`<g class="dial-hand" transform="rotate(${angleFor(state.health).toFixed(2)} 60 60)">`
      +`<line class="dial-needle" x1="60" y1="60" x2="60" y2="22"></line>`
      +`<circle class="dial-tip" cx="60" cy="22" r="3.4"></circle></g>`
      +`<circle class="dial-hub" cx="60" cy="60" r="5"></circle>`
      +`<text class="dial-value" x="60" y="60">${state.health}</text></svg></div>`
      +`<div class="bat-hp-selector"><button data-tyrant-hp data-delta="-1" ${front!=="tyrant"||state.health<=0?"disabled":""} aria-label="Rotate down">−</button>`
      +`<strong>${state.health} / 20</strong>`
      +`<button data-tyrant-hp data-delta="1" ${front!=="tyrant"||state.health>=20?"disabled":""} aria-label="Rotate up">+</button></div>`
      +`</div>`;
    const atkLeft=(b.attackDeck||[]).length,flipOnly=b.attack==null&&b.startFlip!=null;
    const atk=b.attack!=null?b.attack:b.startFlip;
    const attackPanel=`<div class="bat-track-cell bat-attack-cell ${tyrantTurn?"front":""}">`
      +`<div class="suite-card portrait bat-track-art" data-attack-art="${atk===null||atk===undefined?"":atk}"></div>`
      +`<div class="bat-track-name">${atk===null||atk===undefined?"Tyrant Attack":escape(ATTACK_NAMES[atk])}</div>`
      +`<div class="bat-track-state">${atk===null||atk===undefined?"none revealed":flipOnly?"Starting flip: it does not attack, it only sets the commit color.":escape(ATTACK_TEXT[atk])}</div>`
      +`<div class="bat-track-state">${atkLeft} in deck${(b.attackDiscard||[]).length?` · ${b.attackDiscard.length} discarded`:""}</div></div>`;
    const host=$("batTrack");
    host.innerHTML=attackPanel+cells.join("")+dial;
    renderTyrantSteps(b,draws,bag,drawn,tyrantDie,tyrantTurn);
    host.querySelectorAll("[data-attack-art]").forEach(art=>{
      const i=art.dataset.attackArt;
      if(i===""){art.classList.add("placeholder-card");art.innerHTML="<span>Tyrant Attack</span>";return;}
      art.classList.remove("placeholder-card");art.innerHTML="";
      art.style.backgroundImage="url('assets/BAT_TyrantAttacks_TTS.png?v=fonts-1')";
      art.style.backgroundSize=`${ATTACK_NAMES.length*100}% 100%`;
      art.style.backgroundPosition=`${Number(i)/(ATTACK_NAMES.length-1)*100}% 0%`;
    });
    host.querySelectorAll("[data-track-art]").forEach(art=>{
      const slot=art.dataset.trackArt;
      // The Buff HP card is drawn as its own track now, so only Splices
      setSprite(art,state.spliceCards[b.order[Number(slot)]]);
    });
  }

  function renderSplices() {
    $("batSpliceCount").textContent=`${state.splices} / 5`;
    const displayed=Array.from({length:state.splices},(_,i)=>state.spliceCards[i]||{type:"legacy",i:0});
    $("batSpliceNames").innerHTML=displayed.map((card,i)=>`<button class="bat-splice-name ${card.tapped?"tapped":""}" data-bat-splice="${i}" aria-pressed="${!!card.tapped}" title="${escape(cardName(card))}: tap to mark ${card.tapped?"ready":"used"}">${escape(cardName(card))}</button>`).join("");
  }

  function renderEffect() {
    const host=$("batEffect"),c=state.current;
    if(!c){host.innerHTML=`<p class="hint">${escape(state.notice||"Reveal an Experiment to see its effect controls.")}</p>`;return;}
    const card=cards[c.e],actions=[];
    // Resolving deals the next Experiment at once, so this card can be on the
    // table while the PREVIOUS turn still owes a Recovery. Showing its
    // controls then reads as "the next turn has started" - and nothing works,
    // because it has not.
    const turnNotStarted=state.turnLocked&&!c.phase;
    if(c.e===0&&!c.flipped) actions.push(`<button data-bat-action="flip" class="bat-required">Flip active Rat</button>`);
    if(c.e===1&&!c.phase&&!c.usedFallback&&!canCommitColor("yellow")) actions.push(`<button data-bat-action="fine-fallback" class="bat-required">No Yellow available · +1 Target</button>`);
    if(c.e===5&&!c.phase&&!canCommitColor("purple")) actions.push(`<button data-bat-action="load-redraw" class="bat-required">No Purple available · draw replacement</button>`);
    if(c.e===6&&c.committed.includes("blue")&&!c.peeked) actions.push(`<button data-bat-action="peek">Look at next Experiment</button>`);
    if(c.e===7&&!c.phase&&!c.usedFallback&&!canCommitColor("green")) actions.push(`<button data-bat-action="rapid-fallback" class="bat-required">No Green available · discard stronger Upgrade</button>`);
    if(c.e===14&&!c.phase&&!c.blocked) actions.push(`<button data-bat-action="exclude" class="bat-required">Randomly exclude active Rat die</button>`);
    if(c.e===15&&!c.phase&&!c.reduced) actions.push(`<button data-bat-action="contain">Reduce Target by 2 and roll Yellow</button>`);
    if(c.e===18&&!c.phase&&!c.reduced) actions.push(`<button data-bat-action="method">Reduce Target to 0</button>`);
    if(c.e===17&&canSucceed()&&active().upgrades.length&&c.options.some(x=>x.type==="u")) {
      actions.push(`<label>Held Upgrade to swap <select id="batSwapFrom">${active().upgrades.map((u,i)=>`<option value="${i}">${escape(cardName(u))}</option>`).join("")}</select></label>`);
      actions.push(`<label>Revealed Upgrade to take <select id="batSwapTo">${c.options.map((u,i)=>u.type==="u"?`<option value="${i}">${escape(cardName(u))}</option>`:"").join("")}</select></label>`);
      actions.push(`<button data-bat-action="swap">Plan optional swap</button>`);
    }
    // #batEffect keeps the running notice; the controls go under the
    // Experiment card itself, which already carries the name, Target and
    // effect text they act on.
    host.innerHTML=state.notice?`<p class="hint">${escape(state.notice)}</p>`:"";
    const slot=$("batEffectActions"),show=actions.length&&!turnNotStarted;
    if(slot){
      slot.classList.toggle("hidden",!show);
      slot.innerHTML=show?`<div class="compact-actions">${actions.join("")}</div>`:"";
    }
  }

  // How a battle ends. Nobulous has an opinion either way; one line is picked
  // at random when the game ends and kept, so a re-render never changes it.
  const ENDINGS={
    loss:{title:"All the lab rats have been knocked out.",quotes:[
      "The Tyrant works. The Rats do not. Only one of those was the experiment.",
      "Four subjects, four knockouts. Finally, a result I can reproduce.",
      "No matter. I will order more Rats. The supplier stopped asking why."]},
    win:{title:"The Tyrant has been defeated.",quotes:[
      "You destroyed my Tyrant. I am recording this as unsolicited peer review.",
      "Beaten by its own test subjects. I hope the Tyrant is suitably embarrassed.",
      "A minor setback. I still have the Splices, the Specimens, and a sudden abundance of motivation."]}
  };
  function checkEnd(){
    if(!inBattle()||!state.battle) return;
    if(!state.endGame){
      let kind=null;
      if(state.health<=0) kind="win";
      else if(state.rats.every(r=>r.down)) kind="loss";
      if(kind){const q=ENDINGS[kind].quotes;
        state.endGame={kind,quote:q[Math.floor(Math.random()*q.length)],dismissed:false};save();}
    }
    const dlg=$("batEndDialog");
    if(!dlg||!state.endGame||state.endGame.dismissed||dlg.open) return;
    $("batEndTitle").textContent=ENDINGS[state.endGame.kind].title;
    $("batEndQuote").textContent=state.endGame.quote;
    dlg.classList.toggle("won",state.endGame.kind==="win");
    dlg.showModal();
  }

  function render() {
    $("batDifficulty").value=state.difficulty;$("batRat").selectedIndex=state.activeRat;
    $("batOverlay").textContent=(window.NOBULOUS_TIER&&batTier()!=="0")
      ? `Experiment deck · NRJ Tier ${window.NOBULOUS_TIER.name(batTier())} module cards in play`
      : "Experiment deck · Prototyrant research";
    renderBATModules();renderSwapPrompt();renderBanked();
    $("batStats").innerHTML=`<div class="suite-stat"><span>Splices</span><strong>${state.splices} / 5</strong></div><div class="suite-stat"><span>Experiments</span><strong>${state.rounds}</strong></div><div class="suite-stat"><span>Deck</span><strong>${state.deck.length}</strong></div><div class="suite-stat"><span>Prototyrant HP</span><strong>${state.health}</strong></div><div class="suite-stat bat-red-stat"><span>Red</span>${state.red.zone==="setaside"||state.red.zone==="rolled"?`<span class="rat-die red setaside" title="Communal Red die · set aside until moved to a Rat"><span class="face">${state.red.face||""}</span><span class="tiny">R</span></span>`:`<strong>${names[state.red.holder]}</strong>`}${!inBattle()&&state.current&&!state.turnLocked?`<button data-bat-reset="1" class="bat-reset-turn" title="Set Red aside again, send back any borrowed die and clear every selection, so a different Rat can be chosen. Unavailable once the dice are rolled.">Reset turn</button>`:""}</div><div class="suite-stat bat-banished-stat"><span>Banished</span><div class="bat-banished-row">${state.rats.flatMap(r=>r.dice.filter(d=>d.zone==="banished")).sort(byColor).map(d=>`<span class="rat-die ${d.color} banished-chip" title="${d.color} · banished"><span class="face"></span><span class="tiny">${d.color[0].toUpperCase()}</span></span>`).join("")||`<span class="bat-banished-empty">None</span>`}</div></div>`;
    renderRats();renderSplices();renderBattle();renderPool();renderEffect();
    checkEnd();
    const c=state.current,el=$("batEncounter"),caption=$("batEncounterText");
    if(c){
      const card=cards[c.e];el.classList.remove("placeholder-card");el.removeAttribute("style");el.classList.add("bat-experiment-card");
      el.innerHTML=`<header>${escape(card.name)}<small>Build-a-Tyrant Experiment</small></header><div class="target-number">${target()}</div><div class="target-label">Target</div><div class="experiment-effect">${escape(card.effect)}</div><div class="experiment-flavor">${escape(card.flavor)}</div><footer>Specimen revealed: +1 Target total (once).</footer>`;
      caption.textContent=`${c.successes} ${c.successes===1?"success":"successes"} · Strategy phase ${c.phase} of ${c.e===16?1:2} · ${c.committed.length} dice committed`;
    } else {el.classList.remove("bat-experiment-card");el.classList.add("placeholder-card");el.removeAttribute("style");el.innerHTML=`<span>${state.splices>=5?"Prototyrant awake — begin battle":"Reveal an Experiment"}</span>`;caption.textContent="";}
    const resolveDue=dueActions().has("resolve");
    ["A","B","C"].forEach((letter,i)=>{if(letter==="C")$("batUpgradeCPanel").classList.toggle("hidden",!(c?.options[2]));setSprite($("batUpgrade"+letter),c?.options[i]);const button=$("batSuccess"+letter);button.disabled=!c?.options[i]||!canSucceed();button.classList.toggle("bat-rec-due",resolveDue&&!button.disabled);if(letter==="C")button.classList.toggle("hidden",!(c?.options[2]));});
    $("batFail").disabled=!c;
    // Once the roll cannot reach the Target, failing is the only move left,
    // so Failure takes the red "you must press this" treatment rather than
    // the gold "this is next" one. It stays an ordinary button while a
    // Success is still on the table - failing is a choice then, not a duty.
    // Only once every Strategy roll is spent. `resolveDue` is not the test:
    // it goes true whenever nothing happens to be selected, which is not the
    // same as having no roll left - so Failure used to redden while the Rat
    // still had a throw that could save the Experiment.
    const mustFail=!!c&&c.phase>=maxPhase(c)&&!canSucceed();
    $("batFail").classList.toggle("bat-required",mustFail);
    $("batFail").classList.remove("bat-rec-due");
    $("batRoller").innerHTML=`<div class="roller-head"><div><p class="kicker">Strategy phase ${c?Math.min(c.phase+1,c.e===16?1:2):1}</p><h2>${active().name} · ${selected().length+(state.red.selected?1:0)} selected</h2></div><div class="compact-actions"><button id="batRollSelected" class="primary${due("roll")}" ${!c||c.phase>=maxPhase(c)?"disabled":""}>Roll selected</button><button id="batAllocate" class="${due("allocate").trim()}" ${c&&(c.pending||[]).length?"":"disabled"}>Add selected dice to the Experiment</button><button id="batReadyAll">Ready personal dice</button></div></div><div class="roll-result">${c?`${totalSuccesses()} successes toward Target ${target()}. Select available dice; after the first roll, select highlighted misses to reroll.`:"Reveal an Experiment to begin."}</div>`;
  }

  // With no Reveal button, the table always keeps an Experiment on offer.
  // ------------------------------------------------------------------
  // NRJ modules: the drawn Experimental Protocol, and the Research Notes
  // claimed and spent by hand - their conditions are situational, so the
  // table judges them exactly as it would with the physical cards.
  // ------------------------------------------------------------------
  // The check decides what happens to the borrowed die, so it sits with the
  // rolled dice of the Rat that borrowed it rather than over by the cards.
  function borrowCheckBlock(i){
    if(inBattle()||i!==state.activeRat||!borrowCheckDue()) return "";
    const die=personalDice().find(x=>x.id===state.returnCheck.dieId);
    const owner=die?state.rats[Number(die.id.split("-")[1])].name:"its owner";
    return `<button data-bat-borrow-check="1" class="bat-return-check${due("retcheck")}" `
      +`title="The borrowed ${die?die.color:""} die is rolled by itself: a miss banishes it, otherwise it goes back to ${owner}.">`
      +`Roll check</button>`;
  }
  // Dice that have been added to the Experiment: locked in, not clickable,
  // and shown where their successes now live.
  function renderBanked(){
    const host=document.getElementById("batBanked");
    if(!host) return;
    const c=state.current, list=(c?.banked||[]);
    host.classList.toggle("hidden",!(c&&list.length));
    if(!c||!list.length){host.innerHTML="";return;}
    host.innerHTML=`<span class="bat-banked-label">Added to the Experiment</span>`
      +`<span class="rat-dice-row">`
      +list.map(b=>`<span class="rat-die ${b.color} banked" title="${b.color} · ${faceLabel(b.face)} · added to the Experiment"><span class="face">${b.face||""}</span><span class="tiny">${b.color[0].toUpperCase()}</span></span>`).join("")
      +`</span><strong class="bat-banked-total">${c.successes} / ${target()}</strong>`;
  }
  function renderSwapPrompt(){
    const host=document.getElementById("batSwapPrompt");
    if(!host) return;
    const c=state.current;
    const on=!inBattle()&&c&&c.e===3&&!c.swapped;
    host.classList.toggle("hidden",!on);
    host.innerHTML=on?`<div class="bat-swap-inner"><p>Contaminated Tissue</p>`
      +`<button data-bat-swap="1" class="bat-required">Discard both Upgrades and reveal two new</button></div>`:"";
  }
  function renderBATModules(){
    const host=document.getElementById("batModules");
    if(!host)return;
    const tier=state.tier||"0",notes=state.notes||[];
    const on=tier!=="0"&&(state.protocol!=null||notes.length);
    host.classList.toggle("hidden",!on);
    if(!on)return;
    let html="";
    if(state.protocol!=null){
      const pr=BAT_PROTOCOLS[state.protocol];
      html+=`<div class="bat-protocol"><p class="kicker">Experimental Protocol &middot; Tier I</p>`
        +`<h3>${pr[0]}</h3><p>${pr[1]}</p>`
        +`${state.protocol===2?`<p class="hint">Applied automatically: Experiments with printed Target 5+ are at -1. Exhaust 2 of the active Rat's available dice after every such attempt.</p>`:`<p class="hint">Apply this at the table; the lab does not enforce it.</p>`}</div>`;
    }
    if(notes.length){
      html+=`<div class="bat-notes"><p class="kicker">Research Notes &middot; Tier III</p><div class="bat-note-grid">`
        +BAT_NOTES.map((note,i)=>{
          const st=notes[i]||{};
          return `<article class="bat-note ${st.spent?"spent":st.claimed?"claimed":""}">`
            +`<strong>${note[0]}</strong>`
            +`<small><b>Claim:</b> ${note[1]}</small>`
            +`<small><b>Spend:</b> ${note[2]}</small>`
            +`${st.spent?`<span class="bat-note-state">Spent</span>`
              :st.claimed?`<button data-bat-note-spend="${i}">Spend</button>`
              :`<button data-bat-note-claim="${i}">Claim</button>`}</article>`;
        }).join("")
        +`</div></div>`;
    }
    host.innerHTML=html;
  }
  // Do not gate on the decks here: draw() knows that an empty Upgrade deck is
  // a reshuffle and an empty Experiment deck is the Splicing Machine
  // Malfunction. Gating meant an exhausted deck simply idled with no
  // Experiment on the table and no way to move.
  function ensureExperiment(){if(!state.current&&state.splices<5){draw();return true;}return false;}
  function claimBATNote(i,spend){
    state.notes??=[];
    const st=state.notes[i]||(state.notes[i]={claimed:false,spent:false});
    if(spend){if(!st.claimed||st.spent)return;st.spent=true;setNotice(`${BAT_NOTES[i][0]} spent: ${BAT_NOTES[i][2]}`);}
    else{if(st.claimed)return;st.claimed=true;setNotice(`${BAT_NOTES[i][0]} claimed.`);}
    save();render();
  }

  function handleClick(event) {
    if(!event.target.closest("#screen-bat, #batEndDialog")) return;
    const button=event.target.closest("button");
    const panel=event.target.closest(".bat-rat");
    if(!button&&!panel) return;
    if(button&&!button.matches("[data-new-game='bat'],#batEndYes,#batEndNo,[data-bat-die],[data-bat-red],[data-bat-borrow],[data-bat-return],[data-bat-swap],[data-bat-borrow-check],[data-bat-reset],[data-bat-allocate],[data-move-red],[data-rat-side],[data-rat-hp],[data-rat-roll],[data-rat-recover],[data-rat-rollzero],[data-rat-ability],[data-bat-note-claim],[data-bat-note-spend],[data-pool-roll],[data-pool-recover],[data-pool-exhaust],[data-pool-apply],[data-apply-hits],[data-hit-target],[data-bat-held],[data-bat-drop],[data-track-hp],[data-tyrant-hp],[data-tyrant-die],[data-tyrant-draw],[data-roar-exhaust],[data-goto-target],[data-tyrant-attack],[data-bat-splice],[data-bat-action],#batRollSelected,#batAllocate,#batReadyAll,#batSuccessA,#batSuccessB,#batSuccessC,#batFail")) return;
    event.preventDefault();event.stopImmediatePropagation();
    if(button?.dataset.newGame==="bat") {state=fresh(state.difficulty);save();ensureExperiment()||render();return;}
    if(button?.id==="batEndYes"){$("batEndDialog").close();state=fresh(state.difficulty);save();ensureExperiment()||render();return;}
    if(button?.id==="batEndNo"){$("batEndDialog").close();if(state.endGame)state.endGame.dismissed=true;
      state.notice=state.endGame&&state.endGame.kind==="win"?"The Tyrant is defeated. The board is left as it ended.":"Every Rat is knocked out. The board is left as it ended.";
      save();render();return;}
    if(button?.dataset.trackHp!==undefined){const b=state.battle;if(b){const slot=button.dataset.trackHp,delta=Number(button.dataset.delta);
      if(slot==="buff")b.buffHp=Math.max(0,Math.min(b.buffMax,b.buffHp+delta));
      else{const i=Number(slot);b.hp[i]=Math.max(0,Math.min(b.max[i],b.hp[i]+delta));}
      save();render();}return;}
    if(button?.dataset.tyrantDie!==undefined){const die=personalDice().find(d=>d.id===button.dataset.tyrantDie);if(die){die.selected=!die.selected;save();render();}return;}
    if(button?.dataset.tyrantDraw!==undefined){const b=state.battle;if(b&&b.revealed&&!b.rolled){
      const n=Number(button.dataset.tyrantDraw)||2,pool=tyrantDice();
      pool.forEach(die=>{die.selected=false;die.face="";});
      let hits=0;
      shuffle([...pool.keys()]).slice(0,n).forEach(i=>{
        pool[i].selected=true;pool[i].face=rollFace(pool[i].color);hits+=faceValue(pool[i].face);});
      const base=hits;let extra="";
      if(b.attack===0){hits+=3;extra=" +3 from Overwhelming Mass";}
      if(b.attack===3){const live=b.hp.filter(v=>v>0).length;hits+=live;extra=` +${live} from Spliced Reflexes`;}
      if(b.attack===4){                         // Terrifying Roar
        hits=0;b.roarPending=true;
        personalDice().forEach(d=>{d.selected=false;});
        extra=" — no damage. Choose 1 available die in the shared pool to exhaust";
      }
      b.tyrantHits=hits;b.hitTarget=null;b.rolled=true;
      const tgt=attackTarget(b);
      b.attackRat=state.rats.indexOf(tgt);
      state.notice=`The Tyrant drew ${n} and rolled ${base}${extra}. `
        +(b.attack===4?"":`${hits} ${hits===1?"hit":"hits"} against ${tgt.name}.`);
      save();render();}return;}
    if(button?.dataset.tyrantHp!==undefined){if(!state.battle||frontSlot(state.battle)!=="tyrant")return;state.health=Math.max(0,Math.min(20,state.health+Number(button.dataset.delta)));save();render();return;}
    if(button?.dataset.batDrop){const [ratIndex,cardIndex]=button.dataset.batDrop.split(":").map(Number);const rat=state.rats[ratIndex];if(rat?.upgrades[cardIndex]){const [gone]=rat.upgrades.splice(cardIndex,1);state.discard.push(cardName(gone));setNotice(`${rat.name} destroyed ${cardName(gone)}.`);}return;}
    if(button?.dataset.batHeld){const [ratIndex,cardIndex]=button.dataset.batHeld.split(":").map(Number);const card=state.rats[ratIndex]?.upgrades[cardIndex];if(card){card.tapped=!card.tapped;save();render();}return;}
    if(button?.dataset.batSplice!==undefined){const index=Number(button.dataset.batSplice);const card=state.spliceCards[index];if(card){card.tapped=!card.tapped;save();render();}return;}
    if(button?.dataset.batAllocate!==undefined||button?.id==="batAllocate"){allocateSelected();save();render();return;}
    if(button?.dataset.batReset!==undefined){resetTurn();save();render();return;}
    if(button?.dataset.batBorrowCheck!==undefined){borrowCheck();save();render();return;}
    if(button?.dataset.batSwap!==undefined){swapUpgrades();save();render();return;}
    if(button?.dataset.batBorrow!==undefined){lendDie(Number(button.dataset.batBorrow));save();render();return;}
    if(button?.dataset.batReturn!==undefined){returnBorrowed();save();render();return;}
    if(button?.dataset.batDie) return chooseDie(button.dataset.batDie);
    if(button?.dataset.batRed) {if(state.current?.e===10)return setNotice("Red cannot be used for this Experiment.");state.red.selected=!state.red.selected;save();render();return;}
    if(button?.dataset.moveRed!==undefined) {
      const to=Number(button.dataset.moveRed);
      if(!redTakers().includes(to)) return setNotice(
        state.current?.e===10 ? "Restricted Materials keeps Red on the active Rat."
        : state.rats[to].down ? `${state.rats[to].name} is knocked out and cannot hold Red.`
        : "Red goes to a Rat other than the active one.");
      state.red.holder=to;state.red.zone="available";state.red.selected=false;
      // Restricted Materials puts Red on the ACTIVE Rat, which commits nobody.
      if(to!==state.activeRat) state.turnRedPlaced=true;
      save();render();return;}
    if(button?.dataset.ratSide!==undefined) {const rat=state.rats[Number(button.dataset.ratSide)];rat.side=rat.side==="front"?"back":"front";save();render();return;}
    if(button?.dataset.ratHp!==undefined) {const rat=state.rats[Number(button.dataset.ratHp)];
      const was=rat.down;
      rat.hp=Math.max(0,rat.hp+Number(button.dataset.delta));
      // `down` was set on a knockout and cleared nowhere, so a Rat put out by
      // mistake stayed out: the +/- buttons moved the number and left it down.
      // Tie it to the Health instead, which makes + the undo.
      rat.down=rat.hp<=0;
      if(was&&!rat.down) setNotice(`${rat.name} is back on ${rat.hp} HP.`);
      save();render();return;}
    if(button?.dataset.batAction) return effectAction(button.dataset.batAction);
    if(button?.id==="batRollSelected") return roll();
    if(button?.dataset.poolRoll!==undefined){const b=state.battle;if(!b)return;
      const max=strFor(active()),used=b.ratRolls||0;
      if(used>=max) return setNotice(`${active().name} has used all ${max} Strategy rolls (STR ${max}). Apply the damage.`);
      if(used===0){
        const chk=colorCheck(b,selected().filter(d=>d.zone==="available"));
        if(!chk.ok) return setNotice(`Commit color is ${chk.need}: ${chk.why}. Red does not count.`);
      }
      const dice=selected().filter(d=>d.zone!=="exhausted"),red=state.red.selected&&state.red.zone==="available";
      const redAgain=state.red.selected&&state.red.zone==="rolled";
      if(dice.length+(red?1:0)>6) return setNotice("Commit at most 6 dice from the shared pool.");
      let gained=0;
      dice.forEach(d=>{d.face=rollFace(d.color);gained+=faceValue(d.face);d.zone="rolled";d.selected=false;});
      if(red){state.red.face=rollFace("red");gained+=faceValue(state.red.face);state.red.zone="rolled";state.red.selected=false;}
      else if(redAgain){state.red.face=rollFace("red");gained+=faceValue(state.red.face);state.red.selected=false;}
      b.ratRolls=used+1;
      const left=max-b.ratRolls;
      state.notice=`${active().name} rolled ${gained} damage (STR ${b.ratRolls}/${max}).`
        +(left>0?` Select misses and reroll, or apply the damage.`:` No rerolls left — apply the damage.`);
      save();render();return;}
    if(button?.dataset.poolApply!==undefined){const bt=state.battle;if(!bt)return;
      const anyRolled=personalDice().some(d=>d.zone==="rolled")||state.red.zone==="rolled";
      if(!anyRolled)return;
      const n=rolledDamage();
      if(n>0) applyTyrantDamage(n);
      personalDice().forEach(d=>{if(d.zone==="rolled"){d.zone="exhausted";d.selected=false;d.face="";}});
      if(state.red.zone==="rolled"){state.red.zone="available";state.red.selected=false;state.red.face="";}
      bt.needRec=true;   // the turn does not pass until REC is done
      state.notice=(n>0?`${n} damage applied.`:`No damage — the rolled dice are exhausted.`)
        +` Now recover ${active().name}’s dice: select up to ${RAT_REC[state.activeRat]+2} exhausted dice and press Recover.`;
      save();render();
      const recBtn=document.querySelector("[data-pool-recover]");
      if(recBtn){recBtn.focus();recBtn.scrollIntoView({behavior:"smooth",block:"center"});}
      return;}
    if(button?.dataset.poolExhaust!==undefined){personalDice().forEach(d=>{if(d.zone==="rolled"){d.zone="exhausted";d.selected=false;}});
      if(state.red.zone==="rolled"){state.red.zone="available";state.red.selected=false;state.red.face="";}
      save();render();return;}
    if(button?.dataset.tyrantAttack!==undefined){
      const b=state.battle;if(!b||b.turn!=="tyrant"||b.revealed)return;
      if(b.attack!==null&&b.attack!==undefined) b.attackDiscard.push(b.attack);
      if(!b.attackDeck.length){b.attackDeck=shuffle(b.attackDiscard);b.attackDiscard=[];
        state.notice="Tyrant Attack deck ran out — the discard was reshuffled.";}
      b.attack=b.attackDeck.pop();b.revealed=true;
      state.notice=`Tyrant Attack: ${ATTACK_NAMES[b.attack]} — ${ATTACK_TEXT[b.attack]}. Now draw and roll.`;save();render();return;}
    if(button?.dataset.poolRecover!==undefined){
      // needRec means "this Rat still owes its recovery". The dice used to be
      // handed back before this was consulted, so a second press paid out again.
      if(!state.battle||!state.battle.needRec)
        return setNotice("Recovery is taken once, after the damage is applied.");
      const cap=RAT_REC[state.activeRat]+2;let n=0;
      if(state.red.zone==="rolled"){state.red.zone="available";state.red.selected=false;state.red.face="";}
      personalDice().forEach(d=>{if(d.zone==="rolled"){d.zone="exhausted";d.selected=false;d.face="";}});
      personalDice().filter(d=>d.selected&&d.zone==="exhausted").slice(0,cap).forEach(d=>{d.zone="available";d.face="";d.selected=false;n++;});
      const bt=state.battle,gated=bt&&bt.needRec;
      if(gated){bt.needRec=false;bt.turn="tyrant";bt.revealed=false;bt.rolled=false;bt.ratRolls=0;
        const r=active();
        // Acute Hearing tapped this turn grants +1 STR on this Rat's next turn;
        // whatever bonus it held for this turn is now spent.
        r.strNext=r.upgrades.some(c=>c.tapped&&STR_NEXT(c))?1:0;
        state.notice=`${active().name} recovered ${n} ${n===1?"die":"dice"}. The Tyrant acts now.`;}
      else state.notice=`${active().name} recovered ${n} ${n===1?"die":"dice"} to the shared pool.`;
      save();render();
      if(gated) document.querySelector(".bat-tyrant")?.scrollIntoView({behavior:"smooth",block:"center"});
      return;}
    if(button?.dataset.hitTarget!==undefined){const b=state.battle;if(!b)return;
      const v=button.dataset.hitTarget;b.hitTarget=b.hitTarget===v?null:v;save();render();return;}
    if(button?.dataset.gotoTarget!==undefined){const b=state.battle;if(!b||!b.rolled)return;
      const idx=b.attackRat!=null?b.attackRat:state.activeRat,rat=state.rats[idx];
      state.notice=`Choose how ${rat.name} takes ${b.tyrantHits} damage: pick an untapped Upgrade to absorb it, or apply it to Health.`;
      save();render();
      const card=document.querySelector(`[data-bat-active="${idx}"]`);
      if(card){card.scrollIntoView({behavior:"smooth",block:"center"});card.classList.add("bat-target-flash");
        setTimeout(()=>card.classList.remove("bat-target-flash"),1800);
        card.querySelector("[data-apply-hits]")?.focus();}
      return;}
    if(button?.dataset.roarExhaust!==undefined){const b=state.battle;if(!b||!b.roarPending)return;
      const pick=personalDice().filter(d=>d.selected&&d.zone==="available");
      if(pick.length!==1){setNotice("Terrifying Roar: select exactly 1 available die in the shared pool, then press the button again.");
        document.getElementById("batPoolPanel")?.scrollIntoView({behavior:"smooth",block:"center"});return;}
      pick[0].zone="exhausted";pick[0].selected=false;pick[0].face="";
      b.roarPending=false;b.tyrantHits=0;b.hitTarget=null;b.turn="rats";b.rolled=false;b.revealed=false;b.attackRat=null;
      state.notice=`Terrifying Roar exhausted a ${pick[0].color} die. The Rats' turn.`;save();render();return;}
    if(button?.dataset.applyHits!==undefined){const b=state.battle;if(!b||!b.rolled||b.roarPending)return;
      const hits=b.tyrantHits,rat=state.rats[b.attackRat!=null?b.attackRat:state.activeRat]||active();
      let direct=0;
      if(b.attack===5){direct=Math.min(1,hits);}   // Crushing Blow bypasses armor
      if(b.hitTarget!==null&&b.hitTarget!==undefined){
        const j=Number(b.hitTarget),card=rat.upgrades[j];
        if(card){
          const armorHits=hits-direct;
          if(armorHits>=cardValue(card)){rat.upgrades.splice(j,1);state.discard.push(cardName(card));state.notice=`${armorHits} hits destroyed ${cardName(card)}.`;}
          else state.notice=`${armorHits} hits could not meet ${cardName(card)} (Value ${cardValue(card)}) — it holds.`;
          if(direct){rat.hp-=direct;state.notice+=` Crushing Blow put ${direct} through to Health.`;
            if(rat.hp<=0){rat.hp=0;rat.down=true;state.notice+=` ${rat.name} was knocked out.`;}}
        }
      } else {
        rat.hp-=hits;
        if(rat.hp<=0){rat.hp=0;rat.down=true;state.notice=`${rat.name} was knocked out.`;}
        else state.notice=`${rat.name} took ${hits} ${hits===1?"hit":"hits"} and is on ${rat.hp} HP.`;
      }
      // Unstable Growth: a surviving target is hit again with 2 dice, no new card.
      if(b.attack===6 && !rat.down){
        const pool=tyrantDice();let again=0;
        pool.forEach(d=>{d.selected=false;d.face="";});
        shuffle([...pool.keys()]).slice(0,2).forEach(i=>{
          pool[i].selected=true;pool[i].face=rollFace(pool[i].color);again+=faceValue(pool[i].face);});
        b.tyrantHits=again;b.hitTarget=null;b.attack=null;
        state.notice+=` Unstable Growth: the Tyrant attacks again for ${again}.`;
        save();render();return;
      }
      b.attackRat=null;
      if(state.rats[state.activeRat]?.down){
        const k=keepAttackerStanding();
        state.notice+= k>=0 ? ` ${state.rats[k].name} takes over as the attacking Rat.`
                            : ` Every Rat is knocked out — the Tyrant wins.`;
      }
      b.tyrantHits=0;b.hitTarget=null;b.turn="rats";b.rolled=false;b.revealed=false;
      tyrantDice().forEach(d=>{d.selected=false;d.face="";});
      save();render();return;}
    const noteClaim=button?.closest("[data-bat-note-claim]");
    if(noteClaim){return claimBATNote(Number(noteClaim.dataset.batNoteClaim),false);}
    const noteSpend=button?.closest("[data-bat-note-spend]");
    if(noteSpend){return claimBATNote(Number(noteSpend.dataset.batNoteSpend),true);}
    const ratZero=button?.closest("[data-rat-rollzero]");if(ratZero){return rollZero(Number(ratZero.dataset.ratRollzero));}
    const ratRoll=button?.closest("[data-rat-roll]");if(ratRoll){state.activeRat=Number(ratRoll.dataset.ratRoll);return roll();}
    const ratRecover=button?.closest("[data-rat-recover]");
    if(ratRecover&&state.returnCheck) return setNotice("Roll the borrowed die's return check first.");
    // Recovery is step 9: it needs a turn under way (turnLocked, set by the
    // roll) and the Experiment already resolved (so the card on the table is
    // the NEXT one, still at phase 0). Recovering clears turnLocked, so this
    // also makes a second press impossible - no flag to leave stale.
    if(ratRecover&&!state.turnLocked)
      return setNotice("Recovery is taken once, at the end of the turn.");
    if(ratRecover&&state.current&&state.current.phase)
      return setNotice("Resolve this Experiment before recovering.");
    if(ratRecover){const i=Number(ratRecover.dataset.ratRecover),rat=state.rats[i],extra=recBonusFor(i),rec=RAT_REC[i]+extra;let n=0;
      rat.dice.filter(d=>d.selected&&d.zone==="exhausted").slice(0,rec).forEach(d=>{d.zone="available";d.face="";d.selected=false;n++;});
      if(state.red.zone==="rolled"){state.red.zone="available";state.red.selected=false;state.red.face="";}
      // Recovering nothing is still the end of the turn.
      state.turnLocked=false;state.turnRedPlaced=false;
      // Mottle's "+1 die THIS TURN" has to go when the turn goes, whether or
      // not any dice actually came back. Clearing it only when n and extra
      // were both non-zero let the bonus ride into later turns, where
      // recBonusFor() applies it without rechecking that a Specimen is even
      // on the table - so Mottle recovered 2 on a printed REC of 1.
      state.recBonus=null;
      state.notice=n?`${rat.name} recovered ${n} ${n===1?"die":"dice"} (REC ${RAT_REC[i]}${extra?` + ${extra} from ${ratAbility(i).name}`:""}).`:`${rat.name} recovered nothing — the turn passes.`;
      save();render();return;}
    const ratAbilityBtn=button?.closest("[data-rat-ability]");
    if(ratAbilityBtn){const [i,kind]=ratAbilityBtn.dataset.ratAbility.split(":");useRatAbility(Number(i),kind);return;}
    if(button?.id==="batReadyAll") {if(state.current)return setNotice("Recover personal dice between Experiments.");personalDice().forEach(d=>{if(d.zone!=="banished"){d.zone="available";d.face="";}d.selected=false;});save();render();return;}
    if(button?.id?.startsWith("batSuccess")) return resolve("ABC".indexOf(button.id.slice(-1)));
    if(button?.id==="batFail") return resolve(null);
    if(panel&&!button) return changeRat(Number(panel.dataset.batActive));
  }

  ["pointerover","focusin"].forEach(t=>document.addEventListener(t,e=>{if(e.target.closest?.("[data-bat-held],[data-bat-splice]"))showHeldPreview(e.target);else hideHeldPreview();}));
  ["pointerout","focusout"].forEach(t=>document.addEventListener(t,hideHeldPreview,true));
  window.addEventListener("scroll",hideHeldPreview,true);
  document.addEventListener("click",handleClick,true);
  $("batDifficulty").onchange=event=>{state=fresh(event.target.value);save();ensureExperiment()||render();};
  window.addEventListener("nobulous-tier",()=>{
    if(batTier()===(state.tier||"0"))return render();
    state=fresh(state.difficulty);save();ensureExperiment()||render();
  });
  $("batRat").onchange=event=>changeRat(event.target.selectedIndex);
  window.BAT_LAB={render:()=>{ensureExperiment()||render();}};
})();
