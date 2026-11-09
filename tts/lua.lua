--=====================================================================
-- THE NOBULOUS SET  --  Tabletop Simulator control script
--
-- Setup only. It deals the cards and holds the counters; it never
-- enforces a rule in play, so you can always do whatever you like.
--
-- FOUR BOXES HOLD EVERY CARD. A setup button takes out what that game
-- needs, performs the printed setup -- the random mixes AND the tier
-- swaps -- and leaves everything else in the box. Nothing is parked on
-- the table "ready to be sorted by hand" any more.
--
-- BOX, HOME, NAP_CREDIT and EXHIBIT_BLOCK are GENERATED above this line
-- by build_mod.py and are not in this file: the box GUIDs come from the
-- save it is building, and the two card-index tables are read out of
-- generator/build_nap.py and generator/build_nrj.py so that a reordered
-- card table cannot leave a stale index behind here.
--=====================================================================

STATE = { game = nil, difficulty = 'Standard', tier = 0,
          splices = 0, credits = 0, session = 0, backdoors = 0 }

-- THE PRINTED NUMBERS, in one place. This script enforces nothing; it only
-- SAYS them, which is exactly how they drifted - every one below used to be
-- a hand copy inside the function that announced it. generator/
-- check_app_sync.py now holds these four tables against bat.DIFFICULTY,
-- nap.LEVELS, aos.LEVELS and the finale table in rules/nrj.html.
LEVELS = { 'Easy', 'Standard', 'Hard', 'Nobulous' }
-- BAT: Specimens shuffled into the Upgrade deck, and the Tyrant's Health.
BAT_DIFF = { Easy = {5, 9}, Standard = {6, 10}, Hard = {7, 12}, Nobulous = {8, 14} }
-- NAP: the Credit goal, and how many Setbacks are in the Assignment deck.
NAP_DIFF = { Easy = {5, 3}, Standard = {6, 3}, Hard = {7, 4}, Nobulous = {8, 5} }
-- AoS: the 8-Program mix, Routine / Specialized / Unstable. Each step up
-- trades one Routine for one Unstable; Specialized stays at 3.
AOS_MIX = { Easy = {3, 3, 2}, Standard = {2, 3, 3}, Hard = {1, 3, 4}, Nobulous = {0, 3, 5} }
-- The finale: dice that START exhausted, Yellow / Green / Blue / Purple.
-- Red is never one of them - session 5 allows only Red and Yellow.
IMP_TIRED = { Easy = {0, 0, 0, 0}, Standard = {3, 2, 2, 2},
              Hard = {3, 3, 3, 2}, Nobulous = {3, 3, 4, 4} }
-- The Council's attention advances one step at the end of every session, so
-- it is derived from the clock rather than tracked by hand.
ATTENTION = { 'Yellow', 'Green', 'Blue', 'Purple', 'Red' }

PANEL = nil
FACEUP = {0, 180, 0}
FACEDOWN = {0, 180, 180}
-- Staging points for a card or deck on its way home or into a merge.
-- They sit OVER THE EMPTY FRONT OF THE TABLE, not past its edge: a deck
-- that waits a step at z 30 is a deck falling on the floor. pad() keeps
-- decks being merged in the same step from landing on each other.
OFF = {0, 10, -20}

function pad(i) return {(i - 3) * 7, 10, -20} end

function attentionNow()
  local s = math.max(1, STATE.session + 1)
  return ATTENTION[((s - 1) % 5) + 1]
end

function attentionNext()
  local s = math.max(1, STATE.session + 1)
  return ATTENTION[(s % 5) + 1]
end

function say(msg) broadcastToAll(msg, {0.9, 0.86, 0.75}) end

-- ------------------------------------------------------------- the boxes
function boxOf(game) return getObjectFromGUID(BOX[game]) end

-- The box a card or deck belongs to. Cards taken out of a deck are named
-- "<deck label> <n>", so the trailing number comes off before the lookup.
function homeBox(nick)
  if not nick or nick == '' then return nil end
  local game = HOME[nick] or HOME[(nick:gsub(' %d+$', ''))]
  if not game then return nil end
  return boxOf(game)
end

function putHome(obj)
  if not obj then return end
  local b = homeBox(obj.getName())
  if b then
    obj.setLock(false)
    b.putObject(obj)
  end
end

