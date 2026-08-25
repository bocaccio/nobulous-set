--=====================================================================
-- THE NOBULOUS SET  --  Tabletop Simulator control script
--
-- Everything starts inside the Card Bank. The table opens showing only the
-- dice, the chip and this panel. Choose a game, set the options, press
-- Start Game, and the decks are dealt, combined and shuffled.
--
-- It never enforces a rule. It deals and counts, nothing else.
--=====================================================================

--[[LAYOUT]]

STATE = { phase = 'setup', game = nil, difficulty = 'Standard',
          tiers = { false, false, false },
          splices = 0, credits = 0, suspicion = 0, attempts = 0, backdoors = 0 }

BANK, PANEL, BUSY = nil, nil, false

FACE_DOWN, FACE_UP = { 0, 180, 180 }, { 0, 180, 0 }
DECK_Y = 2.0

-- The panel sits in the middle of the table while you set up, then moves clear
-- so the cards can be dealt into that space.
PANEL_SETUP = { 0, 1.02, 0 }
PANEL_PLAY  = { 0, 1.02, 15.5 }

-- Button geometry, in tile-local units. The tile spans about +/-0.5, and the
-- panel is scaled 3.4, so anything much past 0.45 lands off the table. Widths
-- and heights are thousandths of a local unit; keep W below the column pitch
-- or the buttons overlap. Adjust here, not in the layout below.
BTN_W, BTN_H, BTN_FONT = 200, 55, 45
LBL_FONT = 40
COL, ROW = 0.22, 0.17          -- pitch between columns / rows

TIER_NAMES = { 'I Agenda', 'II Contamination', 'III Exploitation' }

-- Program deck by difficulty, and the two BAT dials.
AOS_PROGRAM = { Easy = 'Routine Programs', Standard = 'Specialized Programs',
                Hard = 'Unstable Programs' }
BAT_HEALTH  = { Easy = 20, Standard = 22, Hard = 24 }
BAT_SPECIMENS = { Easy = 2, Standard = 3, Hard = 4 }

-- ---------------------------------------------------------------- helpers
function say(msg) broadcastToAll(msg, { 0.9, 0.86, 0.75 }) end

function tierOn(n) return STATE.tiers[n] == true end

function anyTier()
  return tierOn(1) or tierOn(2) or tierOn(3)
end

function spot(label, fallback)
  local p = LAYOUT[label]
  if p then return { p[1], DECK_Y, p[2] } end
  return fallback or { 0, DECK_Y, 0 }
end

--- Find one entry in the bank by nickname. Returns its guid, or nil.
function inBank(nick)
  if not BANK then return nil end
  for _, e in ipairs(BANK.getObjects()) do
    if e.nickname == nick then return e.guid end
  end
  return nil
end

--- Take a named object out of the bank and drop it at pos.
function draw(nick, pos, rot, done)
  local guid = inBank(nick)
  if not guid then
    if done then done(nil) end
    return
  end
  local obj = BANK.takeObject({
    guid = guid, position = pos, rotation = rot or FACE_DOWN,
    smooth = false,
    callback_function = function(o) if done then done(o) end end })
  return obj
end

--- Put an object back in the bank.
function stow(obj)
  if obj and BANK then BANK.putObject(obj) end
end

--- Move n cards off the top of src into target, then continue.
function moveCards(src, target, n, done)
  local moved = 0
  local function step()
    if moved >= n or src == nil then
      if done then done() end
      return
    end
    moved = moved + 1
    local c = src.takeObject({ position = target.getPosition() + Vector(0, 3, 0),
                               smooth = false })
    Wait.frames(function()
      if c then target.putObject(c) end
      Wait.frames(step, 4)
    end, 4)
  end
  step()
end

--- Run a list of functions one after another, each receiving `next`.
function chain(steps, done)
  local i = 0
  local function step()
    i = i + 1
    if steps[i] then steps[i](step) else if done then done() end end
  end
  step()
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

