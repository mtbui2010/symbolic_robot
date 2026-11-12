"""Markdown tables from <results dir>/summary.json of the protocol suite: python -m bench report factory protocol <dir> [more dirs]"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def pv(p: float) -> str:
    return "<0.0001" if p < 1e-4 else f"{p:.4f}".rstrip("0").rstrip(".")


def ci(d: dict) -> str:
    return f"{d['mean']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]"


def arms_table(arms: dict) -> str:
    out = ["| arm | episodes | success | wrong-done | distance m | questions | t_sim s | wall s | timeouts |", "|---|---|---|---|---|---|---|---|---|"]
    for a, v in arms.items():
        out.append(f"| {a} | {v['episodes']} | {v['success']:.3f} | {v['wrong_done']:.3f} | {v['distance_m']} | {v['questions']} | {v['t_sim']} | {v['wall_s']} | {v['timeouts']} |")
    return "\n".join(out)


def vs_table(vs: dict, base: str = "A") -> str:
    out = [f"| arm vs {base} | tasks | combined W/L/tie (p) | success W/L (p) | distance W/L (p) | d success | d wrong-done | d distance m | d questions | d distance m, both succeed (n) |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for a, c in vs.items():
        w, s, d, b = c["combined"], c["success_only"], c["distance_only"], c["d_distance_both_success"]
        out.append(f"| {a} | {c['n_tasks']} | {w['wins']}/{w['losses']}/{w['ties']} ({pv(w['p'])}) | {s['wins']}/{s['losses']} ({pv(s['p'])}) | {d['wins']}/{d['losses']} ({pv(d['p'])}) | "
                   f"{ci(c['d_success'])} | {ci(c['d_wrong_done'])} | {ci(c['d_distance_m'])} | {ci(c['d_questions'])} | {b['mean']:+.2f} [{b['ci95'][0]:+.2f}, {b['ci95'][1]:+.2f}] ({b['n']}) |")
    return "\n".join(out)


def main(dirs):
    for d in dirs:
        s = json.loads(Path(d, "summary.json").read_text())
        print(f"\n### {Path(d).name}: {s['n_episodes']} episodes\n\n" + arms_table(s["arms"]) + "\n\n" + vs_table(s["vs_A"]) + "\n")
        print("C vs B:\n\n" + vs_table({"C": s["C_vs_B"]}, "B") + "\n")
        print("Verdict (pre-registered rule):", json.dumps(s["verdict"]))
        for pol, v in s["by_policy"].items():
            print(f"\n**policy {pol}** ({v['tasks']} tasks)\n\n" + arms_table(v["arms"]) + "\n\n" + vs_table(v["vs_A"]))


if __name__ == "__main__":
    main(sys.argv[1:])
