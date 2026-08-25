-- Minimal stand-in for the TTS object API: enough surface to drive a whole
-- setup end to end and see what errors. Waits fire immediately.
ERRORS, LOG, OBJECTS = {}, {}, {}

function mkObj(nick, qty, kind)
  local o = { nick = nick, qty = qty or 1, locked = false, pos = { 0, 0, 0 } }
  o.type = kind or 'Deck'
  if o.qty == 1 and o.type == 'Deck' then o.type = 'Card' end
  o.getName = function() return o.nick end
  o.getQuantity = function() return o.qty end
  o.getPosition = function() return Vector(o.pos[1] or 0, o.pos[2] or 0, o.pos[3] or 0) end
  o.setLock = function(v) o.locked = v end
  o.setPosition = function(p) o.pos = p end
  o.setPositionSmooth = function(p) o.pos = p end
  o.setRotationSmooth = function() end
  o.shuffle = function()
    if o.type ~= 'Deck' then
      table.insert(ERRORS, 'shuffle() on a ' .. o.type .. ': ' .. o.nick)
    end
  end
  o.putObject = function(x)
    if not x then table.insert(ERRORS, 'putObject(nil) into ' .. o.nick) return end
    o.qty = o.qty + (x.qty or 1)
    for i, y in ipairs(OBJECTS) do if y == x then table.remove(OBJECTS, i) break end end
    return o
  end
  o.takeObject = function(p)
    if o.type ~= 'Deck' then
      table.insert(ERRORS, 'takeObject() on a ' .. o.type .. ': ' .. o.nick)
      return nil
    end
    o.qty = o.qty - 1
    if o.qty <= 1 then o.type = 'Card' end      -- TTS collapses a 1-card deck
    local c = mkObj(o.nick .. ' [card]', 1, 'Card')
    if p and p.position then c.pos = p.position end
    table.insert(OBJECTS, c)
    if p and p.callback_function then p.callback_function(c) end
    return c
  end
  o.UI = { setXml = function() end }
  return o
end

function mkPanel(nick)
  local o = mkObj(nick, 1, 'Tile')
  return o
end

BANKOBJ = mkObj('Card Bank', 1, 'Bag')
BANKOBJ.type = 'Bag'
BANKOBJ.contents = {}
BANKOBJ.getObjects = function()
  local t = {}
  for i, o in ipairs(BANKOBJ.contents) do
    table.insert(t, { guid = 'g' .. i, nickname = o.nick, index = i - 1 })
  end
  return t
end
BANKOBJ.takeObject = function(p)
  local idx = tonumber(string.sub(p.guid, 2))
  local o = table.remove(BANKOBJ.contents, idx)
  if not o then
    table.insert(ERRORS, 'bank had nothing for ' .. tostring(p.guid))
    if p.callback_function then p.callback_function(nil) end
    return nil
  end
  if p.position then o.pos = p.position end
  table.insert(OBJECTS, o)
  if p.callback_function then p.callback_function(o) end
  return o
end
BANKOBJ.putObject = function(o)
  if not o then table.insert(ERRORS, 'banked a nil object') return end
  table.insert(BANKOBJ.contents, o)
  for i, x in ipairs(OBJECTS) do if x == o then table.remove(OBJECTS, i) break end end
  return o
end

function getAllObjects()
  local t = { PANEL, SETUP, BANKOBJ }
  for _, o in ipairs(OBJECTS) do table.insert(t, o) end
  return t
end

function broadcastToAll(m) table.insert(LOG, m) end
Wait = { frames = function(f) if f then f() end end,
         time = function(f) if f then f() end end }
JSON = { decode = function() return nil end, encode = function() return '' end }
Global = { call = function() end }
self = nil

local VecMT = {}
VecMT.__add = function(a, b) return Vector(a.x + b.x, a.y + b.y, a.z + b.z) end
function Vector(x, y, z) return setmetatable({ x = x, y = y, z = z }, VecMT) end