-- ---------------------------------------------------------------- teardown
--- Sweep every loose deck, card and cover back into the bank.
function returnAll(done)
  if not BANK then if done then done() end return end
  local n = 0
  for _, o in ipairs(getAllObjects()) do
    local t = o.type
    if (t == 'Deck' or t == 'Card' or t == 'Tile') and o ~= PANEL and o ~= BANK then
      -- Tiles that are not the panel are the AoS covers.
      o.setLock(false)
      BANK.putObject(o)
      n = n + 1
    end
  end
  Wait.frames(function() if done then done(n) end end, 20)
end

-- ---------------------------------------------------------------- setups
function setupBAT(done)
  local hp = BAT_HEALTH[STATE.difficulty]
  local spec = BAT_SPECIMENS[STATE.difficulty]
  local upgrades, specimens, mods

  chain({
    function(next) draw('Lab Rats (A / B)', spot('Lab Rats (A / B)'), FACE_UP,
                        function() next() end) end,
    function(next) draw('Encounters', spot('Encounters'), FACE_DOWN,
                        function() next() end) end,
    function(next) draw('Tyrant Attacks', spot('Tyrant Attacks'), FACE_DOWN,
                        function() next() end) end,
    function(next) draw('Upgrades', spot('Upgrades'), FACE_DOWN,
                        function(o) upgrades = o; next() end) end,
    function(next) draw('Specimens', spot('Specimens'), FACE_DOWN,
                        function(o) specimens = o; next() end) end,
    -- shuffle the difficulty's Specimens into the Upgrade deck
    function(next)
      if not (upgrades and specimens) then next() return end
      specimens.shuffle()
      Wait.frames(function() moveCards(specimens, upgrades, spec, next) end, 10)
    end,
    function(next) stow(specimens); Wait.frames(next, 10) end,
    -- Tier II: the 6 Unauthorized Modifications go in as well
    function(next)
      if not tierOn(2) then next() return end
      draw('Unauthorized Modifications', spot('Upgrades'), FACE_DOWN, function(o)
        mods = o
        Wait.frames(function()
          if upgrades and mods then upgrades.putObject(mods) end
          Wait.frames(next, 10)
        end, 10)
      end)
    end,
    function(next)
      if upgrades then upgrades.shuffle() end
      next()
    end,
    function(next)
      if tierOn(1) then
        draw('Experimental Protocols', spot('Experimental Protocols'), FACE_DOWN,
             function() next() end)
      else next() end
    end,
    function(next)
      if tierOn(3) then
        draw('Research Notes', spot('Research Notes'), FACE_DOWN,
             function() next() end)
      else next() end
    end,
  }, function()
    STATE.splices = 0
    local msg = 'BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' .. hp ..
                '. ' .. spec .. ' Specimens shuffled into the Upgrade deck.'
    if tierOn(2) then msg = msg .. ' The 6 Modifications went in too.' end
    say(msg)
    if done then done() end
  end)
end

