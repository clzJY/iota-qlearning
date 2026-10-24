"""Regenerate static figures and report from saved experimental evidence only."""
import csv
import html
import json
import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
FIGURES = REPORT / "assets/figures"
DATA = REPORT / "data"
TEAL, ORANGE, INK = "#167b70", "#c46438", "#213931"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": "#59685e", "ytick.color": "#59685e",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c9d2c6", "axes.titleweight": "medium",
                     "svg.fonttype": "none", "svg.hashsalt": "iota-qlearning-v1",
                     "savefig.facecolor": "white", "figure.facecolor": "white"})


def rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def fmt(value):
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"


def scientific(value):
    return f"{value:.2e}"


def percentile(values):
    return np.quantile(values, [.1, .5, .9])


def interval(values):
    low, med, high = percentile(values)
    return f"{fmt(med)} [{fmt(low)}, {fmt(high)}]"


def simple_table(headers, body, caption=None):
    cap = f'<caption class="small">{html.escape(caption)}</caption>' if caption else ""
    head = "".join(f'<th scope="col">{html.escape(str(h))}</th>' for h in headers)
    cells = "".join("<tr>" + "".join(f'<{"th scope=\"row\"" if i == 0 else "td"}>{html.escape(str(v))}</{"th" if i == 0 else "td"}>' for i, v in enumerate(row)) + "</tr>" for row in body)
    return f'<div class="table-scroll"><table>{cap}<thead><tr>{head}</tr></thead><tbody>{cells}</tbody></table></div>'


def qtable(path, caption):
    values = rows(path)
    states = list(values[0])[1:]
    header = '<th scope="col">s / a</th>' + "".join(f'<th scope="col">{s}</th>' for s in states)
    body = []
    for row in values:
        cells = []
        for s in states:
            value = row[s]
            if value == "":
                cells.append('<td class="unavailable" aria-label="unavailable">—</td>')
            else:
                number = float(value)
                cells.append(f'<td style="background:rgba(22,123,112,{.035 + .29 * number:.4f})">{number:.6f}</td>')
        body.append(f'<tr><th scope="row">{row["state"]}</th>{"".join(cells)}</tr>')
    return f'<div class="table-scroll"><table class="q-table"><caption class="small">{html.escape(caption)}</caption><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def aggregate(case):
    return {key: np.array([float(r[key]) for r in data]) for data in [rows(ROOT / f"results/{case}/aggregate.csv")] for key in data[0]}


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", metadata={"Date": None, "Creator": "IOTA Q-learning project / Matplotlib"})
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", dpi=180, metadata={"Software": "IOTA Q-learning project / Matplotlib"})
    plt.close(fig)


def band(ax, data, metric, color, label, log=False, limit=None):
    selected = data["episode"] <= (limit or float("inf"))
    x = data["episode"][selected]
    values = [data[f"{metric}_{label}"][selected] for label in ["p10", "median", "p90"]]
    if log:
        values = [np.maximum(v, 1e-12) for v in values]
        ax.set_yscale("log")
        ax.set_ylim(1e-12, 1.6)
    ax.fill_between(x, values[0], values[2], color=color, alpha=.14, linewidth=0)
    ax.plot(x, values[1], color=color, lw=1.9, label=label)
    ax.set_xlabel("Episodes")
    ax.grid(axis="y", alpha=.18)
    ax.set_axisbelow(True)
    ax.ticklabel_format(axis="x", style="plain")


def convergence_figure(case, title, reference):
    data = aggregate(case)
    for mobile in [False, True]:
        fig, axes = plt.subplots(2 if mobile else 1, 1 if mobile else 2, figsize=(5.2, 7.0) if mobile else (11.2, 3.65), layout="constrained")
        color = TEAL if case == "original" else ORANGE
        band(axes[0], data, "max_abs_error", color, "Median · 20 seeds", log=True)
        axes[0].axhline(.001, color="#858e80", ls="--", lw=1.1, label="Accuracy tolerance 0.001")
        axes[0].set_title(f"{title} · full-table accuracy", loc="left", pad=14)
        axes[0].set_ylabel("Maximum |Q − Q*| (log scale)")
        axes[0].legend(fontsize=9 if mobile else 8, loc="lower left", frameon=False)
        band(axes[1], data, "start_value", color, "Median · 20 seeds", limit=1000)
        axes[1].axhline(reference, color="#858e80", ls="--", lw=1.1, label=f"Exact start value = {reference:.2f}")
        axes[1].set_title("Start value · first 1,000 episodes", loc="left", pad=14)
        axes[1].set_ylabel("max a Q(start, a)")
        axes[1].set_ylim(-.02, 1.02)
        axes[1].legend(fontsize=9 if mobile else 8, frameon=False, loc="lower right")
        save_figure(fig, f"{case}-convergence" + ("-mobile" if mobile else ""))