-- The named deck, wherever it currently is: inside a box, or already out
-- on the table from an earlier setup.
function findDeck(label)
  for _, g in pairs(BOX) do
    local b = getObjectFromGUID(g)
    if b then
      for _, e in ipairs(b.getObjects()) do
        if e.nickname == label then return b, e.guid end
      end
    end
  end
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == label then return nil, nil, o end
  end
  return nil, nil, nil
end

-- Take the named deck OUT of its box and put it at pos.
function deckOut(label, pos, rot)
  local b, gu, loose = findDeck(label)
  if b then
    return b.takeObject({guid = gu, position = pos, rotation = rot or FACEDOWN,
                         smooth = false})
  end
  if loose then
    loose.setLock(false)
    loose.setPosition(pos)
    loose.setRotation(rot or FACEDOWN)
    return loose
  end
  say('MISSING DECK: ' .. label)     -- a label that matches nothing, out loud
  return nil
end

-- ---------------------------------------------------------- the sequencer
-- TTS spawns an object over a frame or two, so a deck taken from a box
-- cannot be dealt from in the same frame. Every setup is a list of steps
-- run a few frames apart rather than one long function.
QUEUE = {}

function step(fn) table.insert(QUEUE, fn) end

function pump()
  if #QUEUE == 0 then return end
  local fn = table.remove(QUEUE, 1)
  local ok, err = pcall(fn)
  if not ok then say('Setup error: ' .. tostring(err)) end
  Wait.frames(pump, 8)
end

function run() Wait.frames(pump, 3) end

-- ------------------------------------------------------------- card tools
function shuffled(t)
  local a = {}
  for i, v in ipairs(t) do a[i] = v end
  for i = #a, 2, -1 do
    local j = math.random(i)
    a[i], a[j] = a[j], a[i]
  end
  return a
end

function count(deck)
  if not deck then return 0 end
  local q = deck.getQuantity()
  if q < 0 then return 1 end          -- a single card, not a deck
  return q
end

-- Shuffle, keep n at random, and put the rest back in the box. This is
-- "take that many at random and return the rest to the box", which every
-- one of the four games asks for somewhere in its setup.
function keepN(deck, n)
  if not deck then return nil end
  if n <= 0 then putHome(deck); return nil end
  deck.shuffle()
  for _ = 1, count(deck) - n do
    deck.takeObject({position = OFF, smooth = false,
                     callback_function = function(o) putHome(o) end})
  end
  return deck
end

-- Pull one named card out of a deck and send it home.
function dropCard(deck, nick)
  if not deck then return end
  for _, e in ipairs(deck.getObjects()) do
    if e.nickname == nick then
      deck.takeObject({guid = e.guid, position = OFF, smooth = false,
                       callback_function = function(o) putHome(o) end})
      return
    end
  end
end

function merge(a, b)
  if a and b then a.putObject(b) end
  return a
end

-- Deal a whole deck face-up in a row, centred on x = 0.
function spread(deck, n, z, rot, gap)
  if not deck then return end
  gap = gap or 5.5
  local x0 = -((n - 1) * gap) / 2
  for i = 1, n - 1 do
    deck.takeObject({position = {x0 + i * gap, 3, z}, rotation = rot or FACEUP,
                     smooth = false})
  end
  deck.setPosition({x0, 3, z})
  deck.setRotation(rot or FACEUP)
end

-- --------------------------------------------------------------- counters
function bump(key, delta, label)
  STATE[key] = math.max(0, (STATE[key] or 0) + delta)
  refreshPanel()
  if label then say(label .. ': ' .. STATE[key]) end
end

function resetCounters()
  STATE.splices, STATE.credits = 0, 0
  STATE.session, STATE.backdoors = 0, 0
  refreshPanel()
end

-- Everything that belongs to a box goes back into it, including single
-- cards dealt out of a deck. Anything else on the table - the dice, the
-- panel - has no home and is left alone.
function packUp(quiet)
  QUEUE = {}
  for _, o in ipairs(getAllObjects()) do
    local b = homeBox(o.getName())
    if b and o ~= b then
      o.setLock(false)
      b.putObject(o)
    end
  end
  STATE.game = nil
  resetCounters()
  refreshPanel()
  if not quiet then say('Everything back in its box.') end
end

