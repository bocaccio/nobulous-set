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

BANK, PANEL, SETUP, TRACKER, BUSY = nil, nil, nil, nil, false

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
BAT_BUFF = { Easy = 0, Standard = 2, Hard = 4, Brutal = 6 }
BAT_SPECIMENS = { Easy = 2, Standard = 3, Hard = 4, Brutal = 4 }
BAT_WINRATE = { Easy = '~84%', Standard = '~78%', Hard = '~70%', Brutal = '~60%' }

-- The two games mean different things by difficulty, and no longer offer the
-- same choices: BAT gained Brutal with the Buff HP rules, while AoS has only
-- the three Program decks.
DIFFICULTIES = {
  BAT = { 'Easy', 'Standard', 'Hard', 'Brutal' },
  AoS = { 'Easy', 'Standard', 'Hard' },
}

function difficulties()
  return DIFFICULTIES[STATE.game] or DIFFICULTIES.BAT
end

--- Keep the setting inside the chosen game's range, so switching from BAT on
-- Brutal to AoS cannot ask for a Program deck that does not exist.
function clampDifficulty()
  local ok = difficulties()
  for _, v in ipairs(ok) do if v == STATE.difficulty then return end end
  STATE.difficulty = ok[#ok]
end

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
  if not (src and target) then if done then done() end return end
  -- Taking every card would leave the deck as a single Card, which cannot be
  -- taken from. Tier I does exactly this: all 4 Following Setbacks.
  local have = src.getQuantity and src.getQuantity() or -1
  if have >= 0 and n >= have then
    target.putObject(src)
    Wait.frames(function() if done then done() end end, 10)
    return
  end
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

--- Deal a deck out card by card to the given spots.
--
-- The deck arrives already sitting on spots[1], so this only takes cards to
-- the other spots and lets the last one stay where the deck was. TTS destroys
-- a deck the moment it drops to a single card, which makes the reference dead:
-- an earlier version took three cards and then tried to move the deck to the
-- fourth spot, so that card never moved and sat under spot one -- four Lab
-- Rats, three visible.
function dealOut(deck, spots, done)
  if not deck or #spots == 0 then if done then done() end return end
  local i = 1
  local function one()
    i = i + 1
    if i > #spots then
      if done then done() end
      return
    end
    deck.takeObject({ position = spots[i], rotation = FACE_UP, smooth = false })
    Wait.frames(one, 8)
  end
  one()
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
    if (t == 'Deck' or t == 'Card' or t == 'Tile')
       and o ~= PANEL and o ~= SETUP and o ~= TRACKER and o ~= BANK then
      -- Tiles that are not the two panels are the AoS covers. Missing SETUP
      -- here put the setup panel itself into the bank on Start Game, which
      -- took the UI with it.
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
    function(next)
      draw('Lab Rats (A / B)', spot('Lab Rats (A / B) 1'), FACE_UP, function(deck)
        local spots = {}
        for i = 1, 4 do spots[i] = spot('Lab Rats (A / B) ' .. i) end
        dealOut(deck, spots, next)
      end)
    end,
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
        local spots = {}
        for i = 1, 4 do
          spots[i] = spot('Time Slots + FINF ' .. i, { -4.4, DECK_Y, 1.4 })
        end
        dealOut(deck, spots, next)
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
        local spots = {}
        for i = 1, 5 do spots[i] = spot('Element Mats ' .. i) end
        dealOut(deck, spots, next)
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

--=====================================================================
-- The panels are XML UI, not createButton. A classic button draws its
-- label into a texture which the tile's scale then magnifies, so the text
-- goes soft as you zoom in, and a long label is shrunk to fit rather than
-- given room. XML renders real text and lays out by width, which is what
-- these panels need now the games are spelled out in full.
--
-- If a panel floats at the wrong height or reads mirrored, UI_LIFT and
-- UI_SPIN are the two numbers to adjust.
--=====================================================================
UI_LIFT = 12          -- how far the panel sits above the tile face
-- How far down the nameplate the Select a New Game button sits. Positive is
-- down; -200 put it off the top of the table and 200 was too low. To retune
-- without a rebuild: Scripting window, edit this line, Save & Play.
NAME_UI_DROP = 110
SETUP_UI_SCALE = 0.34 -- the setup tile is full size again
UI_SPIN = '0 0 180'   -- rights the text against the tile's own rotation

GAME_NAMES = {
  BAT = 'Build-A-Tyrant',
  NAP = 'Nobulous Apprenticeship Program',
  AoS = 'Automaton of Shale',
  IMP = 'Imposter Scenario',
}
GAME_ORDER = { 'BAT', 'NAP', 'AoS', 'IMP' }

C_PICKED  = '#2f6b52'
C_IDLE    = '#2b2724'
C_TIER_ON = '#6f5bbd'      -- the tiers get their own colour, on and off
C_TIER    = '#3b3560'
C_OFF     = '#3a3530'
C_TEXT    = '#f2ede2'
C_GOLD    = '#d4a72c'

function esc(t)
  t = string.gsub(t, '&', '&amp;')
  t = string.gsub(t, '<', '&lt;')
  return (string.gsub(t, '>', '&gt;'))
end

function attrs(t)
  local out = {}
  for k, v in pairs(t) do table.insert(out, k .. '="' .. tostring(v) .. '"') end
  table.sort(out)
  return table.concat(out, ' ')
end

function tag(name, a, inner)
  if inner == nil then return '<' .. name .. ' ' .. attrs(a) .. '/>' end
  return '<' .. name .. ' ' .. attrs(a) .. '>' .. inner .. '</' .. name .. '>'
end

function xbtn(id, text, colour, extra)
  local a = { id = id, onClick = 'uiButton', color = colour,
              textColor = C_TEXT, fontSize = 34 }
  for k, v in pairs(extra or {}) do a[k] = v end
  return tag('Button', a, esc(text))
end

function xtext(text, size, colour, extra)
  local a = { fontSize = size or 30, color = colour or C_TEXT,
              alignment = 'MiddleLeft' }
  for k, v in pairs(extra or {}) do a[k] = v end
  return tag('Text', a, esc(text))
end

--- Wrap a panel's contents.
--
-- uiScale is the UI's own scale, which multiplies the tile's. The setup
-- anchor is a speck rather than a tile -- a transparent image on a tile still
-- renders as a black slab -- so its UI scales up by the same factor the tile
-- scales down, and comes out the same size with nothing behind it.
--
-- drop shifts the contents down the tile, for art whose usable area is not
-- centred. Positive y is down here: negating it sent the button up off the
-- table.
function panelWrap(inner, w, h, uiScale, drop)
  uiScale = uiScale or 0.34
  local y = (drop or 0)
  return tag('Panel', { position = '0 ' .. y .. ' -' .. UI_LIFT,
                        rotation = UI_SPIN, width = w, height = h,
                        scale = uiScale .. ' ' .. uiScale .. ' ' .. uiScale,
                        color = '#00000000' }, inner)
end

--- The setup wizard: a column of games, each with its options beside it.
function refreshSetup()
  if not SETUP then return end
  if STATE.phase == 'playing' then SETUP.UI.setXml('') return end

  local rows = {}
  table.insert(rows, tag('Text', { fontSize = 46, color = C_GOLD,
      alignment = 'MiddleCenter', preferredHeight = 78 }, 'SET UP A GAME'))

  for _, code in ipairs(GAME_ORDER) do
    local picked = (STATE.game == code)
    local left = xbtn('pick' .. code, GAME_NAMES[code],
                      picked and C_PICKED or C_IDLE, { flexibleWidth = 58 })

    -- The chosen game's options sit to the right of its own button.
    local right
    if not picked then
      right = tag('Panel', { flexibleWidth = 42, color = '#00000000' }, '')
    elseif code == 'BAT' or code == 'AoS' then
      local note = (code == 'AoS') and AOS_PROGRAM[STATE.difficulty]
                   or ('20 +' .. BAT_BUFF[STATE.difficulty] .. ' Buff, ' ..
                       BAT_SPECIMENS[STATE.difficulty] .. ' Specimens, ' ..
                       BAT_WINRATE[STATE.difficulty])
      right = tag('HorizontalLayout', { flexibleWidth = 42, spacing = 8 },
                  xbtn('btnDiff', STATE.difficulty, C_OFF,
                       { preferredWidth = 160 }) ..
                  xtext(note, 26, C_TEXT, { flexibleWidth = 1 }))
    else
      right = tag('Panel', { flexibleWidth = 42, color = '#00000000' },
                  xtext('no difficulty setting', 26, '#9a9288'))
    end
    table.insert(rows, tag('HorizontalLayout',
        { preferredHeight = 86, spacing = 14 }, left .. right))
  end

  local tiers = {}
  for n = 1, 3 do
    table.insert(tiers, xbtn('tier' .. n,
        (tierOn(n) and '* ' or '') .. 'NRJ ' .. TIER_NAMES[n],
        tierOn(n) and C_TIER_ON or C_TIER, { flexibleWidth = 1 }))
  end
  table.insert(rows, tag('HorizontalLayout',
      { preferredHeight = 78, spacing = 14 }, table.concat(tiers)))

  table.insert(rows, xbtn('btnStart',
      STATE.game and ('START ' .. GAME_NAMES[STATE.game]) or 'Choose a game above',
      STATE.game and C_PICKED or C_OFF,
      { preferredHeight = 92, fontSize = 40 }))

  SETUP.UI.setXml(panelWrap(tag('VerticalLayout',
      { padding = '34 34 28 28', spacing = 14 }, table.concat(rows)),
      1080, 1080, SETUP_UI_SCALE))
end

--- The nameplate. Title and Select a New Game, nothing else -- the counters
-- live on the tracker now.
function refreshNameplate()
  if not PANEL then return end
  -- Spacers either side keep the button at its own size and centred, rather
  -- than stretching to fill the row.
  local spacer = tag('Panel', { flexibleWidth = 1, color = '#00000000' }, '')
  PANEL.UI.setXml(panelWrap(tag('HorizontalLayout',
      { padding = '30 30 18 24' },
      spacer ..
      xbtn('btnNewGame', 'Select a New Game', '#7a3028',
           { preferredWidth = 120, preferredHeight = 38, fontSize = 15 }) ..
      spacer), 1180, 320, 0.34, NAME_UI_DROP))
end

-- Two slots, labelled for whichever game is running. Games that track only one
-- thing leave the second slot empty.
TRACK_SLOTS = {
  BAT = { { 'Splices', 'splices', 'spl', '/ 5' },
          { 'Tyrant HP', 'tyrant', 'hp', '' } },
  NAP = { { 'Credits', 'credits', 'cr', '/ 6' } },
  AoS = { { 'Backdoors', 'backdoors', 'bd', '/ 2' } },
  IMP = { { 'Attempts', 'attempts', 'at', '/ 9' },
          { 'Suspicion', 'suspicion', 'su', '' } },
}

--- The play tracker: one slot per counter, sitting over the painted frame.
function refreshTracker()
  if not TRACKER then return end
  local slots = STATE.phase == 'playing' and TRACK_SLOTS[STATE.game] or nil
  if not slots then
    TRACKER.UI.setXml('')
    return
  end

  local cells = {}
  for i = 1, 2 do
    local s = slots[i]
    local inner
    if s then
      local suffix = s[4] ~= '' and (' ' .. s[4]) or ''
      inner = tag('VerticalLayout', { spacing = 2 },
          xtext(s[1], 30, '#b8b2a6', { alignment = 'MiddleCenter',
                                       preferredHeight = 34 }) ..
          tag('HorizontalLayout', { spacing = 8, preferredHeight = 62 },
              xbtn(s[3] .. 'Minus', '-', '#3a3530', { preferredWidth = 62 }) ..
              xtext(STATE[s[2]] .. suffix, 46, C_TEXT,
                    { alignment = 'MiddleCenter', flexibleWidth = 1 }) ..
              xbtn(s[3] .. 'Plus', '+', '#3a3530', { preferredWidth = 62 })))
    else
      inner = ''
    end
    table.insert(cells, tag('Panel',
        { flexibleWidth = 1, color = '#00000000' }, inner))
  end

  TRACKER.UI.setXml(panelWrap(tag('HorizontalLayout',
      { padding = '34 34 26 26', spacing = 26 }, table.concat(cells)),
      1536, 512))
end

function refreshPanel()
  refreshNameplate()
  refreshSetup()
  refreshTracker()
end

--- Every XML button routes here through the panel's forwarding stub.
function uiClick(params)
  local id = params and params.id
  if not id then return end
  if id == 'btnStart' then startGame() return end
  if id == 'btnNewGame' then packUp() return end
  if id == 'btnDiff' then btnDiff() return end
  for _, code in ipairs(GAME_ORDER) do
    if id == 'pick' .. code then
      STATE.game = code
      clampDifficulty()
      refreshPanel()
      return
    end
  end
  for n = 1, 3 do
    if id == 'tier' .. n then setTier(n) return end
  end
  local counters = {
    splMinus = { 'splices', -1, 'Splices' }, splPlus = { 'splices', 1, 'Splices' },
    crMinus = { 'credits', -1, 'Credits' }, crPlus = { 'credits', 1, 'Credits' },
    bdMinus = { 'backdoors', -1, 'Backdoor Routines' },
    bdPlus = { 'backdoors', 1, 'Backdoor Routines' },
    atMinus = { 'attempts', -1, 'Attempts' }, atPlus = { 'attempts', 1, 'Attempts' },
    suMinus = { 'suspicion', -1, 'Suspicion' }, suPlus = { 'suspicion', 1, 'Suspicion' },
    hpMinus = { 'tyrant', -1, 'Tyrant Health' },
    hpPlus = { 'tyrant', 1, 'Tyrant Health' },
  }
  local c = counters[id]
  if c then bump(c[1], c[2], c[3]) end
end

-- ---------------------------------------------------------------- clicks

function btnDiff()
  local order = difficulties()
  local i = 1
  for k, v in ipairs(order) do if v == STATE.difficulty then i = k end end
  STATE.difficulty = order[(i % #order) + 1]
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

function btnPack() packUp() end

-- ---------------------------------------------------------------- lifecycle
function locate()
  for _, o in ipairs(getAllObjects()) do
    local n = o.getName()
    if n == 'Control Panel' then PANEL = o end
    if n == 'Setup Panel' then SETUP = o end
    if n == 'Tracker' then TRACKER = o end
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