function setupNAP(done)
  local assignment, opportunities, setbacks, impostor
  local usedSetbacks = tierOn(1) and 'Following Setbacks' or 'Setbacks'
  local usedOpps = tierOn(3) and 'Devious Opportunities' or 'Opportunities'
  local nSetbacks = tierOn(1) and 4 or 3

  chain({
    function(next) draw('Apprentices', spot('Apprentices'), FACE_UP,
                        function() next() end) end,
    function(next) draw('Final Exams', spot('Final Exams'), FACE_DOWN,
                        function() next() end) end,
    -- the Assignment deck is built where the Tasks deck sits
    function(next) draw('Tasks', spot('Tasks'), FACE_DOWN,
                        function(o) assignment = o; next() end) end,
    -- Tier II swaps 4 Tasks out for the 4 Impostor Tasks
    function(next)
      if not (tierOn(2) and assignment) then next() return end
      assignment.shuffle()
      Wait.frames(function()
        for i = 1, 4 do
          local c = assignment.takeObject({ position = { 0, 6, -30 }, smooth = false })
          if c then stow(c) end
        end
        Wait.frames(next, 15)
      end, 10)
    end,
    function(next)
      if not tierOn(2) then next() return end
      draw('Impostor Tasks', spot('Tasks'), FACE_DOWN, function(o)
        impostor = o
        Wait.frames(function()
          if assignment and impostor then assignment.putObject(impostor) end
          Wait.frames(next, 10)
        end, 10)
      end)
    end,
    -- all six Opportunities
    function(next)
      draw(usedOpps, spot('Tasks'), FACE_DOWN, function(o)
        opportunities = o
        Wait.frames(function()
          if assignment and opportunities then assignment.putObject(opportunities) end
          Wait.frames(next, 10)
        end, 10)
      end)
    end,
    -- 3 of the 6 Setbacks (4 of 4 on Tier I); the rest stay in the bank
    function(next)
      draw(usedSetbacks, spot('Setbacks'), FACE_DOWN, function(o)
        setbacks = o
        if not setbacks then next() return end
        setbacks.shuffle()
        Wait.frames(function() moveCards(setbacks, assignment, nSetbacks, next) end, 10)
      end)
    end,
    function(next) stow(setbacks); Wait.frames(next, 10) end,
    function(next)
      if assignment then assignment.shuffle() end
      next()
    end,
    -- Time Slots and the FINF track card, dealt face up to their own spots
    function(next)
      draw('Time Slots + FINF', spot('Time Slots + FINF 1'), FACE_UP, function(deck)
        if not deck then next() return end
        local i = 0
        local function one()
          i = i + 1
          if i > 4 then Wait.frames(next, 10) return end
          local p = spot('Time Slots + FINF ' .. i, { -4.4, DECK_Y, 1.4 })
          if i == 4 or deck.remainder then
            deck.takeObject({ position = p, rotation = FACE_UP, smooth = false })
          else
            deck.takeObject({ position = p, rotation = FACE_UP, smooth = false })
          end
          Wait.frames(one, 8)
        end
        one()
      end)
    end,
  }, function()
    STATE.credits = 0
    local msg = 'NAP ready. Assignment deck built and shuffled: 26 Tasks + 6 ' ..
                (tierOn(3) and 'Devious ' or '') .. 'Opportunities + ' ..
                nSetbacks .. ' ' .. usedSetbacks .. '. FINF track -1.'
    if tierOn(2) then msg = msg .. ' 4 Impostor Tasks swapped in.' end
    say(msg)
    if done then done() end
  end)
end

function setupAoS(done)
  local programLabel = AOS_PROGRAM[STATE.difficulty]
  local limitations, corrupted

  chain({
    function(next) draw('Technicians', spot('Technicians'), FACE_UP,
                        function() next() end) end,
    -- the chosen Program deck goes where the Program deck sits
    function(next) draw(programLabel, spot('Specialized Programs'), FACE_DOWN,
                        function() next() end) end,
    function(next) draw('Advanced Programs', spot('Advanced Programs'), FACE_DOWN,
                        function() next() end) end,
    function(next) draw('Limitations', spot('Limitations'), FACE_DOWN,
                        function(o) limitations = o; next() end) end,
    -- Tier II: the 6 Corrupted Limitations shuffle into the Limitation deck
    function(next)
      if not tierOn(2) then next() return end
      draw('Corrupted Limitations', spot('Limitations'), FACE_DOWN, function(o)
        corrupted = o
        Wait.frames(function()
          if limitations and corrupted then limitations.putObject(corrupted) end
          Wait.frames(next, 10)
        end, 10)
      end)
    end,
    function(next)
      if limitations then limitations.shuffle() end
      next()
    end,
    -- five Element Mats, face up
    function(next)
      draw('Element Mats', spot('Element Mats 1'), FACE_UP, function(deck)
        if not deck then next() return end
        local i = 0
        local function one()
          i = i + 1
          if i > 5 then Wait.frames(next, 10) return end
          deck.takeObject({ position = spot('Element Mats ' .. i),
                            rotation = FACE_UP, smooth = false })
          Wait.frames(one, 8)
        end
        one()
      end)
    end,
    -- covers on the two two-sided decks
    function(next)
      draw('Program Cover', spot('Specialized Programs', nil), FACE_UP,
           function() next() end)
    end,
    function(next)
      draw('Advanced Cover', spot('Advanced Programs', nil), FACE_UP,
           function() next() end)
    end,
    function(next)
      if tierOn(1) then
        draw('Nobulous Interference', spot('Nobulous Interference'), FACE_DOWN,
             function() next() end)
      else next() end
    end,
    function(next)
      if tierOn(3) then
        draw('Backdoor Routines', spot('Backdoor Routines'), FACE_DOWN,
             function() next() end)
      else next() end
    end,
  }, function()
    STATE.backdoors = 0
    local msg = 'AoS ready -- ' .. programLabel ..
                '. Technician starts 2 HP / 2 STR / 3 REC.'
    if tierOn(2) then msg = msg .. ' 6 Corrupted Limitations shuffled in.' end
    if tierOn(3) then msg = msg .. ' Max 2 Backdoor Routines per game.' end
    say(msg)
    if done then done() end
  end)
