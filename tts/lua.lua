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
          splices = 0, credits = 0, suspicion = 0, attempts = 0, backdoors = 0,
          tyrant = 20 }

BANK, PANEL, SETUP, BUSY = nil, nil, nil, false

FACE_DOWN, FACE_UP = { 0, 180, 180 }, { 0, 180, 0 }
DECK_Y = 2.0

-- Where the setup surface goes when it is out of the way. Below the table, so
-- the middle is clear for the cards.
SETUP_SHOWN, SETUP_HIDDEN = { 0, 1.02, 0 }, { 0, -12, 0 }

-- Button geometry. A tile with Stretch takes its image aspect, so local extent
-- is NOT +/-0.5 on both axes: the nameplate art is 2.83:1, giving it roughly
-- +/-0.5 across but only +/-0.18 up the plate. The setup art is square, so it
-- has the full range both ways. Both tiles are scaled 8, so a local pitch of
-- 0.16 is about 1.3 units of table between button centres.
--
-- If buttons still crowd each other, raise the pitches or lower the widths --
-- everything below is expressed in these numbers.
-- TTS shrinks a label to fit its button, then the tile's scale magnifies the
-- result -- so small buttons on a heavily scaled tile give blurry text. These
-- are bigger and the tiles are scaled less, which is sharper on both counts.
-- Row pitch is set well above button height: an earlier pass at 0.14 still
-- overlapped, so rows now sit 0.23 apart.
BTN_W, BTN_H, BTN_FONT, LBL_FONT = 110, 54, 44, 40
ROW_1, ROW_2, ROW_3, ROW_4 = 0.34, 0.11, -0.12, -0.35
NAME_ROW_A, NAME_ROW_B = -0.06, -0.29

TIER_NAMES = { 'I Agenda', 'II Contamination', 'III Exploitation' }

AOS_PROGRAM = { Easy = 'Routine Programs', Standard = 'Specialized Programs',
                Hard = 'Unstable Programs' }

-- The Tyrant's base Health is always 20. Harder modes add Buff Health on top,
-- which has to come off before any normal Health does. The tracker below just
-- counts the total down, so a game can start anywhere -- 8 Buff is the stated
-- ceiling for anyone who wants it, but nothing here enforces a limit.
BAT_BASE_HP = 20
BAT_BUFF = { Easy = 0, Standard = 2, Hard = 4 }
BAT_SPECIMENS = { Easy = 2, Standard = 3, Hard = 4 }

function tyrantStart()
  return BAT_BASE_HP + (BAT_BUFF[STATE.difficulty] or 0)
end

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
  STATE.tyrant = tyrantStart()
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
  local buff = BAT_BUFF[STATE.difficulty] or 0
  local spec = BAT_SPECIMENS[STATE.difficulty]
  STATE.tyrant = tyrantStart()
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
    local msg = 'BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' ..
                BAT_BASE_HP .. (buff > 0 and (' + ' .. buff ..
                ' Buff (remove Buff first)') or '') .. '. ' .. spec ..
                ' Specimens shuffled into the Upgrade deck.'
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
    showSetup(false)
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
    showSetup(true)
    STATE.phase = 'setup'
    STATE.game = nil
    resetCounters()
    BUSY = false
    refreshPanel()
    say('Table cleared -- ' .. (n or 0) .. ' objects back in the Card Bank.')
  end)
end

-- ---------------------------------------------------------------- panel
function showSetup(visible)
  if not SETUP then return end
  SETUP.setLock(false)
  SETUP.setPosition(visible and SETUP_SHOWN or SETUP_HIDDEN)
  Wait.time(function() if SETUP then SETUP.setLock(true) end end, 0.5)
end

--- Buttons sit in the tile's local space, x left to right and z bottom to
-- top, matching the artwork. The tile's 180 degree Y rotation turns the image
-- and its buttons together, so no axis flip is applied here -- an earlier
-- version negated both and produced a mirrored panel.
function mkBtn(tile)
  return function(label, fn, x, z, w, col)
    tile.createButton({ click_function = fn, function_owner = self, label = label,
      position = { x, 0.2, z }, width = w or BTN_W, height = BTN_H,
      font_size = BTN_FONT, color = col or { 0.16, 0.15, 0.13 },
      font_color = { 1, 1, 1 } })
  end
end

function mkLbl(tile)
  return function(text, x, z, w)
    tile.createButton({ click_function = 'nop', function_owner = self, label = text,
      position = { x, 0.2, z }, width = w or BTN_W, height = BTN_H,
      font_size = LBL_FONT, color = { 0.93, 0.91, 0.85 },
      font_color = { 0.13, 0.11, 0.09 } })
  end
end

