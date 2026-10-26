(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const ASSET = "assets/";
  const STORE = "nobulous-suite-v1";
  const COLORS = ["purple","purple","purple","purple","blue","blue","blue","blue","green","green","green","green","yellow","yellow","yellow","yellow","red"];
  const FACE = {
    purple:["✦","✦","✦","✦","✷",""], blue:["✦","✦","✦","✷","",""],
    green:["✦","✦","✷","","",""], yellow:["✦","✷","","","",""], red:["✦","✦","✦","✦","✦","✷"]
  };
  const NAP_TASKS = [
    ["Organize the Specimen Cabinet",2,3,"Y",0],["Prepare the Tissue Samples",3,5,"G",1],["Calibrate the Neural Imager",4,5,"B",1],["Stabilize the Prototype Brain",5,7,"P",2],["Sterilize the Surgical Tools",3,4,"Y",0],["Label the Neural Samples",3,4,"G",0],["Monitor the Growth Vats",3,5,"B",0],["Tune the Cranial Resonator",5,6,"P",0],["Prepare the Transplant Rig",4,5,"G",1],["Align the Memory Probes",4,9,"B",1],["Test the Cerebral Coupler",4,5,"B",1],["Recalibrate the Bone Saw",4,9,"P",1],["Prime the Synaptic Pump",5,9,"P",1],["Map the Council Brain",6,7,"P",1],["Condition the Donor Tissue",3,5,"Y",1],["Verify the Identity Matrix",4,9,"B",2],["Complete the Splice Protocol",5,7,"P",2],["Document the Procedure",3,4,"G",0],["Suture the Donor Incision",4,9,"Y",1],["Decode Nobulous' Lecture Notes",4,5,"G",0],["Update Nobulous' Lab Notes",3,4,"Y",0],["Inventory the Spare Organs",3,4,"G",0],["Clean the Restraint Table",4,5,"B",0],["Reassemble the Automaton Hand",6,8,"P",1],["Dispose of Failed Samples",4,9,"B",1],["Sharpen the Surgical Implements",4,5,"P",0]
  ];
  const NAP_OPPS = ["Take an Unauthorized Break","Raid the Supply Closet","Borrow Better Instruments","Study Nobulous' Notes","Salvage Useful Components","Practice on a Spare Brain"];
  const NAP_REQUEST_EFFECTS = [
    "If completed with exactly 2 successes across all committed dice this strategy phase, recover 1 committed die.","If completed using 3 or fewer dice, recover 1 committed die.","One Blue Crit counts as 3 successes here.","If dice of 3+ colors contribute, add 1 success.","If completed without using a Crit, recover 1 committed die.","If this is the Primary, add 1 success after rolling.","If Exact, gain 1 Health.","Purple Crits count as 3 successes here.","If Exact, recover 1 committed die.","If you exactly meet the target, recover 1 committed die.","If Exact, recover 1 committed die.","One Purple Crit counts as 3 successes here.","If completed using exactly 3 dice, recover 1 committed die.","If completed as a Request, permanently increase REC by 1.","If completed in one attempt, recover 1 committed die.","If dice of 3+ colors contribute, add 1 success.","If completed with no stored dice, recover 1 committed die.","If completed as Primary, recover 1 committed die.","If completed using exactly 4 dice, recover 1 committed die.","Look at the next 3 Assignment cards and return them in any order.","Look at the next Assignment; return it to the top or bottom.","If completed, recover 1 exhausted Yellow or Green die.","If completed using 4 or fewer dice, recover 1 committed die.","If completed as a Request, permanently increase STR by 1.","If completed in one attempt, recover 1 exhausted die.","If completed using a Crit, recover 1 committed die."
  ];
  // A completed Opportunity is kept as a coupon. `progress` is the number of
  // successes it is worth when spent on an Assignment; untargeted coupons
  // instead set a flag the dice rules read.
  // Final Exams, in deck order: name, subject, dot, base Target, printed
  // restriction, and the machine-checkable form of that restriction.
  //   noRed        Red may not be committed
  //   minColors    distinct colors among committed dice
  //   minDice      committed dice
  //   needCrit     at least one Crit among the successes
  //   contribute   {color: count} of SUCCESSFUL dice required
  //   contributeAny [[colors], count] of successful dice across those colors
  //   scoring      a printed change to how successes are counted
  const NAP_EXAMS = [
    ["Cranial Integrity Inspection","Anatomy","B",5,"Commit dice of at least 3 different colors.",{minColors:3}],
    ["Fine Motor Assessment","Anatomy","Y",6,"At least 1 Yellow and 1 Blue die must contribute.",{contribute:{yellow:1,blue:1}}],
    ["Physiological Stress Test","Anatomy","P",6,"At least 2 Blue/Purple dice total must contribute.",{contributeAny:[["blue","purple"],2]}],
    ["Council Etiquette Simulation","Theory","G",5,"Red cannot be committed; use at least 3 colors.",{noRed:true,minColors:3}],
    ["Identity Recall Demonstration","Theory","P",6,"At least 1 Blue and 1 Purple die must contribute.",{contribute:{blue:1,purple:1}}],
    ["Final Impostor Examination","Theory","Y",7,"Use at least 4 different colors. A Red Crit counts as 1 success.",{minColors:4,scoring:"redCrit1"}],
    ["Neural Response Screening","Engineering","G",5,"At least 1 Crit must contribute to complete this Assignment.",{needCrit:true}],
    ["Adaptive Reasoning Trial","Engineering","B",6,"Commit at least 4 dice. One Yellow Crit counts as 3 successes.",{minDice:4,scoring:"yellowCrit3"}],
    ["Council Recognition Drill","Engineering","B",6,"Red cannot be committed. At least 1 Purple die must contribute.",{noRed:true,contribute:{purple:1}}],
    ["Procedural Knowledge Review","Procedure","Y",6,"Red cannot be committed; use at least 3 different colors.",{noRed:true,minColors:3}],
    ["Unexpected Policy Debate","Procedure","P",7,"Commit at least 4 dice from at least 3 different colors.",{minDice:4,minColors:3}],
    ["Nobulous' Comprehensive Review","Procedure","G",7,"Commit at least 5 dice from at least 3 different colors.",{minDice:5,minColors:3}],
  ];
  // --- NRJ module cards for NAP -------------------------------------
  // Carried on an Assignment as {type, i, nrj:true}: a module card keeps the
  // base type so every Setback/Task/Opportunity rule still applies to it.
  const NAP_FOLLOWING = [
    ["Nobulous Needs This Now","Y",7,"While unresolved, the first die you commit to another Assignment each Time Slot must match that Assignment's recovery-color dot."],
    ["Unscheduled Demonstration","G",7,"While unresolved, you must commit at least one die here before committing dice to another Assignment in this Time Slot."],
    ["Minor Laboratory Fire","B",8,"At the end of each Time Slot this remains unresolved, exhaust 1 available die."],
    ["Where Did I Put That?","P",8,"While unresolved, one die committed here cannot be recovered by Special Recovery."],
  ];
  const NAP_IMPOSTOR = [
    ["Neural Extraction Practicum","Anatomy",5,6,"One die committed here remains locked until the end of the Day even if completed."],
    ["Load-Bearing Prosthetics","Engineering",4,5,"At least 2 applied successes must come from the same color."],
    ["Emergency Specimen Handling","Procedure",4,5,"Before rolling, commit at least 2 dice initially."],
    ["Containment Drill","Theory",4,5,"If unresolved, exhaust 1 available die before flipping it to Demand."],
  ];
  // Devious Opportunities. "exam" cards are kept and spent during the Final
  // Exam; "now" cards resolve on completion.
  const NAP_DEVIOUS = [
    ["Borrow the Master's Notes","G",3,"Exhaust 2 available dice to immediately complete one Request-side non-Credit Task with printed Target 3 or less.","now"],
    ["Raid the Supply Cabinet","Y",3,"Final Exam: recover 3 exhausted dice of different colors before any one exam.","exam"],
    ["Extra Credit?","G",3,"Gain 1 Credit in the subject of the most recently completed Task; then reveal an additional Assignment.","now"],
    ["Helpful Test Subject","B",3,"Final Exam: after rolling one exam, reroll any number of failed dice.","exam"],
    ["Nobulous Owes You One","P",4,"Final Exam: reduce one exam's Target by 3.","exam"],
    ["Definitely Curriculum-Approved","Y",3,"Final Exam: ignore one exam's printed restriction.","exam"],
  ];
  function napTier(){return window.NOBULOUS_TIER?window.NOBULOUS_TIER.forGame("nap"):"0";}
  function napExamCard(i){const e=NAP_EXAMS[i];return{name:e[0],file:"NAP_FinalExams_TTS.png",i,cols:10,rows:2,target:e[3],demand:e[3],dot:e[2],skulls:0};}
  const NAP_COUPONS = [
    {effect:"Cancel 1 Health loss.",progress:0},
    {effect:"One die counts as any color for one roll.",progress:0},
    {effect:"Add 1 success to a roll.",progress:1},
    {effect:"Reduce one Assignment's remaining need by 2.",progress:2},
    {effect:"Add 2 successes to an Assignment, without rolling.",progress:2},
    {effect:"One Crit counts as 3 successes.",progress:0}];
  const NAP_OPPORTUNITY_EFFECTS = NAP_COUPONS.map(c=>`Spend: ${c.effect}`);
  const NAP_TASK_SUBJECTS = ["Theory","Anatomy","Engineering","Anatomy","Procedure","Theory","Anatomy","Engineering","Engineering","Engineering","Engineering","Procedure","Procedure","Anatomy","Anatomy","Theory","Procedure","Theory","Procedure","Theory",null,null,null,null,null,null];
  const NAP_SUBJECTS = ["Anatomy","Engineering","Procedure","Theory"];
  const NAP_SUBJECT_ICONS = {
    Anatomy:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.3l-1.7-1.6C5.1 15 2 12.2 2 8.7 2 5.9 4.1 3.8c1.6 0 3.1.7 4 1.9.9-1.2 2.4-1.9 4-1.9C17.9 3.8 20 5.9 20 8.7c0 3.5-3.1 6.3-8.3 11z"/></svg>',
    Engineering:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8.4a3.6 3.6 0 100 7.2 3.6 3.6 0 000-7.2zm9 4.5v-1.8l-2.2-.5a7 7 0 00-.6-1.5l1.2-1.9-1.3-1.3-1.9 1.2a7 7 0 00-1.5-.6L14.2 4h-1.8l-.5 2.5a7 7 0 00-1.5.6L8.5 5.9 7.2 7.2l1.2 1.9a7 7 0 00-.6 1.5L5.4 11v1.8l2.4.5a7 7 0 00.6 1.5l-1.2 1.9 1.3 1.3 1.9-1.2a7 7 0 001.5.6l.5 2.4h1.8l.5-2.4a7 7 0 001.5-.6l1.9 1.2 1.3-1.3-1.2-1.9a7 7 0 00.6-1.5z"/></svg>',
    Procedure:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.7 3.3a1 1 0 00-1.4 0l-9 9-1.3 3.4a.6.6 0 00.8.8l3.4-1.3 9-9a1 1 0 000-1.4zM8.6 15.9l-4 4a1.4 1.4 0 102 2l4-4z"/></svg>',
    Theory:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4.4h6.2c1 0 1.8.8 1.8 1.8v13c0-.8-.8-1.4-1.8-1.4H4zm16 0h-6.2c-1 0-1.8.8-1.8 1.8v13c0-.8.8-1.4 1.8-1.4H20z"/></svg>'
  };
  const NAP_SETBACKS = [["Power Failure",6,"Y"],["Contaminated Workbench",6,"G"],["Jammed Centrifuge",7,"G"],["Broken Neural Imager",7,"B"],["Escaped Specimen",8,"B"],["Automaton Malfunction",8,"P"]];
  const SCENARIOS = [
    ["The Physician's Greeting","Knowledge","Anatomy",8,"The first NAP card spent also performs Special Recovery."],["An Old Injury","Knowledge","Anatomy",9,"At least 2 Purple or Blue dice must contribute."],["The Chamber Mechanism","Knowledge","Engineering",8,"Success: recover 2 exhausted dice."],["Failed Apparatus","Knowledge","Engineering",10,"Failure: place two cards in Suspicion."],["Order of Precedence","Knowledge","Procedure",9,"Commit at least 3 different colors."],["The Vote","Knowledge","Procedure",8,"Success: recover all exhausted dice of one color."],["A Disputed Citation","Knowledge","Theory",9,"Suspicion does not increase this Target."],["The Long Argument","Knowledge","Theory",10,"Spend at most one NAP card."],["The Ceremonial Seal","Physical","Power",8,"At least one Purple die must contribute."],["An Unwelcome Embrace","Physical","Power",9,"+1 STR for this Scenario."],["The Narrow Stair","Physical","Mobility",8,"Success: next Scenario Target −1."],["A Sudden Fall","Physical","Mobility",10,"Cannot be avoided with an AoS card."],["The Long Session","Physical","Defense",9,"Commit at least 6 dice."],["Tainted Wine","Physical","Defense",10,"Failure must lose 1 Health."],["Across the Chamber","Physical","Senses",8,"Look at the next Scenario before rolling."],["The Darkened Corridor","Physical","Senses",9,"Yellow dice cannot contribute."],["Tracks in the Yard","Cover-Up","Approach",8,"Success: recover one die of each of two colors."],["The Night Watchman's Account","Cover-Up","Approach",9,"A Crit counts as 3 successes."],["An Open Window","Cover-Up","Concealment",8,"At least 3 different colors must contribute."],["Someone Was Seen","Cover-Up","Concealment",10,"If avoided, put it on top instead of bottom."],["Rope Burns","Cover-Up","Restraint",9,"Discard one Research card at random before rolling."],["The Sedative Ledger","Cover-Up","Restraint",9,"Success: recover 3 exhausted dice."],["The Missing Hours","Cover-Up","Extraction",10,"An additional +1 Target per Suspicion."],["A Second Search","Cover-Up","Extraction",8,"Remove one Suspicion, then attempt normally."]
  ];

  const shuffle = a => { a=[...a]; for(let i=a.length-1;i;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; };
  const freshDice = () => COLORS.map((color,id)=>({id,color,zone:"available",selected:false,face:""}));
  const fresh = () => ({
    config:{mode:"standalone",tier:"0",finale:"sample",tierOverride:{bat:"",nap:"",aos:""}},
    nap:{day:1,slot:0,hp:2,str:2,rec:2,credits:0,creditGoal:6,coupons:[],deviousCoupons:[],couponWild:false,distinctRecover:false,phase:"apprenticeship",exam:null,outcome:null,completedCredits:[],apprentice:"Prodigy",deck:[],discard:[],rows:[[],[],[]],recoveryDots:[null,null,null],primaryDot:null,choice:null,finf:{mode:"reduce",level:1,cards:[0],spent:[],drawn:[],pendingCurrent:[]},pendingReward:null,nextSlotBonus:{str:0,rec:0,crit:0},activeSlotBonus:{str:0,rec:0,crit:0},notice:"",dice:freshDice(),rollsUsed:0,phaseCommittedSuccesses:0,recovering:false,rollResult:""},
    nrj:{hp:4,str:2,rec:3,attempts:0,suspicion:0,deck:[],discard:[],current:null,pool:18,eligibleAvoid:3,dice:freshDice(),nextDiscount:0}
  });
  let state=fresh();
  let napPileView="deck";
  try{const s=JSON.parse(localStorage.getItem(STORE));if(s)state={...fresh(),...s,config:{...fresh().config,...s.config}};}catch(_){ }
  if(state.nap.notice===undefined)state.nap.notice="";
  if(!Array.isArray(state.nap.rows)){state.nap.rows=[[],[],[]];if(Array.isArray(state.nap.row))state.nap.rows[state.nap.slot||0]=state.nap.row;delete state.nap.row;}
  state.nap.rows=state.nap.rows.map(row=>row.map(a=>({...a,storedDice:a.storedDice||[]})));
  state.nap.completedCredits??=state.nap.rows.flat().filter(a=>a.completed&&a.type==="t").map(a=>({type:"t",i:a.i}));
  state.nap.rollsUsed??=0;state.nap.phaseCommittedSuccesses??=0;state.nap.recovering??=false;state.nap.rollResult??="";
  state.nap.recoveryDots??=[null,null,null];
  state.nap.primaryDot??=null;
  state.nap.discard??=[];state.nap.pendingReward??=null;if(state.nap.pendingReward&&!state.nap.pendingReward.cardType)state.nap.pendingReward={...state.nap.pendingReward,cardType:"o",cardIndex:state.nap.pendingReward.kind==="distinct"?1:4,text:state.nap.pendingReward.kind==="distinct"?NAP_OPPORTUNITY_EFFECTS[1]:NAP_OPPORTUNITY_EFFECTS[4]};state.nap.creditGoal??=6;state.nap.coupons??=[];state.nap.deviousCoupons??=[];state.nap.distinctRecover??=false;state.nap.couponWild??=false;state.nap.phase??="apprenticeship";state.nap.exam??=null;state.nap.outcome??=null;state.nap.recoverOverride??=null;state.nap.nextSlotBonus??={str:0,rec:0,crit:0};state.nap.activeSlotBonus??={str:0,rec:0,crit:0};state.nrj.discard??=[];
  state.nap.finf={mode:"reduce",level:1,cards:[0],spent:[],drawn:[],pendingCurrent:[],...state.nap.finf};
  const mf=state.nap.finf;
  // Saves from the single-card FINF: start again at Standard.
  if(mf.cards===undefined||mf.level===undefined){
    mf.mode="reduce";mf.level=1;mf.cards=[0];mf.spent=[];mf.drawn=[];
    state.nap.deck=(state.nap.deck||[]).filter(c=>c.type!=="f");
  }
  state.nap.apprentice??="Prodigy";
  const save=()=>localStorage.setItem(STORE,JSON.stringify(state));
  function repairNAPSetbackRecovery(){
    const n=state.nap;let repaired=false;
    n.recoveryDots=n.recoveryDots.map((dot,slot)=>{
      if(dot!=="—")return dot;
      const primary=n.rows[(slot+2)%3]?.find(a=>a.source==="primary");
      if(primary?.type!=="s")return dot;
      repaired=true;return NAP_SETBACKS[primary.i][2];
    });
    if(n.primaryDot==="—"){
      const primary=n.rows[n.slot]?.find(a=>a.source==="primary");
      if(primary?.type==="s"){n.primaryDot=NAP_SETBACKS[primary.i][2];repaired=true;}
    }
    if(repaired)save();
  }
  repairNAPSetbackRecovery();

  function setSprite(el,file,index,cols,rows){const col=index%cols,row=Math.floor(index/cols),version=ART_VERSION;el.classList.remove("placeholder-card");el.innerHTML="";el.style.backgroundImage=`url('${ASSET}${file}${version}')`;el.style.backgroundSize=`${cols*100}% ${rows*100}%`;el.style.backgroundPosition=`${cols===1?0:col/(cols-1)*100}% ${rows===1?0:row/(rows-1)*100}%`;}
  function clearSprite(el,text){el.removeAttribute("style");el.classList.add("placeholder-card");el.innerHTML=`<span>${text}</span>`;}
  function stat(label,value){return `<div class="suite-stat"><span>${label}</span><strong>${value}</strong></div>`;}
  function renderDiscard(prefix,entries,label){$(prefix+"DiscardCount").textContent=entries.length;$(prefix+"DiscardTop").textContent=entries.length?label(entries.at(-1)):"Empty";$(prefix+"DiscardList").replaceChildren(...entries.slice().reverse().map(entry=>{const li=document.createElement("li");li.textContent=label(entry);return li;}));}
  function napSubject(card){return card.type==="t"?NAP_TASK_SUBJECTS[card.i]:null;}
  function subjectBadge(subject){const badge=document.createElement("span");badge.className=`nap-subject-badge ${subject?subject.toLowerCase():"unmarked"}`;badge.innerHTML=subject?NAP_SUBJECT_ICONS[subject]:"·";badge.title=subject||"No subject icon";return badge;}
  function storedDiceRow(a){
    const ids=a.storedDice||[];if(!ids.length)return "";
    const dice=ids.map(id=>state.nap.dice.find(d=>d.id===id)).filter(Boolean);
    return `<div class="nap-stored-dice" aria-label="Dice stored on this Assignment">${dice.map(d=>
      `<span class="roll-die ${d.color} stored" title="${d.color} die${d.face?` · ${d.face==="✷"?"Crit":"success"}`:""}"><span class="face">${d.face||""}</span><span class="tiny">${d.color[0].toUpperCase()}</span></span>`).join("")}</div>`;
  }
  function renderNAPSubjectCounts(cards,subjectHostId,otherHostId){
    const subjects=$(subjectHostId),others=$(otherHostId);subjects.replaceChildren();others.replaceChildren();
    [...NAP_SUBJECTS,null].forEach(subject=>{const count=cards.filter(card=>card.type==="t"&&napSubject(card)===subject).length,item=document.createElement("div"),label=document.createElement("span");item.className="nap-subject-count";item.append(subjectBadge(subject));label.textContent=`${subject||"Unmarked"}: ${count}`;item.append(label);subjects.append(item);});
    [["o","Opportunities"],["s","Setbacks"],["f","FINF"]].forEach(([type,name])=>{const item=document.createElement("span");item.className="nap-other-count";item.textContent=`${name}: ${cards.filter(card=>card.type===type).length}`;others.append(item);});
  }
  function renderNAPCoupons(){
    const n=state.nap,held=n.coupons||[],devious=n.deviousCoupons||[],host=$("napCoupons");
    $("napCouponPanel").classList.toggle("hidden",!held.length&&!devious.length);
    host.replaceChildren();
    // Devious Opportunities are banked until the Final Exam.
    devious.forEach((index,slot)=>{
      const card=NAP_DEVIOUS[index],art=napCard("o",index,true),item=document.createElement("article");
      item.className="nap-coupon devious";
      const pic=document.createElement("div");
      pic.className="suite-card landscape nap-coupon-card";
      pic.setAttribute("role","img");pic.setAttribute("aria-label",card[0]+" coupon");
      setSprite(pic,art.file,art.i,art.cols,art.rows);
      const body=document.createElement("div");body.className="nap-coupon-body";
      const name=document.createElement("strong");name.textContent=card[0];
      const text=document.createElement("small");text.textContent=card[3].replace("Final Exam: ","");
      body.append(name,text);
      const usable=n.phase==="exam"&&n.exam&&n.exam.stage==="exam";
      if(usable){
        const spend=document.createElement("button");
        spend.dataset.napDevious=String(slot);spend.textContent="Spend";
        body.append(spend);
      }else{
        const hint=document.createElement("small");hint.className="hint";
        hint.textContent="Spendable during the Final Exam.";
        body.append(hint);
      }
      item.append(pic,body);host.append(item);
    });
    held.forEach((index,slot)=>{
      const meta=NAP_COUPONS[index],card=napCard("o",index),item=document.createElement("article");
      item.className="nap-coupon";
      const art=document.createElement("div");
      art.className="suite-card landscape nap-coupon-card";
      art.setAttribute("role","img");
      art.setAttribute("aria-label",NAP_OPPS[index]+" coupon");
      setSprite(art,card.file,card.i,card.cols,card.rows);
      const body=document.createElement("div");
      body.className="nap-coupon-body";
      const name=document.createElement("strong");name.textContent=NAP_OPPS[index];
      const text=document.createElement("small");text.textContent=meta.effect;
      body.append(name,text);
      if(meta.progress&&!(n.phase==="exam"&&n.exam.stage==="exam")){
        const hint=document.createElement("small");
        hint.className="hint";
        hint.textContent="Spend from the Assignment you want it on.";
        body.append(hint);
      }else{
        const spend=document.createElement("button");
        spend.dataset.napCoupon=String(slot);
        spend.textContent="Spend";
        body.append(spend);
      }
      item.append(art,body);host.append(item);
    });
  }
  function useDeviousIgnore(id){
    const n=state.nap,held=n.deviousCoupons||[];
    if(!held.length||n.pendingReward)return;
    const row=napRow(),a=row.find(x=>String(x.id)===String(id));
    if(!a||a.type!=="s"||a.completed||a.ignored)return;
    a.ignored=true;
    const spent=held[0];
    n.deviousCoupons=held.slice(1);
    n.notice=`${NAP_DEVIOUS[spent][0]} discarded: ${napCard(a.type,a.i,a.nrj,a.dot).name} no longer restricts you or charges upkeep. It still has to be resolved.`;
    save();renderNAP();
  }
  function spendDeviousCoupon(slot){
    const n=state.nap,held=n.deviousCoupons||[],index=held[slot];
    if(index===undefined||n.phase!=="exam"||n.exam.stage!=="exam")return;
    const card=NAP_DEVIOUS[index];
    if(index===1){
      // Recover 3 exhausted dice of different colors.
      n.recoverOverride=3;n.distinctRecover=true;
      n.recovering=n.dice.some(d=>d.zone==="exhausted");
      n.dice.forEach(d=>d.selected=false);
      n.rollResult=`${card[0]} spent: recover 3 exhausted dice of different colors.`;
    }else if(index===3){
      n.rollsUsed=Math.max(0,n.rollsUsed-1);
      n.rollResult=`${card[0]} spent: select the failed dice and roll again.`;
    }else if(index===4){
      n.exam.reduce=(n.exam.reduce||0)+3;
      n.rollResult=`${card[0]} spent: this exam's Target drops by 3.`;
    }else{
      n.exam.ignoreRule=true;
      n.rollResult=`${card[0]} spent: this exam's printed restriction is ignored.`;
    }
    n.deviousCoupons=held.filter((_,at)=>at!==slot);
    save();renderNAP();
  }
  function spendNAPCoupon(slot,assignmentId){
    const n=state.nap,held=n.coupons||[],index=held[slot];
    if(index===undefined||n.pendingReward)return;
    const meta=NAP_COUPONS[index];
    if(n.phase==="exam"&&n.exam.stage==="exam"){
      // In an exam there is no Assignment row: the coupon acts on the exam.
      if(index===0){n.hp++;n.rollResult=`${NAP_OPPS[index]} spent: 1 Health loss cancelled.`;}
      else if(index===1){n.exam.wild=true;n.rollResult=`${NAP_OPPS[index]} spent: a color requirement is satisfied.`;}
      else if(index===3){n.exam.reduce=(n.exam.reduce||0)+2;n.rollResult=`${NAP_OPPS[index]} spent: this exam's Target drops by 2.`;}
      else if(index===5){n.activeSlotBonus.crit++;n.rollResult=`${NAP_OPPS[index]} spent: one Crit counts as 3 successes.`;}
      else {n.exam.bonus=(n.exam.bonus||0)+meta.progress;n.rollResult=`${NAP_OPPS[index]} spent: +${meta.progress} to this exam.`;}
      n.coupons=held.filter((_,at)=>at!==slot);save();renderNAP();return;
    }
    if(meta.progress){
      // Targeted: it is worth successes on one Assignment, no roll needed.
      const row=napRow(),a=row.find(x=>x.id==assignmentId);
      if(!a||a.completed||a.type==="o")return;
      a.progress=(a.progress||0)+meta.progress;
      const card=napCard(a.type,a.i,a.nrj,a.dot),need=a.demandSide?card.demand:card.target;
      n.rollResult=`${NAP_OPPS[index]} spent on ${card.name}: +${meta.progress} ${meta.progress===1?"success":"successes"}.`;
      if(a.progress>=need)completeNAPAssignment(a,{successes:meta.progress,priorStored:(a.storedDice||[]).length});
    }else if(index===0){
      n.hp++;n.rollResult=`${NAP_OPPS[index]} spent: 1 Health loss cancelled.`;
    }else if(index===1){
      n.couponWild=true;n.rollResult=`${NAP_OPPS[index]} spent: one die counts as any color for your next application.`;
    }else{
      n.activeSlotBonus.crit++;n.rollResult=`${NAP_OPPS[index]} spent: one Crit counts as 3 successes.`;
    }
    n.coupons=held.filter((_,at)=>at!==slot);
    save();renderNAP();
  }
  // ------------------------------------------------------------------
  // Special Recovery: recover ALL exhausted dice of one color. The Savant
  // trades one of them for a die of a neighbouring color.
  // ------------------------------------------------------------------
  function napSpecialRecovery(color){
    const n=state.nap;let note="";
    if(!color)return note;
    let pool=n.dice.filter(d=>d.zone==="exhausted"&&d.color===color);
    if(n.apprentice==="Savant"&&pool.length){
      pool=pool.slice(0,-1);            // all but 1 of the special color
      const i=NAP_COLOR_ORDER.indexOf(color),near=[NAP_COLOR_ORDER[(i+3)%4],NAP_COLOR_ORDER[(i+1)%4]];
      for(const c of near){
        const die=n.dice.find(d=>d.zone==="exhausted"&&d.color===c);
        if(die){die.zone="available";die.face="";note=` Savant also recovered 1 ${c} die.`;break;}
      }
    }
    pool.forEach(d=>{d.zone="available";d.face="";});
    return note;
  }

  // ------------------------------------------------------------------
  // The Final Exam
  // ------------------------------------------------------------------
  function enterFinalExam(){
    const n=state.nap;
    // Leaving the apprenticeship: discard unresolved Assignments and exhaust
    // their stored dice.
    const left=[];
    n.rows.forEach((cards,i)=>{
      cards.forEach(a=>{
        (a.storedDice||[]).forEach(id=>{const die=n.dice.find(x=>x.id===id);if(die){die.zone="exhausted";die.face="";die.selected=false;}});
        n.discard.push({type:a.type,i:a.i});
        if(!a.completed)left.push(napCard(a.type,a.i,a.nrj,a.dot).name);
      });
      n.rows[i]=[];
    });
    n.dice.filter(d=>d.zone==="rolled"||d.zone==="stored").forEach(d=>{d.zone="exhausted";d.face="";d.selected=false;});
    // Short of the goal: exhaust 1 available die per missing Credit, in order.
    let missing=Math.max(0,n.creditGoal-n.credits),short=0;
    const order=["red","purple","blue","green","yellow"];
    for(let i=0;missing>0&&i<80;i++){
      if(!n.dice.some(x=>x.zone==="available"))break;
      const die=n.dice.find(x=>x.zone==="available"&&x.color===order[i%order.length]);
      if(die){die.zone="exhausted";die.face="";missing--;short++;}
    }
    n.phase="exam";
    n.exam={stage:"prep",index:0,pool:[],drawn:[],log:[],wild:false,bonus:0,reduce:0};
    n.choice=null;n.rollsUsed=0;n.rollResult="";
    // Preparation: 1 exhausted die, plus 1 per Credit above the goal.
    const excess=Math.max(0,n.credits-n.creditGoal);
    n.recoverOverride=1+excess;
    n.recovering=n.dice.some(d=>d.zone==="exhausted");
    n.dice.forEach(d=>d.selected=false);
    n.notice=`Leaving the apprenticeship.${left.length?` Discarded unresolved: ${left.join(", ")}.`:""}`
      +`${short?` Short of the Credit goal: ${short} available ${short===1?"die":"dice"} exhausted.`:""}`
      +` Preparation: recover ${n.recoverOverride} exhausted ${n.recoverOverride===1?"die":"dice"}`
      +`${excess?" (excess-Credit picks must be different colors)":""}, then the queued recovery runs.`;
    if(!n.recovering)finishExamPrep();
    save();renderNAP();
  }
  function finishExamPrep(){
    const n=state.nap;
    n.recoverOverride=null;
    const note=napSpecialRecovery({P:"purple",B:"blue",G:"green",Y:"yellow"}[n.recoveryDots[n.slot]]);
    // Build the exam pool: 1 card per subject at 0-1 Credits, 2 at 2-3, 3 at 4+.
    const per={};
    n.completedCredits.forEach(c=>{const sub=NAP_TASK_SUBJECTS[c.i];if(sub)per[sub]=(per[sub]||0)+1;});
    n.exam.credits=per;
    const pool=[];
    NAP_SUBJECTS.forEach(sub=>{
      const held=per[sub]||0,take=held<=1?1:(held<=3?2:3);
      NAP_EXAMS.map((e,i)=>[e,i]).filter(([e])=>e[1]===sub).slice(0,take).forEach(([,i])=>pool.push(i));
    });
    n.exam.pool=pool;
    n.exam.drawn=shuffle(pool.slice()).slice(0,3);
    n.exam.stage="exam";
    n.exam.index=0;
    n.rollsUsed=0;
    n.notice=`${note?note.trim()+" ":""}Exam pool: ${pool.length} cards; three drawn. FINF is not used during the Final Exam.`;
  }
  function examTarget(){
    const n=state.nap,e=NAP_EXAMS[n.exam.drawn[n.exam.index]];
    const held=(n.exam.credits||{})[e[1]]||0;
    return Math.max(1,e[3]-held-(n.exam.reduce||0));
  }
  function examCommitted(){return state.nap.dice.filter(d=>d.zone==="rolled");}
  function examCheck(){
    const n=state.nap,rule=NAP_EXAMS[n.exam.drawn[n.exam.index]][5];
    const committed=examCommitted(),successful=committed.filter(d=>d.face);
    const colors=new Set(committed.map(d=>d.color)),fails=[];
    if(!committed.length)fails.push("Commit and roll dice first.");
    if(n.exam.ignoreRule)return fails;      // "Definitely Curriculum-Approved"
    if(rule.noRed&&committed.some(d=>d.color==="red"))fails.push("Red cannot be committed.");
    if(rule.minColors&&colors.size<rule.minColors)fails.push(`Needs ${rule.minColors} different colors; you have ${colors.size}.`);
    if(rule.minDice&&committed.length<rule.minDice)fails.push(`Needs at least ${rule.minDice} dice; you committed ${committed.length}.`);
    if(rule.needCrit&&!successful.some(d=>d.face==="✷"))fails.push("At least 1 Crit must contribute.");
    if(rule.contribute&&!n.exam.wild)Object.entries(rule.contribute).forEach(([color,count])=>{
      if(successful.filter(d=>d.color===color).length<count)fails.push(`Needs ${count} successful ${color} ${count===1?"die":"dice"}.`);
    });
    if(rule.contributeAny&&!n.exam.wild){
      const want=rule.contributeAny[0],count=rule.contributeAny[1];
      if(successful.filter(d=>want.includes(d.color)).length<count)
        fails.push(`Needs ${count} successful dice among ${want.join("/")}.`);
    }
    return fails;
  }
  function examSuccesses(){
    const n=state.nap,rule=NAP_EXAMS[n.exam.drawn[n.exam.index]][5];
    const successful=examCommitted().filter(d=>d.face);
    let got=successful.reduce((sum,d)=>sum+(d.face==="✷"?2:1),0);
    if(rule.scoring==="redCrit1")got-=successful.filter(d=>d.color==="red"&&d.face==="✷").length;
    if(rule.scoring==="yellowCrit3"&&successful.some(d=>d.color==="yellow"&&d.face==="✷"))got+=1;
    if(n.activeSlotBonus.crit&&successful.some(d=>d.face==="✷"))got+=1;
    return got+(n.exam.bonus||0);
  }
  function resolveExam(){
    const n=state.nap;if(n.phase!=="exam"||n.exam.stage!=="exam")return;
    const fails=examCheck();
    if(fails.length){n.rollResult=`Restriction not met. ${fails.join(" ")}`;save();renderNAP();return;}
    const i=n.exam.drawn[n.exam.index],e=NAP_EXAMS[i];
    const target=examTarget(),got=examSuccesses(),shortfall=Math.max(0,target-got);
    if(n.activeSlotBonus.crit)n.activeSlotBonus.crit=0;
    n.hp=Math.max(0,n.hp-shortfall);
    examCommitted().forEach(die=>{die.zone="exhausted";die.face="";die.selected=false;});
    n.exam.bonus=0;n.exam.reduce=0;n.exam.wild=false;n.exam.ignoreRule=false;
    n.exam.log.push({name:e[0],target,got,shortfall});
    n.discard.push({type:"e",i});
    if(n.hp<=0){
      n.phase="over";n.outcome="lost";n.exam.stage="done";
      n.notice=`${e[0]}: ${got} of ${target}. ${shortfall} Health lost - you fail out.`;
      save();renderNAP();return;
    }
    const note=napSpecialRecovery({P:"purple",B:"blue",G:"green",Y:"yellow"}[e[2]]);
    n.notice=`${e[0]}: ${got} of ${target}.${shortfall?` Lost ${shortfall} Health.`:" Passed cleanly."}${note}`;
    n.exam.index++;
    n.rollsUsed=0;
    if(n.exam.index>=n.exam.drawn.length){
      n.phase="over";n.outcome="won";n.exam.stage="done";
      n.notice+=" All three exams survived - you pass.";
    }else if(n.dice.some(die=>die.zone==="exhausted")){
      n.exam.stage="recover";
      n.recovering=true;
      n.dice.forEach(die=>die.selected=false);
      n.notice+=` Recover up to REC (${n.rec}), then the next exam.`;
    }
    save();renderNAP();
  }
  function renderNAPExam(){
    const n=state.nap,host=$("napExam"),on=n.phase==="exam"||n.phase==="over";
    host.classList.toggle("hidden",!on);
    $("napSlotActions").classList.toggle("hidden",on);
    if(!on)return;
    if(n.phase==="over"){
      const won=n.outcome==="won";
      host.innerHTML=`<div class="section-head"><div><p class="kicker">Final Exam</p><h2>${won?"Apprenticeship complete":"Failed out"}</h2></div></div>`
        +`<ol class="nap-exam-log">${(n.exam.log||[]).map(r=>`<li>${r.name} - ${r.got} of ${r.target}${r.shortfall?` (lost ${r.shortfall} Health)`:""}</li>`).join("")}</ol>`
        +`<p class="hint">${won?`Passed all three with ${n.hp} Health remaining.`:"Health reached 0."} Start a new test to play again.</p>`;
      return;
    }
    if(n.exam.stage==="prep"||n.exam.stage==="recover"){
      const prep=n.exam.stage==="prep";
      host.innerHTML=`<div class="section-head"><div><p class="kicker">Final Exam</p><h2>${prep?"Preparation":"Between exams"}</h2></div></div>`
        +`<p class="hint">${prep
          ?`Recover ${n.recoverOverride} exhausted ${n.recoverOverride===1?"die":"dice"} in the dice panel and confirm. The queued Special Recovery runs next.`
          :`Recover up to REC (${n.rec}) in the dice panel and confirm to face exam ${n.exam.index+1} of ${n.exam.drawn.length}.`}</p>`;
      return;
    }
    const i=n.exam.drawn[n.exam.index],e=NAP_EXAMS[i],card=napExamCard(i);
    const held=(n.exam.credits||{})[e[1]]||0,committed=examCommitted(),fails=examCheck(),got=examSuccesses();
    host.innerHTML=`<div class="section-head"><div><p class="kicker">Final Exam ${n.exam.index+1} of ${n.exam.drawn.length}</p><h2>${e[0]}</h2></div><strong class="nap-roll-count">Target ${examTarget()}</strong></div>`
      +`<div class="nap-exam-body"><div id="napExamCard" class="suite-card landscape nap-top-card" role="img" aria-label="${e[0]}"></div>`
      +`<div class="nap-exam-info"><p><b>${e[1]}</b> &middot; base Target ${e[3]} &minus; ${held} Credit${held===1?"":"s"}${n.exam.reduce?` &minus; ${n.exam.reduce} coupon`:""} = <b>${examTarget()}</b></p>`
      +`<p class="nap-exam-rule">${e[4]}</p>`
      +`<p>Committed ${committed.length} ${committed.length===1?"die":"dice"} &middot; ${got} ${got===1?"success":"successes"}</p>`
      +`${fails.length?`<p class="hint">${fails.join(" ")}</p>`:`<p class="hint">Restriction met. Resolving loses 1 Health per success below Target.</p>`}`
      +`<button id="napExamResolve" class="primary" ${fails.length?"disabled":""}>Resolve exam</button></div></div>`;
    setSprite($("napExamCard"),card.file,card.i,card.cols,card.rows);
    $("napExamResolve").onclick=resolveExam;
  }
  function renderNAPDiscard(){
    const n=state.nap,items=n.discard;
    $("napDeckCount").textContent=n.deck.length;
    $("napDeckView").classList.toggle("empty",!n.deck.length);
    $("napDiscardCount").textContent=items.length;
    $("napDiscardTop").textContent=items.length?napCard(items.at(-1).type,items.at(-1).i).name:"Empty";
    const list=$("napDiscardList");list.replaceChildren();
    items.slice().reverse().forEach((card,index)=>{
      const li=document.createElement("li"),button=document.createElement("button"),subject=napSubject(card),name=document.createElement("span"),label=document.createElement("small");
      li.className="nap-discard-item";button.type="button";button.className="nap-discard-card";button.dataset.napDiscardIndex=items.length-1-index;button.append(subjectBadge(subject));name.textContent=napCard(card.type,card.i,card.nrj,card.dot).name;
      label.textContent=subject||({t:"Unmarked Task",o:"Opportunity",s:"Setback",f:"FINF",e:"Final Exam"}[card.type]||"Card");
      button.append(name,label);li.append(button);list.append(li);
    });
    renderNAPSubjectCounts(n.deck,"napDeckSubjectCounts","napDeckOtherCounts");
    renderNAPSubjectCounts(n.discard,"napDiscardSubjectCounts","napDiscardOtherCounts");
    renderNAPPileView();
    renderNAPCredits();
  }
  function renderNAPPileView(){const deck=napPileView==="deck";$("napDeckView").classList.toggle("hidden",!deck);$("napDiscardView").classList.toggle("hidden",deck);$("napDeckTab").setAttribute("aria-pressed",String(deck));$("napDiscardTab").setAttribute("aria-pressed",String(!deck));}
  function renderNAPCredits(){
    const n=state.nap,host=$("napCreditCards");host.replaceChildren();$("napCreditCount").textContent=`${n.credits} ${n.credits===1?"Credit":"Credits"}`;
    n.completedCredits.forEach((card,index)=>{const c=napCard(card.type,card.i,card.nrj,card.dot),button=document.createElement("button"),art=document.createElement("div");button.type="button";button.className="nap-credit-card";button.dataset.napCreditIndex=index;art.className="suite-card landscape";art.setAttribute("role","img");art.setAttribute("aria-label",`${c.name} card face`);setSprite(art,c.file,c.i,c.cols,c.rows);button.append(art);host.append(button);});
    const earlier=Math.max(0,n.credits-n.completedCredits.length);if(earlier){const p=document.createElement("p");p.className="hint";p.textContent=`${earlier} previously earned ${earlier===1?"Credit has":"Credits have"} no saved card record.`;host.append(p);}
    if(!n.credits){const p=document.createElement("p");p.className="hint";p.textContent="Completed Credit Tasks will appear here.";host.append(p);}
  }
  function showNAPCard(card){
    if(!card)return;
    hideNAPHoverCard();
    const c=napCard(card.type,card.i,card.nrj,card.dot),dialog=$("napDiscardDialog"),art=$("napDiscardCardArt");
    $("napDiscardCardTitle").textContent=c.name;
    $("napDiscardCardType").textContent=napSubject(card)||({t:"Unmarked Task",o:"Opportunity",s:"Setback",f:"FINF",e:"Final Exam"}[card.type]||"Assignment");
    setSprite(art,c.file,c.i,c.cols,c.rows);art.setAttribute("aria-label",`${c.name} card face`);
    dialog.showModal();
  }
  // A Crit is worth 2 successes, a hit 1, a blank none. Reported after every
  // roll and on each rolled die, so a result can be read without counting.
  function rollTally(dice){
    const t={crits:0,hits:0,misses:0,successes:0};
    dice.forEach(x=>{
      if(x.face==="✷"){t.crits++;t.successes+=2;}
      else if(x.face==="✦"){t.hits++;t.successes+=1;}
      else t.misses++;
    });
    return t;
  }
  function tallyText(t){
    return `${t.successes} success${t.successes===1?"":"es"} · `
      +`${t.crits} Crit${t.crits===1?"":"s"}, ${t.hits} hit${t.hits===1?"":"s"}, `
      +`${t.misses} miss${t.misses===1?"":"es"}`;
  }
  function faceLabel(face){
    return face==="✷" ? "Crit · 2 successes"
      : face==="✦" ? "Hit · 1 success" : "Miss · 0 successes";
  }
  const DIE_ORDER=["red","purple","blue","green","yellow"];   // Red sits left of Purple
  const byColor=(a,b)=>DIE_ORDER.indexOf(a.color)-DIE_ORDER.indexOf(b.color);
  let napHoverPreview=null;
  function showNAPHoverCard(card,anchor){
    if(!card||!anchor)return;
    const c=napCard(card.type,card.i,card.nrj,card.dot);
    if(!napHoverPreview){napHoverPreview=document.createElement("div");napHoverPreview.className="suite-card landscape nap-hover-preview";napHoverPreview.setAttribute("role","img");document.body.append(napHoverPreview);}
    setSprite(napHoverPreview,c.file,c.i,c.cols,c.rows);
    napHoverPreview.setAttribute("aria-label",`${c.name} card face`);
    napHoverPreview.hidden=false;
    const rect=anchor.getBoundingClientRect(),width=napHoverPreview.getBoundingClientRect().width,height=width*5/7;
    let left=rect.right+12;
    if(left+width>innerWidth-12)left=Math.max(12,rect.left-width-12);
    napHoverPreview.style.left=`${left}px`;
    napHoverPreview.style.top=`${Math.max(12,Math.min(rect.top,innerHeight-height-12))}px`;
  }
  function hideNAPHoverCard(){if(napHoverPreview)napHoverPreview.hidden=true;}
  function napHoverTarget(target){
    const anchor=target.closest?.("[data-nap-discard-index],[data-nap-peek-card-index]");
    if(!anchor)return null;
    const discardIndex=anchor.dataset.napDiscardIndex;
    const card=discardIndex!==undefined?state.nap.discard[Number(discardIndex)]:state.nap.pendingReward?.order?.[Number(anchor.dataset.napPeekCardIndex)];
    return card?{anchor,card}:null;
  }
  document.addEventListener("pointerover",e=>{if(e.pointerType!=="mouse"&&e.pointerType!=="pen")return;const target=napHoverTarget(e.target);if(target)showNAPHoverCard(target.card,target.anchor);});
  document.addEventListener("pointerout",e=>{const target=napHoverTarget(e.target);if(target&&!target.anchor.contains(e.relatedTarget))hideNAPHoverCard();});
  document.addEventListener("focusin",e=>{const target=napHoverTarget(e.target);if(target)showNAPHoverCard(target.card,target.anchor);});
  document.addEventListener("focusout",e=>{if(napHoverTarget(e.target))hideNAPHoverCard();});
  function renderNAPApprentice(){const names=["Prodigy","Slacker","Technician","Savant","Opportunist","Lab Rat"],n=state.nap,index=Math.max(0,names.indexOf(n.apprentice));$("napApprentice").value=names[index];setSprite($("napApprenticeCard"),`NAP_Apprentices_TTS${index%2?"_back":""}.png`,Math.floor(index/2),3,1);$("napApprenticeCard").setAttribute("aria-label",`${names[index]} Apprentice card`);
    const ability=NAP_ABILITIES[names[index]],uses=napUses();
    const spent=names[index]==="Lab Rat"?uses.labRatDay:names[index]==="Prodigy"?uses.prodigySlot:false;
    $("napAbility").innerHTML=`<p class="mini-label">${ability.when}${spent?" \u00b7 used":""}</p><p>${ability.text}</p>`
      +(names[index]==="Lab Rat"&&!uses.labRatDay
        ? `<button data-nap-labrat type="button">Exhaust a die instead of losing 1 Health</button>` : "");}
  // ------------------------------------------------------------------
  // NRJ tiers. One campaign-wide setting, which any table may override for
  // isolated playtesting. BAT and AoS keep their own storage, so they read
  // this through window.NOBULOUS_TIER rather than sharing state.
  // ------------------------------------------------------------------
  const TIER_NAMES=["None","I \u00b7 Agenda","II \u00b7 Contamination","III \u00b7 Exploitation"];
  function tierOverrides(){state.config.tierOverride??={bat:"",nap:"",aos:""};return state.config.tierOverride;}
  function tierFor(game){const o=tierOverrides()[game];return o?o:(state.config.tier||"0");}
  function tierName(value){return TIER_NAMES[Number(value)||0];}
  window.NOBULOUS_TIER={
    forGame:game=>tierFor(game),
    name:value=>tierName(value),
    globalTier:()=>state.config.tier||"0",
    override:game=>tierOverrides()[game]||"",
    setOverride:(game,value)=>{tierOverrides()[game]=value||"";save();window.dispatchEvent(new CustomEvent("nobulous-tier"));},
  };
  function renderTierPickers(){
    [["batTier","bat"],["napTier","nap"],["aosTier","aos"]].forEach(([id,game])=>{
      const sel=$(id);if(!sel)return;
      sel.querySelector("[value='']").textContent=`Follow campaign (${tierName(state.config.tier)})`;
      sel.value=tierOverrides()[game]||"";
      if(game==="aos"&&$("aosTierNote")){const t=tierFor("aos");
        $("aosTierNote").textContent=t==="0"?"Base Programs and Limitations only.":`Tier ${tierName(t)} module cards are in play.`;}
    });
  }
  function overlayText(game){
    const tier=tierFor(game||"nap"),over=tierOverrides()[game||"nap"];
    if(tier==="0")return "No NRJ tier \u00b7 base cards only";
    return `NRJ Tier ${tierName(tier)} active${over?" (table override)":""} \u00b7 module cards are mixed in.`;
  }

  const ruleFiles={bat:["assets/BAT_Rulebook.pdf?v=fonts-2","BAT rules PDF"],nap:["assets/NAP_Rulebook.pdf?v=fonts-1","NAP rules PDF"],aos:["assets/AoS_Rulebook.pdf?v=fonts-1","AoS rules PDF"],nrj:["assets/NRJ_Campaign_Supplement.pdf?v=fonts-1","NRJ rules PDF"]};
  function updateTopbar(){const game=$("gameNav")?.value||"home",link=$("rulesLink"),resetBtn=$("resetBtn"),record=$("recordBtn");
    const rules=ruleFiles[game];if(rules){link.href=rules[0];link.textContent=rules[1];link.hidden=false}else link.hidden=true;
    resetBtn.hidden=game==="home";resetBtn.textContent=game==="nrj"?"New finale":"New test";
    record.hidden=game==="home";record.textContent=`${$("recordPanel").classList.contains("hidden")?"Show":"Hide"} Playtest record`;}

  // ---- Home page card browser ------------------------------------------
  // catalog.json is generated by generator/build_catalog.py from the same data
  // the printed cards are built from, so names and order cannot drift.
  // Fetched with no-store: the card list is rebuilt whenever a card changes,
  // and a stale cached copy would quietly hide new cards.
  let cardCatalog=null,catalogPending=null;
  function loadCardCatalog(){
    if(cardCatalog)return Promise.resolve(cardCatalog);
    catalogPending??=fetch("catalog.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json();})
      .then(data=>{cardCatalog=data;return data;});
    return catalogPending;
  }
  // Every sheet cell is 500x700 (or 700x500) with the card art inset by GUTTER.
  // The preview crops to the art itself so every card fills the box the same way:
  // otherwise a card whose body matches the cream gutter looks smaller than the rest.
  const CELL_LONG=700,CELL_SHORT=500,GUTTER=15;
  // Every card image carries this tag; bump it whenever the sheets are rebuilt.
  const ART_VERSION="?v=ratnames";
  function peekStyle(deck,index,side,boxW){
    const back=side==="back"&&deck.back;
    // A deck may name one back for all its cards, or one per card.
    const sheet=back?((deck.backs&&deck.backs[index])||deck.back):deck.sheet;
    const cols=back&&!deck.backIsSheet?1:deck.cols,rows=back&&!deck.backIsSheet?1:deck.rows;
    const i=back&&!deck.backIsSheet?0:index;
    const col=i%cols,row=Math.floor(i/cols);
    const cellW=deck.landscape?CELL_LONG:CELL_SHORT,cellH=deck.landscape?CELL_SHORT:CELL_LONG;
    const k=boxW/(cellW-2*GUTTER);
    return `background-image:url('${ASSET}${sheet}${ART_VERSION}');`
      +`background-size:${(cols*cellW*k).toFixed(1)}px ${(rows*cellH*k).toFixed(1)}px;`
      +`background-position:${(-(col*cellW+GUTTER)*k).toFixed(1)}px ${(-(row*cellH+GUTTER)*k).toFixed(1)}px`;
  }
  function showCardPeek(el){
    const peek=$("cardPeek"),deck=el._peekDeck;if(!deck)return;
    peek.className=`card-peek ${deck.landscape?"landscape":"portrait"}`;
    const r=el.getBoundingClientRect();
    // The art is 470x670 at 200dpi. Showing it at those pixels means no resampling,
    // so the print stays as crisp as the card itself; shrink only to fit the window.
    const artW=deck.landscape?CELL_LONG-2*GUTTER:CELL_SHORT-2*GUTTER;
    const artH=deck.landscape?CELL_SHORT-2*GUTTER:CELL_LONG-2*GUTTER;
    const fit=Math.min(1,(innerHeight-24)/artH,(innerWidth-24)/artW);
    const w=Math.round(artW*fit),h=Math.round(artH*fit);
    peek.setAttribute("style",peekStyle(deck,Number(el.dataset.peekIndex),el.dataset.peekSide,w));
    peek.style.width=`${w}px`;peek.style.height=`${h}px`;
    // Prefer the left of the row; fall back to the right when the card will not fit.
    const left=r.left-w-12,right=r.right+12;
    peek.style.left=`${left>=8?left:(right+w<=innerWidth-8?right:Math.max(8,innerWidth-w-8))}px`;
    peek.style.top=`${Math.max(8,Math.min(innerHeight-h-8,r.top-h/2+r.height/2))}px`;
  }
  function hideCardPeek(){const peek=$("cardPeek");peek.classList.add("hidden");peek.setAttribute("style","");}
  function renderCardList(game,host){
    const data=cardCatalog?.[game];
    if(!data){host.textContent="No card list available.";return;}
    host.replaceChildren();
    const count=data.decks.reduce((n,d)=>n+d.cards.length,0);
    const head=document.createElement("p");head.className="game-cards-head";
    head.textContent=`${count} cards in ${data.decks.length} decks`;host.append(head);
    const list=document.createElement("ol");list.className="card-list";
    data.decks.forEach(deck=>{
      const group=document.createElement("li");group.className="card-list-deck";
      const title=document.createElement("p");title.className="card-list-deck-title";
      title.textContent=`${deck.title} · ${deck.cards.length}`;group.append(title);
      deck.cards.forEach((card,index)=>{
        const row=document.createElement("div");row.className="card-row";
        const text=document.createElement("div");text.className="card-row-text";
        const name=document.createElement("strong");name.textContent=card.name;
        const kind=document.createElement("small");kind.textContent=card.kind;
        text.append(name,kind);
        const sides=document.createElement("div");sides.className="card-row-sides";
        const faces=[["front",card.name,deck.landscape]];
        if(deck.back||deck.backs)faces.push(["back",card.backName||deck.backLabel,deck.landscape]);
        faces.forEach(([side,label])=>{
          const b=document.createElement("button");b.type="button";b.className="card-side";
          b.textContent=side==="front"?"Front":"Back";
          b.dataset.peekIndex=String(index);b.dataset.peekSide=side;b._peekDeck=deck;
          b.title=`${label} · hover to preview`;
          b.addEventListener("mouseenter",()=>{$("cardPeek").classList.remove("hidden");showCardPeek(b);});
          b.addEventListener("focus",()=>{$("cardPeek").classList.remove("hidden");showCardPeek(b);});
          b.addEventListener("mouseleave",hideCardPeek);b.addEventListener("blur",hideCardPeek);
          sides.append(b);
        });
        row.append(text,sides);group.append(row);
      });
      list.append(group);
    });
    host.append(list);
  }
  function sizeCardList(host){
    // Tall enough to be useful, short enough that a scroll brings all of it into view.
    host.style.maxHeight=`${Math.max(240,Math.min(420,innerHeight-140))}px`;
    // The panel is absolutely positioned, so the page needs padding to scroll past it.
    $("screen-home").style.paddingBottom=`${Math.round(host.getBoundingClientRect().height)+48}px`;
  }
  function toggleCardList(game,button){
    const host=$(`cards-${game}`),open=host.classList.contains("hidden");
    if(!open){host.classList.add("hidden");button.textContent="Show Cards";button.setAttribute("aria-expanded","false");$("screen-home").style.paddingBottom="";hideCardPeek();return;}
    button.textContent="Hide Cards";button.setAttribute("aria-expanded","true");
    host.classList.remove("hidden");host.textContent="Loading cards\u2026";
    loadCardCatalog().then(()=>{renderCardList(game,host);sizeCardList(host);})
      .catch(()=>{host.textContent="Card list could not be loaded.";});
  }
  function showScreen(name){document.querySelectorAll(".game-screen").forEach(x=>x.classList.toggle("hidden",x.id!==`screen-${name}`));$("gameNav").value=name;document.querySelectorAll(".aos-only").forEach(x=>x.classList.toggle("hidden",name!=="aos"));if(name==="bat")window.BAT_LAB?.render();if(name==="nap")renderNAP();if(name==="nrj")renderNRJ();updateTopbar();window.scrollTo({top:0,behavior:"smooth"});}

  const FINF_SLOTS=["Morning","Afternoon","Evening"];
  function napCard(type,i,nrj,dot){
    if(nrj){
      if(type==="s"){const c=NAP_FOLLOWING[i];return{name:c[0],file:"NRJ_NAP_FollowingSetbacks_TTS.png",i,cols:4,rows:1,target:c[2],demand:c[2],dot:c[1],skulls:0,text:c[3],nrj:true};}
      if(type==="t"){const c=NAP_IMPOSTOR[i];return{name:c[0],file:"NRJ_NAP_ImpostorTasks_TTS.png",i,cols:4,rows:1,target:c[2],demand:c[3],dot:dot||"P",skulls:0,text:c[4],subject:c[1],nrj:true};}
      if(type==="o"){const c=NAP_DEVIOUS[i];return{name:c[0],file:"NRJ_NAP_DeviousOpportunities_TTS.png",i,cols:6,rows:1,target:c[2],demand:c[2],dot:c[1],skulls:0,text:c[3],when:c[4],nrj:true};}
    }
    if(type==="e")return napExamCard(i);if(type==="f")return{name:`FINF ${i+1} · ${FINF_SLOTS[i]||""}`,file:"NAP_SlotsFINF_TTS.png",i:3+(i||0),cols:6,rows:1,target:0,demand:0,dot:"—",skulls:0};if(type==="t")return {name:NAP_TASKS[i][0],file:"NAP_Tasks_TTS.png",i,cols:10,rows:3,target:NAP_TASKS[i][1],demand:NAP_TASKS[i][2],dot:NAP_TASKS[i][3],skulls:NAP_TASKS[i][4]};if(type==="o")return{name:NAP_OPPS[i],file:"NAP_Opportunities_TTS.png",i,cols:6,rows:1,target:[3,3,4,4,3,4][i],demand:[3,3,4,4,3,4][i],dot:i<4?"Y":"G",skulls:0};return{name:NAP_SETBACKS[i][0],file:"NAP_Setbacks_TTS.png",i,cols:6,rows:1,target:NAP_SETBACKS[i][1],demand:NAP_SETBACKS[i][1],dot:NAP_SETBACKS[i][2],skulls:0};}
  const NAP_ABILITIES={
    "Prodigy":{when:"Once per Time Slot",text:"When using two dice of the same color as wild, only one of those dice must roll a success."},
    "Slacker":{when:"Passive",text:"Your Time Slot rows hold a maximum of 3 Assignments instead of 4."},
    "Technician":{when:"Passive",text:"When you complete a Setback, recover 2 exhausted dice."},
    "Savant":{when:"Passive",text:"During special recovery, recover all but 1 exhausted die of the special color and recover 1 exhausted die of an adjacent color."},
    "Opportunist":{when:"Passive",text:"When you complete an Assignment on its Request side, recover 1 exhausted die of that Assignment's recovery-color dot."},
    "Lab Rat":{when:"Once per Day",text:"The first time you would lose Health, you may exhaust one available die instead."}};
  const NAP_COLOR_ORDER=["purple","blue","green","yellow"];
  const DOT_COLOR={P:"purple",B:"blue",G:"green",Y:"yellow"};
  function napUses(){const n=state.nap;n.appUses??={};n.appUses.prodigySlot??=false;n.appUses.needsFirstDone??=false;
    n.appUses.labRatDay??=false;return n.appUses;}
  function recoverOneNAP(color,reason){
    const die=state.nap.dice.find(d=>d.zone==="exhausted"&&d.color===color);
    if(!die)return false;
    die.zone="available";die.face="";
    state.nap.notice=`${state.nap.apprentice}: recovered 1 ${color} die (${reason}).`;
    return true;
  }
  function napRow(){return state.nap.rows[state.nap.slot];}
  function napRowMax(){return state.nap.apprentice==="Slacker"?3:4;}
  function openNAPCount(row){return row.filter(a=>!a.completed).length;}
  function buildNAPDeck(setbacks){
    const tier=napTier();
    let tasks=[...Array(26).keys()].map(i=>({type:"t",i}));
    // Tier II: each Impostor Task replaces a Credit Task of its own subject,
    // inheriting that Task's color dot. They grant no Credits.
    if(tier==="2"||tier==="3"){
      NAP_IMPOSTOR.forEach((imp,i)=>{
        const same=tasks.filter(c=>NAP_TASK_SUBJECTS[c.i]===imp[1]);
        if(!same.length)return;
        const victim=same[Math.floor(Math.random()*same.length)];
        tasks=tasks.filter(c=>c!==victim);
        tasks.push({type:"t",i,nrj:true,dot:NAP_TASKS[victim.i][3]});
      });
    }
    // Tier III: the Devious Opportunities replace the base Opportunities.
    const opps=(tier==="3"?NAP_DEVIOUS:NAP_OPPS).map((_,i)=>
      tier==="3"?{type:"o",i,nrj:true}:{type:"o",i});
    // Tier I: 3 of the 4 Following Setbacks stand in for the 3 base Setbacks.
    const sb=(tier==="1"||tier==="2"||tier==="3")
      ? shuffle([0,1,2,3]).slice(0,3).map(i=>({type:"s",i,nrj:true}))
      : setbacks;
    return tasks.concat(opps,sb);
  }
  function buildNAP(){const setback=shuffle([...Array(6).keys()]).slice(0,3).map(i=>({type:"s",i}));const apprentice=state.nap.apprentice||"Prodigy",creditGoal=state.nap.creditGoal||4;state.nap={day:1,slot:0,hp:2,str:2,rec:2,credits:0,creditGoal,coupons:[],deviousCoupons:[],couponWild:false,distinctRecover:false,phase:"apprenticeship",exam:null,outcome:null,completedCredits:[],apprentice,deck:shuffle(buildNAPDeck(setback)),discard:[],rows:[[],[],[]],recoveryDots:[null,null,null],primaryDot:null,choice:null,finf:{mode:"reduce",level:1,cards:[0],spent:[],drawn:[],pendingCurrent:[]},pendingReward:null,nextSlotBonus:{str:0,rec:0,crit:0},activeSlotBonus:{str:0,rec:0,crit:0},notice:"",dice:freshDice(),rollsUsed:0,phaseCommittedSuccesses:0,recovering:false,rollResult:""};save();renderNAP();}
  function drawNAPAssignment(){
    const card=state.nap.deck.pop();
    if(card?.type!=="f")return card;
    const n=state.nap,f=n.finf,slot=card.i%3,row=n.rows[slot];
    f.drawn=[...(f.drawn||[]),card.i];n.discard.push(card);
    let where="no room in that row";
    if(openNAPCount(row)+(slot===n.slot?1+f.pendingCurrent.length:0)<napRowMax()){
      const extra=drawNAPAssignment();
      if(extra){
        if(slot===n.slot)f.pendingCurrent.push(extra);
        else row.unshift({...extra,demandSide:false,progress:0,storedDice:[],id:`finf-${Date.now()}-${slot}`,source:"finf"});
        where=`1 Assignment added to ${FINF_SLOTS[slot]}`;
      }else where="the deck ran out";
    }
    n.notice=`FINF ${slot+1} (${FINF_SLOTS[slot]}) drawn: ${where}.`;
    return drawNAPAssignment();
  }
  function revealNAP(){const n=state.nap;if(n.phase!=="apprenticeship")return;if(n.choice||openNAPCount(napRow())>=napRowMax()||!n.deck.length)return;const choice=[];while(choice.length<2&&n.deck.length){const card=drawNAPAssignment();if(card)choice.push(card);}n.choice=choice.length?choice:null;if(!n.choice)placePendingFINF(napRow());save();renderNAP();}
  function placePendingFINF(row){for(const extra of state.nap.finf.pendingCurrent.splice(0)){if(openNAPCount(row)<napRowMax())row.unshift({...extra,demandSide:false,progress:0,storedDice:[],id:`finf-${Date.now()}-current`,source:"finf"});else state.nap.discard.push(extra);}}
  function chooseNAP(which){
    const n=state.nap;if(!n.choice?.[which])return;
    const row=napRow();let c=n.choice[which];
    if(n.choice.some(x=>x.type==="s"))c=n.choice.find(x=>x.type==="s");
    n.discard.push(...n.choice.filter(x=>x!==c));
    const primary={...c,demandSide:false,progress:0,storedDice:[],id:Date.now(),source:"primary"};
    row.unshift(primary);n.primaryDot=napCard(c.type,c.i,c.nrj,c.dot).dot;n.recoveryDots[(n.slot+1)%3]=n.primaryDot;
    placePendingFINF(row);
    const skulls=napCard(c.type,c.i,c.nrj,c.dot).skulls||0,added=[];let blocked=false;
    for(let k=0;k<skulls;k++){
      if(openNAPCount(row)<napRowMax()&&n.deck.length){
        const extra=drawNAPAssignment();
        if(extra&&openNAPCount(row)<napRowMax()){row.splice(k+1,0,{...extra,demandSide:false,progress:0,storedDice:[],id:`skull-${Date.now()}-${k}`,source:"skull"});added.push(napCard(extra.type,extra.i,extra.nrj,extra.dot).name);}
        else if(extra)n.discard.push(extra);
      }else if(!blocked){primary.demandSide=true;blocked=true;}
    }
    placePendingFINF(row);
    n.notice=skulls?`${skulls} Skull${skulls===1?"":"s"}: ${added.length?`added ${added.join(" and ")}`:"no card added"}${blocked?"; the row was full, so the Primary rotated to Demand.":". Added cards do not resolve their own Skulls."}`:n.notice;
    n.choice=null;save();renderNAP();
  }
  function advanceNAP(){
    const n=state.nap;if(n.phase!=="apprenticeship")return;if(n.pendingReward){n.rollResult="Finish the completed card's reward first.";renderNAP();return;}
    const endedSlot=n.slot;n.recovering=false;n.dice.forEach(d=>d.selected=false);
    const row=n.rows[n.slot],expired=[];
    const followed=[],nextSlot=(n.slot+1)%3;
    for(let i=row.length-1;i>=0;i--){
      const a=row[i];
      if(a.completed)continue;
      if(a.type==="o"){(a.storedDice||[]).forEach(id=>{const die=n.dice.find(d=>d.id===id);if(die)die.zone="exhausted";});a.storedDice=[];a.progress=0;}
      if(a.type==="o"&&a.demandSide){expired.push(napCard(a.type,a.i,a.nrj,a.dot).name);n.discard.push({type:a.type,i:a.i});row.splice(i,1);continue;}
      if(a.type==="t"&&a.nrj&&a.i===3&&!a.demandSide){
        const die=n.dice.find(d=>d.zone==="available");
        if(die){die.zone="exhausted";die.face="";}
      }
      a.demandSide=true;
      if(a.type==="s"&&a.nrj){
        // "An unresolved Following Setback moves into the next Time Slot,
        // including Evening to the next Morning."
        if(a.i===2&&!a.ignored){const die=n.dice.find(d=>d.zone==="available");if(die){die.zone="exhausted";die.face="";}}
        row.splice(i,1);n.rows[nextSlot].push(a);followed.push(napCard(a.type,a.i,a.nrj,a.dot).name);
      }
    }
    n.dice.filter(d=>d.zone==="rolled").forEach(d=>{d.zone="exhausted";d.selected=false;});
    const queuedDot=n.recoveryDots[n.slot];
    const savant=napSpecialRecovery({P:"purple",B:"blue",G:"green",Y:"yellow"}[queuedDot]);
    n.notice=expired.length?`Last chance expired: ${expired.join(", ")} discarded.`:"";
    if(followed.length)n.notice=(n.notice?n.notice+" ":"")+`${followed.join(", ")} follows you into the next Time Slot.`;
    n.rollResult="";
    n.rollsUsed=0;n.phaseCommittedSuccesses=0;if(n.choice)n.discard.push(...n.choice);n.choice=null;
    const uses=napUses();uses.prodigySlot=false;uses.needsFirstDone=false;
    const nextDot=n.primaryDot??queuedDot;n.primaryDot=null;const dayBefore=n.day;n.slot++;if(n.slot>2){n.slot=0;n.day++;n.rows.forEach(cards=>{for(let i=cards.length-1;i>=0;i--)if(cards[i].completed){const [a]=cards.splice(i,1);n.discard.push({type:a.type,i:a.i});}});if(n.deck.length)n.discard.push(n.deck.pop());}
    if(n.day!==dayBefore){uses.labRatDay=false;}
    if(savant)n.notice=(n.notice?n.notice+" ":"")+savant.trim();
    // "Play Days until either you reach your Credit goal or the deck runs out."
    if(n.credits>=n.creditGoal||!n.deck.length){
      n.str-=n.activeSlotBonus.str;n.rec-=n.activeSlotBonus.rec;
      n.activeSlotBonus={str:0,rec:0,crit:0};n.nextSlotBonus={str:0,rec:0,crit:0};
      enterFinalExam();return;
    }
    n.str-=n.activeSlotBonus.str;n.rec-=n.activeSlotBonus.rec;n.activeSlotBonus={...n.nextSlotBonus};n.str+=n.activeSlotBonus.str;n.rec+=n.activeSlotBonus.rec;n.nextSlotBonus={str:0,rec:0,crit:0};n.recoveryDots[n.slot]=nextDot;save();renderNAP();if(endedSlot===2)focusNAPRecover();
  }
  function focusNAPRecover(){const btn=$("napRoller")?.querySelector("[data-recover]");if(!btn)return;btn.focus({preventScroll:true});btn.scrollIntoView({block:"center",behavior:"smooth"});btn.classList.add("attention");setTimeout(()=>btn.classList.remove("attention"),2400);}
  function renderNAPFINF(){
    const f=state.nap.finf,sel=$("napDifficulty");
    sel.value=`${f.mode==="increase"?"inc":"red"}${Math.max(1,f.level||1)}`;
    // Locked once FINF is in play: a card has been drawn, or a Reduce use is spent.
    sel.disabled=(f.drawn||[]).length>0||(f.spent||[]).length>0;
    sel.title=sel.disabled?"FINF is already in play this game.":"";
    const held=(f.cards||[]).map(i=>`${i+1} ${FINF_SLOTS[i]}`
      +((f.spent||[]).includes(i)?" (spent)":(f.drawn||[]).includes(i)?" (drawn)":""));
    $("napFinfHeld").textContent=held.length
      ? `FINF ${f.mode==="increase"?"in the deck":"held"}: ${held.join(", ")}` : "";
  }
  function useLabRatSoak(){
    const n=state.nap,uses=napUses();
    if(n.apprentice!=="Lab Rat"||uses.labRatDay)return;
    const picked=n.dice.filter(d=>d.zone==="available"&&d.selected);
    const die=picked[0]||n.dice.filter(d=>d.zone==="available").sort((a,b)=>NAP_COLOR_ORDER.indexOf(b.color)-NAP_COLOR_ORDER.indexOf(a.color))[0];
    if(!die){n.notice="Lab Rat: no available die to exhaust; take the Health loss.";save();renderNAP();return;}
    die.zone="exhausted";die.selected=false;die.face="";uses.labRatDay=true;
    n.notice=`Lab Rat: exhausted 1 ${die.color} die instead of losing 1 Health.`;
    save();renderNAP();
  }
  function finfHeldFor(slot){
    if(state.nap.phase!=="apprenticeship")return false;   // not used in the exam
    const f=state.nap.finf;
    return f.mode==="reduce"&&(f.cards||[]).includes(slot)&&!(f.spent||[]).includes(slot);
  }
  function useNAPFINFReduce(id){
    const n=state.nap,f=n.finf,slot=n.slot,row=napRow();
    // Only the active Time Slot, and only with the card bearing its number.
    const index=row.findIndex(a=>String(a.id)===String(id));
    if(index<0||!finfHeldFor(slot)||n.pendingReward)return;
    const a=row[index];
    if(a.completed)return;
    if(a.type==="e")return;                      // never a Final Exam
    row.splice(index,1);
    (a.storedDice||[]).forEach(dieId=>{const die=n.dice.find(d=>d.id===dieId);if(die){die.zone="exhausted";die.selected=false;}});
    n.discard.push({type:a.type,i:a.i});f.spent=[...(f.spent||[]),slot];
    const left=(f.cards||[]).filter(i=>!(f.spent||[]).includes(i)).map(i=>FINF_SLOTS[i]);
    n.notice=`FINF ${slot+1} (${FINF_SLOTS[slot]}) removed ${napCard(a.type,a.i,a.nrj,a.dot).name}.`
      +(left.length?` Still held: ${left.join(", ")}.`:" No FINF cards left.");
    save();renderNAP();
  }
  function renderNAPSlots(){
    const names=["Morning","Afternoon","Evening"],host=$("napTimeSlots"),roller=$("napRoller"),choice=$("napChoice"),reward=$("napReward"),actions=$("napSlotActions");
    host.innerHTML="";
    names.forEach((name,i)=>{
      const box=document.createElement("article"),dot=state.nap.recoveryDots[i],color={P:"purple",B:"blue",G:"green",Y:"yellow"}[dot];
      box.className=`nap-slot nap-slot-${name.toLowerCase()} ${state.nap.slot===i?"active":""}`;
      box.innerHTML=`<div class="nap-slot-label"><span>Day ${state.nap.day}${state.nap.slot===i?" · Active now":""}</span><strong>${openNAPCount(state.nap.rows[i])}/${napRowMax()} open Assignments</strong></div><div class="nap-slot-left"><div class="assignment nap-time-frame"><div class="suite-card landscape nap-time-card"></div></div><div class="nap-recovery"><span class="nap-recovery-dot ${color||"unassigned"}" aria-hidden="true"></span><span>${color?`${color[0].toUpperCase()+color.slice(1)} dice recover at the end of this Time Slot`:"No color queued for this Time Slot"}</span></div></div><div class="nap-slot-assignments"></div>`;
      setSprite(box.querySelector(".nap-time-card"),"NAP_SlotsFINF_TTS.png",i,6,1);
      const row=box.querySelector(".nap-slot-assignments");
      if(!state.nap.rows[i].length)row.innerHTML="<p class='hint'>No Assignments in this Time Slot.</p>";
      state.nap.rows[i].forEach(a=>{
        const c=napCard(a.type,a.i,a.nrj,a.dot),card=document.createElement("article");card.className=`assignment ${a.completed?"nap-completed-assignment":""}`;
        // Module cards carry their printed text on the card record itself.
        const effect=a.nrj?(napCard(a.type,a.i,a.nrj,a.dot).text||"")
          :a.type==="t"&&!a.demandSide?NAP_REQUEST_EFFECTS[a.i]
          :a.type==="o"?NAP_OPPORTUNITY_EFFECTS[a.i]:"";
        card.innerHTML=`<div class="suite-card landscape ${a.completed?"nap-completed":a.demandSide?"nap-demand":""}"></div>${a.completed?`<span>Completed${a.rewardClaimed===false?" · reward available":""}</span>`:a.type==="o"?"":`<span>Stored ${a.progress}</span>${storedDiceRow(a)}`}${a.ignored?`<span>Restrictions ignored</span>`:""}${a.source==="finf"||a.source==="skull"?`<span>Added by ${a.source==="finf"?"FINF":"Skull"} · its Skulls ignored</span>`:""}${a.completed&&effect?`<small class="nap-completed-effect">${effect}</small>`:""}<div class="assignment-actions">${i===state.nap.slot&&!a.completed?`<button data-nap-assign="${a.id}">Apply selected dice</button><button data-complete="${a.id}" class="primary">Complete</button>`:""}${i===state.nap.slot&&!a.completed&&a.type==="s"&&!a.ignored&&(state.nap.deviousCoupons||[]).length&&!state.nap.pendingReward?`<button data-nap-dev-ignore="${a.id}">Discard a Devious card: ignore this Setback</button>`:""}${i===state.nap.slot&&!a.completed&&finfHeldFor(i)&&a.type!=="e"&&!state.nap.pendingReward?`<button data-nap-reduce="${a.id}">Use FINF ${i+1} (${FINF_SLOTS[i]}) to remove this card</button>`:""}${i===state.nap.slot&&!a.completed&&a.type!=="o"&&!state.nap.pendingReward?(state.nap.coupons||[]).map((ci,slot)=>NAP_COUPONS[ci].progress?`<button data-nap-coupon-use="${slot},${a.id}">${NAP_OPPS[ci]}: +${NAP_COUPONS[ci].progress} ${NAP_COUPONS[ci].progress===1?"success":"successes"}</button>`:"").join(""):""}</div>`;
        setSprite(card.querySelector(".suite-card"),c.file,c.i,c.cols,c.rows);row.appendChild(card);
      });
      if(i===state.nap.slot){box.querySelector(".nap-slot-left").insertBefore(actions,box.querySelector(".nap-recovery"));const bottom=document.createElement("div");bottom.className="nap-active-bottom";bottom.append(roller);box.append(choice,reward,bottom);}
      host.appendChild(box);
    });
  }
  function eligibleNAPReward(){const p=state.nap.pendingReward;if(!p||p.kind==="peek")return[];return state.nap.dice.filter(d=>d.zone==="exhausted"&&(p.kind==="committed"?p.eligibleIds.includes(d.id):p.kind==="distinct"?!p.usedColors.includes(d.color):p.kind==="restricted"?!["red","purple"].includes(d.color):p.kind==="yellowGreen"?["yellow","green"].includes(d.color):true));}
  function finishNAPReward(){const p=state.nap.pendingReward;if(p){const a=state.nap.rows.flat().find(x=>x.id===p.cardId);if(a)a.rewardClaimed=true;}state.nap.pendingReward=null;}
  function renderNAPReward(){
    const p=state.nap.pendingReward,host=$("napReward");
    host.classList.toggle("hidden",!p);host.replaceChildren();hideNAPHoverCard();
    if(!p)return;
    const title=document.createElement("h3");title.textContent=napCard(p.cardType,p.cardIndex).name+" · reward";
    const hint=document.createElement("p");hint.textContent=p.text;host.append(title,hint);
    if(p.kind==="peek"){
      const list=document.createElement("div");list.className="nap-peek-list";
      p.order.forEach((card,i)=>{
        const line=document.createElement("div"),number=document.createElement("span"),name=document.createElement("button");
        number.textContent=`${i+1}.`;name.type="button";name.className="nap-peek-card-name";
        name.textContent=napCard(card.type,card.i,card.nrj,card.dot).name;name.dataset.napPeekCardIndex=i;
        name.title="Hover to preview; select to enlarge";line.append(number,name);
        for(const [label,delta] of [["↑",-1],["↓",1]]){
          const b=document.createElement("button");b.type="button";b.textContent=label;
          b.dataset.napPeekMove=`${i},${delta}`;b.disabled=i+delta<0||i+delta>=p.order.length;line.append(b);
        }
        list.append(line);
      });
      host.append(list);
      if(p.cardIndex===20){const bottom=document.createElement("button");bottom.textContent=p.toBottom?"Return to top":"Put card on bottom";bottom.dataset.napPeekBottom="";host.append(bottom);}
    }else{
      const buttons=document.createElement("div");buttons.className="nap-reward-dice";
      eligibleNAPReward().forEach(d=>{const b=document.createElement("button");b.className=`roll-die ${d.color} exhausted`;b.textContent=d.color;b.dataset.napRewardDie=d.id;buttons.appendChild(b);});
      host.append(buttons);
    }
    const done=document.createElement("button");done.textContent=p.kind==="peek"?"Return cards to deck":"Done with reward";done.dataset.napRewardDone="";host.append(done);
  }
  function renderNAP(){const n=state.nap;$("napOverlay").textContent=overlayText("nap");renderTierPickers();$("napStats").innerHTML=stat("Day",n.day)+stat("Time",["Morning","Afternoon","Evening"][n.slot])+stat("HP",n.hp)+stat("STR",n.str)+stat("REC",n.rec)+stat("Credits",`${n.credits} / ${n.creditGoal}`)+stat("Deck",n.deck.length)+stat("Rolls",`${n.rollsUsed} / ${n.str}`);renderNAPDiscard();renderNAPApprentice();renderNAPCoupons();renderNAPSlots();renderNAPReward();renderNAPFINF();renderNAPExam();$("napNotice").textContent=n.notice||"";$("napNotice").classList.toggle("hidden",!n.notice);$("napChoice").classList.toggle("hidden",!n.choice);$("napChoiceB").parentElement.classList.toggle("hidden",!n.choice?.[1]);if(n.choice)n.choice.forEach((x,i)=>{const c=napCard(x.type,x.i,x.nrj,x.dot);setSprite($(i?"napChoiceB":"napChoiceA"),c.file,c.i,c.cols,c.rows);});renderRoller("nap");}

  function buildNRJ(){const byDomain=["Knowledge","Physical","Cover-Up"].flatMap(d=>shuffle(SCENARIOS.map((x,i)=>x[1]===d?i:null).filter(i=>i!==null)).slice(0,4));state.nrj={hp:4,str:2,rec:3,attempts:0,suspicion:0,deck:shuffle(byDomain),discard:[],current:null,pool:18,eligibleAvoid:3,dice:freshDice(),nextDiscount:0};save();renderNRJ();}
  function drawNRJ(){if(state.nrj.current||state.nrj.attempts>=9)return;if(!state.nrj.deck.length)buildNRJ();state.nrj.current=state.nrj.deck.pop();save();renderNRJ();}
  function nrjTarget(){if(state.nrj.current===null)return null;const s=SCENARIOS[state.nrj.current],ignore=s[0]==="A Disputed Citation",extra=s[0]==="The Missing Hours"?state.nrj.suspicion:0;const reduction=Number($("nrjNapMatch").value||0)*2+Number($("nrjBatMatch").value||0)*3+Number($("nrjSpecimen").value||0)*5+Number($("nrjAosStable").value||0)*4+Number($("nrjAosHot").value||0)*2+Number($("nrjWrong").value||0)*2;return Math.max(0,s[3]+(ignore?0:state.nrj.suspicion)+extra-state.nrj.nextDiscount-reduction);}
  function clearNRJInputs(){["nrjNapMatch","nrjBatMatch","nrjSpecimen","nrjAosStable","nrjAosHot","nrjWrong"].forEach(id=>$(id).value=0);}
  function resolveNRJ(success,choice="hp"){if(state.nrj.current===null)return;const s=SCENARIOS[state.nrj.current];const spent=["nrjNapMatch","nrjBatMatch","nrjSpecimen","nrjAosStable","nrjAosHot","nrjWrong"].reduce((n,id)=>n+Number($(id).value||0),0);if(spent>state.nrj.pool)return;state.nrj.pool-=spent;if(!success){state.nrj.suspicion+=s[0]==="Failed Apparatus"?2:1;if(choice==="hp"||s[0]==="Tainted Wine")state.nrj.hp--;else{let n=2;state.nrj.dice.filter(d=>d.zone==="available").forEach(d=>{if(n){d.zone="banished";n--;}});if(n)state.nrj.hp--;}}state.nrj.nextDiscount=success&&s[0]==="The Narrow Stair"?1:0;state.nrj.attempts++;state.nrj.discard.push(state.nrj.current);state.nrj.current=null;clearNRJInputs();save();renderNRJ();}
  function renderNRJ(){const n=state.nrj;$("nrjOverlay").textContent=`${$("nrjPoolMode")?.value==="campaign"?"Campaign":"Standalone sample"} · survive 9 attempts`;$("nrjStats").innerHTML=stat("HP",n.hp)+stat("STR",n.str)+stat("REC",n.rec)+stat("Attempts",`${n.attempts} / 9`)+stat("Suspicion",n.suspicion)+stat("Research",n.pool)+stat("Avoid cards",n.eligibleAvoid);renderDiscard("nrj",n.discard,i=>SCENARIOS[i][0]);if(n.current===null){clearSprite($("nrjScenario"),n.attempts>=9?(n.hp>0?"Finale survived":"The Imposter was exposed"):"Reveal a Scenario");$("nrjScenarioText").textContent="";}else{const s=SCENARIOS[n.current];setSprite($("nrjScenario"),"NRJ_ImposterScenarios_TTS.png",n.current,10,3);$("nrjScenarioText").innerHTML=`<strong>${s[0]} · ${s[1]} / ${s[2]}</strong><br>Printed Target ${s[3]} · ${s[4]}`;}updateNRJTarget();renderRoller("nrj");}
  function updateNRJTarget(){const t=nrjTarget();$("nrjTarget").textContent=t===null?"—":t;}

  function renderNAPRoller(host,dice){
    const n=state.nap;
    
    host.innerHTML=`<div class="roller-head"><div><p class="kicker">20 Strong dice</p><h2>Active Time Slot dice</h2></div><strong class="nap-roll-count">Strategy rolls ${n.rollsUsed} / ${n.str}</strong></div><div class="nap-dice-zones${n.recovering?" recovering":""}"><section class="nap-dice-zone"><h3>Available</h3><div class="nap-dice-list" data-zone="available"></div></section><div class="nap-dice-columns"><section class="nap-dice-zone"><h3>Rolled</h3><div class="nap-dice-list" data-zone="rolled"></div></section><section class="nap-dice-zone"><h3>Exhausted</h3><div class="nap-dice-list" data-zone="exhausted"></div></section><section class="nap-dice-zone"><h3>Stored on cards</h3><div class="nap-dice-list" data-zone="stored"></div></section><section class="nap-dice-zone"><h3>Banished</h3><div class="nap-dice-list" data-zone="banished"></div></section></div><div class="nap-dice-actions"><button data-roll="nap" class="primary" ${n.recovering||n.rollsUsed>=n.str||n.pendingReward||!dice.some(d=>(d.zone==="available"||d.zone==="rolled")&&d.selected)?"disabled":""}>${n.rollsUsed?"Roll / reroll selected":"Roll selected"}</button><button data-recover="nap"${n.recovering?' class="primary"':""}>${n.recovering?`Confirm recovery (${recoverPicked("nap").length} / ${recoverCap("nap")})`:"Recover up to REC"}</button><button data-ready="nap" ${n.recovering?"disabled":""}>Ready all</button><button data-nap-exhaust ${n.recovering?"disabled":""}>Exhaust unassigned</button>${n.recovering?'<button data-recover-cancel="nap" class="recover-cancel">Cancel recovery</button>':""}</div>${n.recovering?`<p class="hint">Recovery: tap exhausted dice to choose up to ${recoverCap("nap")}, then Confirm recovery.</p>`:""}<div class="roll-result" role="status"></div>`;
    [...dice].sort(byColor).forEach(d=>{const b=document.createElement("button");b.className=`roll-die ${d.color} ${d.zone} ${d.selected?"selected":""}`;const face=document.createElement("span");face.className="face";face.textContent=d.face||"";b.appendChild(face);const tiny=document.createElement("span");tiny.className="tiny";tiny.textContent=d.color[0].toUpperCase();b.appendChild(tiny);b.title=`${d.color} · ${d.zone}${d.zone==="rolled"||d.face?` · ${faceLabel(d.face)}`:""}`;b.setAttribute("aria-label",`${d.color} ${d.zone}${d.zone==="rolled"||d.face?` · ${faceLabel(d.face)}`:""}`);b.onclick=()=>{if(n.recovering){toggleRecoverDie("nap",d);return;}if(d.zone!=="available"&&d.zone!=="rolled")return;d.selected=!d.selected;save();renderRoller("nap");};host.querySelector(`[data-zone="${d.zone}"]`).appendChild(b);});
    host.querySelector(".roll-result").textContent=n.rollResult;
  }
  function renderRoller(game){const host=$(`${game}Roller`),dice=state[game].dice;if(game==="nap"){renderNAPRoller(host,dice);return;}const rec=!!state[game].recovering;host.classList.toggle("recovering",rec);host.innerHTML=`<div class="roller-head"><div><p class="kicker">20 Strong dice</p><h2>${rec?`Tap exhausted dice to recover (up to ${recoverCap(game)})`:"Tap available dice to commit"}</h2></div><div class="compact-actions"><button data-roll="${game}" class="primary" ${rec?"disabled":""}>Roll selected</button><button data-recover="${game}"${rec?' class="primary"':""}>${rec?`Confirm recovery (${recoverPicked(game).length} / ${recoverCap(game)})`:"Recover up to REC"}</button><button data-ready="${game}" ${rec?"disabled":""}>Ready all</button>${rec?`<button data-recover-cancel="${game}">Cancel recovery</button>`:""}</div></div><div class="roller-dice"></div><div class="roll-result"></div>`;const row=host.querySelector(".roller-dice");[...dice].sort(byColor).forEach(d=>{const b=document.createElement("button");b.className=`roll-die ${d.color} ${d.zone} ${d.selected?"selected":""}`;const face=document.createElement("span");face.className="face";face.textContent=d.face||"";b.appendChild(face);const tiny=document.createElement("span");tiny.className="tiny";tiny.textContent=d.color[0].toUpperCase();b.appendChild(tiny);b.title=`${d.color} · ${d.zone}${d.zone==="rolled"||d.face?` · ${faceLabel(d.face)}`:""}`;b.onclick=()=>{if(rec){toggleRecoverDie(game,d);return;}if(d.zone!=="available")return;d.selected=!d.selected;save();renderRoller(game);};row.appendChild(b);});}
  function rollSelected(game){const n=state[game],dice=n.dice.filter(d=>d.selected&&(d.zone==="available"||game==="nap"&&d.zone==="rolled"));if(!dice.length||game==="nap"&&(n.rollsUsed>=n.str||n.pendingReward))return;let successes=0;dice.forEach(d=>{d.face=FACE[d.color][Math.floor(Math.random()*6)];successes+=d.face==="✷"?2:d.face==="✦"?1:0;d.zone=game==="nap"?"rolled":"exhausted";d.selected=false;});if(game==="nap"){n.rollsUsed++;n.phaseCommittedSuccesses=0;n.rollResult=`Strategy roll ${n.rollsUsed} of ${n.str}: ${tallyText(rollTally(dice))} from ${dice.length} ${dice.length===1?"die":"dice"}. ${n.rollsUsed<n.str?"Select unassigned rolled dice to apply or reroll.":"No Strategy rolls remain; apply any unassigned rolled dice."}`;save();renderNAP();return;}save();renderRoller(game);$(`${game}Roller`).querySelector(".roll-result").textContent=`${tallyText(rollTally(dice))} from ${dice.length} ${dice.length===1?"die":"dice"}.`;}
  function completeNAPAssignment(a,context={}){
    const n=state.nap;if(n.pendingReward||a.completed)return;
    const committed=[...new Set([...(a.committedDice||[]),...(a.storedDice||[])])],committedDice=committed.map(id=>n.dice.find(d=>d.id===id)).filter(Boolean);
    (a.storedDice||[]).forEach(id=>{const d=n.dice.find(x=>x.id===id);if(d){d.zone="exhausted";d.selected=false;}});
    a.completed=true;a.completedDay=n.day;a.rewardClaimed=true;
    // The card says "Assignment", and an Impostor Task is one.
    if(n.apprentice==="Technician"&&a.type==="s"){
      const back=n.dice.filter(d=>d.zone==="exhausted").slice(0,2);
      back.forEach(d=>{d.zone="available";d.face="";d.selected=false;});
      if(back.length)n.notice=`Technician: ${napCard(a.type,a.i,a.nrj,a.dot).name} repaired - recovered ${back.length} ${back.length===1?"die":"dice"}.`;
    }
    if(n.apprentice==="Opportunist"&&a.type==="t"&&!a.demandSide)
      recoverOneNAP(DOT_COLOR[napCard(a.type,a.i,a.nrj,a.dot).dot],`${napCard(a.type,a.i,a.nrj,a.dot).name} completed as a Request`);
    // Impostor Tasks are Mandatory and grant no Credits, and the unmarked
    // Tasks are not Credit Tasks either.
    if(a.type==="t"&&!a.nrj&&NAP_TASK_SUBJECTS[a.i]){n.credits++;n.completedCredits.push({type:"t",i:a.i});}
    const reward=(kind,remaining,text,extra={})=>{n.pendingReward={kind,remaining,text,cardId:a.id,cardType:a.type,cardIndex:a.i,usedColors:[],...extra};a.rewardClaimed=false;};
    if(a.type==="o"&&!a.nrj){
      // Kept, not paid out: it goes to hand and is spent whenever you like.
      n.coupons=[...(n.coupons||[]),a.i];
      n.notice=`${NAP_OPPS[a.i]} completed. Kept as a coupon — ${NAP_COUPONS[a.i].effect}`;
    }else if(a.type==="o"&&a.nrj){
      const card=NAP_DEVIOUS[a.i];
      if(card[4]==="exam"){
        n.deviousCoupons=[...(n.deviousCoupons||[]),a.i];
        n.notice=`${card[0]} completed. Kept for the Final Exam — ${card[3].replace("Final Exam: ","")}`;
      }else{
        n.notice=`${card[0]} completed. Resolve now: ${card[3]}`;
      }
    }
    if(a.type!=="t"||a.demandSide)return;
    const i=a.i,target=napCard("t",i).target,total=a.progress||context.successes||0,used=a.diceUsed||committedDice.length,crits=a.critUsed?1:0;
    if(i===6&&total===target)n.hp++;
    if(i===13)n.rec++;
    if(i===23)n.str++;
    if(i===19||i===20){const count=Math.min(i===19?3:1,n.deck.length),order=[];for(let j=0;j<count;j++)order.push(n.deck.pop());if(count)reward("peek",0,NAP_REQUEST_EFFECTS[i],{order});return;}
    if(i===21){reward("yellowGreen",1,NAP_REQUEST_EFFECTS[i]);return;}
    if(i===24&&(context.manual||a.attempts===1)){reward("any",1,NAP_REQUEST_EFFECTS[i]);return;}
    const eligible=(i===0&&n.phaseCommittedSuccesses===2)||(i===1&&used<=3)||(i===4&&!crits)||([8,9,10].includes(i)&&total===target)||(i===12&&used===3)||(i===14&&a.attempts===1)||(i===16&&context.priorStored===0)||(i===17&&a.source==="primary")||(i===18&&used===4)||(i===22&&used<=4)||(i===25&&crits>0);
    const unassignedHits=i===0&&n.dice.some(d=>d.zone==="rolled"&&(d.face==="✦"||d.face==="✷"));
    if(!unassignedHits&&((eligible&&committed.length)||context.manual&&[0,1,4,8,9,10,12,14,16,17,18,22,25].includes(i)))reward(context.manual&&!committed.length?"any":"committed",1,NAP_REQUEST_EFFECTS[i],{eligibleIds:committed});
  }
  // Printed effects on the NRJ module cards that the lab can check. The rest
  // stay table-judged; each is named here so it is clear which is which.
  //   Following 0  Nobulous Needs This Now - first die to another Assignment
  //                must match that Assignment's dot
  //   Following 1  Unscheduled Demonstration - work it before anything else
  //   Impostor  1  Load-Bearing Prosthetics - 2 successes of one color
  //   Impostor  2  Emergency Specimen Handling - commit 2 dice to start
  function moduleBlock(a, dice, successful){
    const n = state.nap, row = napRow();
    const card = napCard(a.type, a.i, a.nrj, a.dot);
    // A Following Setback's own restriction on working other Assignments.
    const demo = row.find(x => x.type === "s" && x.nrj && x.i === 1 && !x.completed && !x.ignored);
    if (demo && demo.id !== a.id && !(demo.storedDice || []).length)
      return `${napCard("s", 1, true).name}: commit at least one die here before working anything else.`;
    const needs = row.find(x => x.type === "s" && x.nrj && x.i === 0 && !x.completed && !x.ignored);
    if (needs && needs.id !== a.id && !napUses().needsFirstDone) {
      const want = DOT_COLOR[card.dot];
      if (!dice.some(d => d.color === want))
        return `${napCard("s", 0, true).name}: the first die you commit elsewhere this Time Slot must be ${want}.`;
    }
    // Impostor Task restrictions.
    if (a.type === "t" && a.nrj) {
      if (a.i === 1) {
        const byColor = {};
        successful.forEach(d => byColor[d.color] = (byColor[d.color] || 0) + 1);
        if (!Object.values(byColor).some(c => c >= 2))
          return `${card.name}: at least 2 applied successes must come from the same color.`;
      }
      if (a.i === 2 && !(a.storedDice || []).length && dice.length < 2)
        return `${card.name}: commit at least 2 dice on the first attempt.`;
    }
    return "";
  }
  function applyNAPDice(id){
    const n=state.nap,row=napRow(),a=row.find(x=>x.id==id),dice=n.dice.filter(d=>d.zone==="rolled"&&d.selected);
    if(n.pendingReward||!a||a.completed||!dice.length)return;
    // A Following Setback prints its own restriction instead of locking the row.
    const uses=napUses(),lock=row.find(x=>x.type==="s"&&!x.nrj&&!x.completed&&!x.ignored);
    if(lock&&a.id!==lock.id){
      // "No other Assignment may be worked until this Setback is resolved."
      n.rollResult=`${napCard("s",lock.i,lock.nrj,lock.dot).name} blocks the row: resolve the Setback first.`;
      save();renderNAP();return;
    }
    const successful=dice.filter(d=>d.face),dot={P:"purple",B:"blue",G:"green",Y:"yellow"}[napCard(a.type,a.i,a.nrj,a.dot).dot],counts={};
    successful.forEach(d=>counts[d.color]=(counts[d.color]||0)+1);
    const valid=successful.some(d=>d.color==="red"||d.color===dot)||Object.values(counts).some(count=>count>=2);
    let prodigy=false;
    if(!valid&&n.apprentice==="Prodigy"&&!uses.prodigySlot){
      const all={};dice.forEach(d=>all[d.color]=(all[d.color]||0)+1);
      prodigy=Object.entries(all).some(([color,count])=>count>=2&&dice.some(d=>d.color===color&&d.face));
      if(prodigy)uses.prodigySlot=true;
    }
    let wild=false;
    if(!valid&&!prodigy&&n.couponWild&&successful.length){
      wild=true;n.couponWild=false;      // "Raid the Supply Closet"
    }
    if(!valid&&!prodigy&&!wild){n.rollResult="Select a successful die matching this card's dot, Red, or two successful dice of another color.";save();renderRoller("nap");return;}
    const blocked=moduleBlock(a,dice,successful);
    if(blocked){n.rollResult=blocked;save();renderNAP();return;}
    if(a.type!=="s"||!a.nrj){
      const needs=row.find(x=>x.type==="s"&&x.nrj&&x.i===0&&!x.completed);
      if(needs&&needs.id!==a.id)napUses().needsFirstDone=true;   // once per slot
    }
    const priorStored=(a.storedDice||[]).length,request=a.type==="t"&&!a.demandSide;
    let gained=successful.reduce((sum,d)=>sum+(d.face==="✷"?2:1),0),opportunity=a.type==="o";
    if(request){if(a.i===2&&successful.some(d=>d.color==="blue"&&d.face==="✷"))gained++;if([7,11].includes(a.i))gained+=successful.filter(d=>d.color==="purple"&&d.face==="✷").length;if([3,15].includes(a.i)&&new Set([...a.storedDice.map(id=>n.dice.find(d=>d.id===id)?.color),...successful.map(d=>d.color)]).size>=3)gained++;if(a.i===5&&a.source==="primary")gained++;}
    if(n.activeSlotBonus.crit&&successful.some(d=>d.face==="✷")){gained++;n.activeSlotBonus.crit--;}
    if(opportunity){(a.storedDice||[]).forEach(id=>{const stored=n.dice.find(d=>d.id===id);if(stored)stored.zone="exhausted";});a.storedDice=[];a.progress=0;}
    else a.progress+=gained;
    a.attempts=(a.attempts||0)+1;
    a.diceUsed=(a.diceUsed||0)+dice.length;a.critUsed=!!a.critUsed||dice.some(d=>d.face==="✷");a.committedDice=[...new Set([...(a.committedDice||[]),...dice.map(d=>d.id)])];
    n.phaseCommittedSuccesses+=successful.reduce((sum,d)=>sum+(d.face==="✷"?2:1),0);
    dice.forEach(d=>{d.zone=opportunity||!d.face?"exhausted":"stored";d.selected=false;if(!opportunity&&d.face)a.storedDice.push(d.id);});
    const completed=(opportunity?gained:a.progress)>=(a.demandSide?napCard(a.type,a.i,a.nrj,a.dot).demand:napCard(a.type,a.i,a.nrj,a.dot).target);
    if(completed)completeNAPAssignment(a,{successes:gained,priorStored});
    n.rollResult=`${gained} successes applied to ${napCard(a.type,a.i,a.nrj,a.dot).name}${completed?" · completed":opportunity?" · no progress stored":" · stored"}.`;
    save();renderNAP();
  }
  function recoverCap(game){const n=state[game];return (game==="nap"&&n.recoverOverride!=null)?n.recoverOverride:(n.rec||2);}
  function recoverPicked(game){return state[game].dice.filter(d=>d.zone==="exhausted"&&d.selected);}
  function rollerRender(game,text){if(game==="nap")state.nap.rollResult=text;save();renderRoller(game);if(game!=="nap"){const el=$(`${game}Roller`)?.querySelector(".roll-result");if(el)el.textContent=text;}}
  function recover(game){
    const n=state[game],cap=recoverCap(game);
    if(!n.recovering){
      if(!n.dice.some(d=>d.zone==="exhausted")){rollerRender(game,"No exhausted dice to recover.");return;}
      n.dice.forEach(d=>d.selected=false);n.recovering=true;
      rollerRender(game,`Select up to ${cap} exhausted ${cap===1?"die":"dice"} to recover, then confirm.`);return;
    }
    const picked=recoverPicked(game).slice(0,cap);
    picked.forEach(d=>{d.zone="available";d.face="";d.selected=false;});
    n.recovering=false;n.dice.forEach(d=>d.selected=false);
    rollerRender(game,picked.length?`Recovered ${picked.length} ${picked.length===1?"die":"dice"}: ${picked.map(d=>d.color).join(", ")}.`:"No dice selected; nothing recovered.");
    if(game==="nap"){n.distinctRecover=false;if(n.exam&&n.exam.stage==="exam")n.recoverOverride=null;advanceExamStage();}
  }
  function cancelRecover(game){const n=state[game];n.recovering=false;n.dice.forEach(d=>d.selected=false);rollerRender(game,"Recovery canceled.");if(game==="nap")advanceExamStage();}
  function advanceExamStage(){
    const n=state.nap;
    if(n.phase!=="exam")return;
    if(n.exam.stage==="prep")finishExamPrep();
    else if(n.exam.stage==="recover")n.exam.stage="exam";
    save();renderNAP();
  }
  function toggleRecoverDie(game,d){if(d.zone!=="exhausted")return;if(!d.selected&&recoverPicked(game).length>=recoverCap(game))return;
    if(game==="nap"&&(state.nap.exam?.stage==="prep"||state.nap.distinctRecover)&&!d.selected
       &&recoverPicked("nap").some(x=>x.color===d.color)){
      state.nap.rollResult="Excess-Credit recovery may not pick the same color twice.";save();renderNAP();return;}d.selected=!d.selected;save();renderRoller(game);}
  function ready(game){state[game].recovering=false;state[game].dice.forEach(d=>{if(d.zone==="banished"||game==="nap"&&d.zone==="stored")return;d.zone="available";d.face="";d.selected=false;});save();renderRoller(game);}

  document.addEventListener("click",e=>{
    const discarded=e.target.closest("[data-nap-discard-index]");if(discarded){showNAPCard(state.nap.discard[Number(discarded.dataset.napDiscardIndex)]);return;}
    const credit=e.target.closest("[data-nap-credit-index]");if(credit){showNAPCard(state.nap.completedCredits[Number(credit.dataset.napCreditIndex)]);return;}
    const peekCard=e.target.closest("[data-nap-peek-card-index]");if(peekCard&&state.nap.pendingReward?.kind==="peek"){showNAPCard(state.nap.pendingReward.order[Number(peekCard.dataset.napPeekCardIndex)]);return;}
    const open=e.target.closest("[data-open-game]");if(open)showScreen(open.dataset.openGame);
    const ng=e.target.closest("[data-new-game]");if(ng){if(ng.dataset.newGame==="nap")buildNAP();if(ng.dataset.newGame==="nrj")buildNRJ();}
    const ac=e.target.closest("[data-nap-assign]");if(ac)applyNAPDice(ac.dataset.napAssign);
    const cc=e.target.closest("[data-complete]");if(cc){const a=napRow().find(x=>x.id==cc.dataset.complete);if(a&&!a.completed&&!state.nap.pendingReward)completeNAPAssignment(a,{manual:true});save();renderNAP();}
    const finfReduce=e.target.closest("[data-nap-reduce]");if(finfReduce){useNAPFINFReduce(finfReduce.dataset.napReduce);return;}
    if(e.target.closest("[data-nap-labrat]")){useLabRatSoak();return;}
    const devIgnore=e.target.closest("[data-nap-dev-ignore]");
    if(devIgnore){useDeviousIgnore(devIgnore.dataset.napDevIgnore);return;}
    const dev=e.target.closest("[data-nap-devious]");
    if(dev){spendDeviousCoupon(Number(dev.dataset.napDevious));return;}
    const couponSpend=e.target.closest("[data-nap-coupon]");
    if(couponSpend){spendNAPCoupon(Number(couponSpend.dataset.napCoupon));return;}
    const couponUse=e.target.closest("[data-nap-coupon-use]");
    if(couponUse){const [slot,id]=couponUse.dataset.napCouponUse.split(",");spendNAPCoupon(Number(slot),id);return;}
    const rewardDie=e.target.closest("[data-nap-reward-die]");if(rewardDie){const p=state.nap.pendingReward,d=state.nap.dice.find(x=>x.id==rewardDie.dataset.napRewardDie);if(p&&d&&eligibleNAPReward().includes(d)){d.zone="available";d.face="";d.selected=false;p.remaining--;p.usedColors.push(d.color);if(!p.remaining||!eligibleNAPReward().length)finishNAPReward();state.nap.rollResult=`Recovered ${d.color} die from ${napCard(p.cardType,p.cardIndex).name}.`;save();renderNAP();}}
    const peekMove=e.target.closest("[data-nap-peek-move]");if(peekMove&&state.nap.pendingReward?.kind==="peek"){const [i,delta]=peekMove.dataset.napPeekMove.split(",").map(Number),order=state.nap.pendingReward.order,j=i+delta;if(j>=0&&j<order.length){[order[i],order[j]]=[order[j],order[i]];save();renderNAP();}}
    if(e.target.closest("[data-nap-peek-bottom]")&&state.nap.pendingReward?.kind==="peek"){state.nap.pendingReward.toBottom=!state.nap.pendingReward.toBottom;save();renderNAP();}
    if(e.target.closest("[data-nap-reward-done]")){const p=state.nap.pendingReward;if(p?.kind==="peek"){if(p.toBottom)state.nap.deck.unshift(p.order[0]);else p.order.slice().reverse().forEach(card=>state.nap.deck.push(card));}finishNAPReward();save();renderNAP();}
    if(e.target.closest("[data-nap-exhaust]")){state.nap.dice.filter(d=>d.zone==="rolled").forEach(d=>{d.zone="exhausted";d.selected=false;});state.nap.rollResult="Unassigned rolled dice exhausted.";save();renderNAP();}
    const roll=e.target.closest("[data-roll]");if(roll&&["nap","nrj"].includes(roll.dataset.roll))rollSelected(roll.dataset.roll);
    const recCancel=e.target.closest("[data-recover-cancel]");if(recCancel){cancelRecover(recCancel.dataset.recoverCancel);return;}
    const rec=e.target.closest("[data-recover]");if(rec)recover(rec.dataset.recover);
    const readyBtn=e.target.closest("[data-ready]");if(readyBtn)ready(readyBtn.dataset.ready);
  });
  $("napDeckTab").onclick=()=>{napPileView="deck";renderNAPPileView();};
  $("napDiscardTab").onclick=()=>{napPileView="discard";renderNAPPileView();};
  $("napDiscardClose").onclick=()=>$("napDiscardDialog").close();
  $("napDiscardDialog").onclick=e=>{if(e.target===$("napDiscardDialog"))e.target.close();};
  document.querySelectorAll("[data-cards-toggle]").forEach(b=>b.onclick=()=>toggleCardList(b.dataset.cardsToggle,b));
  addEventListener("resize",()=>document.querySelectorAll(".game-cards:not(.hidden)").forEach(sizeCardList));
  addEventListener("scroll",()=>{if(!$("cardPeek").classList.contains("hidden"))hideCardPeek();},true);
  $("homeBtn").onclick=()=>showScreen("home");$("gameNav").onchange=e=>showScreen(e.target.value);
  ["campaignMode","nrjTier","finaleMode"].forEach(id=>{const key={campaignMode:"mode",nrjTier:"tier",finaleMode:"finale"}[id];$(id).value=state.config[key];$(id).onchange=e=>{state.config[key]=e.target.value;save();window.dispatchEvent(new CustomEvent("nobulous-tier"));};});
  [["batTier","bat"],["napTier","nap"],["aosTier","aos"]].forEach(([id,game])=>{
    const sel=$(id);if(!sel)return;
    sel.onchange=e=>{window.NOBULOUS_TIER.setOverride(game,e.target.value);};
  });
  window.addEventListener("nobulous-tier",()=>{renderTierPickers();window.AOS_LAB?.render?.();if(!$("screen-nap").classList.contains("hidden"))renderNAP();window.BAT_LAB?.render?.();});
  $("napReveal").onclick=revealNAP;$("napAdvance").onclick=advanceNAP;document.querySelectorAll("[data-nap-choice]").forEach(b=>b.onclick=()=>chooseNAP(Number(b.dataset.napChoice)));
  $("napCreditGoal").value=String(state.nap.creditGoal||6);
  $("napCreditGoal").onchange=e=>{
    const n=state.nap,goal=Number(e.target.value);
    n.creditGoal=goal;
    n.notice=`Difficulty set: ${({5:"Easy",6:"Standard",7:"Hard",8:"Nobulous"})[goal]} - earn ${goal} Credits to reach the Final Exam.`;
    save();renderNAP();
  };
  $("napDifficulty").onchange=e=>{
    const n=state.nap,f=n.finf,v=e.target.value,inc=v.startsWith("inc"),level=Number(v.slice(3));
    if((f.drawn||[]).length||(f.spent||[]).length){
      n.notice="FINF is already in play; the difficulty is locked for this game.";renderNAP();return;}
    // Deal that many of the three FINF cards at random.
    f.mode=inc?"increase":"reduce";f.level=level;
    f.cards=shuffle([0,1,2]).slice(0,level).sort();f.spent=[];f.drawn=[];
    n.deck=n.deck.filter(c=>c.type!=="f");
    const named=f.cards.map(i=>`${i+1} ${FINF_SLOTS[i]}`).join(", ");
    if(inc){
      n.deck=shuffle([...n.deck,...f.cards.map(i=>({type:"f",i}))]);
      n.notice=`Increase ${level}: FINF ${named} shuffled into the Assignment deck.`;
    }else{
      n.notice=`Reduce ${level}: FINF ${named} flipped aside, one use each.`;
    }
    save();renderNAP();
  };
  $("napApprentice").onchange=e=>{state.nap.apprentice=e.target.value;save();renderNAP();};
  $("nrjBuildPool").onclick=buildNRJ;$("nrjDraw").onclick=drawNRJ;$("nrjAvoid").onclick=()=>{if(state.nrj.current===null||state.nrj.eligibleAvoid<1)return;const s=SCENARIOS[state.nrj.current];if(s[0]==="A Sudden Fall")return;state.nrj.eligibleAvoid--;state.nrj.pool=Math.max(0,state.nrj.pool-1);if(s[0]==="Someone Was Seen")state.nrj.deck.push(state.nrj.current);else state.nrj.deck.unshift(state.nrj.current);state.nrj.current=null;save();renderNRJ();};$("nrjSuccess").onclick=()=>resolveNRJ(true);$("nrjFailHp").onclick=()=>resolveNRJ(false,"hp");$("nrjFailDice").onclick=()=>resolveNRJ(false,"dice");["nrjNapMatch","nrjBatMatch","nrjSpecimen","nrjAosStable","nrjAosHot","nrjWrong"].forEach(id=>$(id).oninput=updateNRJTarget);
  if(!state.nap.deck.length)buildNAP();if(!state.nrj.deck.length)buildNRJ();showScreen("home");
  window.addEventListener("pageshow",()=>showScreen($("gameNav")?.value||"home"));
  $("homeBtn")?.addEventListener("click",updateTopbar);
  $("recordBtn").addEventListener("click",()=>{const panel=$("recordPanel"),show=panel.classList.contains("hidden");panel.classList.toggle("hidden",!show);$("recordBtn").setAttribute("aria-pressed",String(show));updateTopbar();if(show)panel.scrollIntoView({behavior:"smooth",block:"start"});});
  $("resetBtn").addEventListener("click",()=>{const game=$("gameNav")?.value;if(!game||game==="home"||game==="aos")return;const btn=document.querySelector(`[data-new-game="${game}"]`);if(btn)btn.click();});
  updateTopbar();
})();
