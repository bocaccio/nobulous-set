--=====================================================================
-- THE NOBULOUS SET  --  Tabletop Simulator control script
--
-- Setup only. It deals the cards and holds the counters; it never
-- enforces a rule in play, so you can always do whatever you like.
--
-- FOUR BAGS HOLD EVERY CARD, one per game, along the back rail. A setup
-- button takes out what that game needs, performs the printed setup --
-- the random mixes AND the tier swaps -- and leaves everything else in
-- the bag. Nothing is parked on the table "ready to be sorted by hand".
--
-- BOX, HOME, NAP_CREDIT and EXHIBIT_BLOCK are GENERATED above this line
-- by build_mod.py and are not in this file: the box GUIDs come from the
-- save it is building, and the two card-index tables are read out of
-- generator/build_nap.py and generator/build_nrj.py so that a reordered
-- card table cannot leave a stale index behind here.
--=====================================================================

STATE = { game = nil, difficulty = 'Standard', tier = 0,
          splices = 0, credits = 0, session = 0, backdoors = 0,
          -- Which number was last typed over the Chip, so the trim
          -- control can re-turn it to the colour you are judging.
          chip = 1,
          -- Which rulebook the corner is showing, so a setup does not
          -- respawn the object to load what is already in it.
          rules = 'BAT',
          -- WHICH CHARACTER EACH GAME IS SHOWING. One entry per game
          -- that has a choice, because the choice outlives the setup:
          -- press Set up AoS after picking the Compiler and you want
          -- the Compiler, not whoever is first in the list.
          pick = { NAP = 1, AoS = 1, IMP = 1 },
          -- WHETHER THE LAST PART HAS BEEN STARTED. The finale button
          -- deals cards and shuffles decks, so it is a thing you do
          -- once; this is what takes it off the panel afterwards.
          finale = false,
          -- 4 is Reduce 1, which rules/nap.html calls Standard.
          finf = 4,
          -- What the dial face was last set to, the way chip is what
          -- the colour face was last set to.
          dial = 0 }

-- THE PRINTED NUMBERS, in one place. This script enforces nothing; it only
-- SAYS them, which is exactly how they drifted - every one below used to be
-- a hand copy inside the function that announced it. generator/
-- check_app_sync.py now holds these four tables against bat.DIFFICULTY,
-- nap.LEVELS, aos.LEVELS and the finale table in rules/nrj.html.
LEVELS = { 'Easy', 'Standard', 'Hard', 'Nobulous' }
-- BAT: Specimens shuffled into the Upgrade deck, and the Tyrant's Health.
-- Specimens, the Tyrant's CORE Health, its OUTER LAYER. The layer is 0
-- at every rung: the Tyrant is Splices and a core, and a layer is a
-- fine-tuning dial the player raises. One point of it costs the Rats
-- 4 to 8 points of win rate - simulation/price_buff.py - so it is not
-- a number to set lightly.
BAT_DIFF = { Easy = {5, 9, 0}, Standard = {6, 10, 0}, Hard = {7, 12, 0}, Nobulous = {8, 14, 0} }
-- NAP: the Credit goal, and how many Setbacks are in the Assignment deck.
-- (Credit goal, Setbacks shuffled in).  Standard carries 2 as of
-- 2026-11-12 and the column is deliberately not monotone - it is fewer than
-- Easy's 3, and Standard is held to the band by its Credit goal instead.
NAP_DIFF = { Easy = {5, 3}, Standard = {6, 2}, Hard = {7, 4}, Nobulous = {8, 5} }
-- NAP's second dial, from rules/nap.html: Increase 1-3 shuffles that
-- many of the 3 FINF cards INTO the Assignment deck, Reduce 1-3 lays
-- them out face-up to spend. Standard is Reduce 1. The two directions
-- are not symmetrical and the setup does genuinely different things
-- with them, so the direction is stored rather than a signed number.
FINF_SET = { {'Increase', 1}, {'Increase', 2}, {'Increase', 3},
             {'Reduce', 1}, {'Reduce', 2}, {'Reduce', 3} }
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

-- TYPING A NUMBER OVER THE CHIP turns it to that colour, the way a
-- number turns a die. 1 to 5 are the colours in the order above.
--
-- THE FIVE ANGLES ARE THE ONLY THING TO ADJUST if a number lands on the
-- wrong colour: where the art's zero sits is not something a script can
-- know, and five segments are 72 degrees apart.
--
-- CHIP_FACE and CHIP_FACE_Z are both GENERATED from build_mod.py,
-- because the dial's rotation values in the save and the angles this
-- script turns it to have to be the same numbers. They were not,
-- twice: first the values went round in steps of 72 from zero while
-- the script had its own table, then the face was written down here as
-- 180 - the token's MIRRORED underside, which shows a dial running the
-- wrong way round and reads as a trim that has drifted.

-- The dial's other face is REAL now, and generated: CHIP_DIAL holds
-- the angle that brings each of its 0-20 numbers to the player's
-- edge, measured off the scan, and CHIP_DIAL_Z is which way up it
-- is. What used to stand here was CHIP_NUM - five angles for a
-- 'number side' that did not exist, because a Custom_Token carries
-- one image and shows it mirrored underneath.

PANEL = nil
chr39 = string.char(39)
FACEUP = {0, 180, 0}
FACEDOWN = {0, 180, 180}
-- WHERE EVERYTHING GOES. FELT, ROW_CHAR, ROW_MAIN, ROW_SIDE, ROW_TIER
-- and ROW_PITCH are all GENERATED by build_mod.py from the felt Jon
-- measured with the Mat controls and the one card scale there.
--
-- They were four literals here - 14.8, 5.7, -3.1, -11.9 - that fitted
-- a table 1.5 units deeper than the real one, which is how the bottom
-- row of dice came to hang over the back edge. A row is the thing to
-- move by changing the card scale or the felt, not by editing four
-- numbers in a comment that says they are multiples of a card.
--
--   ROW_CHAR  characters, flush with the back edge (landscape there)
--   ROW_MAIN  the decks you draw from
--   ROW_SIDE  mats, slots and the Research Pool
--   ROW_TIER  what a tier adds; the dice take everything below it

-- A single card a tier deals sits out at the right, on the SIDE row
-- rather than the tier row: the tier row is the lowest cards on the
-- table, and keeping it clear at the right-hand end is what gives the
-- exhausted dice the whole bottom band.
TIER_X = 24.0

-- THE LEFT-HAND CARD COLUMN, one number for all four games. A
-- landscape card against the left edge with a 0.3 margin: BAT's Lab
-- Rats, AoS's Technician, NAP's Apprentice and the Imposter all stand
-- here, so the four tables open the same way and a change of card
-- scale moves all four together.
CHAR_X = FELT.x0 + 0.30 + CARD_L / 2

-- Staging points for a card or deck on its way home or into a merge. They
-- sit OVER the table, not past its edge: a deck that waits a step beyond
-- the rim is a deck falling on the floor. They are spread out so decks
-- merged in the same step do not land on each other.
-- THE STAGING BAND. A deck being built is held in the air here while
-- cards are moved between decks, and it used to be held over ROW_TIER
-- - which is where AoS spreads the Research Notes and the Imposter
-- scenario the Backdoor Routines. A card that never makes it into a
-- bag falls out of the air onto whatever is below, and Jon found an
-- Apprentice in the middle of the table that way.
--
-- A MARGIN, NOT A MECHANISM. putHome keeps trying until the bag takes
-- the card, which is what actually stops this; the band is below every
-- row so that the rare card which defeats even that lands on bare felt
-- instead of in the middle of a row, where it reads as a card the
-- setup dealt. check_app_sync.py holds it below the lowest row.
-- SIX SLOTS, AND OFF IS ONE OF THEM.
--
-- OFF WAS pad(3) - the same three numbers - and every takeObject in
-- this script drops its card at OFF on the way to wherever it is
-- going. So a deck parked on pad(3) spent the step with cards landing
-- on top of it, and AoS parked the Specialized Programs there: Jon's
-- table came out with a correct 8-card Program deck AND five of its
-- own cards lying in the staging band, one copy in the deck and one
-- on the felt. Nothing about the deck was wrong, which is why nothing
-- that reads a deck could see it.
--
-- Derived rather than typed, so the two cannot be made to coincide
-- again: OFF takes the leftmost slot and pad() hands out the rest.
--
-- FIVE SLOTS, NOT SIX. pad() is called with four distinct numbers and
-- never has been with more, so the band is as wide as it always was
-- and OFF simply has one of the slots. Six would have pushed its
-- right-hand end out under BAT's Dial and the Health readout beside
-- it, which stand in this same strip because it is the only clear one
-- left under four rows of cards.
BAND_PITCH = CARD_W + 1.0
BAND_PADS = 4
function pad(i) return {(i - BAND_PADS / 2) * BAND_PITCH, 14, OFF_Z} end

OFF_Z = FELT.z0 + 2.0
OFF = {-(BAND_PADS / 2) * BAND_PITCH, 14, OFF_Z}
-- AND IT IS ONLY AS WIDE AS THE SPOTS THEMSELVES. OFF and pad() share
-- one row of six; past that the band is ordinary felt, which is where
-- BAT stands its Dial. Reading the band as the whole row called that
-- Dial a stranded card.
OFF_X = (BAND_PADS / 2) * BAND_PITCH + CARD_W / 2

-- ------------------------------------------------------------ the BAT table
-- JON LAID THIS OUT BY HAND AND ASKED FOR IT SQUARED UP, so the shape
-- is his and only the arithmetic is mine. Four Lab Rats down the left,
-- each with three Upgrade spaces beside it; on the right a column of
-- five: the two decks, the revealed Experiment and two Upgrades, the
-- Tyrant's row, and the five Splices along the bottom.
--
-- ONE GRID, FOUR ROWS. The Rats set the rows - an Upgrade space has
-- its TOP level with its Rat's top, which is what BAT_BOX_DROP is: a
-- landscape card is CARD_W deep and a portrait one CARD_L, so the
-- portrait space hangs (CARD_L - CARD_W) / 2 lower to share a top
-- edge. Derived rather than typed, so it stays true at any card scale.
--
-- THE WIDTH IS THE BINDING CONSTRAINT. A Rat and eight portrait
-- columns is 8.21 + 8 x 5.86 = 55.1 of the felt's 56.5, which leaves
-- no room for generosity anywhere: the column pitch is a shade UNDER a
-- card, so a card overhangs its space by a tenth the way NAP's do.
-- Four rows at 7.82 is the same bargain against the depth, and what
-- the bottom row has to clear is the dice strip at ROW_TIER.
BAT_COL = CARD_W - 0.02
BAT_ROW_PITCH = 7.82
BAT_RAT_X = CHAR_X
BAT_RAT_Z1 = 14.80
BAT_LEFT1 = -16.45
BAT_RIGHT1 = 1.75
BAT_ROWS = 4
BAT_UPGRADES = 3
BAT_SPLICES = 5
BAT_BOX_DROP = (CARD_W - CARD_L) / 2

-- A drawn space is the pitch less a hair, not a card: see above.
BAT_BOX_HW = (BAT_COL - 0.25) / 2
BAT_BOX_HD = (BAT_ROW_PITCH - 0.25) / 2
-- ...and a two-column space is two pitches less the same hair.
BAT_WIDE_HW = (2 * BAT_COL - 0.25) / 2

function batRatZ(i) return BAT_RAT_Z1 - (i - 1) * BAT_ROW_PITCH end
function batRowZ(i) return batRatZ(i) + BAT_BOX_DROP end
function batLeftX(k) return BAT_LEFT1 + (k - 1) * BAT_COL end
function batRightX(k) return BAT_RIGHT1 + (k - 1) * BAT_COL end

-- WHICH COLUMN IS WHICH on the right. Row 1 is the two decks, row 2
-- what they reveal and what you did not take, row 3 the Tyrant's,
-- row 4 the Splices.
BAT_EXPERIMENTS, BAT_UPGRADE_DECK = 1, 2
-- ...AND WHAT THE NRJ TIERS PUT OUT, in the two columns row 1 has
-- left. Both are cards you keep in front of you for the whole game
-- rather than cards that pass through a turn, so they belong beside
-- the decks and not in the rows that cycle.
--
-- THE SIX RESEARCH NOTES ARE ONE FACE-UP STACK. rules/nrj.html lays
-- them "face-up beside the table" and a row of six is 35 units wide;
-- this table has four rows of cards on it and no 35 units anywhere.
-- Spread the stack when you want to read them, the way the
-- Apprentices and the Technicians are a stack you choose out of.
BAT_PROTOCOL, BAT_NOTES = 3, 4
BAT_REVEALED = 1                       -- revealed Experiment, then 2 Upgrades
-- TWO DISCARDS, past the three revealed cards in the same row. An
-- Experiment is finished with when it is done and two Upgrades are
-- revealed for every one taken, so both piles fill every turn and
-- neither had anywhere to be.
BAT_EXP_DISCARD, BAT_UPG_DISCARD = 4, 5
-- THE DECK FIRST, THEN WHAT IT REVEALS. It was the other way round
-- and read backwards against row 2, where the Experiment and Upgrade
-- decks sit left of the cards they turn over. Jon's call: a row
-- should run in the direction you deal it.
BAT_ATTACK_DECK, BAT_ATTACK_UP, BAT_BUFF = 1, 2, 3
-- THE TYRANT'S OWN DICE, over the two Splices at the right-hand end:
-- one space two columns wide, because a handful of dice is not a card
-- and reads better in a wide tray than in a card-shaped box.
BAT_TYRANT_DICE = 4                    -- the first of the two columns

-- The Dial sits below the rightmost Splice, clear of the row above it.
BAT_CHIP_X = BAT_RIGHT1 + (BAT_SPLICES - 1) * BAT_COL
BAT_CHIP_Z = -16.0

-- THE HEALTH READOUT, beside the Dial and left of it. The Dial is a
-- disc with twenty-one numbers printed round its rim, which is exact
-- and unreadable across a table; this is the same number in one large
-- figure with a button either side of it. The two cannot disagree -
-- the buttons turn the Dial and write the figure in the same call.
-- CENTRED UNDER THE FOURTH SPLICE, which is Jon's placing and puts
-- it in the Tyrant's own column of the table rather than wherever
-- the arithmetic left room. BAT_READOUT_HW is generated by
-- build_mod.py, which builds the plate; what has to hold is that the
-- plate clears the staging band on its left and the Dial on its
-- right, and check_app_sync.py measures both.
BAT_READOUT_SPLICE = 4
BAT_READOUT_X = batRightX(BAT_READOUT_SPLICE)
BAT_READOUT_Z = BAT_CHIP_Z

-- WHERE THE EXHAUSTED CORNER STOPS AT EITHER END. Its left edge lines
-- up with the second Splice - Jon's own call, and it leaves the first
-- Splice's width of felt clear beside the Rats - and its right edge
-- stops short of the readout, which stands between it and the Dial.
BAT_EXHAUST_X0 = BAT_RIGHT1 + BAT_COL - BAT_BOX_HW
BAT_EXHAUST_X1 = BAT_READOUT_X - BAT_READOUT_HW - 0.6

-- THE BUFF HP TRACK'S FIFTEEN SPACES. The card is a 5x3 grid of
-- 11mm squares 0.6mm apart, numbered 15 down to 1 left to right and
-- top to bottom (generator/build_bat.py), and the battle stands the
-- Health die on this difficulty's number.
--
-- The PITCH is those two numbers: 11.6mm of a 63.5mm card is 0.1827
-- of its width. The OFFSET is measured, because where the grid
-- starts depends on how deep the heading and the tip text above it
-- come out, which only the rendered card knows - the grid's centre
-- sits one pitch below the card's. check_app_sync re-measures the
-- art and holds both numbers to it.
BUFF_PITCH = CARD_W * (11.6 / 63.5)
BUFF_GRID_DZ = -BUFF_PITCH
BUFF_SPACES = 15

function buffSpace(v)
  if not v or v < 1 or v > BUFF_SPACES then return nil end
  local i = BUFF_SPACES - v
  local row = math.floor(i / 3)
  local col = i % 3
  return batRightX(BAT_BUFF) + (col - 1) * BUFF_PITCH,
         batRowZ(3) + BUFF_GRID_DZ + (2 - row) * BUFF_PITCH
end

-- BAT'S TWO SPARE STAT DICE, in a column off the exhausted corner's
-- left edge. Jon's placing: they were left in the shared dice band at
-- the bottom of the table with everything else, where in a game whose
-- whole bottom row is Rats and unit dice they were just two more dice
-- in a crowd.
--
-- The band comes from build_mod (EXHAUST_Z) rather than being derived
-- here a second time from ROW_TIER and the felt, so a band that moves
-- takes the column with it instead of leaving two dice sitting inside
-- the corner they are meant to stand beside.
--
-- CENTRED ON A 2.0 PITCH, not spread over thirds of the band. The
-- band is 4.03 deep, so thirds put the two dice 1.34 apart and a
-- die is 1.8 across - the harness caught them overlapping each
-- other. 2.0 clears a die's width and still leaves both wholly
-- inside the band.
BAT_STAT_X = BAT_EXHAUST_X0 - 1.6
BAT_STAT_GAP = 2.0
BAT_STAT_Z = {(EXHAUST_Z[1] + EXHAUST_Z[2]) / 2.0 + BAT_STAT_GAP / 2.0,
              (EXHAUST_Z[1] + EXHAUST_Z[2]) / 2.0 - BAT_STAT_GAP / 2.0}