-- ----------------------------------------------------------------- setups
function setupBAT()
  packUp(true)
  STATE.game = 'BAT'
  local spec, hp = BAT_DIFF[STATE.difficulty][1], BAT_DIFF[STATE.difficulty][2]
  local upg, sp

  step(function()
    spread(deckOut('Lab Rats (A / B)', {0, 3, 9}, FACEUP), 4, 9, FACEUP, 9)
  end)
  step(function()
    local exp = deckOut('Encounters', {-10, 3, 0})
    if exp then exp.shuffle() end
    local ta = deckOut('Tyrant Attacks', {10, 3, 0})
    if ta then ta.shuffle() end
    -- The Buff HP card is OPTIONAL (rules/bat.html, Fine-tuning): it holds
    -- part of the Tyrant's Health and is spent first.
    deckOut('Buff HP Track', {18, 3, 0}, FACEUP)
    upg = deckOut('Upgrades', {0, 3, 0})
    sp = deckOut('Specimens', pad(5))
  end)

  -- TIER II REMOVES SIX **ORDINARY** UPGRADES, and says so by NAME.
  -- Taking six off the top removes ordinary cards only while the
  -- Specimens happen to be elsewhere in the deck, which is an assumption
  -- about deck order that nothing here enforces - and the claim that this
  -- step must precede the Specimen mix rested on it. Named, it cannot eat
  -- a Specimen whatever order the steps run in.
  if STATE.tier >= 2 then
    step(function()
      local n = 0
      for _, e in ipairs(upg and upg.getObjects() or {}) do
        if n < 6 and string.sub(e.nickname, 1, 9) == 'Upgrades ' then
          dropCard(upg, e.nickname)
          n = n + 1
        end
      end
    end)
    step(function() merge(upg, deckOut('Unauthorized Modifications', pad(1))) end)
  end

  step(function() sp = keepN(sp, spec) end)
  step(function() merge(upg, sp) end)
  step(function() if upg then upg.shuffle() end end)

  if STATE.tier >= 1 then
    step(function()
      local p = keepN(deckOut('Experimental Protocols', OFF), 1)
      if p then p.setPosition({-18, 3, -9}); p.setRotation(FACEUP) end
    end)
  end
  if STATE.tier >= 3 then
    step(function()
      spread(deckOut('Research Notes', {0, 3, -17}, FACEUP), 6, -17, FACEUP)
    end)
  end

  step(function()
    STATE.splices = 0
    refreshPanel()
    say('BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' .. hp ..
        ' (Health dial), ' .. spec ..
        ' Specimens shuffled into the Upgrade deck. Four Lab Rats are out:' ..
        ' pick a side for each, then one Purple, Blue, Green and Yellow die' ..
        ' each, and the Red die on a random Rat. Five Splices awaken the' ..
        ' Tyrant.' ..
        (STATE.tier >= 1 and ' TIER I: your Experimental Protocol is face-up.' or '') ..
        (STATE.tier >= 2 and ' TIER II: 6 ordinary Upgrades out, the 6 Modifications in.' or '') ..
        (STATE.tier >= 3 and ' TIER III: the 6 Research Notes are face-up beside the table.' or '') ..
        ' The Buff HP card is optional -- hold part of the Health on it and' ..
        ' spend that first.')
  end)
  run()
end