end

--- Imposter: 4 Knowledge + 4 Physical + 4 Cover-Up, shuffled to 12.
-- The sheet is ordered in three blocks of 8, so index decides the domain.
function setupImposter(done)
  draw('Council Test Scenarios', spot('Council Test Scenarios'), FACE_DOWN,
    function(deck)
      if not deck then if done then done() end return end
      local keep = {}
      for block = 0, 2 do
        local pick = {}
        while #pick < 4 do
          local n = math.random(1, 8) + block * 8
          local dup = false
          for _, v in ipairs(pick) do if v == n then dup = true end end
          if not dup then table.insert(pick, n) end
        end
        for _, v in ipairs(pick) do table.insert(keep, v) end
      end
      table.sort(keep, function(a, b) return a > b end)   -- take from the back

      local i = 0
      local function one()
        i = i + 1
        if i > #keep then
          Wait.frames(function()
            stow(deck)                                    -- the other 12
            STATE.suspicion, STATE.attempts = 0, 0
            say('Imposter Scenario. 4 Knowledge, 4 Physical and 4 Cover-Up ' ..
                'drawn and shuffled. 4 HP / 2 STR / 3 REC. Nine attempts.')
            if done then done() end
          end, 15)
          return
        end
        deck.takeObject({ index = keep[i] - 1,
                          position = spot('Council Test Scenarios') ,
                          rotation = FACE_DOWN, smooth = false })
        Wait.frames(one, 6)
      end
      one()
    end)
end

-- ---------------------------------------------------------------- start
function startGame()
  if BUSY or not STATE.game then return end
  BUSY = true
  say('Setting up ' .. STATE.game .. '...')

  returnAll(function()
    resetCounters()
    movePanel(PANEL_PLAY)
    local finish = function()
      STATE.phase = 'playing'
      BUSY = false
      refreshPanel()
    end
    if STATE.game == 'BAT' then setupBAT(finish)
    elseif STATE.game == 'NAP' then setupNAP(finish)
    elseif STATE.game == 'AoS' then setupAoS(finish)
    else setupImposter(finish) end
  end)
end

function packUp()
  if BUSY then return end
  BUSY = true
  returnAll(function(n)
    movePanel(PANEL_SETUP)
    STATE.phase = 'setup'
    STATE.game = nil
    resetCounters()
    BUSY = false
    refreshPanel()
    say('Table cleared -- ' .. (n or 0) .. ' objects back in the Card Bank.')
  end)
end

-- ---------------------------------------------------------------- panel
function movePanel(pos)
  if not PANEL then return end
  PANEL.setLock(false)
  PANEL.setPositionSmooth(pos, false, true)
  Wait.time(function() if PANEL then PANEL.setLock(true) end end, 1.0)