-- The active Rat is marked at the top right corner of its card, far
-- enough in that the die sits ON the card rather than over its edge.
--
-- THE RECOVERY DIE IS WHAT MARKS IT, and it is the rulebook that says
-- so rather than this file: the component list calls it "the Recovery
-- die, which marks the active Lab Rat all game", the Splice Phase
-- says to "put the Recovery die on it after seeing the Experiment and
-- the two Upgrades", and the battle moves the Recovery die to the
-- attacking Rat. check_app_sync reads the die's name OUT of those
-- sentences and compares it with the call below, so the two cannot
-- drift - which is the whole reason this is worth a comment. The mod
-- has had the Health die here and then the Strategy die, each time
-- because somebody picked one instead of reading the book. Jon's
-- call, 2026-11-12: it is Recovery, and the Strategy die is unused.
--
-- A RAT'S OWN STATS ARE PRINTED ON ITS CARD, which is why any of the
-- three could do this job and none of them is tracking a number.
-- There are four Rats and one of each die.
--
-- The setup starts it on the top Rat; the Red die - the one die a Rat
-- is given at random - sits in the opposite corner of whichever Rat
-- drew it, so the two markings on one card cannot be mistaken for
-- each other.
BAT_MARK_IN = 1.25
function batMarkX() return BAT_RAT_X + CARD_L / 2 - BAT_MARK_IN end
function batMarkZ(r) return batRatZ(r) + CARD_W / 2 - BAT_MARK_IN end
function batRedZ(r) return batRatZ(r) - CARD_W / 2 + BAT_MARK_IN end

-- A ROW OF FOUR DICE UNDER EVERY RAT, which is what the setup message
-- used to ASK THE PLAYER TO DO: "one Purple, Blue, Green and Yellow die
-- each". There are exactly four of each colour in the pool and four
-- Rats, so this is the whole supply dealt out, one row per Rat, and no
-- shared heap at the bottom of the table for four players to reach
-- across each other into.
--
-- LEFT TO RIGHT IN THE ORDER THE COLOURS RESTRICT IN - Purple with no
-- Upgrades held, Yellow with three - so a row reads the same way the
-- rule does.
BAT_RAT_DICE = { 'Purple', 'Blue', 'Green', 'Yellow' }

