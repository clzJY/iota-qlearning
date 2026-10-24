"""Run the declared suite; retain every episode and every seed for audit/replotting."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import platform
from pathlib import Path

import numpy as np

from qlearning import RoomWorld, greedy_path, reference_q, sustained_threshold_episode, train

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    rows = list(rows)
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(text.getvalue().encode(), mtime=0))
    else:
        path.write_text(text.getvalue(), encoding="utf-8", newline="")


def table_rows(world, values):
    # A numeric zero is a valid estimate; an empty cell is an unavailable action.
    for s, name in enumerate(world.states):
        yield {"state": name, **{n: float(values[s, a]) if world.mask[s, a] else "" for a, n in enumerate(world.states)}}


def run_suite(config_path, output, only=None):
    raw = config_path.read_bytes()
    config = json.loads(raw)
    output.mkdir(parents=True, exist_ok=True)
    selected = [e for e in config["experiments"] if only is None or e["id"] == only]
    if not selected:
        raise ValueError("Unknown experiment ID")
    summary = []
    for experiment in selected:
        settings = {**config["defaults"], **{k: v for k, v in experiment.items() if k in config["defaults"]}}
        world = RoomWorld(config["graph"], experiment["goal"], settings["goal_reward"], settings["step_reward"])
        folder = output / experiment["id"]
        folder.mkdir(parents=True, exist_ok=True)
        write_csv(folder / "reference_q.csv", table_rows(world, reference_q(world, settings["gamma"])))
        histories = []
        for seed in config["seeds"]:
            run = train(world, experiment["start"], settings, seed)
            seed_folder = folder / f"seed_{seed:02d}"
            seed_folder.mkdir(exist_ok=True)
            write_csv(seed_folder / "initial_q.csv", table_rows(world, run["initial"]))
            write_csv(seed_folder / "final_q.csv", table_rows(world, run["q"]))
            write_csv(seed_folder / "visits.csv", table_rows(world, run["visits"]))
            write_csv(seed_folder / "trace.csv.gz", run["trace"])
            snapshot_rows = []
            for episode, values in run["snapshots"].items():
                for row in table_rows(world, values):
                    snapshot_rows.append({"episode": episode, **row})
            write_csv(seed_folder / "snapshots.csv", snapshot_rows)
            path, success = greedy_path(world, run["q"], experiment["start"], settings["max_steps"])
            all_starts = {s: {"path": p, "success": ok, "steps": len(p) - 1, "optimal_steps": world.distances()[s]}
                          for s in world.states for p, ok in [greedy_path(world, run["q"], s, settings["max_steps"]) ]}
            last = run["trace"][-1]
            row = {
                "experiment": experiment["id"], "start": experiment["start"], "goal": experiment["goal"],
                "seed": seed, "epsilon": settings["epsilon"],
                "final_error": last["max_abs_error"], "final_residual": last["bellman_residual"],
                "min_visits": last["min_visits"], "unvisited_pairs": last["unvisited_pairs"],
                "total_steps": last["total_steps"],
                "truncated_episodes": sum(r["truncated"] for r in run["trace"][1:]),
                "greedy_steps": len(path) - 1, "greedy_success": success,
                "optimal_steps": world.distances()[experiment["start"]],
                "greedy_path": " → ".join(path),
                "error_threshold_episode": sustained_threshold_episode(run["trace"], "max_abs_error", settings["error_threshold"], settings["stability_window"]),
                "delta_threshold_episode": sustained_threshold_episode(run["trace"], "delta_q", settings["error_threshold"], settings["stability_window"]),
            }
            summary.append(row)
            metadata = {"experiment": experiment, "settings": settings, "seed": seed,
                        "config_sha256": hashlib.sha256(raw).hexdigest(),
                        "learner_sha256": hashlib.sha256((ROOT / "code/qlearning.py").read_bytes()).hexdigest(),
                        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        "python": platform.python_version(), "numpy": np.__version__,
                        "rng": "numpy.default_rng / PCG64", "evaluation_ties": "alphabetically first exact maximum",
                        "summary": row, "all_start_evaluation": all_starts}
            (seed_folder / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
            histories.append(run["trace"])
        # Save the numerical data behind every ensemble figure as plain CSV.
        aggregate = []
        for episode in range(settings["episodes"] + 1):
            row = {"episode": episode}
            for metric in ["max_abs_error", "delta_q", "bellman_residual", "min_visits", "total_steps", "start_value"]:
                values = [history[episode][metric] for history in histories]
                for label, quantile in [("p10", .1), ("median", .5), ("p90", .9)]:
                    row[f"{metric}_{label}"] = float(np.quantile(values, quantile))
            aggregate.append(row)
        write_csv(folder / "aggregate.csv", aggregate)
        print(f"{experiment['id']}: {len(histories)} seeds, max final error {max(r['final_error'] for r in summary if r['experiment'] == experiment['id']):.6g}", flush=True)
    if only is None:
        write_csv(output / "summary.csv", summary)
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        (output / "config.json").write_bytes(raw)
    else:
        (output / only / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments.json")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--only", help="Run one experiment ID instead of the complete suite")
    args = parser.parse_args()
    run_suite(args.config.resolve(), args.output.resolve(), args.only)
