"""Markdown tables from <results dir>/summary.json: python -m bench report --domain factory --suite messy <dir> [more dirs]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .report_protocol import ci, pv


def arms_table(arms: dict) -> str:
    out = ["| arm | episodes | success | wrong-done | distance m | questions | unusable answers | clarified | placement-fault fails | fail classes |", "|---|---|---|---|---|---|---|---|---|---|"]
    for a, v in arms.items():
        fc = ", ".join(f"{k} {n}" for k, n in sorted(v["fail_classes"].items()))
        out.append(f"| {a} | {v['episodes']} | {v['success']:.3f} | {v['wrong_done']:.3f} | {v['distance_m']} | {v['questions']} | {v['unusable_answers']} | {v['clarified']} | {v['failed_after_placement_fault']} | {fc} |")
    return "\n".join(out)


def vs_table(vs: dict, base: str = "A") -> str:
    out = [f"| arm vs {base} | tasks | combined W/L/tie (p) | success W/L (p) | distance W/L (p) | d success | d wrong-done | d distance m | d questions |", "|---|---|---|---|---|---|---|---|---|"]
    for a, c in vs.items():
        w, s, d = c["combined"], c["success_only"], c["distance_only"]
        out.append(f"| {a} | {c['n_tasks']} | {w['wins']}/{w['losses']}/{w['ties']} ({pv(w['p'])}) | {s['wins']}/{s['losses']} ({pv(s['p'])}) | {d['wins']}/{d['losses']} ({pv(d['p'])}) | "
                   f"{ci(c['d_success'])} | {ci(c['d_wrong_done'])} | {ci(c['d_distance_m'])} | {ci(c['d_questions'])} |")
    return "\n".join(out)


def main(dirs):
    for d in dirs:
        s = json.loads(Path(d, "summary.json").read_text())
        print(f"\n### {Path(d).name}: {s['n_episodes']} episodes\n\n" + arms_table(s["arms"]) + "\n\n" + vs_table(s["vs_A"]) + "\n\nD vs C:\n\n" + vs_table({"D": s["D_vs_C"]}, "C"))
        print("\nVerdict (pre-registered rule):", json.dumps(s["verdict"]))
        m = s["messy_subset"]
        print(f"\n**the {m['tasks']} messy-policy tasks (without knows, wrong)**\n\n" + arms_table(m["arms"]) + "\n\n" + vs_table(m["vs_A"]))
        for pol, v in s["by_policy"].items():
            print(f"\n**policy {pol}** ({v['tasks']} tasks; policy-level win C/D: {v['policy_level_win']})\n\n" + arms_table(v["arms"]) + "\n\n" + vs_table(v["vs_A"]))
        print("\npartial_name by edit kind (success per arm):", json.dumps(s["partial_name_by_variant"]))


if __name__ == "__main__":
    main(sys.argv[1:])