-- THE BAND BETWEEN ONE RAT AND THE NEXT, and all of it. The row pitch
-- is 7.82 and a Rat is a landscape card 5.88 deep, so there are 1.94
-- units of felt between two Rats that nothing else wants; a die is
-- 1.62 across at DIE_SCALE, which leaves a sixth of a unit at each
-- edge. Centred in the band rather than measured down from the card,
-- so moving a Rat row moves its dice and the clearance stays even at
-- both ends. check_app_sync.py measures it; the harness fails if a
-- die touches a card.
BAT_DIE_PITCH = 1.9
function batDieZ(r) return batRatZ(r) - BAT_ROW_PITCH / 2 end
function batDieX(i)
  return BAT_RAT_X + (i - (#BAT_RAT_DICE + 1) / 2) * BAT_DIE_PITCH
end

-- SOMEWHERE FOR DICE THAT ARE OUT FOR GOOD: one space, the same size
-- as every other, in the top right corner of the grid. That corner
-- is the only part of the row nothing else wants - the two decks
-- take the left of it and the Rats' spaces stop well short.
--
-- A function rather than a table so it cannot be read before
-- batRightX exists, and derived from the grid so it stays a card
-- the day the card scale changes.
function batBanished()
  local x, z = batRightX(BAT_SPLICES), batRowZ(1)
  return { x - BAT_BOX_HW, x + BAT_BOX_HW,
           z + BAT_BOX_HD, z - BAT_BOX_HD }
end

-- ------------------------------------------------------------ the AoS table
-- FIVE ELEMENT MATS ACROSS THE MIDDLE, because that is where the dice
-- go and it is the only part of this game that needs room around it:
-- every element must receive at least one die, and an element holds up
-- to its Target plus one. The decks and the two cards they reveal run
-- along the top, what a tier adds runs along the bottom.
--
-- A GAME WITH A TURN, NOT A BOARD. AoS reveals a Program and a
-- Limitation, allocates, rolls, and sets the Program aside - so the
-- spaces that matter are the two decks, the two cards face-up beside
-- them, and somewhere for what has been finished with.
AOS_COL = CARD_W - 0.02
AOS_ROW1 = 13.635                      -- decks and what they reveal
AOS_ROW2 = 3.335                       -- the five element mats
AOS_ROW3 = -6.965                      -- set aside, and what a tier adds
AOS_BOX_HW = (AOS_COL - 0.25) / 2
AOS_BOX_HD = (CARD_L - 0.30) / 2
-- The Technician is landscape, so its space is turned and its top is
-- levelled with the portrait spaces beside it - the same relation the
-- BAT table uses between a Lab Rat and its Upgrades.
AOS_WIDE_HW = (CARD_L - 0.30) / 2
AOS_WIDE_HD = (CARD_W - 0.30) / 2
-- A LIFT, NOT A DROP. BAT hangs a portrait space below a landscape
-- card to share its top edge; here it is the landscape card that
-- has to rise to meet the portrait spaces beside it, which is the
-- same number the other way round.
AOS_WIDE_LIFT = (CARD_L - CARD_W) / 2

AOS_TECH_X = CHAR_X
AOS_DECK1 = AOS_TECH_X + CARD_L / 2 + 0.35 + AOS_COL / 2
AOS_RIGHT = FELT.x1 - 0.30 - AOS_COL / 2

function aosCol(k) return AOS_DECK1 + (k - 1) * AOS_COL end

-- Centred rows: the mats and the Backdoor Routines are read as a row
-- rather than as a list, so they sit about the middle of the felt.
function aosMid(k, n) return (k - (n + 1) / 2) * AOS_COL end

-- WHICH SPACE IS WHICH along the top: THE TWO DECKS TOGETHER, then
-- the two cards they reveal. Reordered 2026-11-12, from deck / card /
-- deck / card. You draw from both decks in the same step - "reveal the
-- Program, then reveal exactly 1 Limitation" - so the two decks are
-- one reach, and the two face-up cards are read together as the thing
-- you are about to allocate against.
AOS_PROGRAMS, AOS_LIMITS = 1, 2        -- the two decks, side by side
AOS_PROGRAM, AOS_LIMIT = 3, 4          -- and what each has revealed

-- AND THE PROGRAMS FINISHED WITH THIS CYCLE. Not SET ASIDE, which is
-- the pile a Program leaves the game by: this is the one it comes back
-- from when the deck is rebuilt.
--
-- IT LEFT THE TOP ROW on 2026-11-12 and now sits in the right-hand
-- column, directly above the banished dice - so that column reads
-- TIER CARD / DISCARD / BANISHED DICE from the back of the table
-- forward, and the top row is the four spaces of a turn and nothing
-- else. aosCol(5) is free.
AOS_DISCARD_X = AOS_RIGHT
AOS_DISCARD_Z = AOS_ROW2
AOS_MATS = 5
AOS_BACKDOORS = 6

-- The NAP Time Slot column, down the left. It has to clear the dice at
-- -26.5 on one side and the Assignment deck, which reaches -14.07, on
-- the other; a landscape card is 8.71 across, so there is exactly one
-- place for it.
SLOT_X = -19.5

-- NAP's right-hand column: the Apprentices to choose from, then the FINF
-- card, then the Final Exams, top to bottom. 7.0 apart, which clears a
-- landscape card's 6.24 depth, and the last of them sits at -14.4 with
-- its bottom edge at -17.5 - the deepest anything goes on this felt.
NAP_X = 23.5
-- A CARD AND A HAIR, which is the same pitch the rows use: an
-- Assignment turned on its side is a card long, so anything tighter
-- has a rotated card lapping into the next row. It was 8.75 against a
-- card of 8.71; both come from ROW_PITCH now, so the clearance holds
-- at any card scale instead of at one.
NAP_GAP = ROW_PITCH

-- The Assignment deck, top left, with the Time Slots running down
-- underneath it and four Assignment spaces beside each.
ASSIGN_X = -19.5

-- FOUR SPACES PER TIME SLOT, because rules/nap.html says never exceed 4
-- Assignments in a row. Four landscape cards plus the Time Slot itself
-- is 43.5 units of a 56-unit felt, which is what sets the pitch: 8.5 is
-- a shade under a card's 8.71, so a full row tucks rather than spreads,
-- and that is what leaves room for the Apprentice stack at 23.5 without
-- pushing it off the edge.
ASSIGN_SLOTS = 4

-- NOT DEALT BY A SETUP, DELIBERATELY. These decks belong to a part
-- of a game the setup does not reach - each is dealt by the finale
-- button of the game it belongs to, not by the setup:
--
--   Final Exams     you reach them; the exam button starts them
--   Tyrant Attacks  nothing draws one until the Tyrant is awake, which is
--                   five Splices away
--   Buff HP Track   the front layer of the Tyrant track, so the battle
--                   deals it and stands the Health die on the
--                   difficulty's number. rules/bat.html still calls the
--                   card optional - a player who does not want it can
--                   push the whole Health onto the dial and ignore it
--
-- Named here so that "every deck a setup can reach" stays a real check
-- rather than one that quietly stopped covering a deck.
IN_THE_BAG = { 'Final Exams', 'Tyrant Attacks', 'Buff HP Track',
               'Advanced Programs' }

-- The printed layout under the cards. One per game, each its own tile
-- in its own bag, which is what lets them be different felts.
NAP_TABLE = 'NAP Table'
BAT_TABLE = 'BAT Table'
AOS_TABLE = 'AoS Table'
IMP_TABLE = 'IMP Table'

-- Lay a game's overlay down and lock it a moment later: a 56-unit tile
-- that can be dragged is a tile that will be dragged.
function tableOut(label)
  local mat = deckOut(label, {0, 0.98, MAT_Z}, FACEUP)
  if mat then Wait.time(function() if mat then mat.setLock(true) end end, 0.6) end
  return mat
end

-- An Apprentice starts at 2 HP / 2 STR / 2 REC - printed on every one
-- of the six sides, from the single literal in generator/build_nap.py -
-- and the three dice say so in a row UNDER the card rather than in a
-- column beside it.
--
-- The Apprentice and FINF are both landscape and NAP_GAP apart, so the
-- clear band between them is NAP_GAP minus a card's short side, and
-- its centre is exactly NAP_GAP / 2 below the Apprentice. STAT_PITCH
-- has to clear a die, which is 1.8 across now: at 1.5 the three of
-- them overlapped each other, which the harness caught the moment the
-- dice grew.
--
-- The Chip starts in the circle beside Morning, reading 1.
NAP_START = 2
-- The FINF space, one row under the Apprentice. Named because three
-- things now want it: the setup that lays the cards there, the snap
-- point under them, and the mat box the template draws from the snap.
FINF_Z = ROW_CHAR - NAP_GAP
STAT_PITCH = 2.1
-- A DIE AND A MARGIN UNDER THE CARD'S BOTTOM EDGE. Every character
-- card in the set is landscape, so this one drop works for all three
-- games and the row cannot end up at a different height in each.
STAT_DROP = CARD_W / 2 + 1.3
function statZ(cardZ) return cardZ - STAT_DROP end
function statRow(x) return {x - STAT_PITCH, x, x + STAT_PITCH} end
STAT_Z = statZ(ROW_CHAR)
CHIP_X = ASSIGN_X - CARD_L / 2 - 1.9
ASSIGN_PITCH = ROW_PITCH

-- The Assignment deck sits over the FIRST Assignment column, with the
-- two cards it reveals each turn beside it.
DECK_X = ASSIGN_X + ASSIGN_PITCH
REVEAL_SLOTS = 2

-- AND THE ONE YOU DID NOT TAKE, next along the same row. "Reveal 2
-- Assignments and take one into the row as your Primary. Discard the
-- other" (rules/nap.html) - so this is a pile that fills every turn,
-- and it is not the Completed Credits pile down the right, which is
-- the record of what you finished.
NAP_DISCARD_X = DECK_X + (REVEAL_SLOTS + 1) * ASSIGN_PITCH

-- "Shuffle the pool and draw 3 Final Exams" (rules/nap.html). They go
-- on the three spaces this row already has - the two the deck revealed
-- into and the discard beside them - because the day is over and all
-- three are empty. The third one IS NAP_DISCARD_X, which is why the
-- draw is laid out as DECK_X + k * ASSIGN_PITCH rather than from a
-- list: the spaces are printed on the mat at that pitch and a draw
-- that does not use it lands between boxes.
EXAM_DRAW = 3

-- THE APPRENTICE IN THE TOP LEFT CORNER, with its three stat dice in
-- the band under it. It stood at the head of the right-hand column
-- over the FINF card; the corner is where the other three games put
-- their character, and this table has room for it because the clock
-- starts a row lower.
NAP_CHAR_X = CHAR_X

-- TWO PILES DOWN THE RIGHT, under the FINF card.
--
-- Completed Assignments stay in their Time Slot until End of Day and
-- then go face-up to a discard (rules/nap.html), so that pile is always
-- wanted. The second is for Tier III only: four of the six Devious
-- Opportunities pay nothing when completed, and you keep the card to
-- spend at the Final Exam (rules/nrj.html). A pile rather than four
-- spaces - they are kept, not laid out, and they stack.
--
-- Tier I's Following Setbacks and Tier II's Imposter Tasks need no
-- space at all: both go INTO the Assignment deck.
PILE_X = 23.5

-- A READOUT ABOVE EACH PILE, in the band between it and the card above
-- it - the same NAP_GAP / 2 the stat dice use, for the same reason.
-- Named here because setupNAP deals them and packUp sends them back.
CREDIT_PILE = 'Credit Record'
BANK_PILE = 'Banked Opportunities'
COUNTER_LIFT = NAP_GAP / 2

-- A 3DText IS NOT A CARD, and it was being dealt like one. build_mod.py
-- authors both plates lying flat and locked - rotX 90 is what makes a
-- 3DText readable from above - and deckOut turns whatever it takes out
-- FACEDOWN, which stood the plate on edge, pointing away. There was no
-- number over the Completed Credits pile and no hover text either,
-- which reads exactly like a counter that is not counting; the counter
-- was working the whole time and had nothing anyone could see.
TEXT_ROT = {90, 0, 0}
TEXT_Y = 1.5

function counterOut(nick, z)
  local o = deckOut(nick, {PILE_X, TEXT_Y, z}, TEXT_ROT)
  if o then o.setLock(true) end
  return o
end

-- Where the character you keep ends up. NAP's belongs at the head of its
-- own column; the other two are dealt across the table and keep the
-- middle.
CHAR_HOME = { NAP = {NAP_CHAR_X, ROW_CHAR},
              AoS = {AOS_TECH_X, AOS_ROW1 + AOS_WIDE_LIFT},
              IMP = {CHAR_X, ROW_CHAR} }

function col(i) return (i - 2.5) * (CARD_W + 1.0) end


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

-- THE MARKERS ARE NOT IN A BAG. The Chip and the Health, Strategy and
-- Recovery dice sit loose on the table, so a setup finds them by name
-- where they are rather than taking them out of anything, and Pack up
-- puts them back at DICE_HOME instead of bagging them.
function marker(name)
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == name then return o end
  end
  return nil
end

-- EVERY OBJECT OF THAT NAME, in an order that does not change.
-- marker() answers with whichever one getAllObjects reaches first,
-- which is the whole answer for the Chip or the Health die because
-- there is one of each - but there are four Purple dice, and BAT gives
-- one to every Rat. Sorted by GUID so the same die goes to the same
-- Rat on every setup: getAllObjects promises no order, and a row that
-- reshuffles itself between two setups of the same game looks like a
-- bug even when it is not.
function markersNamed(name)
  local out = {}
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == name then table.insert(out, o) end
  end
  table.sort(out, function(a, b) return a.getGUID() < b.getGUID() end)
  return out
end

-- THE FACE FIRST, THE MOVE AFTER, AND A FRAME BETWEEN THEM.
--
-- setPositionSmooth is a tween; setRotationValue is a physics call that
-- re-seats the object. Issued in that order in the same frame, the
-- rotation cancelled the move: the three stat dice stayed down in the
-- dice row showing the right numbers, while the Chip - the one call
-- here that passes no value - moved as it should. That difference is
-- what the symptom was.
--
-- And a BACKSTOP, because the above is a diagnosis made at a distance
-- from the table. Half a second later, a die that is still not where it
-- was sent is put there outright: setPosition is instant, so there is
-- no tween for anything to interrupt.
function setMarker(name, x, z, value, face, onto)
  return moveMarker(marker(name), x, z, value, face, onto)
end

-- WHERE A MARKER IS LET GO. 1.6 is a height for bare felt, and every
-- marker move in the mod used it whatever was already lying at the
-- destination.
--
-- THAT IS A BUG WHEREVER A DIE STANDS ON A CARD. A die is 1.62 across
-- at DIE_SCALE, so its own bottom is 0.81 below its centre: let go at
-- 1.6 its underside is at 0.79, which is below the face of a card
-- lying on the felt. The move is made with collide off - that is what
-- lets it cross the table without shoving cards about - so nothing
-- stops the die arriving INSIDE the card, and which way Unity then
-- pushes the pair apart is not ours to choose. BAT stands two dice on
-- a Lab Rat and one on the Buff HP track, and all three have now been
-- seen to lose: the Red die started under its Rat (Jon, 2026-11-12)
-- and the Health die under the Buff card before that.
DROP_Y = 1.6
-- What the three on-card calls pass, so a call site says which it
-- means instead of ending in a bare true.
ONTO = true

-- SO ASK THE TABLE RATHER THAN WORKING IT OUT. How thick a card is,
-- how thick the overlay is and where the felt's surface really sits
-- are Unity's numbers, not this script's, and every attempt to derive
-- them here would be a guess that goes stale the day a scale changes.
-- getBounds is a world-space box: this finds the tallest thing already
-- standing at the destination and puts the die on top of it, by 0.05 -
-- near enough to no fall at all, so the die cannot bounce off a corner
-- it was placed on.
--
-- IT NEVER GOES LOWER THAN DROP_Y, so a destination with nothing at it
-- behaves exactly as it did before.
function dropOnto(o, x, z)
  local half
  if not pcall(function() half = o.getBounds().size.y / 2 end) then
    return DROP_Y
  end
  local top
  for _, c in ipairs(getAllObjects()) do
    if c ~= o then
      pcall(function()
        local b = c.getBounds()
        if math.abs(b.center.x - x) <= b.size.x / 2
           and math.abs(b.center.z - z) <= b.size.z / 2 then
          local t = b.center.y + b.size.y / 2
          if not top or t > top then top = t end
        end
      end)
    end
  end
  if not top then return DROP_Y end
  return math.max(DROP_Y, top + half + 0.05)
end

-- THE SAME MOVE, GIVEN THE OBJECT. BAT's dice rows cannot go through
-- setMarker - there are four dice to one name - and the tween, the
-- backstop and the ordering below are the part that was hard to get
-- right, so they are not written twice.
function moveMarker(o, x, z, value, face, onto)
  if not o then return nil end
  local name = o.getName() or 'that die'
  -- ONTO WHATEVER IS THERE, for the three dice that stand on a card.
  -- Measured before the move, because the die is still at its old
  -- position and so is not its own answer.
  local y = onto and dropOnto(o, x, z) or DROP_Y
  o.setLock(false)
  if value then
    local ok = pcall(function() o.setRotationValue(value) end)
    if not ok then say(name .. ' has no numbered faces to set.') end
  end
  Wait.frames(function()
    o.setPositionSmooth({x, y, z}, false, true)
    Wait.frames(function()
      local p = o.getPosition()
      if math.abs(p.x - x) > 1.0 or math.abs(p.z - z) > 1.0 then
        o.setPosition({x, y, z})
      end
      -- THE TURN GOES LAST, AND IT IS NOT A TWEEN. The Chip was turned
      -- with setRotationSmooth at the top of this step and the move
      -- started two frames later, which cancelled it part way round -
      -- the same collision that stopped the stat dice moving, with the
      -- roles the other way about. Nothing can interrupt a setRotation
      -- that happens after everything else has landed.
      if face then
        local r = o.getRotation()
        o.setRotation({r.x, face[1], face[2]})
      end
    end, 30)
  end, 2)
  return o
end

-- ONE PURPLE, BLUE, GREEN AND YELLOW UNDER EVERY RAT.
--
-- The Tyrant's six dice - 2 Purple / 2 Blue / 1 Green / 1 Yellow - come
-- out of this same supply when it wakes, so they come off the Rats'
-- rows; there is no separate Tyrant die in the mod to deal.
function batRatDice()
  for i, colour in ipairs(BAT_RAT_DICE) do
    local pool = markersNamed(colour)
    for r = 1, BAT_ROWS do
      if pool[r] then moveMarker(pool[r], batDieX(i), batDieZ(r)) end
    end
    if #pool < BAT_ROWS then
      say('Only ' .. #pool .. ' ' .. colour .. ' dice found -- ' ..
          BAT_ROWS .. ' Rats need ' .. BAT_ROWS .. '.')
    end
  end
end

-- THE TWO FACES, AND WHICH GAME READS WHICH. They were one chip with
-- a picture on each side until the day a Custom_Token turned out to
-- show its one image mirrored underneath; they are two objects now,
-- and no game reads both. The one a game does not read goes into its
-- own box at setup rather than lying on the table being a thing to
-- wonder about.
FACE_OF = { Chip = 'NAP', Dial = 'BAT' }

function stowFaces(game)
  for nick, owner in pairs(FACE_OF) do
    if owner ~= game then
      local o = marker(nick)
      if o then
        o.setLock(false)
        putHome(o)
      end
    end
  end
end

-- EVERY LOOSE THING, BY GUID. This walked DICE_HOME, which is keyed
-- by NAME - and there are four Purple dice, four Blue, four Green and
-- four Yellow with one name each between them, so marker() found the
-- first of each and Pack up left fourteen of the seventeen dice
-- wherever the game had put them. MARKER_HOME is generated by
-- build_mod.py as it lays each object down, so every die, the Chip
-- and the Dial all know their own place and no two of them share an
-- entry.
function markersHome()
  for id, p in pairs(MARKER_HOME) do
    local o = getObjectFromGUID(id)
    if o then
      o.setLock(false)
      o.setPositionSmooth({p[1], 1.6, p[2]}, false, true)
    else
      -- ...OR OUT OF A BOX. A setup stows the face its game does not
      -- read, and getObjectFromGUID cannot see inside a bag, so Pack
      -- up has to go and look. Without this the Chip stayed in the
      -- NAP box after a game of BAT and the next NAP setup found no
      -- Chip to turn.
      fetchHome(id, p)
    end
  end
end

function fetchHome(id, p)
  for _, g in pairs(BOX) do
    local b = getObjectFromGUID(g)
    for _, e in ipairs(contents(b) or {}) do
      if e.guid == id then
        b.takeObject({guid = id, position = {p[1], 1.6, p[2]},
                      smooth = false})
        return true
      end
    end
  end
  return false
end

-- Which deck a card belongs to. DECK_OF is generated from decks.py and
-- answers to both names: a 'Task 7' and an 'Assignment' both go home
-- to 'Assignment'.
function deckLabel(name)
  local base = (name or ''):gsub(' %d+$', '')
  return DECK_OF[base] or base
end

-- The three TTS types that have an inside. Everything else - Card,
-- Dice, Tile, 3DText, Figurine - does not.
CONTAINER = { Deck = true, Bag = true, Infinite = true }

-- WHAT IS INSIDE AN OBJECT, or nil if it is not the kind of thing that
-- has an inside.
--
-- ASK WHAT IT IS; DO NOT ASK IT FOR ITS CONTENTS AND SEE. getObjects()
-- exists on every TTS object, so `o.getObjects and o.getObjects()` is
-- not a guard in front of the call - it IS the call, and the test in
-- front of it always passes. And TTS does not raise when the call is
-- wrong: it prints a red
--
--   Lua Error <getObjects>: Attempting to call getObjects() on an
--   object that does not support getObjects()
--
-- into the chat, attributed to the object, and hands back nil. pcall
-- cannot suppress a message, which is why wrapping it was no use at
-- all: Jon's chat filled up with one line per die on every load.
--
-- So the only way not to see it is not to make the call. obj.type is
-- a plain string on every object and costs nothing to read.
--
-- WHAT IT COST BEFORE: firstCard is asked of every object on the
-- table, which took boxFor with it, and boxFor is how putHome and the
-- whole pack-up decide where a thing belongs. cardsAt had the same
-- line from the day the pile counters were written, so a die resting
-- near a pile silently stopped the count - which is half of why the
-- plate over the Completed Credits pile never showed a number.
function contents(obj)
  if not obj then return nil end
  local ok, kind = pcall(function() return obj.type end)
  if ok and kind ~= nil and not CONTAINER[kind] then return nil end
  local got, kids = pcall(function() return obj.getObjects() end)
  if got and kids then return kids end
  return nil
end

-- The first card inside something, or nil if it holds none.
function firstCard(obj)
  local kids = contents(obj)
  if kids then
    for _, e in ipairs(kids) do
      if e.nickname and e.nickname ~= '' then return e.nickname end
    end
  end
  return nil
end

-- WHICH BAG AN OBJECT BELONGS IN, asked of the object rather than of
-- its name. A PILE THE PLAYER BUILT HAS NO NAME: the Completed Credits
-- pile is precisely that, cards dropped on each other, and TTS gives
-- the deck it makes no nickname at all. homeBox had nothing to look up,
-- so Pack up walked past the biggest pile on the table and then
-- reported it as still out under a blank name.
function boxFor(obj)
  if not obj then return nil end
  local b = homeBox(obj.getName())
  if not b then b = homeBox(firstCard(obj)) end
  -- NOTHING IS ITS OWN HOME. A box answers to the first deck
  -- inside it, so asking this of one of the four boxes hands back
  -- the box itself - and unmix, which asks it of every object on
  -- the table, would then take every deck out of every box and
  -- tip it onto the felt.
  --
  -- BY GUID, NOT BY ==. Two references to the same TTS object do
  -- not always compare equal, so the identity test quietly did
  -- nothing and the bag was still its own home.
  if b ~= nil and b.getGUID() == obj.getGUID() then return nil end
  return b
end

-- WHAT PACK UP TAKES AWAY, which is not the same as what has a box.
--
-- The Chip and the Dial each have one, because a setup stows the face
-- its game does not read - but Pack up's job for a marker is to put
-- it back in the row at the bottom of the table, which markersHome
-- does. One predicate, so the sweep, the report at the end of it and
-- the harness cannot disagree about which objects are its business.
function packable(o)
  if not o then return nil end
  if MARKER_HOME[o.getGUID()] ~= nil then return nil end
  -- AND THE RULES STAY OUT. Each book has a box, because showRules
  -- puts the three a game does not want back in them - but clearing
  -- the table at the end of a game is no reason to take the rules
  -- away from somebody who may still be reading them.
  if isRulebook(o) then return nil end
  return boxFor(o)
end

-- TAKE THE STRANGERS OUT OF A DECK BEFORE IT IS STOWED.
--
-- A setup MERGES decks: the six Opportunities and the Setbacks go into
-- the Assignment deck, and when the pack-up puts that deck away the
-- Opportunities are inside it. The next setup asked for a deck called
-- Opportunities, found nothing, said MISSING DECK and dealt a
-- 38-card Assignment deck with no Opportunities left to add.
--
-- The strangers come out here and go into the box as single cards; a
-- deckOut gathers its own back up, so the deck is whole again next
-- time without anything having to remember what was merged where.
function unmix()
  for _, o in ipairs(getAllObjects()) do
    if boxFor(o) and count(o) > 1 then
      -- A nameless pile is whatever is in it, not a deck of nothing:
      -- without this every card in the Completed Credits pile counts
      -- as a stranger and the pile is taken apart card by card.
      local mine = deckLabel(o.getName())
      if mine == '' then mine = deckLabel(firstCard(o)) end
      local strays = {}
      for _, e in ipairs(contents(o) or {}) do
        if deckLabel(e.nickname) ~= mine then
          table.insert(strays, e.guid)
        end
      end
      for _, g in ipairs(strays) do
        -- NEVER THE LAST ONE: a deck of one card is a card, and taking
        -- a card out of a card throws.
        if count(o) > 1 then
          o.takeObject({guid = g, position = OFF, smooth = false})
        end
      end
    end
  end
end

-- ONE ATTEMPT AT A BAG IS NOT A PUT. TTS refuses roughly one in three
-- under load - that is what twenty pack-up passes are for - and every
-- other caller here made a single attempt and walked away. A refused
-- put leaves the card hanging in the staging band, from where it drops
-- onto the table looking like something the setup dealt, or simply
-- misses the deal it was being gathered for.
--
-- So look again. The object is gone from getAllObjects() once the bag
-- has it, which is the only honest way to tell that the put took; the
-- GUID is read before the attempt because a swallowed object cannot be
-- asked for it afterwards.
-- NAME A PILE ON THE WAY INTO A BOX. A box cannot see inside a
-- deck it holds - findDeck matches a nickname and the gather loop
-- reads the box's top level - so a nameless pile put away is
-- cards nobody can get back: the next setup deals without them
-- and says nothing at all. The Completed Credits pile is exactly
-- that, cards the player dropped onto each other, and TTS gives
-- the deck it makes no nickname.
--
-- unmix has already taken the strangers out by the time a
-- pack-up reaches this, so what is left belongs to one deck and
-- can be named after it.
function nameIt(obj)
  if not obj or count(obj) <= 1 then return end
  local n = obj.getName()
  if n ~= nil and n ~= '' then return end
  local lab = deckLabel(firstCard(obj))
  if lab and lab ~= '' then obj.setName(lab) end
end

function putHome(obj, tries)
  if not obj then return end
  local b = boxFor(obj)
  if not b then return end
  local gid = obj.getGUID()
  obj.setLock(false)
  b.putObject(obj)
  tries = (tries or 0) + 1
  if tries >= 8 then return end
  Wait.frames(function()
    for _, o in ipairs(getAllObjects()) do
      if o.getGUID() == gid then
        putHome(o, tries)
        return
      end
    end
  end, 6)
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

-- Is this card one of that deck's? A DECK'S CARDS ARE ITS NAME AND A
-- NUMBER, and nothing else is: matching the name and a space made
-- 'Imposter Task 1' a card of the Imposters, so the finale gathered
-- the four Tier II Tasks into the five Imposters and dealt nine
-- characters to choose between.
function isCardOf(name, one)
  name = name or ''
  if name:sub(1, #one + 1) ~= one .. ' ' then return false end
  return name:sub(#one + 2):match('^%d+$') ~= nil
end

-- Take the named deck OUT of its box and put it at pos - AND EVERY
-- CARD OF IT that an earlier game left lying in the box beside it.
--
-- findDeck MATCHES A NICKNAME EXACTLY, and a deck does not survive
-- being played with. column() deals the Time Slots and leaves a deck
-- of one called 'Time Slots' next to two loose 'Time Slot' cards;
-- choosing an Apprentice takes one card out of three. Pack up stows
-- each of those separately, because that is what they are by then, and
-- the next setup took the deck out and dealt whatever was left in it:
-- one Time Slot where there should have been three.
function deckOut(label, pos, rot)
  local b, gu, loose = findDeck(label)
  local d = nil
  if b then
    d = b.takeObject({guid = gu, position = pos, rotation = rot or FACEDOWN,
                      smooth = false})
  elseif loose then
    loose.setLock(false)
    d = loose
  end
  -- The cards of this deck carry a name of their own, which is not the
  -- deck's: a card of Time Slots is a Time Slot.
  local one = CARD_NAME[label] or label
  for _, g in pairs(BOX) do
    local box = getObjectFromGUID(g)
    if box then
      local want = {}
      for _, e in ipairs(box.getObjects()) do
        if isCardOf(e.nickname, one) then table.insert(want, e.guid) end
      end
      for _, gid in ipairs(want) do
        local c = box.takeObject({guid = gid, position = OFF, smooth = false})
        if c then
          if d then d.putObject(c) else d = c end
        end
      end
    end
  end
  -- AND OFF THE TABLE, not only out of the boxes. Sending cards home
  -- and taking them straight back out again is a race: a bag refuses
  -- about one put in three, the refused one is still on the table when
  -- the deck is gathered, and the deal comes up short with nothing to
  -- say so. Changing the FINF setting mid-game lost a card that way
  -- every time it asked for all three.
  --
  -- Safe because a setup packs up first, so the table is bare when one
  -- of these runs; the two that run mid-game - the Apprentice and FINF
  -- buttons - want exactly this.
  for _, o in ipairs(getAllObjects()) do
    if isCardOf(o.getName(), one)
        and (d == nil or o.getGUID() ~= d.getGUID()) then
      o.setLock(false)
      if d then d.putObject(o) else d = o end
    end
  end
  if not d then
    say('MISSING DECK: ' .. label)   -- a label that matches nothing, out loud
    return nil
  end
  -- A DECK TTS BUILDS FOR YOU HAS NO NAME. Gathering one out of loose
  -- cards makes exactly that, and then nothing can put it away:
  -- homeBox reads '' , finds no bag for it and putHome achieves
  -- nothing however many times it tries. Increase 3 puts all three
  -- FINF cards into the Assignment deck, which consumes the FINF deck
  -- object itself, so the next setting had to build one - and the
  -- remainder sat in the staging band at dead centre of the bottom
  -- edge, face down and wearing the Assignment back.
  if count(d) > 1 and d.getName() ~= label then d.setName(label) end
  d.setLock(false)
  d.setPosition(pos)
  d.setRotation(rot or FACEDOWN)
  return d
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
  -- xpcall WITH A HANDLER, not pcall. Both work in TTS, but under the
  -- test harness pcall around a step that calls back into the host
  -- intermittently lost the object bindings and every step died on
  -- "attempt to index a function" - whole runs at a time. xpcall does
  -- not, and it reports the error the same way.
  local ok, err = xpcall(fn, tostring)
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

-- "Take that many at random and return the rest to the bag" - which all
-- four setups ask for somewhere.
--
-- THIS USED TO CUT THE DECK DOWN AND HAND BACK THE DECK, and that is the
-- same stale-reference bug that put a Lab Rat behind its neighbours: cut
-- a deck to one card and the deck object is destroyed, so the reference
-- returned was dead and every setPosition and putObject on it afterwards
-- did nothing at all. It is why the FINF card sat on top of a Time Slot
-- instead of beside it, and it would have done the same to the AoS
-- Program deck at Hard, where the Routine cut is to exactly one.
--
-- So nothing hands back a cut deck any more. Take the KEEPERS out and
-- send the rest home: moveN moves them straight into the deck they are
-- joining, drawOne deals a single card to where it belongs, and cutTo
-- is only for a deck that cannot reach one card.

-- Move n random cards from src into dst, then send src home.
function moveN(src, dst, n)
  if not src then return dst end
  if n <= 0 then putHome(src); return dst end
  src.shuffle()
  -- ASKED FOR ALL OF THEM, give the deck. Taking the last card out of a
  -- deck is taking a card out of a card, because a deck of one is a
  -- card. BAT at Nobulous shuffles in all 8 Specimens, so this was one
  -- difficulty away from throwing.
  if n >= count(src) then
    if dst then dst.putObject(src) else dst = src end
    return dst
  end
  for _ = 1, n do
    local c = src.takeObject({position = OFF, smooth = false})
    if c and dst then dst.putObject(c) end
  end
  putHome(src)
  return dst
end

-- Deal ONE card of a deck to a place, and send the rest home.
function drawOne(label, pos, rot)
  local d = deckOut(label, OFF)
  if not d then return nil end
  d.shuffle()
  local c = d.takeObject({position = pos, rotation = rot or FACEUP,
                          smooth = false})
  putHome(d)
  return c
end

-- Cut a deck down to n, for a deck that cannot reach one card. Anything
-- that can must use moveN or drawOne instead.
function cutTo(deck, n)
  if not deck or n < 2 then return deck end
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
--
-- THE DECK TAKES THE FIRST SLOT AND IS DEALT FROM. It used to be moved to
-- the first slot AFTERWARDS, which does not work: a deck of one card IS a
-- card in TTS, so once the second-to-last card is taken the deck object is
-- destroyed and the reference held here is stale. setPosition on it did
-- nothing and the last card stayed where the deck had been dealt - which
-- is the Lab Rat sitting behind its neighbours in the middle of the row,
-- and the half-hidden Time Slot. Positioned first, the card is already
-- where it belongs when the deck collapses around it.
-- The same, down the table instead of across it, AND IN THE DECK'S OWN
-- ORDER. Which card takeObject hands back is TTS's business, not this
-- script's: asking for three in a row and trusting the order dealt the
-- Time Slots as Morning, Evening, Afternoon - a clock that reads wrong.
-- So each card is taken BY NAME to its own slot, from the last back to
-- the second, which leaves card one in the deck at slot one.
-- THE LAST CARD IS NOT THE DECK, and this is the third shape that trap
-- has taken. Taking the second-to-last card out destroys the deck
-- object and respawns its final card, and TTS does not put that card
-- down exactly where the deck was standing: on Jon's table Morning
-- landed at x -21.72, z 5.95 instead of -19.50, 6.05, while the two
-- cards the loop placed itself were exact to the hundredth.
--
-- So the first slot is set again once the collapse has happened. By
-- POSITION rather than by name, because spread() does not know which
-- card it will be left holding - the prefix is the only handle, and it
-- matches both the card ('Time Slot 1') and the deck it came from
-- ('Time Slots') for the case where no collapse happened at all.
function snapFirst(label, x, z, rot)
  Wait.frames(function()
    local best, bd = nil, 6.0
    for _, o in ipairs(getAllObjects()) do
      local n = o.getName() or ''
      if n ~= '' and string.sub(n, 1, #label) == label then
        local p = o.getPosition()
        local d = math.abs(p.x - x) + math.abs(p.z - z)
        if d < bd then best, bd = o, d end
      end
    end
    if best then
      best.setPosition({x, 1.6, z})
      best.setRotation(rot or FACEUP)
    end
  end, 4)
end

function column(deck, n, x, z0, rot, gap)
  if not deck then return end
  gap = gap or (CARD_W + 0.6)
  -- The cards are named for ONE of them, which is not always the deck's
  -- own name: a card of Time Slots is a Time Slot.
  local label = CARD_NAME[deck.getName()] or deck.getName()
  deck.setPosition({x, 3, z0})
  deck.setRotation(rot or FACEUP)
  for i = n, 2, -1 do
    local want = label .. ' ' .. i
    for _, e in ipairs(deck.getObjects()) do
      if e.nickname == want then
        deck.takeObject({guid = e.guid,
                         position = {x, 3, z0 - (i - 1) * gap},
                         rotation = rot or FACEUP, smooth = false})
        break
      end
    end
  end
  snapFirst(label, x, z0, rot)
end

function spread(deck, n, z, rot, gap)
  if not deck then return end
  gap = gap or (CARD_W + 0.6)
  local x0 = -((n - 1) * gap) / 2
  deck.setPosition({x0, 3, z})
  deck.setRotation(rot or FACEUP)
  for i = 1, n - 1 do
    deck.takeObject({position = {x0 + i * gap, 3, z}, rotation = rot or FACEUP,
                     smooth = false})
  end
  snapFirst(CARD_NAME[deck.getName()] or deck.getName(), x0, z, rot)
end

-- The Assignment spaces beside each Time Slot. Snap points rather than
-- printed mats: they cost nothing, they hold a card square, and they go
-- away with the game rather than sitting on the felt during BAT.
--
-- Global.setSnapPoints takes WORLD positions and replaces the lot, so
-- this builds every row at once. Wrapped, because a snap point is a
-- convenience and must never be the reason a setup fails.
local function snapAt(pts, x, z)
  table.insert(pts, {position = {x, 1.0, z},
                     rotation = {0, 0, 0}, rotation_snap = false})
end

-- EVERY SPACE BAT DRAWS, in table order. The overlay is painted from
-- this list, so a box on the felt and a space in the script cannot
-- disagree: there is one of them.
--
-- The Lab Rats and the two decks are NOT here. Jon asked for no
-- outline under either - a Rat card fills its space and a deck is a
-- stack you can see - but they still get snap points below, because a
-- space you can drop onto is a different thing from a line you can
-- see.
function batBoxes()
  local out = {}
  local function box(x, z)
    table.insert(out, {x = x, z = z, hw = BAT_BOX_HW, hd = BAT_BOX_HD})
  end
  for r = 1, BAT_ROWS do
    for k = 1, BAT_UPGRADES do box(batLeftX(k), batRowZ(r)) end
  end
  box(batRightX(BAT_PROTOCOL), batRowZ(1))
  box(batRightX(BAT_NOTES), batRowZ(1))
  for k = 1, 3 do box(batRightX(k), batRowZ(2)) end
  box(batRightX(BAT_EXP_DISCARD), batRowZ(2))
  box(batRightX(BAT_UPG_DISCARD), batRowZ(2))
  for k = 1, 3 do box(batRightX(k), batRowZ(3)) end
  table.insert(out, {x = batRightX(BAT_TYRANT_DICE) + BAT_COL / 2,
                     z = batRowZ(3), hw = BAT_WIDE_HW, hd = BAT_BOX_HD})
  for k = 1, BAT_SPLICES do box(batRightX(k), batRowZ(4)) end
  return out
end

-- Every space BAT wants. Boxes first, then the places with no box:
-- the four Rats, the two decks, the mark for the active Rat, and the
-- fifteen cells of the Buff HP track.
--
-- THE TRACK'S CELLS ARE MEASURED OFF THE PRINTED CARD, not counted out
-- here: BUFF_CELL is generated by build_mod.py from the rendered
-- BAT_BuffHP sheet, so a redesign of that card moves the snap points
-- with it instead of leaving them where the old boxes were.
function batSnaps()
  local pts = {}
  local function at(x, z)
    table.insert(pts, {position = {x, 1.0, z},
                       rotation = {0, 0, 0}, rotation_snap = false})
  end
  for _, b in ipairs(batBoxes()) do at(b.x, b.z) end
  for r = 1, BAT_ROWS do
    at(BAT_RAT_X, batRatZ(r))
    at(batMarkX(), batMarkZ(r))
    -- AND THE OPPOSITE CORNER, which is the Red die's. The active-Rat
    -- mark has had a snap point since the mark existed and this one
    -- had none, so the one die that moves between Rats every turn -
    -- Red is passed to a non-active Rat at the start of the next one -
    -- was the only marking with nowhere to land square.
    at(batMarkX(), batRedZ(r))
    -- A PLACE TO PUT A DIE BACK. The active-Rat mark has had one all
    -- along; a row of four spent dice under the card is the same kind
    -- of place, and without snap points the row drifts apart over a
    -- game until it is a heap again.
    for i = 1, #BAT_RAT_DICE do at(batDieX(i), batDieZ(r)) end
  end
  at(batRightX(BAT_EXPERIMENTS), batRowZ(1))
  at(batRightX(BAT_UPGRADE_DECK), batRowZ(1))
  local bx, bz = batRightX(BAT_BUFF), batRowZ(3)
  for _, c in ipairs(BUFF_CELL) do at(bx + c[1], bz + c[2]) end
  local ok = pcall(function() Global.setSnapPoints(pts) end)
  if not ok then say('Snap points are not available in this build.') end
  return pts
end

-- EVERY SPACE AoS DRAWS. Like BAT's, the overlay is painted from this
-- list and the snap points are made from it, so a box on the felt and
-- a space you can drop onto cannot disagree.
--
-- The Technician's space is here but drawn turned, because the card
-- is; everything else on this table is portrait.
function aosBoxes()
  local out = {}
  local function box(x, z, hw, hd)
    table.insert(out, {x = x, z = z, hw = hw or AOS_BOX_HW,
                       hd = hd or AOS_BOX_HD})
  end
  box(AOS_TECH_X, AOS_ROW1 + AOS_WIDE_LIFT, AOS_WIDE_HW, AOS_WIDE_HD)
  for k = 1, 4 do box(aosCol(k), AOS_ROW1) end
  box(AOS_DISCARD_X, AOS_DISCARD_Z)      -- above the banished dice
  box(AOS_RIGHT - AOS_COL, AOS_ROW1)     -- Advanced Programs, for the finale
  box(AOS_RIGHT, AOS_ROW1)               -- what a tier deals face-up
  for k = 1, AOS_MATS do box(aosMid(k, AOS_MATS), AOS_ROW2) end
  box(AOS_TECH_X, AOS_ROW3)              -- Programs finished with
  for k = 1, AOS_BACKDOORS do box(aosMid(k, AOS_BACKDOORS), AOS_ROW3) end
  box(AOS_RIGHT, AOS_ROW3)               -- banished dice
  return out
end

function aosSnaps()
  local pts = {}
  for _, b in ipairs(aosBoxes()) do
    table.insert(pts, {position = {b.x, 1.0, b.z},
                       rotation = {0, 0, 0}, rotation_snap = false})
  end
  local ok = pcall(function() Global.setSnapPoints(pts) end)
  if not ok then say('Snap points are not available in this build.') end
  return pts
end

-- Every space NAP wants, in one call: setSnapPoints REPLACES the lot.
function napSnaps(rows, z0, gap)
  local pts = {}
  -- The two cards revealed off the top of the Assignment deck, beside it.
  for k = 1, REVEAL_SLOTS do
    snapAt(pts, DECK_X + k * ASSIGN_PITCH, ROW_CHAR)
  end
  -- Four Assignment spaces beside each Time Slot.
  for r = 0, rows - 1 do
    for k = 1, ASSIGN_SLOTS do
      snapAt(pts, ASSIGN_X + k * ASSIGN_PITCH, z0 - r * gap)
    end
  end
  -- THE CHIP'S CIRCLE BESIDE EACH TIME SLOT. The dial is the one
  -- thing on this table that moves every slot, and it was the one
  -- thing with nowhere to land: the mat has painted these three
  -- circles since make_template.py learned where the Chip goes, and
  -- they had no snap under them. CHIP_X is where the setup already
  -- puts it on Day 1, so the Morning circle is the one it starts in.
  for r = 0, rows - 1 do
    snapAt(pts, CHIP_X, z0 - r * gap)
  end
  -- The Assignment you did not take, beyond the two you revealed.
  snapAt(pts, NAP_DISCARD_X, ROW_CHAR)
  -- The Apprentice in its corner, and the FINF cards at the head of
  -- the right-hand column. Both were dealt onto bare felt - the mat
  -- draws a box for every snap point NAP makes, so no snap meant no
  -- box and nothing to line a card up against.
  snapAt(pts, NAP_CHAR_X, ROW_CHAR)
  snapAt(pts, NAP_X, z0)
  -- The discard pile for completed Assignments, under the FINF card.
  snapAt(pts, PILE_X, z0 - gap)
  -- AND THE COMPLETED OPPORTUNITIES UNDER THAT, ALWAYS. This space
  -- was made at Tier III only, back when the mat called it Devious
  -- Opportunities and those were the only cards anyone banked - but
  -- a completed Opportunity is kept in front of you in EVERY game,
  -- the Devious six only replace the base six at Tier III, and the
  -- box is printed at every tier regardless. Three quarters of the
  -- time the table showed a space that nothing would snap to.
  snapAt(pts, PILE_X, z0 - 2 * gap)
  local ok = pcall(function() Global.setSnapPoints(pts) end)
  if not ok then say('Snap points are not available in this build.') end
  return pts
end

function clearSnaps()
  pcall(function() Global.setSnapPoints({}) end)
end

-- Which deck a game's character comes from, and how many are dealt. BAT
-- is not here: all four Lab Rats stay in play, so there is nothing to
-- choose between them.
CHAR_DECK = { NAP = 'Apprentices', AoS = 'Technicians',
              IMP = 'Imposters (A / B)' }

-- WHO IS ON EACH OF THOSE CARDS. All three decks are two-sided, so
-- three cards are six characters and five are ten; these tables are
-- generated by build_mod.py out of the generator scripts, which is
-- what stops the panel naming someone who is on the other side of a
-- different card.
CHAR_LIST = { NAP = APPRENTICE, AoS = TECHNICIAN, IMP = IMPOSTER }
-- What the button calls them, which is not the deck's name.
CHAR_WORD = { NAP = 'Apprentice', AoS = 'Technician', IMP = 'Imposter' }

function charOf(game)
  local t = CHAR_LIST[game]
  return t and t[STATE.pick[game] or 1] or nil
end

-- Keep the nth character and send the rest home. The side is still
-- yours to pick: every one of these cards is two characters, and
-- flipping it is the one part of setup a script should not do for you.
-- NAP's second dial, dealt. rules/nap.html: Increase shuffles that many
-- of the 3 FINF cards INTO the Assignment deck, where they share its
-- back and stay hidden until drawn; Reduce lays them face-up beside the
-- table to spend. One setting, chosen before the game and kept.
--
-- CALLED BEFORE THE DECK IS SHUFFLED, which is the whole reason it is a
-- step of its own rather than part of the Time Slot step that used to
-- deal one FINF card at random.
function finfOut(asg)
  local set = FINF_SET[STATE.finf] or FINF_SET[4]
  local n = set[2]
  local d = deckOut('FINF', OFF, FACEUP)
  if not d then return end
  d.shuffle()
  if set[1] == 'Increase' then
    moveN(d, asg, n)
    return
  end
  -- TAKE THE ONES WANTED, not the ones not wanted. Taking cards off a
  -- three card deck until one is left takes the last card out of a
  -- deck of one, which is taking a card out of a card; this way the
  -- deck is never emptied and the remainder goes back whole.
  if n >= count(d) then
    d.setPosition({NAP_X, 3, FINF_Z})
    d.setRotation(FACEUP)
    return
  end
  if n == 1 then
    d.takeObject({position = {NAP_X, 3, FINF_Z}, rotation = FACEUP,
                  smooth = false})
    putHome(d)
    return
  end
  -- TWO OF THREE: take the odd one out and leave the rest standing.
  -- Building the stack the other way round - taking the two wanted and
  -- putting one into the other - makes a deck out of a card, which TTS
  -- allows and the harness does not have to.
  for _ = 1, count(d) - n do
    d.takeObject({position = OFF, smooth = false,
                  callback_function = function(o) putHome(o) end})
  end
  d.setPosition({NAP_X, 3, FINF_Z})
  d.setRotation(FACEUP)
end

-- The FINF setting, applied to a table that is already dealt.
--
-- The button only appears once NAP is on the table, so pressing it has
-- to move cards rather than set a number for a later setup to read:
-- take back whatever the last setting put out - off the FINF space AND
-- out of the Assignment deck, because Increase hides them in there -
-- and then deal the new setting into the deck as it now stands.
function finfApply()
  if STATE.game ~= 'NAP' then return false end
  local asg = nil
  for _, o in ipairs(getAllObjects()) do
    if deckLabel(o.getName()) == 'Assignment'
        and (asg == nil or count(o) > count(asg)) then
      asg = o
    end
  end
  if asg then
    local strays = {}
    -- contents(), because the Assignment deck can be down to its
    -- last card by the end of a game, and a deck of one is a card.
    for _, e in ipairs(contents(asg) or {}) do
      if deckLabel(e.nickname) == 'FINF' then table.insert(strays, e.guid) end
    end
    for _, g in ipairs(strays) do
      -- OUT ONTO THE TABLE, not home: deckOut gathers them from there
      -- in a moment, and a trip through the bag is a trip something
      -- can refuse.
      if count(asg) > 1 then
        asg.takeObject({guid = g, position = OFF, smooth = false})
      end
    end
  end
  Wait.frames(function()
    finfOut(asg)
    Wait.frames(function()
      -- A card shuffled into a deck you are already drawing from has
      -- to be lost in it, which the setup gets for free by dealing
      -- FINF before it shuffles.
      if asg and FINF_SET[STATE.finf][1] == 'Increase' then asg.shuffle() end
    end, 10)
  end, 10)
  return true
end

-- The chosen Apprentice, on the table, the right way up.
--
-- SIX CHARACTERS ON THREE CARDS, so a choice is a card AND a side, and
-- APPRENTICE is generated from build_nap.py's own APPS table rather
-- than copied here. Pressing the button again has to put back the one
-- that is out before it can deal another, which is why the stack comes
-- out with takeWhole: deckOut alone would find a deck of two.
function showChar(game)
  local a = charOf(game)
  local label = CHAR_DECK[game]
  if not a or not label or STATE.game ~= game then return end
  local one = CARD_NAME[label] or label
  for _, o in ipairs(getAllObjects()) do
    local n = o.getName() or ''
    if n == label or isCardOf(n, one) then putHome(o) end
  end
  Wait.frames(function()
    local d = deckOut(label, OFF, FACEUP)
    if not d then say('No ' .. label .. ' to deal.') return end
    local home = CHAR_HOME[game]
    local rot = a.back and FACEDOWN or FACEUP
    if count(d) <= 1 then
      d.setPosition({home[1], 3, home[2]})
      d.setRotation(rot)
      altFaceLater(d)
      return
    end
    local want = one .. ' ' .. a.card
    for _, e in ipairs(d.getObjects()) do
      if e.nickname == want then
        altFaceLater(d.takeObject({
          guid = e.guid, position = {home[1], 3, home[2]},
          rotation = rot, smooth = false}))
        putHome(d)
        return
      end
    end
    say('There is no ' .. want .. ' in that stack.')
  end, 6)
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
--
-- ONE PASS IS NOT ENOUGH. TTS drops objects fed to a bag faster than it
-- can animate them, and a single pass over twenty of them left exactly
-- one card on the table after every setup: the Opportunist after NAP, the
-- Technician and an element mat after AoS, an Imposter after the finale.
-- Nothing in the arithmetic was wrong - the putObject simply did not take.
-- So sweep repeatedly, a few frames apart, and if anything is STILL out
-- after the last pass, name it rather than leaving it lying there.
function packUp(quiet)
  QUEUE = {}
  clearSnaps()
  local function loose()
    local t = {}
    for _, o in ipairs(getAllObjects()) do
      -- A MARKER IS SENT HOME, NOT BAGGED. The Chip and the Dial have
      -- a box each - that is how a setup stows the face its game does
      -- not read - but Pack up's job is to put them back in the row
      -- at the bottom of the table, which markersHome has already
      -- done by the time these passes run.
      local b = packable(o)
      if b and o ~= b then table.insert(t, o) end
    end
    return t
  end
  -- A FEW AT A TIME, AND LOOK AGAIN. Four passes that each handed the bag
  -- everything still out was not enough: TTS keeps only some of what it
  -- is given in a frame, and twenty at once still lost one. Each step now
  -- takes a fresh look and posts at most four, so whatever did not take
  -- is simply picked up by the next step rather than being left.
  local function post()
    local t = loose()
    -- EIGHT AT A TIME, not four. Each pass looks again, so a refused
    -- put is simply retried by the next one; the only thing a small
    -- batch bought was more passes to get through the same cards.
    for i = 1, math.min(8, #t) do
      local o = t[i]
      o.setLock(false)
      nameIt(o)
      local b = boxFor(o)
      if b then b.putObject(o) end
    end
  end
  -- TWENTY PASSES, NOT TEN. With the bag refusing roughly one put in
  -- three - which is what TTS does under load - ten passes still left a
  -- card out often enough for the harness to notice. A pass that finds
  -- nothing costs a few frames and nothing else.
  step(markersHome)
  step(unmix)
  for _ = 1, 20 do step(post) end
  step(function()
    local left = {}
    for _, o in ipairs(getAllObjects()) do
      if packable(o) then
        -- A pile has no name of its own; say what is in it rather
        -- than printing an empty string.
        local n = o.getName()
        if n == nil or n == '' then
          n = 'a pile of ' .. (firstCard(o) or 'cards')
        end
        table.insert(left, n)
      end
    end
    -- Only a real Pack up clears the game: a setup calls this first and
    -- has already said which game it is dealing.
    if not quiet then
      STATE.game = nil
      STATE.finale = false
      resetCounters()
      refreshPanel()
    end
    if #left > 0 then
      say('Still on the table: ' .. table.concat(left, ', ') ..
          ' - press Pack up again.')
    elseif not quiet then
      say('Everything back in its bag.')
    end
  end)
end

-- ----------------------------------------------------------------- setups
function setupBAT()
  packUp(true)
  STATE.game = 'BAT'
  STATE.finale = false
  local spec, hp = BAT_DIFF[STATE.difficulty][1], BAT_DIFF[STATE.difficulty][2]
  local upg, sp

  -- THE OVERLAY FIRST, so everything else lands on top of it.
  step(function() tableOut(BAT_TABLE) stowFaces('BAT') end)
  step(function()
    -- A COLUMN, NOT A ROW. The four Rats run down the left-hand side
    -- with their Upgrade spaces beside them, which is how Jon laid the
    -- table out; they used to be a row across the top with nothing to
    -- put beside them.
    column(deckOut('Lab Rats (A / B)', {BAT_RAT_X, 3, batRatZ(1)}, FACEUP),
           4, BAT_RAT_X, batRatZ(1), FACEUP, BAT_ROW_PITCH)
    batSnaps()
  end)
  step(function()
    local exp = deckOut('Encounters',
                        {batRightX(BAT_EXPERIMENTS), 3, batRowZ(1)})
    if exp then exp.shuffle() end
    -- THE TYRANT'S OWN CARDS STAY IN THE BAG. Nothing draws a Tyrant
    -- Attack until it is awake, five Splices away, and the Buff HP
    -- card is optional and holds part of its Health - so both belong
    -- to the battle rather than to the Splice Phase, and the row they
    -- were taking up is the row the Splice Phase is played on.
    upg = deckOut('Upgrades',
                  {batRightX(BAT_UPGRADE_DECK), 3, batRowZ(1)})
    sp = deckOut('Specimens', pad(4))
  end)

  -- TIER II REMOVES SIX **ORDINARY** UPGRADES, and says so by NAME.
  -- Taking six off the top removes ordinary cards only while the
  -- Specimens happen to be elsewhere in the deck, which is an assumption
  -- about deck order that nothing here enforces - and the claim that this
  -- step must precede the Specimen mix rested on it. Named, it cannot eat
  -- a Specimen whatever order the steps run in.
  if STATE.tier >= 2 then
    step(function()
      -- BY THE CARD'S OWN NAME, which is not the deck's: one of
      -- Upgrades is an Upgrade. Matching 'Upgrades ' removed nothing
      -- at all, and Tier II quietly added six Modifications to a full
      -- deck instead of swapping them in.
      local pre = (CARD_NAME['Upgrades'] or 'Upgrades') .. ' '
      local n = 0
      for _, e in ipairs(upg and upg.getObjects() or {}) do
        if n < 6 and string.sub(e.nickname, 1, #pre) == pre then
          dropCard(upg, e.nickname)
          n = n + 1
        end
      end
    end)
    step(function() merge(upg, deckOut('Unauthorized Modifications', pad(1))) end)
  end

  step(function() moveN(sp, upg, spec) end)
  step(function() if upg then upg.shuffle() end end)

  if STATE.tier >= 1 then
    step(function()
      drawOne('Experimental Protocols',
              {batRightX(BAT_PROTOCOL), 3, batRowZ(1)}, FACEUP)
    end)
  end
  if STATE.tier >= 3 then
    step(function()
      deckOut('Research Notes', {batRightX(BAT_NOTES), 3, batRowZ(1)}, FACEUP)
    end)
  end

  step(function()
    -- THE DIAL IS THE TYRANT'S HEALTH (rules/bat.html's components),
    -- so it goes where the Tyrant's cards are - below the rightmost
    -- Splice - turned to the Health this difficulty gives it.
    --
    -- AN OBJECT OF ITS OWN, in the BAT bag, dealt like the overlay.
    -- It was the Chip's other face for a while; two objects cost one
    -- more thing to pack away and save everything else, because no
    -- game reads both.
    -- MOVED, NOT DEALT. The Dial lies on the table beside the Chip
    -- the whole time, so a setup turns it to this difficulty's Health
    -- and slides it under the Splices; Pack up slides it back.
    setMarker('Dial', BAT_CHIP_X, BAT_CHIP_Z, nil,
              {CHIP_DIAL[hp] or CHIP_DIAL[0], 0})
    STATE.dial = hp
    readoutOut(hp)
  end)

  step(function()
    -- THE RECOVERY DIE MARKS THE ACTIVE RAT, and the first Rat is
    -- the one that starts. No value is set: it is a marker here, not
    -- a number, and a die turned to a face would read as one.
    -- ONTO THE CARD, not to the height of bare felt. Both of these
    -- stand on a Lab Rat; see dropOnto.
    setMarker('Recovery', batMarkX(), batMarkZ(1), nil, nil, ONTO)
    -- "...and the Red die on a random Rat" - rules/bat.html's setup,
    -- which until now the script only said in words.
    setMarker('Red', batMarkX(), batRedZ(math.random(BAT_ROWS)), nil, nil,
              ONTO)
    -- AND THE TWO DICE WITH NO JOB IN THEIR OWN COLUMN, beside the
    -- exhausted corner: Health and Strategy, now that Recovery is the
    -- active-Rat mark. No value is set on either, because a Rat's
    -- Health and STR are printed on its own card and the Tyrant's
    -- Health is on the dial - a die turned to a number here would be
    -- claiming to track something.
    setMarker('Health', BAT_STAT_X, BAT_STAT_Z[1])
    setMarker('Strategy', BAT_STAT_X, BAT_STAT_Z[2])
    batRatDice()
  end)

  step(function()
    STATE.splices = 0
    refreshPanel()
    say('BAT ready -- ' .. STATE.difficulty .. '. Tyrant Health ' .. hp ..
        ' (Health dial), ' .. spec ..
        ' Specimens shuffled into the Upgrade deck. Four Lab Rats are out' ..
        ' with a Purple, Blue, Green and Yellow die under each and the Red' ..
        ' die on a random one -- pick a side for each Rat. Five Splices' ..
        ' awaken the Tyrant, and its six dice come off these rows.' ..
        (STATE.tier >= 1 and ' TIER I: your Experimental Protocol is face-up.' or '') ..
        (STATE.tier >= 2 and ' TIER II: 6 ordinary Upgrades out, the 6 Modifications in.' or '') ..
        (STATE.tier >= 3 and (' TIER III: the 6 Research Notes are a face-up' ..
         ' stack on their space -- spread it to read them.') or '') ..
        ' The Tyrant Attacks and the Buff HP card stay in the bag until' ..
        ' the Tyrant wakes; the Buff HP card is optional, and holds part' ..
        ' of the Health at the FRONT of the Tyrant track, ahead of the' ..
        ' Splices, so it has to come off before any of them.')
  end)
  run()
end

function setupNAP()
  packUp(true)
  STATE.game = 'NAP'
  STATE.finale = false
  local goal, sb = NAP_DIFF[STATE.difficulty][1], NAP_DIFF[STATE.difficulty][2]
  -- TIER I IS ONE FOR ONE: three Following Setbacks in, three base ones
  -- out, so the deck still holds the number the difficulty asks for. The
  -- 4-for-3 swap it used to do HANDED a Setback back at Hard and Nobulous,
  -- which made the tier easier than no module at all (fixed 2026-11-07).
  local base = (STATE.tier >= 1) and (sb - 3) or sb
  local asg

  -- The table overlay first, so everything else lands on top of it.
  step(function() tableOut(NAP_TABLE) stowFaces('NAP') end)
  step(function()
    -- ONE STACK. Keep 1 / 2 / 3 takes the one you want out of it and
    -- sends the rest back, so there is no reason to spread three cards
    -- across the table first.
    deckOut('Apprentices', {NAP_CHAR_X, 3, ROW_CHAR}, FACEUP)
    asg = deckOut('Assignment', {DECK_X, 3, ROW_CHAR})
  end)

  if STATE.tier >= 2 then
    -- Each Imposter Task REPLACES a Credit Task of the same subject.
    -- NAP_CREDIT is generated from build_nap.py: the 20 Tasks that carry a
    -- subject are the Credit Tasks, five per subject, and the other six
    -- carry none.
    step(function()
      for _, idx in pairs(NAP_CREDIT) do
        local pick = shuffled(idx)[1]
        dropCard(asg, (CARD_NAME['Assignment'] or 'Assignment') .. ' ' .. pick)
      end
    end)
    step(function() merge(asg, deckOut('Imposter Tasks', pad(2))) end)
  end

  step(function()
    -- TIER III replaces the base Opportunities outright.
    local opps = (STATE.tier >= 3) and 'Devious Opportunities' or 'Opportunities'
    merge(asg, deckOut(opps, pad(1)))
  end)
  step(function() moveN(deckOut('Setbacks', pad(3)), asg, base) end)
  if STATE.tier >= 1 then
    step(function() moveN(deckOut('Following Setbacks', pad(4)), asg, 3) end)
  end
  -- BEFORE THE SHUFFLE. On Increase the FINF cards go into this deck
  -- and have to be lost in it.
  step(function() finfOut(asg) end)
  step(function() if asg then asg.shuffle() end end)

  step(function()
    -- Morning is the active Time Slot for Day 1; the other two sit beside
    -- it. One row, one landscape card plus a margin apart - these used to
    -- be dealt 7 apart, which is less than a card now, so they overlapped.
    -- The Time Slots are a column UNDER THE ASSIGNMENT DECK, in their
    -- own order, because they are a clock and not a hand: Morning at
    -- the top.
    column(deckOut('Time Slots', {ASSIGN_X, 3, FINF_Z}, FACEUP),
           3, ASSIGN_X, FINF_Z, FACEUP, NAP_GAP)
    napSnaps(3, FINF_Z, NAP_GAP)
    -- LOCKED ONCE THEY HAVE LANDED. The clock is the one thing on this
    -- table that never moves, and three cards that cannot be nudged
    -- are three cards an Assignment cannot be dropped on top of by
    -- accident. snapFirst still re-places the first of them four
    -- frames from now, so the lock waits for that.
    Wait.time(function()
      for _, o in ipairs(getAllObjects()) do
        local n = o.getName() or ''
        if n:sub(1, 9) == 'Time Slot' then o.setLock(true) end
      end
    end, 0.9)
    -- A readout over each pile, in the gap above it.
    counterOut(CREDIT_PILE, ROW_CHAR - 2 * NAP_GAP + COUNTER_LIFT)
    counterOut(BANK_PILE, ROW_CHAR - 3 * NAP_GAP + COUNTER_LIFT)
  end)

  step(function()
    -- The Chip to the circle beside Morning, reading 1; the three
    -- dice in a row centred under the Apprentice, at the 2s its own
    -- card prints.
    -- TURNED TO 1 THE WAY TYPING 1 TURNS IT, colour side up, through
    -- the CHIP_FACE table that was calibrated at the table. It used to
    -- use CHIP_NUM - the number side - which is a different face and a
    -- different set of angles, so the dial the setup laid down and the
    -- dial you typed over did not agree.
    setMarker('Chip', CHIP_X, ROW_CHAR - NAP_GAP, nil,
              {CHIP_FACE[ATTENTION[1]], CHIP_FACE_Z})
    STATE.chip = 1
    local sx = statRow(NAP_CHAR_X)
    setMarker('Health', sx[1], STAT_Z, NAP_START)
    setMarker('Strategy', sx[2], STAT_Z, NAP_START)
    setMarker('Recovery', sx[3], STAT_Z, NAP_START)
  end)
  -- THE PANEL'S CHOICE, DEALT. The stack came out a step ago; this
  -- leaves the one the Apprentice button is showing on the table and
  -- sends the other two back, so the panel and the felt agree.
  step(function() showChar('NAP') end)
  step(function()
    STATE.credits = 0
    refreshCounts()
    refreshPanel()
    say('NAP ready -- ' .. STATE.difficulty .. '. ' .. goal ..
        ' Credits reaches the Final Exam. The Assignment deck is built and' ..
        ' shuffled: 26 Tasks + 6 Opportunities + ' .. sb .. ' Setbacks' ..
        (STATE.tier >= 1 and (' (3 Following and ' .. base .. ' base)') or '') ..
        '. ' .. charOf('NAP').name ..
        ' is out at 2 HP / 2 STR / 2 REC -- press Apprentice for another.' ..
        ' Take all 17 dice and work the Morning Time Slot first.' ..
        ' The Final Exams stay in the bag until you reach them.' ..
        (STATE.tier >= 2 and ' TIER II: the 4 Imposter Tasks are in, and one Credit Task of each subject came out.' or '') ..
        ' Completed Assignments pile under the FINF card at End of Day.' ..
        (STATE.tier >= 3 and (' TIER III: the Devious Opportunities replaced the base' ..
         ' six, and four of them BANK - keep the card and spend it at the' ..
         ' Final Exam. The pile under the discard is for those.') or '') ..
        ' FINF ' .. FINF_SET[STATE.finf][1] .. ' ' .. FINF_SET[STATE.finf][2] ..
        (FINF_SET[STATE.finf][1] == 'Increase'
         and ' -- those cards are shuffled into the Assignment deck.'
         or ' -- those cards are face-up under the Apprentice, one use each.'))
  end)
  run()
end

function setupAoS()
  packUp(true)
  STATE.game = 'AoS'
  STATE.finale = false
  local mix = AOS_MIX[STATE.difficulty]
  local prog, lim

  -- The table overlay first, so everything else lands on
  -- top of it.
  step(function() tableOut(AOS_TABLE) stowFaces('AoS') end)

  step(function()
    -- ONE STACK ON THE TECHNICIAN'S SPACE, not three cards across the
    -- table: the layout has one space for the character and Keep 1/2/3
    -- takes the one you want out of the stack, the way NAP's
    -- Apprentices work.
    deckOut('Technicians', {AOS_TECH_X, 3, AOS_ROW1 + AOS_WIDE_LIFT}, FACEUP)
    aosSnaps()
    -- 2 HP / 2 STR / 3 REC, printed on every Technician card
    -- (generator/build_aos.py), in a row under it the way NAP's are.
    local sx = statRow(AOS_TECH_X)
    local sz = statZ(AOS_ROW1 + AOS_WIDE_LIFT)
    setMarker('Health', sx[1], sz, 2)
    setMarker('Strategy', sx[2], sz, 2)
    setMarker('Recovery', sx[3], sz, 3)
  end)
  -- The Program deck is the difficulty: a MIX of all three decks, not a
  -- choice between them. Routine can be 0 at Nobulous, which is why the
  -- deck the other two are merged into is whichever one survives.
  step(function()
    -- Specialized is 3 at every difficulty, so it is the only one of the
    -- three that can be cut without any risk of reaching a single card
    -- and going stale. The other two move INTO it.
    prog = cutTo(deckOut('Specialized Programs', pad(3)), mix[2])
    moveN(deckOut('Routine Programs', pad(1)), prog, mix[1])
    moveN(deckOut('Unstable Programs', pad(4)), prog, mix[3])
  end)
  step(function()
    if prog then
      prog.shuffle()
      prog.setPosition({aosCol(AOS_PROGRAMS), 3, AOS_ROW1})
      prog.setRotation(FACEDOWN)
    end
  end)
  step(function()
    lim = deckOut('Limitations', {aosCol(AOS_LIMITS), 3, AOS_ROW1})
    if STATE.tier >= 2 then merge(lim, deckOut('Corrupted Limitations', pad(2))) end
    if lim then lim.shuffle() end
    -- THE ADVANCED PROGRAMS STAY IN THE BAG. They are the endgame -
    -- three of the eight, after the third cycle - so nothing touches
    -- them for most of a game, and a deck on the table that nothing
    -- touches is a deck in the way. Their space is still drawn.
    spread(deckOut('Element Mats', {0, 3, AOS_ROW2}, FACEUP), AOS_MATS,
           AOS_ROW2, FACEUP, AOS_COL)
  end)
  if STATE.tier >= 1 then
    step(function()
      drawOne('Nobulous Interference', {AOS_RIGHT, 3, AOS_ROW1}, FACEUP)
    end)
  end
  if STATE.tier >= 3 then
    step(function()
      spread(deckOut('Backdoor Routines', {0, 3, AOS_ROW3}, FACEUP),
             AOS_BACKDOORS, AOS_ROW3, FACEUP, AOS_COL)
    end)
  end

  step(function() showChar('AoS') end)
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
  STATE.finale = false
  local t = IMP_TIRED[STATE.difficulty]
  local ex

  -- The table overlay first, so everything else lands on
  -- top of it.
  step(function() tableOut(IMP_TABLE) stowFaces('IMP') end)

  step(function()
    -- ONE STACK IN THE CORNER, where the other three games put their
    -- character, with the stat dice under it. Five Imposters spread
    -- across the top of the table took the whole row and four of them
    -- were going back in the bag the moment you chose.
    deckOut('Imposters (A / B)', {CHAR_X, 3, ROW_CHAR}, FACEUP)
    -- 5 HP / 2 STR / 3 REC, which is what this setup already says in
    -- words at the end of it.
    local sx = statRow(CHAR_X)
    local sz = statZ(ROW_CHAR)
    setMarker('Health', sx[1], sz, 5)
    setMarker('Strategy', sx[2], sz, 2)
    setMarker('Recovery', sx[3], sz, 3)
    ex = deckOut('Exhibits', {col(2), 3, ROW_MAIN})
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
      local one = CARD_NAME['Exhibits'] or 'Exhibits'
      for i = 1, 5 do keep[one .. ' ' .. idx[i]] = true end
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
    -- 10 apart, not the four-column pitch: Devious Opportunities is
    -- landscape and the other two are portrait, so the pitch that suits
    -- four portrait decks has them touching.
    deckOut('Research Notes', {-10.0, 3, ROW_SIDE}, FACEUP)
    deckOut('Devious Opportunities', {0.0, 3, ROW_SIDE}, FACEUP)
    deckOut('Backdoor Routines', {10.0, 3, ROW_SIDE}, FACEUP)
  end)

  step(function() showChar('IMP') end)
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


-- ------------------------------------------------------------ finales
-- EVERY GAME ENDS SOMEWHERE ITS SETUP CANNOT REACH. NAP sits a Final
-- Exam, BAT fights the Tyrant it spent the game building, AoS faces
-- three Advanced Programs. All three are REACHED - you play until the
-- trigger - so no setup can deal them, and until now the cards for all
-- three sat in their boxes with nothing on the table able to take them
-- out. IN_THE_BAG has said so in a comment since the day it was
-- written: "a later script option starts the exam".
--
-- THE SHAPE IS THE SAME THREE TIMES. Put away the spaces belonging to
-- the part of the game that is over, deal what the finale needs, and
-- say in chat the things the rules ask you to do by hand - which are
-- mostly dice, and dice are not something a script can sort out for
-- you once a game has been played over them.
--
-- ONTO BOXES THAT ALREADY EXIST. The overlay is a printed image, built
-- by make_template.py from batBoxes / aosBoxes / napSnaps when the mod
-- is built, so a finale space that is not one of those is a card lying
-- on bare felt with no outline and no snap. Every placement below
-- reuses a box that the Splice Phase, the day or the cycle has just
-- finished with.

-- IS THIS ONE OF THE GAME'S CARDS?
--
-- DECK_OF is generated from decks.py and holds every deck's label and
-- every card's own name, so a lookup in it is the question "is this a
-- card this mod prints" asked of the table that defines the answer.
--
-- NOT o.type. The first version of the sweep below took anything
-- whose type was Card or Deck, which in TTS spares the overlay
-- because a Custom_Tile is a Tile - and in the harness does not,
-- because every leaf object there answers "Card". It bagged the NAP
-- table: the mat is 56 units wide and lies at the middle of the felt,
-- so its CENTRE falls inside an Assignment space, and a sweep by
-- position finds it there. The overlay, the two counters and the
-- rulebooks are all outside DECK_OF, which is what makes this the
-- right question rather than a luckier one.
function isGameCard(o)
  if not o then return false end
  local base = (o.getName() or ''):gsub(' %d+$', '')
  return base ~= '' and DECK_OF[base] ~= nil
end

-- Clear these spaces into the boxes the cards came from.
function clearBoxes(boxes)
  for _, o in ipairs(getAllObjects()) do
    if isGameCard(o) and packable(o) then
      local p = o.getPosition()
      for _, b in ipairs(boxes) do
        if math.abs(p.x - b.x) <= b.hw and math.abs(p.z - b.z) <= b.hd then
          -- The Time Slots are locked when they are dealt, and a
          -- locked card cannot be put in a bag.
          o.setLock(false)
          putHome(o)
          break
        end
      end
    end
  end
end

-- ---------------------------------------------------------------- NAP
-- "Discard unresolved Assignments and exhaust their stored dice"
-- (rules/nap.html, Leaving the apprenticeship). The clock has stopped,
-- the deck is finished with either way - you sit the exam when you
-- reach your goal OR when the deck runs out - and FINF is explicitly
-- not used during the Final Exam, in either direction.
--
-- THE COMPLETED CREDITS PILE STAYS, and it is the one a tidy-up would
-- reach for first: it is face-up, it is finished with, and it is the
-- record of which subjects you studied. The exam pool is built out of
-- it. The Banked Opportunities stay too - a coupon has no expiry and
-- may be spent during the Final Exam.
function napExamBoxes()
  local out = {}
  local hw, hd = CARD_L / 2 - 0.15, CARD_W / 2 - 0.15
  local function box(x, z)
    table.insert(out, {x = x, z = z, hw = hw, hd = hd})
  end
  box(DECK_X, ROW_CHAR)                       -- the Assignment deck
  for k = 1, REVEAL_SLOTS do
    box(DECK_X + k * ASSIGN_PITCH, ROW_CHAR)  -- the two it revealed
  end
  box(NAP_DISCARD_X, ROW_CHAR)                -- the one you did not take
  box(NAP_X, FINF_Z)                          -- the FINF cards
  for r = 0, 2 do
    box(ASSIGN_X, FINF_Z - r * NAP_GAP)       -- the Time Slot itself
    for k = 1, ASSIGN_SLOTS do
      box(ASSIGN_X + k * ASSIGN_PITCH, FINF_Z - r * NAP_GAP)
    end
  end
  return out
end

-- "Randomly select 1 Final Exam card from each subject. Include each
-- subject even if you earned no Credits in it." ONE CARD PER SUBJECT
-- AS OF 2026-11-12, whatever the transcript looks like.
--
-- It used to be 1 card at 0-1 Credits in that subject, 2 at 2-3 and 3
-- at 4+, which stacked the pool with the subjects you had already
-- studied: the exams you were best prepared for were also the
-- likeliest to come up, and the Credit ladder pulled in the same
-- direction as the Target reduction it already pays for. The argument
-- for the old shape was that "a lopsided transcript is not safe, it is
-- just differently exposed", and it was the wrong way round - a
-- lopsided transcript made you SAFER, because it kept the subjects you
-- had neglected out of the pool.
--
-- The size is now a constant rather than a function of Credits, and
-- EXAM_POOL_PER_SUBJECT is the whole of it.
EXAM_POOL_PER_SUBJECT = 1

function examPoolSize(_credits)
  return EXAM_POOL_PER_SUBJECT
end

-- WHICH EXAMS YOU SIT, OUT OF WHAT YOU ACTUALLY STUDIED.
--
-- This was the player's job and it is the one piece of NAP setup that
-- cannot be done by eye: it needs the Credit pile counted by subject,
-- a per-subject roll against the table above, and then a draw out of
-- the cards those four rolls produced. Doing it by hand means doing
-- it after a day that has already gone badly.
--
-- Every subject puts in exactly one card, studied or not, so the pool
-- is 4 and you sit 3 of them: each subject has a 75% chance to appear
-- and can appear at most once. Credits do not decide WHICH exams you
-- sit any more, only how far their Targets come down.
--
-- It hands back the three nicknames, the pool size and the line that
-- explains them, because a pool built behind your back is a pool you
-- cannot check. The say() prints what each subject had and what it
-- bought.
function examDraw()
  local c = marker(CREDIT_PILE)
  local _, subj = creditTally(c and c.getGUID())
  local keys, pool, lines = {}, {}, {}
  for s in pairs(NAP_EXAM) do table.insert(keys, s) end
  table.sort(keys)
  for _, s in ipairs(keys) do
    local have = subj[s] or 0
    local n = examPoolSize(have)
    local pick = shuffled(NAP_EXAM[s])
    for i = 1, math.min(n, #pick) do
      table.insert(pool, (CARD_NAME['Final Exams'] or 'Final Exam')
                   .. ' ' .. pick[i])
    end
    table.insert(lines, (NAP_SUBJECT[s] or s) .. ' ' .. have
                 .. ' Credits, ' .. n .. ' card')
  end
  local draw = {}
  for i, nm in ipairs(shuffled(pool)) do
    if i <= EXAM_DRAW then draw[nm] = true end
  end
  return draw, pool, table.concat(lines, ', ')
end

function startExam()
  local goal = NAP_DIFF[STATE.difficulty][1]
  local exams, pool, line = nil, 0, ''
  step(function() clearBoxes(napExamBoxes()) end)
  step(function()
    local draw, cards
    draw, cards, line = examDraw()
    pool = #cards
    exams = deckOut('Final Exams', OFF, FACEDOWN)
    if not exams then
      say('No Final Exams in the NAP box.')
      return
    end
    -- THE DRAW IS WHAT IS LEFT IN THE DECK. Everything outside it goes
    -- home, which is nine cards however the pool came out, and leaves
    -- exactly EXAM_DRAW standing. Nothing is cut to one card on the
    -- way: the shortest this gets is four down to three.
    --
    -- The names are read off first and dropped afterwards, because
    -- dropCard takes a card OUT of the deck and getObjects() is a
    -- snapshot of what was in it.
    local gone = {}
    for _, e in ipairs(exams.getObjects()) do
      if not draw[e.nickname] then table.insert(gone, e.nickname) end
    end
    for _, nm in ipairs(gone) do dropCard(exams, nm) end
  end)
  step(function()
    if not exams then return end
    -- FROM THE LAST SPACE BACK TO THE SECOND, which leaves the deck's
    -- own final card standing on the first - the shape column() uses,
    -- and snapFirst is here for the same reason it is there: taking
    -- the second-to-last card destroys the deck and TTS respawns the
    -- last one near where the deck was rather than on it.
    exams.shuffle()
    local x1 = DECK_X + ASSIGN_PITCH
    exams.setPosition({x1, 3, ROW_CHAR})
    exams.setRotation(FACEUP)
    for k = EXAM_DRAW, 2, -1 do
      exams.takeObject({position = {DECK_X + k * ASSIGN_PITCH, 3, ROW_CHAR},
                        rotation = FACEUP, smooth = false})
    end
    snapFirst(CARD_NAME['Final Exams'] or 'Final Exam', x1, ROW_CHAR, FACEUP)
  end)
  step(function()
    say('FINAL EXAM. The Assignment deck, the Time Slots and FINF are' ..
        ' back in the box -- FINF is not used in the exam, in either' ..
        ' direction. The Completed Credits pile stays out: it is the' ..
        ' record of what you studied and the pool was built from it,' ..
        ' and so do your unspent coupons.' ..
        ' POOL, Credits->cards by subject: ' .. line .. ' = ' .. pool ..
        ' cards, of which ' .. EXAM_DRAW .. ' are drawn face-up on the' ..
        ' row above. BY HAND: discard unresolved Assignments and exhaust their' ..
        ' stored dice; short of ' .. goal .. ' Credits, exhaust 1' ..
        ' available die per missing Credit in the order Red, Purple,' ..
        ' Blue, Green, Yellow, looping as needed. Then recover 1 die,' ..
        ' 1 more per Credit ABOVE ' .. goal .. ' (never the same colour' ..
        ' twice), and the queued Morning recovery.' ..
        ' Each exam Target drops by 1 per Credit you hold in its' ..
        ' subject; lose 1 Health per success short; Special Recovery' ..
        ' uses that card own colour dot. All three are mandatory, and' ..
        ' finishing all three with at least 1 Health wins NAP.')
  end)
  run()
end

-- ---------------------------------------------------------------- BAT
-- The Splice Phase is over the moment the Tyrant has five Splices, so
-- everything the Splice Phase used goes away: both decks, the three
-- cards they reveal each turn and both discards. THE RATS KEEP THEIR
-- OWN UPGRADES - "Each Rat keeps its own Health and its own Upgrades"
-- - so the twelve spaces beside the Rats are not touched, and neither
-- is the Splice row or anything a tier dealt.
function batBattleBoxes()
  local out = {}
  local function box(x, z)
    table.insert(out, {x = x, z = z, hw = BAT_BOX_HW, hd = BAT_BOX_HD})
  end
  box(batRightX(BAT_EXPERIMENTS), batRowZ(1))
  box(batRightX(BAT_UPGRADE_DECK), batRowZ(1))
  for k = 1, 3 do box(batRightX(k), batRowZ(2)) end
  box(batRightX(BAT_EXP_DISCARD), batRowZ(2))
  box(batRightX(BAT_UPG_DISCARD), batRowZ(2))
  return out
end

-- "From left to right, place the five Tyrant Splices in a random
-- order." They are on the track in the order you failed in, which is
-- an order - just not a random one, and it is the order damage has to
-- chew through.
function shuffleSplices()
  local xs, found = {}, {}
  for k = 1, BAT_SPLICES do xs[k] = batRightX(k) end
  for _, o in ipairs(getAllObjects()) do
    if isGameCard(o) and packable(o) then
      local p = o.getPosition()
      if math.abs(p.z - batRowZ(4)) <= BAT_BOX_HD then
        for k = 1, BAT_SPLICES do
          if math.abs(p.x - xs[k]) <= BAT_BOX_HW then
            table.insert(found, o)
            break
          end
        end
      end
    end
  end
  local order = shuffled(xs)
  for i, o in ipairs(found) do
    if order[i] then
      o.setLock(false)
      o.setPositionSmooth({order[i], 1.6, batRowZ(4)}, false, true)
    end
  end
  return #found
end

function startBattle()
  local hp = BAT_DIFF[STATE.difficulty][2]
  local spliced = 0
  local buffCard = nil
  step(function() clearBoxes(batBattleBoxes()) end)
  step(function()
    -- "Shuffle the 7 Tyrant Attack cards face-down, then flip the top
    -- card face-up to start the Attack discard. It does not attack; it
    -- only supplies the first commit color."
    local d = deckOut('Tyrant Attacks',
                      {batRightX(BAT_ATTACK_DECK), 3, batRowZ(3)})
    if not d then say('No Tyrant Attacks in the BAT box.') return end
    d.shuffle()
    d.takeObject({position = {batRightX(BAT_ATTACK_UP), 3, batRowZ(3)},
                  rotation = FACEUP, smooth = false})
  end)
  step(function() spliced = shuffleSplices() end)
  step(function()
    -- THE BUFF HP CARD COMES OUT, because it is the Tyrant's outer
    -- layer and the layer is part of the track whether or not this
    -- difficulty gives it a value. It used to stay in the box and
    -- the briefing called it optional; Jon wants the battle to set
    -- it up, so the Tyrant is a thing on the table rather than a
    -- number in a sentence.
    --
    -- THE DIE GOES ON THE LAYER, NOT ON THE CORE HEALTH. It used to
    -- stand on the core number with the dial reading the same, which
    -- printed the Tyrant's Health twice and gave it twice as much as
    -- the table says. The two are independent stats - an outer layer
    -- and a core, with the five Splices between them - so the die
    -- shows the layer and the dial shows the core. At layer 0 there
    -- is nothing to stand on and the die stays where it is.
    --
    -- LOCKED. The card is furniture once it is down - a die is
    -- pushed along it - and a card that slides when you nudge the
    -- die is worse than no card. onObjectDrop locks it when a
    -- player puts it down, and nothing drops when the script deals
    -- it, so it is locked here.
    -- DEALT LOW, so there is barely any fall to wait out. Every
    -- other deal drops from y 3 and lets physics find the table,
    -- which is fine for a card nothing is about to be stood on.
    buffCard = deckOut('Buff HP Track',
                       {batRightX(BAT_BUFF), 1.2, batRowZ(3)}, FACEUP)
    -- AND THE DIAL, again. setupBAT turned it to the same number,
    -- but a Splice phase is long and the dial is a thing players
    -- turn; the battle is where the Health starts counting down, so
    -- it starts the battle reading what it should.
    setMarker('Dial', BAT_CHIP_X, BAT_CHIP_Z, nil,
              {CHIP_DIAL[hp] or CHIP_DIAL[0], 0})
    STATE.dial = hp
    readoutOut(hp)
  end)
  step(function()
    -- LOCKED ONLY ONCE IT HAS LANDED. Locking it in the step that
    -- dealt it froze it wherever it happened to be at that instant,
    -- which was still in the air - so the card hung above the table
    -- and the Health die went underneath it.
    if buffCard then buffCard.setLock(true) end
  end)
  step(function()
    -- THE DIE LAST, onto a card that has settled and been locked.
    -- Set to 1: the number that counts is the space it stands on,
    -- and a die showing anything else reads as a second number.
    local layer = BAT_DIFF[STATE.difficulty][3] or 0
    local bx, bz = buffSpace(layer)
    if layer > 0 and bx then setMarker('Health', bx, bz, 1, nil, ONTO) end
  end)
  step(function()
    say('TYRANT BATTLE. Tyrant Health ' .. hp .. ' on the dial. Both' ..
        ' decks, the three cards they reveal and both discards are back' ..
        ' in the box; the Rats keep their own Upgrades and their own' ..
        ' Health. The 7 Tyrant Attacks are shuffled with the top card' ..
        ' face-up -- it does not attack, it only sets the first commit' ..
        ' colour. ' .. spliced .. ' Splices put in a random order.' ..
        ' BY HAND: take 2 Purple, 2 Blue, 1 Green and 1 Yellow out of' ..
        ' the Rats own dice into a bag on the Tyrant Dice space -- the' ..
        ' Tyrant draws from those six fresh every round and they never' ..
        ' exhaust; if a colour is short, take it back out of the' ..
        ' banished pile. Sweep every other personal die, available and' ..
        ' exhausted, into one shared pool, all available; banished dice' ..
        ' stay gone and Red is not in the pool. Rat abilities are' ..
        ' silent in the battle. A Splice never chips: meet its printed' ..
        ' Value in ONE attack or the whole attack bounces. Eight rounds' ..
        ' to break five walls. The dial reads the Tyrant CORE Health,' ..
        ' ' .. hp .. ', which nothing can touch until the outer layer' ..
        ' and all five Splices are gone. The Buff HP card is out as' ..
        ' that outer layer, at ' ..
        ((BAT_DIFF[STATE.difficulty][3] or 0) > 0
          and ('' .. BAT_DIFF[STATE.difficulty][3] ..
               ' -- the Health die is standing on it.')
          or '0 at this difficulty -- put the Health die on the track' ..
             ' to give the Tyrant one.'))
  end)
  run()
end

-- ---------------------------------------------------------------- AoS
-- "After the third cycle -- or as soon as the deck is empty -- go to
-- Advanced Programming." What is left of the Program deck, the Program
-- on the table and both piles are finished with.
--
-- THE LIMITATIONS STAY. An Advanced Program is run by the ordinary
-- rule - "Reveal exactly 1 Limitation per Program", and the model runs
-- the finale through the same run_program - so the Limitation deck and
-- the card it has revealed are still in play. The element mats, the
-- Backdoor Routines and whatever a tier laid face-up all stay too.
function aosAdvancedBoxes()
  local out = {}
  local function box(x, z)
    table.insert(out, {x = x, z = z, hw = AOS_BOX_HW, hd = AOS_BOX_HD})
  end
  box(aosCol(AOS_PROGRAMS), AOS_ROW1)    -- whatever is left of the deck
  box(aosCol(AOS_PROGRAM), AOS_ROW1)     -- the Program it last revealed
  box(AOS_DISCARD_X, AOS_DISCARD_Z)      -- and the pile they go to
  box(AOS_TECH_X, AOS_ROW3)              -- Programs set aside for good
  return out
end

function startAdvanced()
  step(function() clearBoxes(aosAdvancedBoxes()) end)
  step(function()
    -- "Select 3 Advanced Programs." Eight are shuffled and set aside
    -- at setup and only three are ever faced; cutTo shuffles, keeps
    -- three and sends the other five back to the box. They go on the
    -- space the mat has always drawn for them.
    local d = cutTo(deckOut('Advanced Programs', pad(1)), 3)
    if not d then say('No Advanced Programs in the AoS box.') return end
    d.setPosition({AOS_RIGHT - AOS_COL, 3, AOS_ROW1})
    d.setRotation(FACEDOWN)
  end)
  step(function()
    say('ADVANCED PROGRAMMING. What is left of the Program deck, the' ..
        ' Program it last revealed and both piles are back in the box.' ..
        ' 3 of the 8 Advanced Programs are face-down on their own' ..
        ' space; the other 5 are back in the box. The Limitation deck' ..
        ' stays -- reveal exactly 1 per Program, as always. They are' ..
        ' longer, 4 or 5 elements, and carry 2 required-colour dots,' ..
        ' except Rapid Approach and Unobserved Entry, which carry 3.' ..
        ' Recover between them. The first begins Stable; each next one' ..
        ' begins Overheated if the one before ended in Catastrophic' ..
        ' Failure. Catastrophic Failure does not stop Advanced' ..
        ' Programming unless Health reaches 0. Work through all three' ..
        ' with at least 1 Health and you have won AoS, whether or not' ..
        ' you completed them.')
  end)
  run()
end

-- WHAT EACH GAME'S LAST BUTTON SAYS AND DOES. Below the functions,
-- because it holds references to them: a table built above them holds
-- three nils. The Imposter scenario has no entry - it IS the finale.
FINALE = {
  NAP = {'Start the Final Exam', startExam, {0.42, 0.25, 0.55}},
  BAT = {'Start the Tyrant Battle', startBattle, {0.17, 0.37, 0.29}},
  AoS = {'Start Advanced Programming', startAdvanced, {0.54, 0.24, 0.18}},
}

-- ONCE. Pressing it twice would deal a second set of Final Exams onto
-- the first and put the Tyrant's Attack deck back through a shuffle it
-- has already had, so the button goes once it has been used and comes
-- back with the next setup.
function btnFinale()
  local f = FINALE[STATE.game]
  if not f or STATE.finale then return end
  STATE.finale = true
  refreshPanel()
  f[2]()
end

-- ------------------------------------------------------------------ panel
-- THE TILE IS WIDE AND SHALLOW. ControlPanel.png is 1473x520 and the tile
-- is "Stretch": true, so the panel's local space is about x +/-2.6 by
-- z +/-1.0. Every row below lives inside that. The layout used to run from
-- z -4.3 to -0.6 in rows 0.9 apart, which put four of its five rows off
-- the top edge of the tile, hanging in the air.
-- WIDTH IS A HALF-EXTENT. A button's `width` and `height` are thousandths
-- of a local unit measured from its CENTRE, so width 1000 is two local
-- units across, not one. The first layout read them as full extents and
-- every button came out at twice its intended size: four setup buttons of
-- 1080 on a 1.15 pitch, which is 2.16 units of button in 1.15 units of
-- room. They overlapped in a row, and height 250 against a 0.40 row pitch
-- overlapped the rows as well.
--
-- So: half-width in local units = width / 1000, and the tile is 2.833 by
-- 1.0 (ControlPanel.png is 1473x520, stretched). One glyph is about
-- 0.00095 * font_size local units wide, which is what keeps a label inside
-- its own button. check_app_sync.py holds all three, and tts/test_setup.py
-- draws every panel state and fails on any two buttons that overlap.
PANEL_UNIT = 500          -- width units per local unit

function refreshPanel()
  -- THE BOOK ITSELF, NOT JUST ITS LABEL. The button has always named
  -- the game you set up, and clicking it loaded that game's PDF - so
  -- the corner showed whichever book was last CLICKED FOR, not the
  -- game on the table. Set up BAT after reading the NAP rules and the
  -- NAP rules stayed in the corner under a button reading "Rules: BAT",
  -- which is worse than no swap at all: the label says it is right.
  --
  -- showRules does nothing when the right book is already loaded, so
  -- this is one respawn on the setup that changes game and a no-op on
  -- every counter bump. No camera move - nobody asked to be flown to
  -- the corner because they pressed Set up.
  if STATE.game then showRules(STATE.game)
  elseif RULES_OBJ then drawRulesButton(RULES_OBJ) end
  if not PANEL then return end
  PANEL.clearButtons()
  local y = 0.2
  local function btn(label, fn, x, z, w, col, fs)
    PANEL.createButton({click_function = fn, function_owner = self, label = label,
      position = {x, y, z}, width = w or 660, height = 150, font_size = fs or 92,
      color = col or {0.16, 0.15, 0.13}, font_color = {1, 1, 1}})
  end
  -- FIVE ROWS AT A 0.36 PITCH, which is what a half-height of 0.15 allows
  -- inside a tile that is 1.0 deep from its middle. The tile art already
  -- prints THE NOBULOUS SET, so no row repeats it.
  btn('Set up BAT', 'btnBAT', -3.43, -0.72, 660, {0.17, 0.37, 0.29})
  btn('Set up NAP', 'btnNAP', -1.15, -0.72, 660, {0.42, 0.25, 0.55})
  btn('Set up AoS', 'btnAoS', 1.15, -0.72, 660, {0.54, 0.24, 0.18})
  btn('Imposter', 'btnIMP', 3.43, -0.72, 660, {0.29, 0.23, 0.42})

  -- THE READOUT IS THE BUTTON. A pale label beside a dark `cycle`
  -- button made you read two things to change one, and the pale half
  -- was the half that said what it was. Dark means clickable here, so
  -- these are dark.
  --
  -- The tier NAME lives in the setup message; the panel has room for
  -- its numeral and nothing more.
  -- SAME BUBBLE AS THE SETUP ROW: height 150 and font 92, like every
  -- other button on the mat. Only the width differs, because the text
  -- is longer - 'Difficulty  Nobulous' does not fit in 660.
  btn('Difficulty  ' .. STATE.difficulty, 'btnDiff', -2.60, -0.36, 1080)
  btn('NRJ Tier  ' .. (STATE.tier == 0 and 'off' or
      ({'I', 'II', 'III'})[STATE.tier]), 'btnTier', 0.50, -0.36, 820)

  -- THE MIDDLE ROW IS THE DEALT GAME'S OWN OPTIONS, and it is empty
  -- until a setup has run. These two move cards that are on the table,
  -- so there is nothing for them to do before there is a table; the
  -- difficulty and the tier stay in the row above, because those are
  -- read BY a setup and have to be set before one.
  --
  -- NOTHING COUNTS ON THIS PANEL ANY MORE. Splices, Credits, Backdoors
  -- and Session all sat here as a number and a +/-, which counted
  -- presses rather than what was on the table and sat at the far end of
  -- it from the thing being counted. bump() and resetCounters() are
  -- still here and still drive STATE, so a row can go back on a button
  -- or on a plate over the pile it describes - which is what the Credit
  -- Record above the Completed Credits pile already does.
  local g = STATE.game
  if CHAR_LIST[g] then
    btn(CHAR_WORD[g] .. '  ' .. charOf(g).name, 'btnChar', -2.44, 0.00, 1240)
  end
  if g == 'NAP' then
    btn('FINF  ' .. FINF_SET[STATE.finf][1] .. ' ' ..
        FINF_SET[STATE.finf][2], 'btnFinf', 0.70, 0.00, 940)
  end
  -- ONE WAY TO CHOOSE A CHARACTER, not two.
  --
  -- Keep 1/2/3 used to stand here beside the character button: it took
  -- a card out of the stack and left the side to you, which is a
  -- second way to choose that knows nothing about the first. Press it
  -- and the panel still named whoever the button last dealt, on a side
  -- nobody had chosen. NAP had already dropped it for exactly that
  -- reason; AoS and the Imposter scenario now have the same button
  -- NAP has, so the argument applies to them too and the row goes.
  --
  -- NOTHING ON THIS PANEL IS A LABEL. A pale strip reading "set up
  -- NAP, AoS or Imposter to choose a character" stood in this row
  -- whenever the game on the table had no character to cycle. Every
  -- other row is a thing you press, so a row you cannot press is a row
  -- you try to press - and it said nothing a player could not read off
  -- the four setup buttons an inch below it. lbl() went with it: the
  -- only thing on this mat is buttons.
  --
  -- WHAT STANDS HERE NOW IS THE LAST BUTTON OF A GAME: the Final Exam,
  -- the Tyrant Battle, Advanced Programming. In the game's own colour,
  -- because it belongs to that game and to no other, and only once
  -- there is a game on the table to finish.
  if FINALE[g] and not STATE.finale then
    btn(FINALE[g][1], 'btnFinale', -2.44, 0.36, 1240, FINALE[g][3])
  end


  btn('Pack up', 'btnPack', -3.80, 0.72, 420, {0.42, 0.18, 0.15})
end

function nop() end
function btnBAT() setupBAT() end
function btnNAP() setupNAP() end
function btnIMP() setupImposter() end
function btnAoS() setupAoS() end
function btnPack() packUp(false); run() end
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

-- THE ONE THAT ACTS AT ONCE. The difficulty, the tier and FINF all
-- change what a setup will deal; this changes what is on the table, so
-- it deals the card as well as recording the choice.
function btnChar()
  local game = STATE.game
  local t = CHAR_LIST[game]
  if not t then return end
  STATE.pick[game] = (STATE.pick[game] % #t) + 1
  refreshPanel()
  local a = charOf(game)
  showChar(game)
  say(CHAR_WORD[game] .. ': ' .. a.name .. ' -- card ' .. a.card .. ', ' ..
      (a.back and 'back' or 'front') .. ' side.')
end

-- IT ACTS AT ONCE TOO, now that it only appears once NAP is dealt.
-- It used to set a number for the next setup to read, which is how
-- Jon came to press Set up NAP a second time - and the second setup
-- was the thing that was broken.
function btnFinf()
  STATE.finf = (STATE.finf % #FINF_SET) + 1
  refreshPanel()
  local s = FINF_SET[STATE.finf]
  local many = s[2] > 1 and 's' or ''
  local live = finfApply()
  say('FINF: ' .. s[1] .. ' ' .. s[2] .. ' -- ' .. s[2] .. ' FINF card' ..
      many .. (s[1] == 'Increase' and ' shuffled into the Assignment deck.'
               or ' face-up to spend, one use each.') ..
      (live and '' or ' Press Set up NAP to deal it.'))
end

function splPlus() bump('splices', 1, 'Splices') end
function splMinus() bump('splices', -1, 'Splices') end
function crPlus() bump('credits', 1, 'Credits') end
function crMinus() bump('credits', -1, 'Credits') end
function bdPlus() bump('backdoors', 1, 'Backdoors claimed') end
function bdMinus() bump('backdoors', -1, 'Backdoors claimed') end
function atPlus() bump('session', 1, 'Session') end
function atMinus() bump('session', -1, 'Session') end

-- THE RAIL'S HEIGHT IS NOT IN THE SAVE. Three guesses buried the mat in
-- the woodwork and a fourth floated it above, so stop guessing: the mat
-- and the four boxes are built a little above the rail, unlocked here so
-- that gravity puts them on whatever surface is actually there, and
-- locked again where they land. They are locked in the save, so a player
-- who never reloads still cannot push them around.
function settle()
  local t = {PANEL}
  for _, g in pairs(BOX) do
    local o = getObjectFromGUID(g)
    if o then table.insert(t, o) end
  end
  -- THE RULEBOOK IS NOT SETTLED. It sits where Jon put it, in the
  -- corner off the felt, and dropping it to find a resting height
  -- would move it off that spot.
  for _, o in ipairs(t) do o.setLock(false) end
  Wait.time(function()
    for _, o in ipairs(t) do if o then o.setLock(true) end end
  end, 2.0)
end

-- WHERE THE DIAL'S ZERO IS IS A PROPERTY OF THE ART, and nothing in
-- here can know it: it was guessed twice and measured off a photograph
-- twice. So it is calibrated at the table instead. The panel carries a
-- +/- that turns the Chip and prints the offset; the number it settles
-- on goes into CHIP_TRIM in build_mod.py, which is where it belongs.
--
-- CHIP_SEGMENT, CHIP_TRIM and CHIP_FACE are all generated from there.
-- This is the same arithmetic as the generator's, so that moving the
-- control moves the dial to angles the save would also have produced -
-- test_setup.py checks that it reproduces the generated table exactly
-- at the generated trim.
function chipFaces()
  for c, a in pairs(CHIP_SEGMENT) do
    CHIP_FACE[c] = (360 - a + CHIP_TRIM) % 360
  end
  return CHIP_FACE
end

-- Turn the Chip to the colour of a typed number, keeping x and z so the
-- dial turns without flipping.
function turnChip(number)
  local col = ATTENTION[number]
  local o = marker('Chip')
  if not o or not col or not CHIP_FACE[col] then return nil end
  local r = o.getRotation()
  o.setRotationSmooth({r.x, CHIP_FACE[col], r.z})
  return col
end

-- THE DIAL IS SETTLED at CHIP_TRIM -17 and its buttons are off the
-- panel. These stay: they are how the next person re-measures it if
-- the art moves, and chipFaces() is what keeps the script's angles and
-- the save's rotation values the same five numbers. Put the two
-- buttons back beside Pack up to use them.
--
-- Three degrees a press, because that is the size the last correction
-- took. Wrapped into -180..180 so the readout stays a number you can
-- read out loud.
function trimBy(d)
  CHIP_TRIM = (CHIP_TRIM + d) % 360
  if CHIP_TRIM > 180 then CHIP_TRIM = CHIP_TRIM - 360 end
  chipFaces()
  local col = turnChip(STATE.chip)
  refreshPanel()
  say('Dial trim ' .. CHIP_TRIM .. ' degrees' ..
      (col and (' -- now showing ' .. col .. '.') or
       ' -- no Chip on the table to turn.'))
end

function trimPlus() trimBy(3) end
function trimMinus() trimBy(-3) end

-- ------------------------------------------------------------- the mat
-- THE FELT WAS MEASURED WITH THESE, and it came to 56.5 by 36.1 - see
-- FELT in build_mod.py, which everything on the table is now built
-- from. Nothing in here can measure a TTS table, so if the felt ever
-- needs re-measuring it is measured the same way: put the six buttons
-- back on the panel's middle row, size the mat until it covers the
-- table, read the numbers off and redraw the template to them.
--
-- Width and depth move independently, because one scale cannot fix a
-- mat that is short across and over along.
MAT_STEP = 0.5

function matSize()
  local o = marker(NAP_TABLE)
  if not o then return nil end
  local s = o.getScale()
  return o, 2 * MAT_ASPECT * s.x, 2 * s.z, o.getPosition().z
end

function matNudge(dw, dd, dz)
  local o, w, d, z = matSize()
  if not o then
    say('Set up NAP first -- the mat is in the NAP box.')
    return
  end
  local s = o.getScale()
  o.setLock(false)
  o.setScale({s.x + dw / (2 * MAT_ASPECT), s.y, s.z + dd / 2})
  local p = o.getPosition()
  o.setPosition({p.x, p.y, p.z + dz})
  o.setLock(true)
  refreshPanel()
  local _, w2, d2, z2 = matSize()
  say(string.format('Mat %.1f wide x %.1f deep, centre z %.2f.', w2, d2, z2))
end

function matWider() matNudge(MAT_STEP, 0, 0) end
function matNarrower() matNudge(-MAT_STEP, 0, 0) end
function matDeeper() matNudge(0, MAT_STEP, 0) end
function matShallower() matNudge(0, -MAT_STEP, 0) end
function matUp() matNudge(0, 0, MAT_STEP / 2) end
function matDown() matNudge(0, 0, -MAT_STEP / 2) end

-- ------------------------------------------------------- the pile counts
-- WHAT IS ACTUALLY ON THE PILE, not a number someone remembered to
-- press. Credits are earned by completing Credit Tasks (rules/nap.html)
-- and NAP_CREDIT - generated from build_nap.py - says which Task
-- numbers those are and which subject each belongs to. The six Tasks
-- that carry no subject earn nothing and are not counted.
--
-- The subject breakdown is not decoration: the Final Exam reduces its
-- target by one for every Credit you hold IN THAT SUBJECT, so it is the
-- number you need and the hardest one to get by eye off a face-up pile.
function cardsAt(x, z, r, skip)
  local out = {}
  for _, o in ipairs(getAllObjects()) do
    if o.getGUID() ~= skip then
      local p = o.getPosition()
      if math.abs(p.x - x) < r and math.abs(p.z - z) < r then
        local kids = contents(o)
        if kids and #kids > 0 then
          for _, e in ipairs(kids) do table.insert(out, e.nickname or '') end
        else
          table.insert(out, o.getName() or '')
        end
      end
    end
  end
  return out
end

-- Which subject a Task belongs to, or nil for the six that earn nothing.
function creditSubject(name)
  local n = tonumber(string.match(name or '', '^Task (%d+)$'))
  if not n then return nil end
  for s, list in pairs(NAP_CREDIT) do
    for _, i in ipairs(list) do
      if i == n then return s end
    end
  end
  return nil
end

function creditTally(skip)
  local subj, total = {}, 0
  for _, nm in ipairs(cardsAt(PILE_X, ROW_CHAR - 2 * NAP_GAP, 3.6, skip)) do
    local s = creditSubject(nm)
    if s then
      subj[s] = (subj[s] or 0) + 1
      total = total + 1
    end
  end
  return total, subj
end

function bankTally(skip)
  local names, n = {}, 0
  for _, nm in ipairs(cardsAt(PILE_X, ROW_CHAR - 3 * NAP_GAP, 3.6, skip)) do
    if string.match(nm, '^Devious Opportunity %d+$')
        or string.match(nm, '^Opportunity %d+$') then
      n = n + 1
      table.insert(names, nm)
    end
  end
  table.sort(names)
  return n, names
end

-- Sorted, because pairs() over a Lua table is in no order at all and a
-- breakdown that reshuffles itself every time you hover is unreadable.
function subjectLine(subj)
  local keys = {}
  for s in pairs(NAP_CREDIT) do table.insert(keys, s) end
  table.sort(keys)
  local parts = {}
  for _, s in ipairs(keys) do
    table.insert(parts, (NAP_SUBJECT[s] or s) .. '  ' .. (subj[s] or 0))
  end
  return table.concat(parts, '\n')
end

function refreshCounts()
  if STATE.game ~= 'NAP' then return end
  local goal = NAP_DIFF[STATE.difficulty][1]
  local c = marker(CREDIT_PILE)
  if c then
    local n, subj = creditTally(c.getGUID())
    STATE.credits = n
    c.TextTool.setValue('CREDITS  ' .. n .. ' / ' .. goal)
    c.setDescription('Credits by subject, which is what each Final Exam'
      .. ' reduces its target by:\n' .. subjectLine(subj)
      .. (n >= goal and '\n\nGoal reached -- sit the Final Exam.' or ''))
  end
  local b = marker(BANK_PILE)
  if b then
    local n, names = bankTally(b.getGUID())
    b.TextTool.setValue('BANKED  ' .. n)
    b.setDescription(n == 0 and 'Nothing banked yet.'
      or ('Banked here:\n' .. table.concat(names, '\n')))
  end
end

-- TTS calls this whenever anything is put down, which is the only
-- moment either pile can change. Cheap: it does nothing unless the card
-- landed near one of them.
function onObjectDrop(color, obj)
  if not obj then return end
  -- PICKED UP, TURNED OVER AND PUT DOWN is a flip no rotation event
  -- hears about: it is physics. Cheap - altFace leaves anything that
  -- is not a landscape card alone on its first line.
  altFace(obj)
  -- THE BUFF HP CARD IS FURNITURE ONCE IT IS DOWN. It holds part of
  -- the Tyrant's Health on a track you push a die along, so a card
  -- that slides when you nudge the die is worse than no card. It
  -- starts in the bag because it is optional; this locks it the moment
  -- it reaches its space, and right-click Unlock takes it away again.
  if STATE.game == 'BAT' and deckLabel(obj.getName()) == 'Buff HP Track' then
    local p = obj.getPosition()
    if math.abs(p.x - batRightX(BAT_BUFF)) < BAT_BOX_HW + 1.0
        and math.abs(p.z - batRowZ(3)) < BAT_BOX_HD + 1.0 then
      obj.setPosition({batRightX(BAT_BUFF), p.y, batRowZ(3)})
      obj.setLock(true)
      say('Buff HP card locked in place -- right-click it to unlock.')
    end
    return
  end
  if STATE.game ~= 'NAP' then return end
  local p = obj.getPosition()
  if math.abs(p.x - PILE_X) < 6.0 then refreshCounts() end
end

-- --------------------------------------------------- BAT's Health readout
-- THE DIAL IS EXACT AND UNREADABLE. Twenty-one numbers round the rim
-- of a disc is the right object for turning and the wrong one for
-- reading across a table, and the Tyrant's Health is the number both
-- players look at most. This is the same number once more in one big
-- figure, with a button either side.
--
-- ONE CALL WRITES BOTH, so they cannot drift: dialSet turns the Dial
-- and relabels the plate. Typing a number over the Dial goes through
-- the same call, which is why onObjectNumberTyped no longer ignores
-- it - TTS turns the disc itself from its RotationValues and this
-- only has to catch up the figure.
READOUT_NAME = 'Health Readout'
READOUT = nil
DIAL_MAX = 20

function readoutOut(n)
  local o = deckOut(READOUT_NAME, {BAT_READOUT_X, 1.2, BAT_READOUT_Z}, FACEUP)
  if o then
    READOUT = o
    o.setLock(true)
    drawReadout()
  end
  return o
end

function drawReadout()
  local o = READOUT
  if not o then return end
  o.clearButtons()
  -- THE TILE IS 2.31 LOCAL UNITS WIDE, which is DialPlate.png's
  -- aspect: x runs +/-1.154 and z +/-0.5. A button's width is in
  -- thousandths of a local unit measured from its CENTRE, so 340 is
  -- 0.34 either side.
  --
  -- THE ARROWS ARE AS BIG AS THE TILE ALLOWS. At 0.80 apart their
  -- half-widths of 0.34 leave 0.06 of clear tile against the
  -- number's 0.40, and their outer edges reach 1.14 of the 1.154
  -- there is. Anything larger either laps the number or hangs off
  -- the plate, and tts/test_setup.py fails on both.
  local function btn(label, fn, x, w, fs)
    o.createButton({click_function = fn, function_owner = self, label = label,
      position = {x, 0.3, 0}, width = w, height = 440, font_size = fs,
      color = {0.16, 0.15, 0.13}, font_color = {1, 1, 1},
      tooltip = 'The Tyrant' .. chr39 .. 's Health'})
  end
  btn('-', 'dialMinus', -0.80, 340, 330)
  btn(tostring(STATE.dial or 0), 'nop', 0, 400, 380)
  btn('+', 'dialPlus', 0.80, 340, 330)
end

-- Turn the Dial and write the figure. `turn` is false when TTS has
-- already turned the disc itself, which it does for a typed number.
function dialSet(n, turn)
  STATE.dial = math.max(0, math.min(DIAL_MAX, math.floor(n)))
  if turn ~= false then
    local d = marker('Dial')
    if d then d.setRotation({0, CHIP_DIAL[STATE.dial] or CHIP_DIAL[0], 0}) end
  end
  drawReadout()
  return STATE.dial
end

function dialPlus() dialSet((STATE.dial or 0) + 1) end
function dialMinus() dialSet((STATE.dial or 0) - 1) end

-- ---------------------------------------------------------- the rulebook
-- A Custom_PDF on the rail in the top right corner, carrying one button
-- that loads the rules for the game you have set up and flies your
-- camera to the page. TTS reads a PDF where it lies, so "open" is the
-- camera and the usual zoom, not a window.
--
-- FOUR BOOKS, NOT ONE BOOK THAT CHANGES.
--
-- It was one Custom_PDF and this swapped its URL with setCustomObject
-- and reload, which is the documented way to do it and did not work:
-- Jon's autosave after a NAP setup still held BAT_Rulebook.pdf as the
-- object's OWN url, so the call had not changed the object's data,
-- let alone failed to fetch a file. No Lua error in the chat, none in
-- Player.log, the right GUID, the right URL table - and the corner
-- went on showing the BAT rules under a button reading "Rules: NAP".
--
-- Each game's book is a component in that game's box now, and its
-- setup deals it to the rail. Taking a thing out of a bag and putting
-- it back is the one piece of machinery here that has never failed.
--
-- RULES_OBJ is whichever one is currently out; a Pack up leaves it
-- there, because the last thing a player wants after a game is for
-- the rules to go away.
RULES_OBJ = nil

function rulesLabel()
  local g = STATE.game
  if not g then return 'Rules: BAT' end
  return 'Rules: ' .. (g == 'IMP' and 'NRJ' or g)
end

-- Is this object one of the four books?
function isRulebook(o)
  if not o then return false end
  local n = o.getName() or ''
  for _, nick in pairs(RULES_NICK) do
    if n == nick then return true end
  end
  return false
end

function drawRulesButton(o)
  if not o then return end
  RULES_OBJ = o
  o.clearButtons()
  -- A NARROW STRIP ALONG THE BOTTOM EDGE, not the face. A button over
  -- the page would swallow the clicks TTS uses to zoom into it, which
  -- is how you actually read the thing.
  o.createButton({click_function = 'btnRules', function_owner = self,
    label = rulesLabel(), position = {0, 0.1, 1.18},
    width = 1500, height = 260, font_size = 160,
    color = {0.16, 0.15, 0.13}, font_color = {1, 1, 1},
    tooltip = 'Look at the rules for the game you set up'})
end

-- Put this game's book on the rail and the others away. Does nothing
-- when the right one is already standing there.
function showRules(game, who)
  local want = RULES_NICK[game]
  if not want then return nil end
  local out, others = nil, {}
  for _, o in ipairs(getAllObjects()) do
    if isRulebook(o) then
      if o.getName() == want then out = o else table.insert(others, o) end
    end
  end
  for _, o in ipairs(others) do
    o.setLock(false)
    putHome(o)
  end
  if not out then
    out = deckOut(want, RULES_POS, RULES_ROT)
    if not out then say('MISSING RULEBOOK: ' .. want) return nil end
    out.setLock(true)
  end
  STATE.rules = game
  drawRulesButton(out)
  if who and Player[who] then
    local p = out.getPosition()
    Player[who].lookAt({position = {p.x, p.y, p.z},
                        pitch = 70, yaw = 180, distance = 9})
  end
  return out
end

function btnRules(obj, color, alt)
  local g = STATE.game or 'BAT'
  if not showRules(g, color) then
    say('That rulebook is not in its box.')
    return
  end
  say((STATE.game and '' or 'No game set up, so these are the BAT rules. ')
      .. 'Zoom in to read, and scroll with the page arrows.')
end

-- TTS calls this when a player types a number with the cursor over an
-- object. Returning true says the script dealt with it.
-- ONE OBJECT, ONE WAY OF READING IT. The Chip shows colours and the
-- Dial shows 0 to 20, and no game uses both - NAP reads the attention
-- colours, BAT reads the Tyrant's Health - so nothing here has to work
-- out which way up anything is.
--
-- The Dial is not handled here at all: it carries its own
-- RotationValues, twenty-one of them, so typing a number at it is
-- TTS's job. This is only the Chip, whose five values TTS would
-- honour too, but this says which colour it turned to.
-- WHICH WAY UP THE ALT VIEW HOLDS THIS CARD.
--
-- A landscape card's preview is rolled 90 degrees one way when the
-- card is face up and 90 the other way when it is face down, so the
-- one angle baked into the save can only ever be right for one of
-- them: with the face-up angle, flipping a Lab Rat gave you side B
-- upside down. ALT_LOOK_UP and ALT_LOOK_DOWN are both generated by
-- build_mod.py and differ by exactly that 180.
--
-- ONLY LANDSCAPE CARDS. A portrait card has no angle at all - zero is
-- the default and the right answer - and giving one to everything is
-- how you turn a preview that works into one that does not.
function isLandCard(o)
  if not o or o.type ~= 'Card' then return false end
  local ok, d = pcall(function() return o.getData() end)
  return ok and d ~= nil and d.SidewaysCard == true
end

-- A VECTOR, NOT A TABLE OF THREE NUMBERS. Every rotation in this
-- script is a plain {x, y, z} and TTS takes them all, so the first
-- version of this assigned one here too and the preview did not
-- change. Every example of alt_view_angle anybody has published uses
-- Vector(), and one report has the plain form erroring outright from
-- the console. The named table is the fallback for a build with no
-- Vector in scope; the save writes that form, so it is known good.
function altVector(a)
  local ok, v = pcall(function() return Vector(a[1], a[2], a[3]) end)
  if ok and v then return v end
  return {x = a[1], y = a[2], z = a[3]}
end

-- WE NEVER LEARNED WHICH OF THE TWO FIXED IT.
--
-- The preview was wrong with a plain {x, y, z} assigned from
-- onObjectRotate alone, and right once it was a Vector assigned from
-- three triggers. Both changes went in together and the line that
-- would have told them apart was never read back, so NEITHER IS
-- KNOWN TO BE THE UNNECESSARY ONE. Taking out the Vector, or any one
-- of the three triggers, is an untested change to a thing that took
-- three attempts to get right.
function altFace(o)
  if not isLandCard(o) then return end
  local want = o.is_face_down and ALT_LOOK_DOWN or ALT_LOOK_UP
  pcall(function() o.alt_view_angle = altVector(want) end)
end

-- AFTER THE TURN, NOT DURING IT. onObjectRotate fires with the flip
-- the card is heading FOR, so is_face_down still reads the old side
-- while the handler runs; two frames later the card is where it is
-- going.
--
-- THREE WAYS TO TURN A CARD OVER, because onObjectRotate alone did
-- not do it at Jon's table. The docs say it is raised for a
-- deliberate rotation and not for physics, which leaves at least two
-- ways to flip a card that it may not cover: F is a player ACTION
-- (Player.Action.FlipOver, its own event), and picking a card up,
-- turning it and dropping it is physics. All three land here, and
-- altFace does nothing it has not been asked to do twice.
function onObjectRotate(obj, spin, flip, color, oldSpin, oldFlip)
  Wait.frames(function() altFace(obj) end, 2)
end

function onPlayerAction(player, action, targets)
  if action == Player.Action.FlipOver then
    for _, o in ipairs(targets or {}) do
      Wait.frames(function() altFace(o) end, 30)
    end
  end
  return true
end

-- AND WHEN THE SCRIPT ITSELF TURNS ONE OVER. showChar deals a
-- character card on whichever side was chosen, which is a flip the
-- player never made and onObjectRotate never hears about.
function altFaceLater(o)
  if o then Wait.frames(function() altFace(o) end, 30) end
end

function onObjectNumberTyped(obj, player_color, number)
  if not obj then return false end
  -- THE DIAL TURNS ITSELF - it carries twenty-one RotationValues, so
  -- TTS does the turning - but the figure beside it has to follow, or
  -- the table shows the Tyrant's Health twice and disagrees with
  -- itself. false says TTS still handles the turn.
  if obj.getName() == 'Dial' then
    dialSet(number, false)
    return false
  end
  if obj.getName() ~= 'Chip' then return false end
  local col = ATTENTION[number]
  if not col or not CHIP_FACE[col] then return false end
  STATE.chip = number
  -- Keeping x and z turns the Chip without flipping it.
  local r = obj.getRotation()
  obj.setRotationSmooth({r.x, CHIP_FACE[col], r.z})
  say('Chip turned to ' .. col .. '.')
  return true
end

-- ----------------------------------------------------------------- onLoad
function onLoad()
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == 'Control Panel' then PANEL = o end
  end
  -- A book carries no button in the save - buttons are made by
  -- script - so without this it is a picture of a page that does
  -- nothing. Whichever one is out is the one that gets it.
  for _, o in ipairs(getAllObjects()) do
    if isRulebook(o) then drawRulesButton(o) end
  end
  -- The readout is in the BAT bag and carries no button in the save
  -- either, so a table reloaded mid-game finds its own plate again.
  for _, o in ipairs(getAllObjects()) do
    if o.getName() == READOUT_NAME then
      READOUT = o
      drawReadout()
    end
  end
  settle()
  local missing = {}
  for game, g in pairs(BOX) do
    if not getObjectFromGUID(g) then table.insert(missing, game) end
  end
  refreshPanel()
  if #missing > 0 then
    say('Missing bag: ' .. table.concat(missing, ', '))
  end
end
