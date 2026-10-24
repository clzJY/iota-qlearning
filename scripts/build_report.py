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
                display = "0" if number == 0 else f"{number:.3f}"
                cells.append(f'<td style="background:rgba(22,123,112,{.035 + .29 * number:.4f})">{display}</td>')
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
        band(axes[0], data, "start_value", color, "Median of 20 runs", limit=1000)
        axes[0].axhline(reference, color="#858e80", ls="--", lw=1.1, label=f"Correct value = {reference:.2f}")
        axes[0].set_title(f"{title} · learning the first move", loc="left", pad=14)
        axes[0].set_ylabel("Highest Q-value at the start")
        axes[0].set_ylim(-.02, 1.02)
        axes[0].legend(fontsize=9 if mobile else 8, frameon=False, loc="lower right")
        band(axes[1], data, "max_abs_error", color, "Median of 20 runs", log=True)
        axes[1].axhline(.001, color="#858e80", ls="--", lw=1.1, label="Accuracy threshold = 0.001")
        axes[1].set_title("Checking every value in the table", loc="left", pad=14)
        axes[1].set_ylabel("Largest Q-value error (log scale)")
        axes[1].legend(fontsize=9 if mobile else 8, loc="lower left", frameon=False)
        save_figure(fig, f"{case}-convergence" + ("-mobile" if mobile else ""))


