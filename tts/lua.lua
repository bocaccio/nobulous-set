--=====================================================================
-- THE NOBULOUS SET  --  Tabletop Simulator control script
-- Setup and tracking only: it deals the decks and holds the counters.
-- It never enforces a rule, so you can always do whatever you like.
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

function attentionNow()
  local s = math.max(1, STATE.session + 1)
  return ATTENTION[((s - 1) % 5) + 1]
end

function attentionNext()
  local s = math.max(1, STATE.session + 1)
  return ATTENTION[(s % 5) + 1]
end

DECKS = {}            -- label -> guid, filled at load
PANEL = nil

-- ---------------------------------------------------------------- helpers
function findDeck(label)
  local g = DECKS[label]
  if not g then return nil end
  return getObjectFromGUID(g)
end

function say(msg) broadcastToAll(msg, {0.9, 0.86, 0.75}) end

function park(obj, pos, rot, locked)
  if not obj then return end
  obj.setPositionSmooth(pos, false, true)
  if rot then obj.setRotationSmooth(rot, false, true) end
  if locked then Wait.time(function() obj.setLock(true) end, 1.2) end
end

function stow(labels, y)
  -- push every deck out of the way, face down, off to the side
  local x = -34
  for _, d in ipairs(labels) do
    local o = findDeck(d)
    if o then
      o.setLock(false)
      o.setPositionSmooth({x, y or 2, -22}, false, true)
      o.setRotationSmooth({0, 180, 180}, false, true)
      x = x + 3
    end
  end
end

function allLabels()
  local t = {}
  for k, _ in pairs(DECKS) do table.insert(t, k) end
  table.sort(t)
  return t
end

-- ---------------------------------------------------------------- counters
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

-- ---------------------------------------------------------------- setups
function clearTable()
  stow(allLabels(), 2)
  resetCounters()
  STATE.game = nil
  refreshPanel()
  say('Table cleared.')
end

