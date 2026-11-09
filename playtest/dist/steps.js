/* Navigation prompts: the steps of one turn, numbered, with the step you can
   act on NOW lit gold and the ones behind it dimmed. BAT had this for the
   Tyrant battle and nothing else did; this is that strip generalised so NAP,
   AoS and the Imposter Scenario get the same thing.

   THE CHIP'S BUTTON IS A PROXY, not a copy. It points at the page's own
   control by selector: the label is read off that control, it is enabled
   exactly when that control is enabled, and clicking the chip clicks the
   real thing. So the strip cannot drift from the game or disagree with it
   about what is legal, because it does not decide anything - it reports.
   Add a step by naming a control, never by restating a rule.

   A step that acts on a particular card - apply dice to an Assignment,
   assign dice to an Element - has no single control to point at. Those pass
   `ready` instead, and render as a label rather than a button, because the
   buttons for them live on the cards where they belong.

   Which step is "now" is the FIRST one that can be acted on, not a position
   in a state machine. A NAP Time Slot and an AoS Program are loops: you can
   roll, apply, roll again. Lighting the first available step is honest about
   that where a cursor marching 1-2-3-4 would not be. */
window.LabSteps = (() => {
  "use strict";

  const esc = t => String(t).replace(/[&<>"]/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const find = sel => {
    if (!sel) return null;
    try { return document.querySelector(sel); } catch (_) { return null; }
  };

  // Usable means the player can actually press it: present, enabled, and
  // not shut away inside a hidden PANEL - the choice panel, the recovery
  // bar - which is a real reason a step is not available yet.
  //
  // A hidden SCREEN is not. Each game renders its own strip, and a game
  // renders at least once while its screen is still off-stage (a New-game
  // click before you navigate to it). Counting that as unavailable made
  // every step read dead until something re-rendered, which is exactly
  // what AoS did. So screens are excluded from the test: ask whether the
  // control is shut away WITHIN its screen, not whether its screen is up.
  const offstage = el => {
    for (let n = el; n && n.classList; n = n.parentElement) {
      if (n.hidden && !/^screen-/.test(n.id || "")) return true;
      if (n.classList.contains("hidden") && !/^screen-/.test(n.id || "")) return true;
    }
    return false;
  };
  const usable = el => !!el && !el.disabled && !offstage(el);

  /* steps: [{ label, ctrl?, ready?, note? }]
     `ctrl` is the control to proxy. `ready` forces the step live even when
     its proxy is not - for a step whose action has moved somewhere else on
     the page, like NAP's Choose the Primary, where Reveal is spent but the
     thing to do is still part of step 1. Without it the strip walks past a
     step you have not finished and lights the next enabled button, which
     on NAP meant pointing at "End time slot" while a choice was open. */
  function render(hostId, steps) {
    const host = document.getElementById(hostId);
    if (!host) return;
    const live = steps.map(s => !!s.ready || (s.ctrl ? usable(find(s.ctrl)) : false));
    const now = live.indexOf(true);
    host.innerHTML = steps.map((s, i) => {
      const el = s.ctrl ? find(s.ctrl) : null;
      // The control's own label, so the chip says what the button says -
      // "Confirm recovery (2 / 4)" and not a stale paraphrase of it.
      const label = (el && el.textContent.trim()) || s.label;
      const state = i === now ? "now" : (now >= 0 && i < now ? "done" : "");
      const body = s.ctrl
        ? `<button data-step-proxy="${esc(s.ctrl)}" class="${i === now ? "primary" : ""}"` +
          `${live[i] ? "" : " disabled"}>${esc(label)}</button>`
        : `<span class="step-label">${esc(s.label)}</span>`;
      const note = s.note ? `<span class="step-note">${esc(s.note)}</span>` : "";
      return `<div class="step ${state}"><span class="step-num">${i + 1}</span>` +
             `<div class="step-stack">${body}${note}</div></div>`;
    }).join("");
  }

  // One delegated listener for every strip. A proxy click IS the real
  // control's click, so whatever that control does - including its own
  // re-render - happens exactly as if the player had pressed it directly.
  document.addEventListener("click", e => {
    const proxy = e.target.closest && e.target.closest("[data-step-proxy]");
    if (!proxy) return;
    const real = find(proxy.dataset.stepProxy);
    if (real && !real.disabled) real.click();
  });

  return { render };
})();