end

function refreshPanel()
  if not PANEL then return end
  PANEL.clearButtons()

  -- The tile carries a 180 degree Y rotation, which mirrors local x and z.
  -- Buttons are written below in natural reading coordinates -- x left to
  -- right, z top to bottom -- and negated here so they land the right way up.
  local function at(x, z) return { -x, 0.2, -z } end

  local function btn(label, fn, x, z, w, col)
    PANEL.createButton({ click_function = fn, function_owner = self, label = label,
      position = at(x, z), width = w or BTN_W, height = BTN_H,
      font_size = BTN_FONT,
      color = col or { 0.16, 0.15, 0.13 }, font_color = { 1, 1, 1 } })
  end
  local function lbl(text, x, z, w)
    PANEL.createButton({ click_function = 'nop', function_owner = self, label = text,
      position = at(x, z), width = w or BTN_W, height = BTN_H,
      font_size = LBL_FONT,
      color = { 0.93, 0.91, 0.85 }, font_color = { 0.13, 0.11, 0.09 } })
  end

  local ON, OFF = { 0.17, 0.37, 0.29 }, { 0.24, 0.23, 0.21 }
  lbl('THE NOBULOUS SET', 0, 0.36, 700)

  if STATE.phase == 'setup' then
    local function gameBtn(code, label, x)
      btn((STATE.game == code and '> ' or '') .. label, 'pick' .. code,
          x, 0.18, 200, STATE.game == code and ON or OFF)
    end
    gameBtn('BAT', 'BAT', -0.33)
    gameBtn('NAP', 'NAP', -0.11)
    gameBtn('AoS', 'AoS', 0.11)
    gameBtn('IMP', 'Imposter', 0.33)

    -- Difficulty drives nothing in NAP or Imposter, so it greys out there.
    if STATE.game == 'BAT' or STATE.game == 'AoS' then
      lbl(STATE.difficulty, -0.32, 0.01, 200)
      btn('difficulty', 'btnDiff', -0.09, 0.01, 220)
      local note = (STATE.game == 'AoS') and AOS_PROGRAM[STATE.difficulty]
                   or ('Tyrant ' .. BAT_HEALTH[STATE.difficulty] .. ' / ' ..
                       BAT_SPECIMENS[STATE.difficulty] .. ' Spec')
      lbl(note, 0.26, 0.01, 440)
    else
      lbl(STATE.game and 'no difficulty setting' or 'choose a game',
          0, 0.01, 620)
    end

    btn((tierOn(1) and '* ' or '') .. 'NRJ I', 'tier1', -0.30, -0.16, 250,
        tierOn(1) and ON or OFF)
    btn((tierOn(2) and '* ' or '') .. 'NRJ II', 'tier2', 0.00, -0.16, 250,
        tierOn(2) and ON or OFF)
    btn((tierOn(3) and '* ' or '') .. 'NRJ III', 'tier3', 0.30, -0.16, 250,
        tierOn(3) and ON or OFF)

    btn(STATE.game and ('START ' .. STATE.game) or 'choose a game',
        'btnStart', 0, -0.35, 480,
        STATE.game and { 0.17, 0.37, 0.29 } or { 0.3, 0.28, 0.25 })
    return
  end

  -- ---- playing
  lbl(STATE.game .. ((STATE.game == 'BAT' or STATE.game == 'AoS')
                     and ('  ' .. STATE.difficulty) or '')
              .. (anyTier() and '  NRJ' or ''), -0.30, 0.18, 300)
  btn('Pack up', 'btnPack', -0.01, 0.18, 220, { 0.42, 0.18, 0.15 })
  btn('Reset', 'btnReset', 0.24, 0.18, 220)

  local g = STATE.game
  if g == 'BAT' then
    lbl('Splices ' .. STATE.splices .. ' / 5', -0.33, -0.02, 240)
    btn('-', 'splMinus', -0.15, -0.02, 90)
    btn('+', 'splPlus', -0.04, -0.02, 90)
    lbl('Tyrant ' .. BAT_HEALTH[STATE.difficulty], 0.22, -0.02, 280)
    if STATE.splices >= 5 then lbl('TYRANT AWAKE', 0, -0.24, 480) end
  elseif g == 'NAP' then
    lbl('Credits ' .. STATE.credits .. ' / 6', -0.33, -0.02, 240)
    btn('-', 'crMinus', -0.15, -0.02, 90)
    btn('+', 'crPlus', -0.04, -0.02, 90)
    if STATE.credits >= 6 then lbl('FINAL EXAM', 0.22, -0.02, 280) end
  elseif g == 'AoS' then
    lbl('Backdoors ' .. STATE.backdoors .. ' / 2', -0.30, -0.02, 300)
    btn('-', 'bdMinus', -0.06, -0.02, 90)
    btn('+', 'bdPlus', 0.05, -0.02, 90)
  else
    lbl('Attempts ' .. STATE.attempts .. ' / 9', -0.36, -0.02, 220)
    btn('-', 'atMinus', -0.19, -0.02, 80)
    btn('+', 'atPlus', -0.09, -0.02, 80)
    lbl('Suspicion ' .. STATE.suspicion, 0.10, -0.02, 220)
    btn('-', 'suMinus', 0.27, -0.02, 80)
    btn('+', 'suPlus', 0.37, -0.02, 80)
  end