function setupNAP()
  packUp(true)
  STATE.game = 'NAP'
  local goal, sb = NAP_DIFF[STATE.difficulty][1], NAP_DIFF[STATE.difficulty][2]
  -- TIER I IS ONE FOR ONE: three Following Setbacks in, three base ones
  -- out, so the deck still holds the number the difficulty asks for. The
  -- 4-for-3 swap it used to do HANDED a Setback back at Hard and Nobulous,
  -- which made the tier easier than no module at all (fixed 2026-11-07).
  local base = (STATE.tier >= 1) and (sb - 3) or sb
  local asg

  step(function()
    spread(deckOut('Apprentices', {0, 3, 9}, FACEUP), 3, 9, FACEUP, 9)
    asg = deckOut('Tasks', {0, 3, 0})
  end)

  if STATE.tier >= 2 then
    -- Each Imposter Task REPLACES a Credit Task of the same subject.
    -- NAP_CREDIT is generated from build_nap.py: the 20 Tasks that carry a
    -- subject are the Credit Tasks, five per subject, and the other six
    -- carry none.
    step(function()
      for _, idx in pairs(NAP_CREDIT) do
        local pick = shuffled(idx)[1]
        dropCard(asg, 'Tasks ' .. pick)
      end
    end)
    step(function() merge(asg, deckOut('Imposter Tasks', pad(2))) end)
  end

  step(function()
    -- TIER III replaces the base Opportunities outright.
    local opps = (STATE.tier >= 3) and 'Devious Opportunities' or 'Opportunities'
    merge(asg, deckOut(opps, pad(1)))
  end)
  step(function() merge(asg, keepN(deckOut('Setbacks', pad(3)), base)) end)
  if STATE.tier >= 1 then
    step(function() merge(asg, keepN(deckOut('Following Setbacks', pad(5)), 3)) end)
  end
  step(function() if asg then asg.shuffle() end end)

  step(function()
    deckOut('Final Exams', {14, 3, 0})
    local f = keepN(deckOut('FINF', pad(4)), 1)
    if f then f.setPosition({-18, 3, -9}); f.setRotation(FACEUP) end
    -- Morning is the active Time Slot for Day 1; the other two sit beside it.
    local slots = deckOut('Time Slots', {-14, 3, 0}, FACEUP)
    if slots then spread(slots, 3, -9, FACEUP, 7) end
  end)

  step(function()
    STATE.credits = 0
    refreshPanel()
    say('NAP ready -- ' .. STATE.difficulty .. '. ' .. goal ..
        ' Credits reaches the Final Exam. The Assignment deck is built and' ..
        ' shuffled: 26 Tasks + 6 Opportunities + ' .. sb .. ' Setbacks' ..
        (STATE.tier >= 1 and (' (3 Following and ' .. base .. ' base)') or '') ..
        '. Choose an Apprentice at 2 HP / 2 STR / 2 REC, take all 17 dice,' ..
        ' and work the Morning Time Slot first.' ..
        (STATE.tier >= 2 and ' TIER II: the 4 Imposter Tasks are in, and one Credit Task of each subject came out.' or '') ..
        (STATE.tier >= 3 and ' TIER III: the Devious Opportunities replaced the base six.' or '') ..
        ' FINF is set to one card at random -- swap it if you want another setting.')
  end)
  run()
end

function setupAoS()
  packUp(true)
  STATE.game = 'AoS'
  local mix = AOS_MIX[STATE.difficulty]
  local prog

  step(function()
    spread(deckOut('Technicians', {0, 3, 9}, FACEUP), 3, 9, FACEUP, 9)
  end)
  -- The Program deck is the difficulty: a MIX of all three decks, not a
  -- choice between them. Routine can be 0 at Nobulous, which is why the
  -- deck the other two are merged into is whichever one survives.
  step(function()
    local r = keepN(deckOut('Routine Programs', pad(1)), mix[1])
    local s = keepN(deckOut('Specialized Programs', pad(3)), mix[2])
    local u = keepN(deckOut('Unstable Programs', pad(5)), mix[3])
    prog = r or s or u
    if prog ~= r then merge(prog, r) end
    if prog ~= s then merge(prog, s) end
    if prog ~= u then merge(prog, u) end
  end)
  step(function()
    if prog then
      prog.shuffle()
      prog.setPosition({0, 3, 0})
      prog.setRotation(FACEDOWN)
    end
  end)
  step(function()
    local lim = deckOut('Limitations', {10, 3, 0})
    if STATE.tier >= 2 then merge(lim, deckOut('Corrupted Limitations', pad(2))) end
    if lim then lim.shuffle() end
    local adv = deckOut('Advanced Programs', {18, 3, 0})
    if adv then adv.shuffle() end
    spread(deckOut('Element Mats', {0, 3, -9}, FACEUP), 5, -9, FACEUP, 8)
  end)
  if STATE.tier >= 1 then
    step(function()
      local n = keepN(deckOut('Nobulous Interference', OFF), 1)
      if n then n.setPosition({-18, 3, -17}); n.setRotation(FACEUP) end
    end)
  end
  if STATE.tier >= 3 then
    step(function()
      spread(deckOut('Backdoor Routines', {0, 3, -17}, FACEUP), 6, -17, FACEUP)
    end)
  end

  step(function()
    STATE.backdoors = 0
    refreshPanel()
    say('AoS ready -- ' .. STATE.difficulty .. '. The 8-card Program deck is' ..
        ' built and shuffled: ' .. mix[1] .. ' Routine, ' .. mix[2] ..
        ' Specialized, ' .. mix[3] .. ' Unstable. Choose a Technician at' ..
        ' 2 HP / 2 STR / 3 REC. All 17 dice start available and EVERY' ..
        ' ELEMENT MUST RECEIVE AT LEAST ONE DIE.' ..
        (STATE.tier >= 1 and ' TIER I: your Nobulous Interference card is face-up.' or '') ..
        (STATE.tier >= 2 and ' TIER II: the 6 Corrupted Limitations are shuffled into the Limitation deck.' or '') ..
        (STATE.tier >= 3 and ' TIER III: the 6 Backdoor Routines are face-up; claim at most 2 per game.' or ''))
  end)
  run()