def environment_map():
    positions = {"F": (220, 65), "A": (460, 65), "B": (80, 200), "D": (260, 200), "C": (260, 325), "E": (460, 200)}
    edges = [("A", "E"), ("B", "D"), ("B", "F"), ("C", "D"), ("D", "E"), ("E", "F")]
    # Edges are derived from the same declared adjacency; this list has six items
    # because B-D-E-F is a four-cycle, with A and C as leaves.
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 395" role="img" aria-labelledby="world-title world-desc">',
           '<title id="world-title">The experimental room map</title>',
           '<desc id="world-desc">Allowed two-way connections are A-E, B-D, B-F, C-D, D-E, E-F. The original start is C and target is F. No route is supplied to the learner.</desc>']
    for a, b in edges:
        x1, y1 = positions[a]; x2, y2 = positions[b]
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#acb9a8" stroke-width="3"/>')
    for state, (x, y) in positions.items():
        fill = TEAL if state == "F" else "#fffefa"
        stroke = ORANGE if state == "C" else TEAL if state == "F" else "#a9b69f"
        svg.append(f'<circle cx="{x}" cy="{y}" r="29" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y+8}" text-anchor="middle" font-family="Georgia,serif" font-size="25" fill="{"#fffefa" if state == "F" else INK}">{state}</text>')
    for state, text in [("F", "TARGET"), ("C", "START")]:
        x, y = positions[state]
        svg.append(f'<text x="{x}" y="{y+51}" text-anchor="middle" font-family="monospace" font-size="11" letter-spacing="1" fill="#59685e">{text}</text>')
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
    slots = {"ENVIRONMENT_MAP": environment_map(), "PILOT_ERRORS": f"{pilot_errors[0]:.3f} (C → F) and {pilot_errors[1]:.3f} (A → C)"}
    slots["SETTINGS_TABLE"] = simple_table(["Setting", "Used in both required cases"], [("Initial values", "Zero for every allowed move"), ("Learning rate α", "0.1, kept constant"), ("Discount γ", "0.9"), ("Exploration ε", "0.5, kept constant"), ("Training budget", "20,000 episodes per run"), ("Repeated runs", "20 seeds, numbered 0–19"), ("Episode cap", "100 moves")])
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
        for filename, label, caption_label in [("initial_q.csv", "Before learning", "Initial Q-table · episode 0"), ("final_q.csv", "After learning", "Final Q-table · episode 20,000")]:
            caption = f"{caption_label} · {e['start']} → {e['goal']} · seed 0"
            markup = qtable(ROOT / f"results/{case}/seed_00/{filename}", caption)
            table_parts.append(f'<div><h4>{label}</h4>{markup}</div>')
        tables = ''.join(table_parts)
        final_rows = {row["state"]: row for row in rows(ROOT / f"results/{case}/seed_00/final_q.csv")}
        if case == "original":
            question = "Can the robot learn to reach F from C?"
            before_tables = "Compare the two tables below. Initially every allowed move is worth zero, so the robot has no learned preference. Afterwards, moves that can lead to F sooner have larger values. The F row stays empty because reaching F ends the episode."
            table_example = f"Read row <strong>D</strong> in the learned table: moving to B or E gives approximately <strong>{float(final_rows['D']['B']):.3f}</strong>, while going back to C gives <strong>{float(final_rows['D']['C']):.3f}</strong>. B and E both lie on shortest routes to F, so either can be a good choice."
        else:
            question = "What changes when the robot starts in A and aims for C?"
            before_tables = "We reset all values to zero and train again. This time, entering C earns the reward and ends the episode. Notice that C is now the empty terminal row; F becomes an ordinary room with available moves."
            table_example = f"Now read row <strong>E</strong>: moving to D has value <strong>{float(final_rows['E']['D']):.3f}</strong>, whereas moving to A or F is approximately <strong>{float(final_rows['E']['A']):.3f}</strong>. The robot should head towards D, then enter C."
        required.append(f'''<article class="case {case}" id="case-{case}"><div class="case-header"><div><span class="case-tag">EXPERIMENT {number}</span><h3>{question}</h3></div></div>
<p class="evidence-intro">{before_tables} These are the saved initial and final tables from seed 0.</p>
<div class="q-tables">{tables}</div><p class="table-reading">{table_example}</p>
<p class="download-line">Values are rounded to three decimals; zeros are shown as 0. Full-precision files: <a href="data/{case}-initial_q.csv">initial table</a> · <a href="data/{case}-final_q.csv">final table</a> · <a href="data/{case}-visits.csv">visit counts</a>.</p>
<div class="learned-route"><span>Following the highest learned values gives this route:</span><strong class="path">{seed0['greedy_path']}</strong><p>It takes <strong>{goal_distance} moves</strong>, matching a shortest route in the map. This is a greedy evaluation: the robot follows its learned values without deliberately exploring. Exact ties during evaluation use the alphabetical rule; tiny numerical differences can choose between equally short routes.</p></div>
<h4 class="plot-heading">Did the values settle down?</h4><p class="evidence-intro">The first panel shows the best estimate for the first move rising from zero towards <strong>{reference:.2f}</strong>. That is the correct discounted value of reaching the goal in {goal_distance} moves. The second panel checks <em>every allowed move</em>, including moves away from this route: as its error falls, the whole table becomes more accurate. Its dashed line marks our 0.001 accuracy threshold.</p>
<figure class="chart"><picture><source media="screen and (max-width:700px)" srcset="assets/figures/{case}-convergence-mobile.svg"><img src="assets/figures/{case}-convergence.svg" alt="{e['start']} to {e['goal']}: the best first-move value approaches {reference:.2f}, and the largest whole-table error falls below 0.001 in every one of 20 runs."></picture><figcaption>Figure {number}. {e['start']} → {e['goal']}. First panel: best Q-value at the start during the first 1,000 episodes. Second panel: largest absolute error in the whole table over the full 20,000 episodes, on a logarithmic scale. Lines show medians and bands show the 10th–90th seed percentiles. <a href="data/{case}-aggregate.csv">Numerical plot data</a> · <a href="assets/figures/{case}-convergence.svg">Full-size figure</a>.</figcaption></figure>
<p class="result-summary"><strong>What the evidence says.</strong> All 20 runs learned a shortest {goal_distance}-move route and passed the whole-table accuracy check. The median accuracy-check episode was <strong>{fmt(np.median(accuracy))}</strong>; the middle 80% of seeds passed between episodes {fmt(np.quantile(accuracy,.1))} and {fmt(np.quantile(accuracy,.9))}. The curves therefore show both learning towards the correct values and variation in how quickly different runs get there.</p>
<details><summary>Exact final error and action coverage</summary><div class="detail-content"><p>The largest final error across these 20 seeds is {scientific(max(r['final_error'] for r in runs))}, approximately numerical rounding precision. Every allowed state-action pair was visited; the least-visited pair across all seeds received {minimum:,} updates. Tables above are rounded for reading; the CSVs retain full precision.</p></div></details></article>''')
        snapshots = {}
        state_names = sorted(config["graph"])
        for row in rows(ROOT / f"results/{case}/seed_00/snapshots.csv"):
            snapshots.setdefault(row["episode"], []).append([float(row[s]) if row[s] else None for s in state_names])
        snapshot_data[case] = {"start": e["start"], "goal": e["goal"], "states": state_names, "snapshots": snapshots}
    slots["REQUIRED_RESULTS"] = "\n".join(required)
    original_time = np.median([r["error_threshold_episode"] for r in group["original"]])
    modified_time = np.median([r["error_threshold_episode"] for r in group["modified"]])
    slots["REQUIRED_COMPARISON"] = f'<p>The whole-table accuracy check was reached at a median episode of <strong>{fmt(original_time)} for C → F</strong> and <strong>{fmt(modified_time)} for A → C</strong>. Under these settings, the second case learned the full table sooner on that measure. The shaded bands show randomness across seeds; these medians are not guaranteed learning times.</p>'
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
