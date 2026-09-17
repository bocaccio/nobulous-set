(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const STORE = "nobulous-bat-v2";
  const cards = window.BAT_EXPERIMENTS;
  const names = ["Rummage", "Fidget", "Whiz", "Mottle"];
  const colors = ["purple", "blue", "green", "yellow"];
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
  const faceValue = face => face === "✷" ? 2 : face === "✦" ? 1 : 0;
  const rollFace = color => faces[color][Math.floor(Math.random()*6)];
  const cardName = card => card.type === "s" ? specimens[card.i] : card.type === "u" ? upgrades[card.i][0] : "Untracked Upgrade";
  const cardValue = card => card.type === "s" ? 5 : card.type === "u" ? upgrades[card.i][1] : 0;
  const save = () => localStorage.setItem(STORE, JSON.stringify(state));
  const personalDice = () => state.rats.flatMap(rat => rat.dice);
  const active = () => state.rats[state.activeRat];
  const selected = () => personalDice().filter(die => die.selected);
  const canCommitColor = color => active().dice.some(d=>d.color===color&&d.zone==="available") ||
    (state.current?.e!==11 && state.rats.some((rat,i)=>i!==state.activeRat&&rat.dice.some(d=>d.color===color&&d.zone==="available")) &&
     [colors,colors.slice(1),colors.slice(2),colors.slice(3)][Math.min(active().upgrades.length,3)].includes(color));

  function fresh(difficulty="Standard") {
    const specimenCount = {Easy:4,Standard:5,Hard:6,Brutal:7,Nobulous:8}[difficulty];
    return {
      difficulty, deck:shuffle([...cards.keys()]),
      upgradeDeck:shuffle([...upgrades.keys()].map(i=>({type:"u",i})).concat(shuffle([...specimens.keys()]).slice(0,specimenCount).map(i=>({type:"s",i})))),
      current:null, splices:0, rounds:0, health:20, notice:"", activeRat:0,
      red:{holder:Math.floor(Math.random()*4),zone:"available",selected:false,face:""},
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
  save();

  function target() {
    const c=state.current;
    if(!c) return null;
    return Math.max(0,cards[c.e].target + (c.options.some(x=>x.type==="s")?1:0) + c.delta);
  }
  function setNotice(message) { state.notice=message; save(); render(); }
  function draw() {
    if(state.current) return setNotice("Resolve the current Experiment first.");
    if(state.splices>=5) return setNotice("The Prototyrant is awake. Begin the battle.");
    if(!state.deck.length || state.upgradeDeck.length<2) return setNotice("The Experiment or Upgrade deck is empty. Resolve the machine malfunction or begin the battle manually.");
    const e=state.deck.pop(), options=[state.upgradeDeck.pop(),state.upgradeDeck.pop()];
    const c={e,options,delta:0,phase:0,successes:0,committed:[],rolled:[],blocked:null,usedFallback:false,flipped:false,peeked:false,reduced:false,swap:null};
    state.current=c;
    if(e===2 && state.upgradeDeck.length) options.push(state.upgradeDeck.pop());
    if(e===3 && state.upgradeDeck.length>=2) c.options=[state.upgradeDeck.pop(),state.upgradeDeck.pop()];
    if(e===4) state.deck.splice(Math.max(0,state.deck.length-2),2);
    if(e===10) {state.red.holder=state.activeRat;state.red.zone="available";state.red.selected=false;}
    state.notice = e===3 ? "The original Upgrades were discarded and replaced." : e===4 ? "Two Experiments were discarded unseen." : "Choose the active Rat, then apply any effect shown below.";
    save(); render();
  }

  function changeRat(index) {
    if(state.current?.phase || state.current?.flipped || state.current?.blocked) return setNotice("Finish this Experiment's setup before changing the active Rat.");
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
    if(action==="load-redraw" && c.e===5 && !c.phase) {if(canCommitColor("purple"))return setNotice("A Purple die is available to commit.");state.current=null;state.notice="Load-Bearing Trial discarded. Revealed Upgrades were replaced.";save();draw();return;}
    if(action==="rapid-fallback" && c.e===7 && !c.phase && !c.usedFallback && c.options.length>1) {if(canCommitColor("green"))return setNotice("A Green die is available to commit.");const discarded=c.options.splice(strongerIndex(c.options),1)[0];c.usedFallback=true;state.notice=`${cardName(discarded)} was discarded. Continue with the remaining Upgrade.`;}
    if(action==="exclude" && c.e===14 && !c.phase && !c.blocked) {const available=rat.dice.filter(d=>d.zone==="available");if(!available.length)return setNotice("No personal die is available to exclude.");const die=available[Math.floor(Math.random()*available.length)];c.blocked=die.id;die.selected=false;state.notice=`${rat.name}'s ${die.color} die was randomly excluded.`;}
    if(action==="peek" && c.e===6 && !c.peeked && c.committed.includes("blue")) {c.peeked=true;state.notice=state.deck.length?`Next Experiment: ${cards[state.deck[state.deck.length-1]].name} · Target ${cards[state.deck[state.deck.length-1]].target}. It remains on top.`:"The Experiment deck is empty.";}
    if(action==="contain" && c.e===15 && !c.phase && !c.reduced) {
      const yellow=rat.dice.find(d=>d.color==="yellow"&&d.zone==="available");
      if(!yellow) return setNotice("The active Rat needs an available Yellow die for this option.");
      c.reduced=true;c.delta=-2;
      if(faceValue(rollFace("yellow"))) {
        const blue=rat.dice.find(d=>d.color==="blue"&&d.zone==="available") || personalDice().find(d=>d.color==="blue"&&d.zone==="available");
        if(blue) {blue.zone="banished";blue.selected=false;state.notice=`Target reduced by 2; ${blue.id}'s Blue die was banished.`;}
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
    if(die.zone==="available") die.selected=!die.selected;
    else if(c?.phase===1 && c.rolled.includes(id) && die.face==="" && c.e!==16) die.selected=!die.selected;
    else if(die.zone==="exhausted" && !c) {die.zone="available";die.face="";die.selected=false;}
    save();render();
  }

  function validateRoll(dice,redSelected) {
    const c=state.current;
    if(!c) return "Reveal an Experiment first.";
    if(c.phase>=2 || (c.phase===1&&c.e===16)) return "No Strategy phase remains for this Experiment.";
    if(c.e===0&&!c.flipped) return "Flip the active Lab Rat first.";
    if(c.e===14&&!c.blocked) return "Randomly exclude an available die first.";
    if(c.e===10&&redSelected) return "Red cannot be used for this Experiment.";
    if(redSelected&&state.red.holder!==state.activeRat) return "Only the active Rat holding Red can commit it.";
    if(c.e===12&&c.phase===1&&dice.some(d=>d.zone==="available")) return "No additional dice may be committed in the second Strategy phase.";
    const borrowed=dice.filter(d=>!d.id.startsWith(`rat-${state.activeRat}-`));
    if(borrowed.length>1 || (c.borrowedId && borrowed.some(d=>d.id!==c.borrowedId))) return "Borrow at most one die from another Rat for the whole Experiment.";
    if(c.e===11&&borrowed.length) return "Borrowing is prohibited by this Experiment.";
    const allowed=[colors,colors.slice(1),colors.slice(2),colors.slice(3)][Math.min(active().upgrades.length,3)];
    if(borrowed.some(d=>!allowed.includes(d.color))) return "That borrowed color is not allowed with this Rat's Upgrade count.";
    if(c.e===9&&c.committed.length+dice.filter(d=>d.zone==="available").length+(redSelected?1:0)>2) return "Only two dice may be committed to this Experiment.";
    return "";
  }

  function roll() {
    const c=state.current;
    const dice=selected();
    const redSelected=state.red.selected&&state.red.zone==="available";
    const error=validateRoll(dice,redSelected);
    if(error) return setNotice(error);
    if(!dice.length&&!redSelected) {if(!c.phase){c.phase=1;state.notice="No dice committed. You may resolve this as a failure.";save();render();}return;}
    let gained=0, forced=0;
    for(const die of dice) {
      const isNew=die.zone==="available";
      die.face=rollFace(die.color);
      if(c.e===13&&c.phase===0&&["purple","blue"].includes(die.color)&&faceValue(die.face)) {die.face=rollFace(die.color);forced++;}
      gained+=faceValue(die.face);
      die.zone="exhausted";die.selected=false;
      if(isNew) {c.committed.push(die.color);c.rolled.push(die.id);if(!die.id.startsWith(`rat-${state.activeRat}-`))c.borrowedId=die.id;}
    }
    if(redSelected){state.red.face=rollFace("red");state.red.zone="setaside";state.red.selected=false;c.committed.push("red");gained+=faceValue(state.red.face);}
    c.successes+=gained;c.phase++;
    state.notice=`Strategy phase ${c.phase}: ${gained} success${gained===1?"":"es"}${forced?`; ${forced} Purple/Blue hit${forced===1?"":"s"} rerolled by Reliability Trial`:""}. Total ${c.successes} / ${target()}.`;
    save();render();
  }

  function canSucceed() {
    const c=state.current;
    if(!c||!c.phase||c.successes<target()) return false;
    if(c.e===1&&!c.usedFallback&&!c.committed.includes("yellow")) return false;
    if(c.e===5&&!c.committed.includes("purple")) return false;
    if(c.e===7&&!c.usedFallback&&!c.committed.includes("green")) return false;
    if(c.e===8&&new Set(c.committed).size<3) return false;
    return true;
  }

  function resolve(choice) {
    const c=state.current;
    if(!c) return;
    if(choice!==null&&!canSucceed()) return setNotice("The roll has not met this Experiment's Target and commitment requirements.");
    if(choice!==null&&!c.options[choice]) return;
    if(choice!==null) {
      state.notice="";
      let kept=c.options[choice];
      if(c.e===18&&c.reduced) {
        const values=c.options.map(cardValue), high=Math.max(...values), low=Math.min(...values);
        if(high!==low) kept=c.options[values.indexOf(low)];
        else kept=c.options[choice];
        state.splices++;
        state.notice=`${cardName(c.options[values.indexOf(high)])} was Spliced into the Prototyrant. `;
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
      state.splices++;
      state.notice=`Failure: ${cardName(c.options[strongerIndex(c.options)])} was Spliced into the Prototyrant.`;
    }
    if(c.borrowedId){const borrowed=personalDice().find(d=>d.id===c.borrowedId);if(borrowed&&!faceValue(rollFace(borrowed.color))){borrowed.zone="banished";state.notice+=" The borrowed die was banished on its return check.";}}
    state.rounds++;state.current=null;
    personalDice().forEach(d=>d.selected=false);state.red.selected=false;
    save();render();
  }

  function setSprite(el,card) {
    if(!card){el.removeAttribute("style");el.classList.add("placeholder-card");el.innerHTML="<span>Upgrade</span>";return;}
    const specimen=card.type==="s",cols=specimen?8:10,rows=specimen?1:2;
    const col=card.i%cols,row=Math.floor(card.i/cols);
    el.classList.remove("placeholder-card");el.innerHTML="";
    el.style.backgroundImage=`url('assets/${specimen?"BAT_Specimens_TTS.png":"BAT_Upgrades_TTS.png"}')`;
    el.style.backgroundSize=`${cols*100}% ${rows*100}%`;
    el.style.backgroundPosition=`${cols===1?0:col/(cols-1)*100}% ${rows===1?0:row/(rows-1)*100}%`;
  }

  function renderRats() {
    const host=$("batRats");host.innerHTML="";
    state.rats.forEach((rat,i)=>{
      const c=state.current;
      const dieButton=die=>`<button class="rat-die ${die.color} ${die.zone} ${die.selected?"selected":""} ${c?.blocked===die.id?"blocked":""} ${c?.phase===1&&c.rolled.includes(die.id)&&die.face===""?"eligible-reroll":""}" data-bat-die="${die.id}" title="${die.color} · ${die.zone}">${die.face||""}</button>`;
      const available=rat.dice.filter(d=>d.zone==="available").map(dieButton).join("");
      const exhausted=rat.dice.filter(d=>d.zone==="exhausted").map(dieButton).join("");
      const red=state.red.holder===i&&state.red.zone==="available"?`<button class="rat-die red ${state.red.selected?"selected":""} ${c?.e===10?"blocked":""}" data-bat-red="1" title="Communal Red die">${state.red.face||""}</button>`:"";
      const box=document.createElement("article");box.className=`bat-rat ${state.activeRat===i?"active":""}`;box.dataset.batActive=i;
      box.innerHTML=`<div class="bat-rat-head"><h3>${rat.name}</h3><button data-rat-side="${i}">Side ${rat.side==="front"?"A":"B"}</button></div><div class="suite-card landscape bat-rat-card"></div><div class="bat-dice-summary"><span>${rat.hp} HP</span><span>${rat.upgrades.length} Upgrades</span><span>${rat.dice.filter(d=>d.zone==="banished").length} Banished</span></div><div class="rat-dice-zones"><div class="rat-dice-zone"><h4>Available</h4><div class="rat-dice-row">${available}${red}</div></div><div class="rat-dice-zone"><h4>Exhausted</h4><div class="rat-dice-row">${exhausted}</div></div></div><div class="bat-rat-actions"><button data-move-red="${i}">Move Red here</button><button data-rat-hp="${i}" data-delta="-1">− HP</button><button data-rat-hp="${i}" data-delta="1">+ HP</button></div>`;
      const sprite=box.querySelector(".bat-rat-card"),col=i;
      sprite.style.backgroundImage=`url('assets/${rat.side==="front"?"BAT_Rats_TTS.png":"BAT_Rats_TTS_back.png"}')`;
      sprite.style.backgroundSize="400% 100%";sprite.style.backgroundPosition=`${col/3*100}% 0`;
      host.appendChild(box);
    });
  }

  function renderEffect() {
    const host=$("batEffect"),c=state.current;
    if(!c){host.innerHTML=`<p>${escape(state.notice||"Reveal an Experiment to see its effect controls.")}</p>`;return;}
    const card=cards[c.e],actions=[];
    if(c.e===0&&!c.flipped) actions.push(`<button data-bat-action="flip">Flip active Rat</button>`);
    if(c.e===1&&!c.phase&&!c.usedFallback) actions.push(`<button data-bat-action="fine-fallback">Yellow unavailable · +1 Target</button>`);
    if(c.e===5&&!c.phase) actions.push(`<button data-bat-action="load-redraw">Purple unavailable · draw replacement</button>`);
    if(c.e===6&&c.committed.includes("blue")&&!c.peeked) actions.push(`<button data-bat-action="peek">Look at next Experiment</button>`);
    if(c.e===7&&!c.phase&&!c.usedFallback) actions.push(`<button data-bat-action="rapid-fallback">Green unavailable · discard stronger Upgrade</button>`);
    if(c.e===14&&!c.phase&&!c.blocked) actions.push(`<button data-bat-action="exclude">Randomly exclude active Rat die</button>`);
    if(c.e===15&&!c.phase&&!c.reduced) actions.push(`<button data-bat-action="contain">Reduce Target by 2 and roll Yellow</button>`);
    if(c.e===18&&!c.phase&&!c.reduced) actions.push(`<button data-bat-action="method">Reduce Target to 0</button>`);
    if(c.e===17&&canSucceed()&&active().upgrades.length&&c.options.some(x=>x.type==="u")) {
      actions.push(`<label>Held Upgrade to swap <select id="batSwapFrom">${active().upgrades.map((u,i)=>`<option value="${i}">${escape(cardName(u))}</option>`).join("")}</select></label>`);
      actions.push(`<label>Revealed Upgrade to take <select id="batSwapTo">${c.options.map((u,i)=>u.type==="u"?`<option value="${i}">${escape(cardName(u))}</option>`:"").join("")}</select></label>`);
      actions.push(`<button data-bat-action="swap">Plan optional swap</button>`);
    }
    host.innerHTML=`<h3>${escape(card.name)} · Target ${target()}</h3><p>${escape(card.effect)}</p><p class="hint">${escape(state.notice)}</p><div class="compact-actions">${actions.join("")}</div>`;
  }

  function render() {
    $("batDifficulty").value=state.difficulty;$("batRat").selectedIndex=state.activeRat;
    $("batOverlay").textContent="Experiment deck · Prototyrant research";
    $("batStats").innerHTML=`<div class="suite-stat"><span>Splices</span><strong>${state.splices} / 5</strong></div><div class="suite-stat"><span>Experiments</span><strong>${state.rounds}</strong></div><div class="suite-stat"><span>Deck</span><strong>${state.deck.length}</strong></div><div class="suite-stat"><span>Prototyrant HP</span><strong>${state.health}</strong></div><div class="suite-stat"><span>Red</span><strong>${state.red.zone==="setaside"?"Set aside":names[state.red.holder]}</strong></div>`;
    $("batDraw").disabled=!!state.current||state.splices>=5;
    renderRats();renderEffect();
    const c=state.current,el=$("batEncounter"),caption=$("batEncounterText");
    if(c){
      const card=cards[c.e];el.classList.remove("placeholder-card");el.removeAttribute("style");el.classList.add("bat-experiment-card");
      el.innerHTML=`<header>${escape(card.name)}<small>Build-a-Tyrant Experiment</small></header><div class="target-number">${target()}</div><div class="target-label">Target</div><div class="experiment-effect">${escape(card.effect)}</div><div class="experiment-flavor">${escape(card.flavor)}</div><footer>Specimen revealed: +1 Target total (once).</footer>`;
      caption.textContent=`${c.successes} ${c.successes===1?"success":"successes"} · Strategy phase ${c.phase} of ${c.e===16?1:2} · ${c.committed.length} dice committed`;
    } else {el.classList.remove("bat-experiment-card");el.classList.add("placeholder-card");el.removeAttribute("style");el.innerHTML=`<span>${state.splices>=5?"Prototyrant awake — begin battle":"Reveal an Experiment"}</span>`;caption.textContent="";}
    ["A","B","C"].forEach((letter,i)=>{if(letter==="C")$("batUpgradeCPanel").classList.toggle("hidden",!(c?.options[2]));setSprite($("batUpgrade"+letter),c?.options[i]);const button=$("batSuccess"+letter);button.disabled=!c?.options[i]||!canSucceed();if(letter==="C")button.classList.toggle("hidden",!(c?.options[2]));});
    $("batFail").disabled=!c;
    $("batRoller").innerHTML=`<div class="roller-head"><div><p class="kicker">Strategy phase ${c?Math.min(c.phase+1,c.e===16?1:2):1}</p><h2>${active().name} · ${selected().length+(state.red.selected?1:0)} selected</h2></div><div class="compact-actions"><button id="batRollSelected" class="primary" ${!c||c.phase>=2||(c.phase===1&&c.e===16)?"disabled":""}>Roll selected</button><button id="batBanishSelected">Banish selected</button><button id="batReadyAll">Ready personal dice</button></div></div><div class="roll-result">${c?`${c.successes} successes toward Target ${target()}. Select available dice; after the first roll, select highlighted misses to reroll.`:"Reveal an Experiment to begin."}</div>`;
  }

  function handleClick(event) {
    if(!event.target.closest("#screen-bat")) return;
    const button=event.target.closest("button");
    const panel=event.target.closest(".bat-rat");
    if(!button&&!panel) return;
    if(button&&!button.matches("[data-new-game='bat'],[data-bat-die],[data-bat-red],[data-move-red],[data-rat-side],[data-rat-hp],[data-bat-action],#batDraw,#batBattle,#batRollSelected,#batBanishSelected,#batReadyAll,#batSuccessA,#batSuccessB,#batSuccessC,#batFail")) return;
    event.preventDefault();event.stopImmediatePropagation();
    if(button?.dataset.newGame==="bat") {state=fresh(state.difficulty);save();render();return;}
    if(button?.id==="batDraw") return draw();
    if(button?.id==="batBattle") {state.splices=Math.max(5,state.splices);save();render();return;}
    if(button?.dataset.batDie) return chooseDie(button.dataset.batDie);
    if(button?.dataset.batRed) {if(state.current?.e===10)return setNotice("Red cannot be used for this Experiment.");state.red.selected=!state.red.selected;save();render();return;}
    if(button?.dataset.moveRed!==undefined) {if(state.current?.e===10)return setNotice("Restricted Materials keeps Red on the active Rat.");state.red.holder=Number(button.dataset.moveRed);state.red.zone="available";state.red.selected=false;save();render();return;}
    if(button?.dataset.ratSide!==undefined) {const rat=state.rats[Number(button.dataset.ratSide)];rat.side=rat.side==="front"?"back":"front";save();render();return;}
    if(button?.dataset.ratHp!==undefined) {const rat=state.rats[Number(button.dataset.ratHp)];rat.hp=Math.max(0,rat.hp+Number(button.dataset.delta));save();render();return;}
    if(button?.dataset.batAction) return effectAction(button.dataset.batAction);
    if(button?.id==="batRollSelected") return roll();
    if(button?.id==="batBanishSelected") {selected().forEach(d=>{d.zone="banished";d.selected=false;d.face="";});save();render();return;}
    if(button?.id==="batReadyAll") {if(state.current)return setNotice("Recover personal dice between Experiments.");personalDice().forEach(d=>{if(d.zone!=="banished"){d.zone="available";d.face="";}d.selected=false;});save();render();return;}
    if(button?.id?.startsWith("batSuccess")) return resolve("ABC".indexOf(button.id.slice(-1)));
    if(button?.id==="batFail") return resolve(null);
    if(panel&&!button) return changeRat(Number(panel.dataset.batActive));
  }

  document.addEventListener("click",handleClick,true);
  $("batDifficulty").onchange=event=>{state=fresh(event.target.value);save();render();};
  $("batRat").onchange=event=>changeRat(event.target.selectedIndex);
  window.BAT_LAB={render};
})();