end

-- ---------------------------------------------------------------- clicks
function nop() end
function pickBAT() STATE.game = 'BAT'; refreshPanel() end
function pickNAP() STATE.game = 'NAP'; refreshPanel() end
function pickAoS() STATE.game = 'AoS'; refreshPanel() end
function pickIMP() STATE.game = 'IMP'; refreshPanel() end

function btnDiff()
  local order = { 'Easy', 'Standard', 'Hard' }
  local i = 1
  for k, v in ipairs(order) do if v == STATE.difficulty then i = k end end
  STATE.difficulty = order[(i % 3) + 1]
  refreshPanel()
end

--- Tiers are cumulative on the way up -- picking III turns on I and II -- but
-- each one can then be switched off on its own.
function setTier(n)
  if tierOn(n) then
    STATE.tiers[n] = false
  else
    for i = 1, n do STATE.tiers[i] = true end
  end
  refreshPanel()
end
function tier1() setTier(1) end
function tier2() setTier(2) end
function tier3() setTier(3) end

function btnStart() startGame() end
function btnPack() packUp() end
function btnReset() resetCounters() end
function splPlus() bump('splices', 1, 'Splices') end
function splMinus() bump('splices', -1, 'Splices') end
function crPlus() bump('credits', 1, 'Credits') end
function crMinus() bump('credits', -1, 'Credits') end
function bdPlus() bump('backdoors', 1, 'Backdoor Routines') end
function bdMinus() bump('backdoors', -1, 'Backdoor Routines') end
function atPlus() bump('attempts', 1, 'Attempts') end
function atMinus() bump('attempts', -1, 'Attempts') end
function suPlus() bump('suspicion', 1, 'Suspicion') end
function suMinus() bump('suspicion', -1, 'Suspicion') end

-- ---------------------------------------------------------------- lifecycle
function locate()
  for _, o in ipairs(getAllObjects()) do
    local n = o.getName()
    if n == 'Control Panel' then PANEL = o end
    if n == 'Card Bank' then BANK = o end
  end
end

function onLoad(saved)
  if saved and saved ~= '' then
    local ok, t = pcall(function() return JSON.decode(saved) end)
    if ok and type(t) == 'table' and t.state then STATE = t.state end
  end
  if type(STATE.tiers) ~= 'table' then STATE.tiers = { false, false, false } end
  locate()
  Wait.frames(function()
    locate()
    movePanel(STATE.phase == 'playing' and PANEL_PLAY or PANEL_SETUP)
    refreshPanel()
  end, 30)
end

function onSave()
  return JSON.encode({ state = STATE })
end