--- The nameplate. Always at the top of the table, all game.
function refreshNameplate()
  if not PANEL then return end
  PANEL.clearButtons()
  local btn, lbl = mkBtn(PANEL), mkLbl(PANEL)
  local A, B = NAME_ROW_A, NAME_ROW_B

  btn('Select a New Game', 'btnNewGame', -0.30, A, 190, { 0.42, 0.18, 0.15 })
  if STATE.phase ~= 'playing' then return end

  --- label, then minus and plus to its right
  local function counter(text, minusFn, plusFn, x, z, w)
    lbl(text, x, z, w or 150)
    btn('-', minusFn, x + 0.25, z, 80)
    btn('+', plusFn, x + 0.43, z, 80)
  end

  local g = STATE.game
  if g == 'BAT' then
    lbl('Splices ' .. STATE.splices .. ' / 5', 0.02, A, 90)
    btn('-', 'splMinus', 0.20, A, 80)
    btn('+', 'splPlus', 0.38, A, 80)
    local buff = STATE.tyrant - BAT_BASE_HP
    counter('Tyrant ' .. STATE.tyrant .. (buff > 0 and ('  +' .. buff) or ''),
            'hpMinus', 'hpPlus', -0.34, B)
    if STATE.splices >= 5 then lbl('AWAKE', 0.36, B, 120) end
  elseif g == 'NAP' then
    lbl('NAP', 0.22, A, 200)
    counter('Credits ' .. STATE.credits .. ' / 6', 'crMinus', 'crPlus', -0.34, B)
    if STATE.credits >= 6 then lbl('FINAL EXAM', 0.36, B, 120) end
  elseif g == 'AoS' then
    lbl('AoS  ' .. STATE.difficulty, 0.22, A, 200)
    counter('Backdoors ' .. STATE.backdoors .. ' / 2', 'bdMinus', 'bdPlus', -0.34, B)
  else
    -- Imposter tracks two counters, so one goes up on the top row.
    lbl('Att ' .. STATE.attempts .. ' / 9', 0.02, A, 90)
    btn('-', 'atMinus', 0.20, A, 80)
    btn('+', 'atPlus', 0.38, A, 80)
    counter('Susp ' .. STATE.suspicion, 'suMinus', 'suPlus', -0.34, B)
  end
end

--- The setup wizard, in the middle of the table. Hidden during play.
function refreshSetup()
  if not SETUP then return end
  SETUP.clearButtons()
  if STATE.phase == 'playing' then return end

  local btn, lbl = mkBtn(SETUP), mkLbl(SETUP)
  local ON, OFF = { 0.17, 0.37, 0.29 }, { 0.24, 0.23, 0.21 }

  -- The plate art already reads SET UP A GAME, so no heading is needed here.
  local function gameBtn(code, label, x)
    btn((STATE.game == code and '> ' or '') .. label, 'pick' .. code, x, ROW_1,
        BTN_W, STATE.game == code and ON or OFF)
  end
  gameBtn('BAT', 'BAT', -0.36)
  gameBtn('NAP', 'NAP', -0.12)
  gameBtn('AoS', 'AoS', 0.12)
  gameBtn('IMP', 'IMP', 0.36)

  -- Difficulty on the left, what it means on the right. It drives nothing in
  -- NAP or Imposter, so it is left off entirely there.
  if STATE.game == 'BAT' or STATE.game == 'AoS' then
    btn(STATE.difficulty, 'btnDiff', -0.20, ROW_2, 170)
    local note = (STATE.game == 'AoS') and AOS_PROGRAM[STATE.difficulty]
                 or ('+' .. BAT_BUFF[STATE.difficulty] .. ' Buff  ' ..
                     BAT_SPECIMENS[STATE.difficulty] .. ' Spec')
    lbl(note, 0.22, ROW_2, 210)
  elseif STATE.game then
    lbl('no difficulty setting', 0, ROW_2, 260)
  end

  btn((tierOn(1) and '* ' or '') .. 'NRJ I', 'tier1', -0.30, ROW_3, 140,
      tierOn(1) and ON or OFF)
  btn((tierOn(2) and '* ' or '') .. 'NRJ II', 'tier2', 0, ROW_3, 140,
      tierOn(2) and ON or OFF)
  btn((tierOn(3) and '* ' or '') .. 'NRJ III', 'tier3', 0.30, ROW_3, 140,
      tierOn(3) and ON or OFF)

  btn(STATE.game and ('START ' .. STATE.game) or 'choose a game', 'btnStart',
      0, ROW_4, 260,
      STATE.game and { 0.17, 0.37, 0.29 } or { 0.3, 0.28, 0.25 })
end

function refreshPanel()
  refreshNameplate()
  refreshSetup()
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
function btnNewGame() packUp() end
function btnPack() packUp() end
function btnReset() resetCounters() end
function splPlus() bump('splices', 1, 'Splices') end
function splMinus() bump('splices', -1, 'Splices') end
function crPlus() bump('credits', 1, 'Credits') end
function crMinus() bump('credits', -1, 'Credits') end
function bdPlus() bump('backdoors', 1, 'Backdoor Routines') end
function bdMinus() bump('backdoors', -1, 'Backdoor Routines') end
function hpPlus() bump('tyrant', 1, 'Tyrant Health') end
function hpMinus() bump('tyrant', -1, 'Tyrant Health') end
function atPlus() bump('attempts', 1, 'Attempts') end
function atMinus() bump('attempts', -1, 'Attempts') end
function suPlus() bump('suspicion', 1, 'Suspicion') end
function suMinus() bump('suspicion', -1, 'Suspicion') end

-- ---------------------------------------------------------------- lifecycle
function locate()
  for _, o in ipairs(getAllObjects()) do
    local n = o.getName()
    if n == 'Control Panel' then PANEL = o end
    if n == 'Setup Panel' then SETUP = o end
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
    showSetup(STATE.phase ~= 'playing')
    refreshPanel()
  end, 30)
end

function onSave()
  return JSON.encode({ state = STATE })
end