end

function setupImposter()
  packUp(true)
  STATE.game = 'IMP'
  local t = IMP_TIRED[STATE.difficulty]
  local ex

  step(function()
    spread(deckOut('Imposters (A / B)', {0, 3, 9}, FACEUP), 5, 9, FACEUP, 7)
    ex = deckOut('Exhibits', {0, 3, 0})
  end)
  -- THE DOSSIER IS 5 OF EACH DOMAIN, not 15 of 24 at large. EXHIBIT_BLOCK
  -- is generated from build_nrj.py's own SCEN table, so the index ranges
  -- cannot drift away from the printed order.
  step(function()
    local keep = {}
    for _, b in pairs(EXHIBIT_BLOCK) do
      local idx = {}
      for i = b[1], b[2] do table.insert(idx, i) end
      idx = shuffled(idx)
      for i = 1, 5 do keep['Exhibits ' .. idx[i]] = true end
    end
    if ex then
      for _, e in ipairs(ex.getObjects()) do
        if not keep[e.nickname] then
          ex.takeObject({guid = e.guid, position = OFF, smooth = false,
                         callback_function = function(o) putHome(o) end})
        end
      end
    end
  end)
  step(function() if ex then ex.shuffle() end end)
  -- The Research Pool stays face-up beside the table, all 18 of them.
  step(function()
    deckOut('Research Notes', {-14, 3, -10}, FACEUP)
    deckOut('Devious Opportunities', {0, 3, -10}, FACEUP)
    deckOut('Backdoor Routines', {14, 3, -10}, FACEUP)
  end)

  step(function()
    STATE.session = 0
    refreshPanel()
    say('Imposter Scenario -- ' .. STATE.difficulty ..
        '. The Dossier is dealt and shuffled face-down: 5 Knowledge,' ..
        ' 5 Physical and 5 Cover-Up at random from the 24 Exhibits.' ..
        ' Imposter starts 5 HP / 2 STR / 3 REC with all 17 dice, less ' ..
        (t[1] + t[2] + t[3] + t[4] == 0 and 'none -- Easy exhausts nothing.'
         or (t[1] .. ' Yellow, ' .. t[2] .. ' Green, ' .. t[3] .. ' Blue and ' ..
             t[4] .. ' Purple, which start exhausted (never Red).')) ..
        ' Nine sessions. Keep all 18 Research Pool cards face-up: a RETAINED' ..
        ' card reduces one Exhibit Target by 2 -- retain at most 3 NAP,' ..
        ' 2 BAT, 2 AoS.')
  end)
  run()
end