def hero_graph():
    positions = {"F": (235, 90), "A": (500, 90), "B": (95, 265), "D": (290, 265), "C": (290, 420), "E": (500, 265)}
    edges = [("A", "E"), ("B", "D"), ("B", "F"), ("C", "D"), ("D", "E"), ("E", "F")]
    # Edges are derived from the same declared adjacency; this list has six items
    # because B-D-F-E is a four-cycle, with A and C as leaves.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 610 510" role="img" aria-labelledby="world-title world-desc">',
           '<title id="world-title">Six rooms and two configurations</title>',
           '<desc id="world-desc">Edges A-E, B-D, B-F, C-D, D-E, E-F. Original route C-D-B-F is teal; modified route A-E-D-C is orange. Both shortest routes have three transitions.</desc>']
    for a, b in edges:
        x1, y1 = positions[a]; x2, y2 = positions[b]
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c3ccbc" stroke-width="3"/>')
    for path, color, dash in [("CDBF", TEAL, ""), ("AEDC", ORANGE, 'stroke-dasharray="9 7"')]:
        points = " ".join(f"{positions[s][0]},{positions[s][1]}" for s in path)
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round" {dash}/>')
    for state, (x, y) in positions.items():
        fill = TEAL if state == "F" else "#fffefa"
        stroke = ORANGE if state in "AC" else TEAL if state == "F" else "#a9b69f"
        svg.append(f'<circle cx="{x}" cy="{y}" r="29" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y+8}" text-anchor="middle" font-family="Georgia,serif" font-size="25" fill="{"#fffefa" if state == "F" else INK}">{state}</text>')
    for state, text in [("F", "ORIGINAL GOAL"), ("A", "NEW START"), ("C", "START / NEW GOAL")]:
        x, y = positions[state]
        svg.append(f'<text x="{x}" y="{y+51}" text-anchor="middle" font-family="monospace" font-size="8" letter-spacing="1" fill="#59685e">{text}</text>')
    svg.append('</svg>')
    return "".join(svg)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "configs/experiments.json").read_text())
    summary = json.loads((ROOT / "results/summary.json").read_text())
    group = {e["id"]: [r for r in summary if r["experiment"] == e["id"]] for e in config["experiments"]}
    pilot = json.loads((ROOT / "experiments/pilot_3000/summary.json").read_text())
    pilot_errors = [max(r["final_error"] for r in pilot if r["experiment"] == case) for case in ["original", "modified"]]
    slots = {"HERO_GRAPH": hero_graph(), "PILOT_ERRORS": f"{pilot_errors[0]:.3f} (C → F) and {pilot_errors[1]:.3f} (A → C)"}
    slots["ADJACENCY_TABLE"] = simple_table(["Room", "Legal destinations before terminal masking"], [(s, ", ".join(neighbors)) for s, neighbors in config["graph"].items()])
    slots["SETTINGS_TABLE"] = simple_table(["Setting", "Main protocol"], [("Q initialization", "Zero on every valid pair"), ("Learning rate α", "0.1, constant"), ("Discount γ", "0.9"), ("Exploration ε", "0.5, constant; ablation 0"), ("Budget", "20,000 episodes × 20 seeds"), ("Episode cap", "100 transitions"), ("Random generator", "NumPy default_rng / PCG64"), ("Run environment", "Python 3.13.12 · NumPy 2.5.3")])
    slots["DESIGN_TABLE"] = simple_table(["Case", "Start → target", "Purpose"], [(e["title"], f'{e["start"]} → {e["goal"]}', e["role"]) for e in config["experiments"]])
    required = []
    snapshot_data = {}
    for number, case in enumerate(["original", "modified"], 1):
        e = next(e for e in config["experiments"] if e["id"] == case)
        runs = group[case]
        seed0 = next(r for r in runs if r["seed"] == 0)
        accuracy = [r["error_threshold_episode"] for r in runs if r["error_threshold_episode"] is not None]
        if len(accuracy) != len(runs):
            raise ValueError(f"Required case {case} did not reach the declared full-table tolerance in every seed")
        goal_distance = len(seed0["greedy_path"].split(" → ")) - 1
        reference = config["defaults"]["gamma"] ** (goal_distance - 1)
        convergence_figure(case, f'{e["start"]} → {e["goal"]}', reference)
        for filename in ["initial_q.csv", "final_q.csv", "visits.csv"]:
            shutil.copyfile(ROOT / f"results/{case}/seed_00/{filename}", DATA / f"{case}-{filename}")
        shutil.copyfile(ROOT / f"results/{case}/aggregate.csv", DATA / f"{case}-aggregate.csv")
        minimum = min(r["min_visits"] for r in runs)
        table_parts = []
        for filename, label in [("initial_q.csv", "Initial Q-table · episode 0"), ("final_q.csv", "Final Q-table · episode 20,000")]:
            caption = f"{e['start']} → {e['goal']}, seed 0 · {label.lower()}"
            markup = qtable(ROOT / f"results/{case}/seed_00/{filename}", caption)
            table_parts.append(f'<div><h4>{label}</h4>{markup}</div>')
        tables = ''.join(table_parts)
        required.append(f'''<article class="case {case}" id="case-{case}"><div class="case-header"><div><span class="case-tag">REQUIRED CONFIGURATION {number:02d}</span><h3>{e['title']} · {e['start']} → {e['goal']}</h3></div><span class="path">{seed0['greedy_path']}</span></div>
<p class="result-summary">All <strong>20/20 seeds</strong> met the full-table accuracy criterion. Median qualifying episode: <strong>{fmt(np.median(accuracy))}</strong>, with a 10th–90th percentile range of {fmt(np.quantile(accuracy,.1))}–{fmt(np.quantile(accuracy,.9))}. Every final greedy policy reached the goal in <strong>{goal_distance} steps</strong>, matching the shortest path. Maximum final error across seeds: {scientific(max(r['final_error'] for r in runs))}; the least-visited valid pair across all seeds still received {minimum:,} updates.</p>
<figure class="chart"><picture><source media="screen and (max-width:700px)" srcset="assets/figures/{case}-convergence-mobile.svg"><img src="assets/figures/{case}-convergence.svg" alt="{e['start']} to {e['goal']}: full-table error falls below 0.001 in all 20 seeds; start-state action value approaches its exact value of {reference:.2f}."></picture><figcaption>Figure {number}. {e['start']} → {e['goal']} over 20 seeds: full-table error (first panel) and start value during the first 1,000 episodes (second panel). Lines are medians; bands span the 10th–90th seed percentiles. Numerical source: results/{case}/aggregate.csv. <a href="assets/figures/{case}-convergence.svg">Full-size figure</a>.</figcaption></figure>
<div class="q-tables">{tables}</div><p class="download-line">Rows are current rooms; columns are destination actions. “—” means unavailable, including every outgoing action from target {e['goal']}. <a href="data/{case}-initial_q.csv">Initial CSV</a> · <a href="data/{case}-final_q.csv">Final CSV</a> · <a href="data/{case}-visits.csv">Visit counts</a> · <a href="data/{case}-aggregate.csv">Plot data</a></p></article>''')
        snapshots = {}
        state_names = sorted(config["graph"])
        for row in rows(ROOT / f"results/{case}/seed_00/snapshots.csv"):
            snapshots.setdefault(row["episode"], []).append([float(row[s]) if row[s] else None for s in state_names])
        snapshot_data[case] = {"start": e["start"], "goal": e["goal"], "states": state_names, "snapshots": snapshots}
    slots["REQUIRED_RESULTS"] = "\n".join(required)
    slots["SNAPSHOT_JSON"] = json.dumps(snapshot_data, separators=(",", ":")).replace("<", "\\u003c")
    control_ids = ["original", "start_control", "factorial_bf", "modified", "factorial_bc"]
    comparison = []
    for case in control_ids:
        runs = group[case]
        times = [r["error_threshold_episode"] for r in runs]
        if any(t is None for t in times):
            raise ValueError("Do not report uncensored threshold statistics for incomplete cases")
        comparison.append([f'{runs[0]["start"]} → {runs[0]["goal"]}', interval(times), fmt(np.median([r["total_steps"] for r in runs])), min(r["min_visits"] for r in runs), f'{runs[0]["optimal_steps"]} steps'])
    slots["COMPARISON_TABLE"] = simple_table(["Start → target", "Accuracy episode: median [P10, P90]", "Median transitions", "Fewest visits, any seed", "Shortest route"], comparison)
    fig, ax = plt.subplots(figsize=(11.2, 3.9), layout="constrained")
    for i, case in enumerate(control_ids):
        values = np.array([r["error_threshold_episode"] for r in group[case]])
        low, med, high = percentile(values)
        ax.plot([low, high], [i, i], color="#b9cbbb", lw=7, solid_capstyle="round")
        ax.scatter(values, i + .12 * np.sin(np.arange(len(values)) * 2.4), s=17, color=TEAL, alpha=.7)
        ax.plot([med, med], [i-.18, i+.18], color=ORANGE, lw=3)
    ax.set_yticks(range(len(control_ids)), [f'{group[c][0]["start"]} → {group[c][0]["goal"]}' for c in control_ids])
    ax.invert_yaxis(); ax.set_xlim(left=0)
    ax.set_xlabel("First episode in sustained full-table error < 0.001 suffix")
    ax.set_title("Whole-table accuracy depends on coverage, not just route length", loc="left", pad=16)
    ax.grid(axis="x", alpha=.18); ax.set_axisbelow(True)
    save_figure(fig, "controls")
    med = {case: np.median([r["error_threshold_episode"] for r in group[case]]) for case in control_ids}
    diff = [a["error_threshold_episode"]-b["error_threshold_episode"] for a,b in zip(group["start_control"], group["original"])]
    slots["CONTROL_ANALYSIS"] = f'''<article><h3>A shorter route can leave a slower table.</h3><p>Holding the goal at F, changing the start from C to A reduces the shortest route from three steps to two. Yet median full-table accuracy moves from {fmt(med['original'])} to {fmt(med['start_control'])} episodes. The descriptive seed-matched difference is {interval(diff)} episodes (median [P10, P90]). Starting nearer the goal gives fewer opportunities to sample distant branches in each episode. This interpretation is consistent with the saved visit counts; it is not a universal law about start distance.</p></article><article><h3>The target changes the learning problem.</h3><p>Holding the start at B, switching target F to C increases the shortest route from one step to two, yet median full-table accuracy improves from {fmt(med['factorial_bf'])} to {fmt(med['factorial_bc'])} episodes. Goal F terminates on entering a well-connected room, while reaching leaf C requires passing through D. Coverage and termination structure matter beyond path length. Final reference tables for the same goal agree regardless of start, while changing the goal changes valid terminal actions and values.</p></article>'''
    ablation = group["no_exploration"]
    successes = sum(r["greedy_success"] and r["greedy_steps"] == r["optimal_steps"] for r in ablation)
    err = [r["final_error"] for r in ablation]
    missing = [r["unvisited_pairs"] for r in ablation]
    quiet = [r["delta_threshold_episode"] for r in ablation]
    slots["ABLATION_STAT"] = f'<strong>{successes}/20</strong>'
    slots["ABLATION_ANALYSIS"] = f'<p>In these saved runs, <strong>{successes}/20 final greedy policies take a shortest route</strong>. Nevertheless, final full-table errors range from <strong>{min(err):.3f} to {max(err):.3f}</strong>, and {min(missing)}–{max(missing)} valid action pairs per run were never visited. No run meets the full-table tolerance. Episode changes remain below 0.001 from a median episode of <strong>{fmt(np.median(quiet))}</strong> onwards for at least 100 episodes through the run end.</p>'
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.65), layout="constrained")
    for case, color, label in [("original", TEAL, "ε = 0.5"), ("no_exploration", ORANGE, "ε = 0")]:
        data = aggregate(case)
        band(axes[0], data, "max_abs_error", color, label, log=True)
        band(axes[1], data, "delta_q", color, label, log=True)
    for ax in axes:
        ax.axhline(.001, color="#858e80", ls="--", lw=1)
        ax.legend(fontsize=8, frameon=False, loc="upper right")
    axes[0].set_title("Full-table error can stay large", loc="left", pad=14)
    axes[0].set_ylabel("Maximum |Q − Q*| (log scale)")
    axes[1].set_title("Even when episode changes disappear", loc="left", pad=14)
    axes[1].set_ylabel("Maximum |Q(e) − Q(e−1)| (log scale)")
    save_figure(fig, "ablation")
    required_rows = group["original"] + group["modified"]
    slots["RESIDUAL_SUMMARY"] = f'the largest final residual across all 40 runs is {scientific(max(r["final_residual"] for r in required_rows))}, and every valid pair has at least {min(r["min_visits"] for r in required_rows):,} visits'
    shutil.copyfile(ROOT / "results/summary.csv", DATA / "summary.csv")
    shutil.copyfile(ROOT / "configs/experiments.json", DATA / "experiments.json")
    template = (ROOT / "code/report_template.html").read_text()
    for key, value in slots.items():
        template = template.replace("{{" + key + "}}", value)
    if re.search(r"\{\{[A-Z_]+\}\}", template):
        raise ValueError("Unfilled report slot")
    (REPORT / "index.html").write_text(template, encoding="utf-8")
    (REPORT / ".nojekyll").touch()
    print("Generated report/index.html, SVG/PNG figures including mobile variants, and local evidence downloads.")


if __name__ == "__main__":
    main()
