--=====================================================================
-- THE NOBULOUS SET  --  Tabletop Simulator control script
-- Setup and tracking only: it deals the decks and holds the counters.
-- It never enforces a rule, so you can always do whatever you like.
--=====================================================================

STATE = { game = nil, difficulty = 'Standard', tier = 0,
          splices = 0, credits = 0, suspicion = 0, attempts = 0, backdoors = 0 }

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
  STATE.suspicion, STATE.attempts, STATE.backdoors = 0, 0, 0
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
  local hp = ({Easy = 20, Standard = 22, Hard = 24})[STATE.difficulty]
  local spec = ({Easy = 2, Standard = 3, Hard = 4})[STATE.difficulty]

  park(findDeck('Lab Rats (A / B)'), {-14, 2, 6}, {0, 180, 0})
  park(findDeck('Encounters'), {-4, 2, 4}, {0, 180, 180})
  park(findDeck('Upgrades'), {2, 2, 4}, {0, 180, 180})
  park(findDeck('Specimens'), {8, 2, 4}, {0, 180, 180})
  park(findDeck('Tyrant Attacks'), {14, 2, -6}, {0, 180, 180})

  if STATE.tier >= 1 then park(findDeck('Experimental Protocols'), {-4, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 2 then park(findDeck('Unauthorized Modifications'), {2, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 3 then park(findDeck('Research Notes'), {8, 2, -10}, {0, 180, 0}) end

  STATE.splices = 0
  refreshPanel()
  say('BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' .. hp ..
      '. Shuffle ' .. spec .. ' Specimens into the Upgrade deck.' ..
      (STATE.tier >= 2 and ' Shuffle the 6 Modifications in as well.' or ''))
end

function setupNAP()
  clearTable()
  STATE.game = 'NAP'
  park(findDeck('Apprentices'), {-14, 2, 6}, {0, 180, 0})
  park(findDeck('Tasks'), {-4, 2, 4}, {0, 180, 180})
  park(findDeck('Opportunities'), {2, 2, 4}, {0, 180, 180})
  park(findDeck('Setbacks'), {8, 2, 4}, {0, 180, 180})
  park(findDeck('Time Slots + FINF'), {-14, 2, -2}, {0, 180, 0})
  park(findDeck('Final Exams'), {14, 2, 6}, {0, 180, 180})

  if STATE.tier >= 1 then park(findDeck('Following Setbacks'), {-4, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 2 then park(findDeck('Impostor Tasks'), {2, 2, -10}, {0, 180, 180}) end
  if STATE.tier >= 3 then park(findDeck('Devious Opportunities'), {8, 2, -10}, {0, 180, 180}) end

  STATE.credits = 0
  refreshPanel()
  local msg = 'NAP ready. Build the Assignment deck: 26 Tasks + 6 Opportunities + 3 of 6 Setbacks.'
  if STATE.tier >= 1 then msg = msg .. ' TIER I: use the 4 Following Setbacks INSTEAD of the 3 base Setbacks.' end
  if STATE.tier >= 2 then msg = msg .. ' TIER II: swap in the 4 Impostor Tasks (they grant no Credit).' end
  if STATE.tier >= 3 then msg = msg .. ' TIER III: use the 6 Devious Opportunities instead of the base 6.' end
  say(msg)
end

function setupAoS(deckLabel)
  clearTable()
  STATE.game = 'AoS'
  park(findDeck('Technicians'), {-14, 2, 6}, {0, 180, 0})
  park(findDeck(deckLabel), {-4, 2, 4}, {0, 180, 180})
  park(findDeck('Limitations'), {4, 2, 4}, {0, 180, 180})
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
  local msg = 'AoS ready -- ' .. deckLabel .. '. Technician starts 2 HP / 2 STR / 3 REC.'
  if STATE.tier >= 2 then msg = msg .. ' TIER II: shuffle the 6 Corrupted Limitations into the Limitation deck.' end
  if STATE.tier >= 3 then msg = msg .. ' TIER III: max 2 Backdoor Routines claimed per game.' end
  say(msg)
end

function setupImposter()
  clearTable()
  STATE.game = 'IMP'
  park(findDeck('Council Test Scenarios'), {0, 2, 6}, {0, 180, 180})
  STATE.suspicion, STATE.attempts = 0, 0
  refreshPanel()
  say('Imposter Scenario. Deal 4 Knowledge, 4 Physical and 4 Cover-Up at random, shuffle those 12. ' ..
      'Imposter starts 4 HP / 2 STR / 3 REC. Nine attempts.')
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
    lbl('Credits  ' .. STATE.credits .. ' / 6', -1.2, -1.5, 1400)
    btn('-', 'crMinus', -0.25, -1.5, 320)
    btn('+', 'crPlus', 0.15, -1.5, 320)
    if STATE.credits >= 6 then lbl('FINAL EXAM', 1.3, -1.5, 1400) end
  elseif g == 'AoS' then
    lbl('Backdoors claimed  ' .. STATE.backdoors .. ' / 2', -0.9, -1.5, 2000)
    btn('-', 'bdMinus', 0.35, -1.5, 320)
    btn('+', 'bdPlus', 0.75, -1.5, 320)
  elseif g == 'IMP' then
    lbl('Attempts  ' .. STATE.attempts .. ' / 9', -1.5, -1.5, 1300)
    btn('-', 'atMinus', -0.62, -1.5, 320)
    btn('+', 'atPlus', -0.22, -1.5, 320)
    lbl('Suspicion  ' .. STATE.suspicion .. '   (+' .. STATE.suspicion .. ' Target)', 1.1, -1.5, 2100)
    btn('-', 'suMinus', 0.2, -1.5, 320)
    btn('+', 'suPlus', 0.6, -1.5, 320)
  end

  btn('Clear table', 'btnClear', 1.75, -0.6, 1100, {0.42, 0.18, 0.15})
  btn('Reset counters', 'btnReset', 0.45, -0.6, 1300)
end

function nop() end
function btnBAT() setupBAT() end
function btnNAP() setupNAP() end
function btnIMP() setupImposter() end
function btnAoS()
  local order = {'Routine Programs', 'Specialized Programs', 'Unstable Programs'}
  local pick = ({Easy = 1, Standard = 2, Hard = 3})[STATE.difficulty]
  setupAoS(order[pick])
end
function btnDiff()
  local order = {'Easy', 'Standard', 'Hard'}
  local i = 1
  for k, v in ipairs(order) do if v == STATE.difficulty then i = k end end
  STATE.difficulty = order[(i % 3) + 1]
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
function atPlus() bump('attempts', 1, 'Attempted Scenarios') end
function atMinus() bump('attempts', -1, 'Attempted Scenarios') end
function suPlus() bump('suspicion', 1, 'Suspicion') end
function suMinus() bump('suspicion', -1, 'Suspicion') end

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