-- ------------------------------------------------------------------ panel
-- THE TILE IS WIDE AND SHALLOW. ControlPanel.png is 1473x520 and the tile
-- is "Stretch": true, so the panel's local space is about x +/-2.6 by
-- z +/-1.0. Every row below lives inside that. The layout used to run from
-- z -4.3 to -0.6 in rows 0.9 apart, which put four of its five rows off
-- the top edge of the tile, hanging in the air.
function refreshPanel()
  if not PANEL then return end
  PANEL.clearButtons()
  local y = 0.2
  local function btn(label, fn, x, z, w, col)
    PANEL.createButton({click_function = fn, function_owner = self, label = label,
      position = {x, y, z}, width = w or 1080, height = 250, font_size = 105,
      color = col or {0.16, 0.15, 0.13}, font_color = {1, 1, 1}})
  end
  local function lbl(text, x, z, w)
    PANEL.createButton({click_function = 'nop', function_owner = self, label = text,
      position = {x, y, z}, width = w or 1080, height = 230, font_size = 100,
      color = {0.93, 0.91, 0.85}, font_color = {0.13, 0.11, 0.09}})
  end

  -- The tile art already prints THE NOBULOUS SET, so the row that used to
  -- repeat it is gone and the four rows fit.
  btn('Set up BAT', 'btnBAT', -1.73, -0.60, 1080, {0.17, 0.37, 0.29})
  btn('Set up NAP', 'btnNAP', -0.58, -0.60, 1080, {0.42, 0.25, 0.55})
  btn('Set up AoS', 'btnAoS', 0.58, -0.60, 1080, {0.54, 0.24, 0.18})
  btn('Imposter', 'btnIMP', 1.73, -0.60, 1080, {0.29, 0.23, 0.42})

  lbl('Difficulty  ' .. STATE.difficulty, -1.88, -0.20, 1240)
  btn('cycle', 'btnDiff', -1.00, -0.20, 400)
  lbl('NRJ Tier  ' .. (STATE.tier == 0 and 'off' or
      ({'I Agenda', 'II Contamination', 'III Exploitation'})[STATE.tier]),
      0.72, -0.20, 1800)
  btn('cycle', 'btnTier', 2.12, -0.20, 400)

  local g = STATE.game
  if g == 'BAT' then
    lbl('Splices  ' .. STATE.splices .. ' / 5', -1.88, 0.20, 1200)
    btn('-', 'splMinus', -1.00, 0.20, 320)
    btn('+', 'splPlus', -0.60, 0.20, 320)
    if STATE.splices >= 5 then lbl('TYRANT AWAKE', 0.90, 0.20, 1400) end
  elseif g == 'NAP' then
    local goal = NAP_DIFF[STATE.difficulty][1]
    lbl('Credits  ' .. STATE.credits .. ' / ' .. goal, -1.88, 0.20, 1200)
    btn('-', 'crMinus', -1.00, 0.20, 320)
    btn('+', 'crPlus', -0.60, 0.20, 320)
    if STATE.credits >= goal then lbl('FINAL EXAM', 0.90, 0.20, 1400) end
  elseif g == 'AoS' then
    lbl('Backdoors  ' .. STATE.backdoors .. ' / 2', -1.88, 0.20, 1200)
    btn('-', 'bdMinus', -1.00, 0.20, 320)
    btn('+', 'bdPlus', -0.60, 0.20, 320)
  elseif g == 'IMP' then
    lbl('Session  ' .. math.min(9, STATE.session + 1) .. ' / 9', -1.88, 0.20, 1200)
    btn('-', 'atMinus', -1.00, 0.20, 320)
    btn('+', 'atPlus', -0.60, 0.20, 320)
    -- Derived, not counted: the attention advances one step at the end of
    -- every session, so a hand counter for it could only ever disagree.
    lbl('Attention  ' .. attentionNow() .. '  then ' .. attentionNext(),
        1.15, 0.20, 2000)
  end

  btn('Pack up', 'btnPack', -1.88, 0.60, 1200, {0.42, 0.18, 0.15})
  btn('Reset counters', 'btnReset', -0.50, 0.60, 1400)
end

function nop() end
function btnBAT() setupBAT() end
function btnNAP() setupNAP() end
function btnIMP() setupImposter() end
function btnAoS() setupAoS() end
function btnPack() packUp() end
function btnReset() resetCounters() end

function btnDiff()
  local i = 1
  for n, v in ipairs(LEVELS) do if v == STATE.difficulty then i = n end end
  STATE.difficulty = LEVELS[(i % #LEVELS) + 1]
  refreshPanel()
  say('Difficulty: ' .. STATE.difficulty .. '. Press a setup button to deal it.')
end

function btnTier()
  STATE.tier = (STATE.tier + 1) % 4
  refreshPanel()
  say('NRJ Tier: ' .. (STATE.tier == 0 and 'off' or STATE.tier) ..
      '. Press a setup button to deal it.')
end

function splPlus() bump('splices', 1, 'Splices') end
function splMinus() bump('splices', -1, 'Splices') end
function crPlus() bump('credits', 1, 'Credits') end
function crMinus() bump('credits', -1, 'Credits') end
function bdPlus() bump('backdoors', 1, 'Backdoors claimed') end
function bdMinus() bump('backdoors', -1, 'Backdoors claimed') end
function atPlus() bump('session', 1, 'Session') end
function atMinus() bump('session', -1, 'Session') end

-- ----------------------------------------------------------------- onLoad
function onLoad()
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == 'Control Panel' then PANEL = o end
  end
  local missing = {}
  for game, g in pairs(BOX) do
    if not getObjectFromGUID(g) then table.insert(missing, game) end
  end
  refreshPanel()
  if #missing > 0 then
    say('Missing box: ' .. table.concat(missing, ', '))
  end
end
