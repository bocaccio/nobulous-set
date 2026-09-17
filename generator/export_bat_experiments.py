"""Export authoritative BAT Experiment text for the browser playtest."""

import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "generator" / "build_bat.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
assignment = next(
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "EXPERIMENTS" for target in node.targets)
)
cards = [dict(name=name, target=target, effect=effect, flavor=flavor)
         for name, target, effect, flavor in ast.literal_eval(assignment.value)]
if len(cards) != 20:
    raise ValueError(f"Expected 20 BAT Experiments, found {len(cards)}")
output = root / "playtest" / "dist" / "bat_experiments.js"
output.write_text("window.BAT_EXPERIMENTS = " + json.dumps(cards, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print(output)