function setupBAT()
  clearTable()
  STATE.game = 'BAT'
  local spec, hp = BAT_DIFF[STATE.difficulty][1], BAT_DIFF[STATE.difficulty][2]

  park(findDeck('Lab Rats (A / B)'), {-14, 2, 6}, {0, 180, 0})
  park(findDeck('Encounters'), {-4, 2, 4}, {0, 180, 180})
  park(findDeck('Upgrades'), {2, 2, 4}, {0, 180, 180})
  park(findDeck('Specimens'), {8, 2, 4}, {0, 180, 180})
  park(findDeck('Tyrant Attacks'), {14, 2, -6}, {0, 180, 180})
  -- The Buff HP card is OPTIONAL (rules/bat.html, Fine-tuning): it holds
  -- part of the Tyrant's Health and is spent first. It used to carry a
  -- difficulty's whole Buff number on top of a flat 20 Health, which is
  -- why this used to stow it at difficulties that had none.
  park(findDeck('Buff HP Track'), {20, 2, -6}, {0, 180, 0})

  if STATE.tier >= 1 then park(findDeck('Experimental Protocols'), {-4, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 2 then park(findDeck('Unauthorized Modifications'), {2, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 3 then park(findDeck('Research Notes'), {8, 2, -10}, {0, 180, 0}) end

  STATE.splices = 0
  refreshPanel()
  say('BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' .. hp ..
      ' (Health dial). Shuffle ' .. spec ..
      ' random Specimens in with the 16 Upgrades.' ..
      ' Five Splices awaken the Tyrant.' ..
      (STATE.tier >= 2 and
       ' TIER II: the 6 Modifications REPLACE 6 ordinary Upgrades.' or '') ..
      ' The Buff HP card is optional -- hold part of the Health on it and' ..
      ' spend that first.')
end

function setupNAP()
  clearTable()
  STATE.game = 'NAP'
  park(findDeck('Apprentices'), {-14, 2, 6}, {0, 180, 0})
  park(findDeck('Tasks'), {-4, 2, 4}, {0, 180, 180})
  park(findDeck('Opportunities'), {2, 2, 4}, {0, 180, 180})
  park(findDeck('Setbacks'), {8, 2, 4}, {0, 180, 180})
  park(findDeck('Time Slots'), {-14, 2, -2}, {0, 180, 0})
  park(findDeck('FINF'), {-14, 2, -6}, {0, 180, 180})
  park(findDeck('Final Exams'), {14, 2, 6}, {0, 180, 180})

  if STATE.tier >= 1 then park(findDeck('Following Setbacks'), {-4, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 2 then park(findDeck('Imposter Tasks'), {2, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 3 then park(findDeck('Devious Opportunities'), {8, 2, -10}, {0, 180, 180}) end

  STATE.credits = 0
  refreshPanel()
  local goal, sb = NAP_DIFF[STATE.difficulty][1], NAP_DIFF[STATE.difficulty][2]
  local msg = 'NAP ready -- ' .. STATE.difficulty .. '. ' .. goal ..
      ' Credits reaches the Final Exam. Build the Assignment deck: 26 Tasks + ' ..
      '6 Opportunities + ' .. sb .. ' of the 6 Setbacks.'
  if STATE.tier >= 1 then
    -- One for one, and that is the whole point of the 2026-11-07 fix: at
    -- Hard and Nobulous a 4-for-3 swap HANDED a Setback back, so the tier
    -- measured easier than no module at all.
    msg = msg .. ' TIER I: shuffle in 3 of the 4 Following Setbacks at random' ..
          ' and set aside 3 base Setbacks -- one out for each one in, so you' ..
          ' still play ' .. sb .. '.'
  end
  if STATE.tier >= 2 then msg = msg .. ' TIER II: add the 4 Imposter Tasks, one per subject; each REPLACES a Credit Task of the same subject and grants no Credit.' end
  if STATE.tier >= 3 then msg = msg .. ' TIER III: use the 6 Devious Opportunities instead of the base 6.' end
  say(msg)
end

function setupAoS()
  clearTable()
  STATE.game = 'AoS'
  park(findDeck('Technicians'), {-14, 2, 6}, {0, 180, 0})
  -- All THREE Program decks, because difficulty is a MIX of them and not a
  -- choice between them. This used to deal one deck named by difficulty,
  -- which is a game nothing in the set describes.
  park(findDeck('Routine Programs'), {-8, 2, 4}, {0, 180, 180})
  park(findDeck('Specialized Programs'), {-2, 2, 4}, {0, 180, 180})
  park(findDeck('Unstable Programs'), {4, 2, 4}, {0, 180, 180})
  park(findDeck('Limitations'), {10, 2, -2}, {0, 180, 180})
  park(findDeck('Advanced Programs'), {12, 2, 4}, {0, 180, 180})

  -- five element mats in a row, face up and locked
  local mats = findDeck('Element Mats')
  if mats then
    mats.setLock(false)
    for i = 1, 5 do
      local c = mats.takeObject({position = {-12 + (i - 1) * 6, 1.6, -8},
                                 rotation = {0, 180, 0}, smooth = true})
      Wait.time(function() if c then c.setLock(true) end end, 1.0)
    end
  end

  if STATE.tier >= 1 then park(findDeck('Nobulous Interference'), {-4, 2, -16}, {0, 180, 180}) end
  if STATE.tier >= 2 then park(findDeck('Corrupted Limitations'), {2, 2, -16}, {0, 180, 180}) end
  if STATE.tier >= 3 then park(findDeck('Backdoor Routines'), {8, 2, -16}, {0, 180, 0}) end

  STATE.backdoors = 0
  refreshPanel()
  local mix = AOS_MIX[STATE.difficulty]
  local msg = 'AoS ready -- ' .. STATE.difficulty ..
      '. Build an 8-card Program deck: ' .. mix[1] .. ' Routine, ' ..
      mix[2] .. ' Specialized, ' .. mix[3] ..
      ' Unstable. Technician starts 2 HP / 2 STR / 3 REC.' ..
      ' Every element must receive at least one die.'
  if STATE.tier >= 2 then msg = msg .. ' TIER II: shuffle the 6 Corrupted Limitations into the Limitation deck.' end
  if STATE.tier >= 3 then msg = msg .. ' TIER III: max 2 Backdoor Routines claimed per game.' end
  say(msg)
end

function setupImposter()
  clearTable()
  STATE.game = 'IMP'
  park(findDeck('Exhibits'), {0, 2, 6}, {0, 180, 180})
  park(findDeck('Imposters (A / B)'), {-14, 2, 6}, {0, 180, 0})
  -- The Research Pool is kept face-up beside the table, all 18 of them.
  park(findDeck('Research Notes'), {14, 2, -10}, {0, 180, 0})
  park(findDeck('Devious Opportunities'), {14, 2, -4}, {0, 180, 0})
  park(findDeck('Backdoor Routines'), {14, 2, 2}, {0, 180, 0})
  STATE.session = 0
  refreshPanel()
  local t = IMP_TIRED[STATE.difficulty]
  say('Imposter Scenario -- ' .. STATE.difficulty ..
      '. Deal 5 Knowledge, 5 Physical and 5 Cover-Up at random from the 24' ..
      ' Exhibits and shuffle those 15 into a face-down Dossier.' ..
      ' Imposter starts 5 HP / 2 STR / 3 REC with all 17 dice, less ' ..
      (t[1] + t[2] + t[3] + t[4] == 0 and 'none -- Easy exhausts nothing.'
       or (t[1] .. ' Yellow, ' .. t[2] .. ' Green, ' .. t[3] .. ' Blue and ' ..
           t[4] .. ' Purple, which start exhausted (never Red).')) ..
      ' Nine sessions. Keep all 18 Research Pool cards face-up: a RETAINED' ..
      ' card reduces one Exhibit Target by 2 -- retain at most 3 NAP,' ..
      ' 2 BAT, 2 AoS.')
end

-- ---------------------------------------------------------------- panel
function refreshPanel()
  if not PANEL then return end
  PANEL.clearButtons()
  local y = 0.2
  local function btn(label, fn, x, z, w, col)
    PANEL.createButton({click_function = fn, function_owner = self, label = label,
      position = {x, y, z}, width = w or 900, height = 260, font_size = 130,
      color = col or {0.16, 0.15, 0.13}, font_color = {1, 1, 1}})
  end
  local function lbl(text, x, z, w)
    PANEL.createButton({click_function = 'nop', function_owner = self, label = text,
      position = {x, y, z}, width = w or 900, height = 220, font_size = 110,
      color = {0.93, 0.91, 0.85}, font_color = {0.13, 0.11, 0.09}})
  end

  lbl('THE NOBULOUS SET', 0, -4.3, 2600)

  btn('Set up BAT', 'btnBAT', -1.7, -3.3, 1100, {0.17, 0.37, 0.29})
  btn('Set up NAP', 'btnNAP', -0.55, -3.3, 1100, {0.42, 0.25, 0.55})
  btn('Set up AoS', 'btnAoS', 0.6, -3.3, 1100, {0.54, 0.24, 0.18})
  btn('Imposter', 'btnIMP', 1.75, -3.3, 1100, {0.29, 0.23, 0.42})

  lbl('Difficulty  ' .. STATE.difficulty, -1.1, -2.4, 1500)
  btn('cycle', 'btnDiff', 0.35, -2.4, 700)
  lbl('NRJ Tier  ' .. (STATE.tier == 0 and 'off' or
      ({'I Agenda', 'II Contamination', 'III Exploitation'})[STATE.tier]), 1.5, -2.4, 1900)
  btn('cycle', 'btnTier', -1.9, -2.4, 700)

  local g = STATE.game
  if g == 'BAT' then
    lbl('Splices  ' .. STATE.splices .. ' / 5', -1.2, -1.5, 1400)
    btn('-', 'splMinus', -0.25, -1.5, 320)
    btn('+', 'splPlus', 0.15, -1.5, 320)
    if STATE.splices >= 5 then lbl('TYRANT AWAKE', 1.3, -1.5, 1400) end
  elseif g == 'NAP' then
    local goal = NAP_DIFF[STATE.difficulty][1]
    lbl('Credits  ' .. STATE.credits .. ' / ' .. goal, -1.2, -1.5, 1400)
    btn('-', 'crMinus', -0.25, -1.5, 320)
    btn('+', 'crPlus', 0.15, -1.5, 320)
    if STATE.credits >= goal then lbl('FINAL EXAM', 1.3, -1.5, 1400) end
  elseif g == 'AoS' then
    lbl('Backdoors claimed  ' .. STATE.backdoors .. ' / 2', -0.9, -1.5, 2000)
    btn('-', 'bdMinus', 0.35, -1.5, 320)
    btn('+', 'bdPlus', 0.75, -1.5, 320)
  elseif g == 'IMP' then
    lbl('Session  ' .. math.min(9, STATE.session + 1) .. ' / 9', -1.5, -1.5, 1300)
    btn('-', 'atMinus', -0.62, -1.5, 320)
    btn('+', 'atPlus', -0.22, -1.5, 320)
    -- Derived, not counted: the attention advances one step at the end of
    -- every session, so a hand counter for it could only ever disagree.
    lbl('Attention  ' .. attentionNow() .. '  then ' .. attentionNext(),
        1.1, -1.5, 2100)
  end

  btn('Clear table', 'btnClear', 1.75, -0.6, 1100, {0.42, 0.18, 0.15})
  btn('Reset counters', 'btnReset', 0.45, -0.6, 1300)
end

function nop() end
function btnBAT() setupBAT() end
function btnNAP() setupNAP() end
function btnIMP() setupImposter() end
function btnAoS() setupAoS() end
function btnDiff()
  local i = 1
  for k, v in ipairs(LEVELS) do if v == STATE.difficulty then i = k end end
  STATE.difficulty = LEVELS[(i % #LEVELS) + 1]
  refreshPanel()
end
function btnTier()
  STATE.tier = (STATE.tier + 1) % 4
  refreshPanel()
end
function btnClear() clearTable() end
function btnReset() resetCounters() end
function splPlus() bump('splices', 1, 'Splices') end
function splMinus() bump('splices', -1, 'Splices') end
function crPlus() bump('credits', 1, 'Credits') end
function crMinus() bump('credits', -1, 'Credits') end
function bdPlus() bump('backdoors', 1, 'Backdoor Routines claimed') end
function bdMinus() bump('backdoors', -1, 'Backdoor Routines claimed') end
function atPlus() bump('session', 1, 'Sessions played') end
function atMinus() bump('session', -1, 'Sessions played') end

-- ---------------------------------------------------------------- lifecycle
function onLoad(saved)
  if saved and saved ~= '' then
    local ok, t = pcall(function() return JSON.decode(saved) end)
    if ok and t then STATE = t.state or STATE; DECKS = t.decks or DECKS end
  end
  if next(DECKS) == nil then
    for _, o in ipairs(getAllObjects()) do
      local n = o.getName()
      if n and n ~= '' and (o.tag == 'Deck' or o.tag == 'Card') then DECKS[n] = o.getGUID() end
      if n == 'Control Panel' then PANEL = o end
    end
  else
    PANEL = getObjectFromGUID(PANEL_GUID or '')
  end
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == 'Control Panel' then PANEL = o end
  end
  refreshPanel()
end

function onSave()
  return JSON.encode({state = STATE, decks = DECKS})
end
