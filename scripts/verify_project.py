"""Check saved evidence and offline assets; optionally replay both required seed-0 runs."""
import argparse
import csv
import gzip
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from qlearning import RoomWorld, bellman_residual, greedy_path, reference_q, sustained_threshold_episode, train


def read_rows(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as handle:
        return list(csv.DictReader(handle))


def matrix(path, world):
    records = read_rows(path)
    assert [r["state"] for r in records] == list(world.states), path
    result = np.zeros(world.mask.shape)
    for s, row in enumerate(records):
        for a, name in enumerate(world.states):
            assert (row[name] != "") == bool(world.mask[s, a]), (path, s, a)
            if row[name] != "":
                result[s, a] = float(row[name])
    return result


class OfflineHTMLCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references, self.ids, self.images, self.scripts = [], [], [], []
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag in {"a", "link", "img", "image", "script"}:
            key = "href" if tag in {"a", "link", "image"} else "src"
            if attrs.get(key): self.references.append(attrs[key])
        if tag == "img": self.images.append(attrs)
        if tag == "script" and attrs.get("src"): self.scripts.append(attrs["src"])


def verify(replay=False):
    config_file = ROOT / "configs/experiments.json"
    config = json.loads(config_file.read_text())
    assert (ROOT / "results/config.json").read_bytes() == config_file.read_bytes()
    summary = json.loads((ROOT / "results/summary.json").read_text())
    assert len(summary) == len(config["experiments"]) * len(config["seeds"])
    checked = 0
    for experiment in config["experiments"]:
        settings = {**config["defaults"], **{k: v for k, v in experiment.items() if k in config["defaults"]}}
        world = RoomWorld(config["graph"], experiment["goal"], settings["goal_reward"], settings["step_reward"])
        oracle = reference_q(world, settings["gamma"])
        np.testing.assert_array_equal(matrix(ROOT / f'results/{experiment["id"]}/reference_q.csv', world), oracle)
        all_metrics = {k: [] for k in ["max_abs_error", "delta_q", "bellman_residual", "min_visits", "total_steps", "start_value"]}
        for seed in config["seeds"]:
            folder = ROOT / f'results/{experiment["id"]}/seed_{seed:02d}'
            initial = matrix(folder / "initial_q.csv", world)
            q = matrix(folder / "final_q.csv", world)
            counts = matrix(folder / "visits.csv", world)
            assert (initial == 0).all()
            assert np.isfinite(q).all() and (q >= 0).all() and (q <= 1 + 1e-12).all()
            assert (counts >= 0).all() and (counts == counts.astype(int)).all()
            meta = json.loads((folder / "metadata.json").read_text())
            assert meta["experiment"] == experiment and meta["settings"] == settings and meta["seed"] == seed
            for key, file in [("config_sha256", config_file), ("learner_sha256", ROOT / "code/qlearning.py"), ("runner_sha256", ROOT / "code/run_experiments.py")]:
                assert meta[key] == hashlib.sha256(file.read_bytes()).hexdigest(), (folder, key)
            matching = [r for r in summary if r["experiment"] == experiment["id"] and r["seed"] == seed]
            assert len(matching) == 1 and matching[0] == meta["summary"]
            trace_raw = read_rows(folder / "trace.csv.gz")
            trace = [{k: float(v) for k, v in row.items()} for row in trace_raw]
            assert len(trace) == settings["episodes"] + 1
            assert [int(r["episode"]) for r in trace] == list(range(settings["episodes"] + 1))
            assert sum(r["steps"] for r in trace) == counts.sum() == trace[-1]["total_steps"]
            assert all(r["steps"] <= settings["max_steps"] for r in trace)
            assert all(r["terminated"] + r["truncated"] == 1 for r in trace[1:])
            last = trace[-1]
            error = float(np.abs(q - oracle)[world.mask].max())
            residual = bellman_residual(world, q, settings["gamma"])
            assert abs(error - last["max_abs_error"]) < 1e-14
            assert abs(residual - last["bellman_residual"]) < 1e-14
            assert last["min_visits"] == counts[world.mask].min()
            assert last["unvisited_pairs"] == (counts[world.mask] == 0).sum()
            row = meta["summary"]
            assert error == row["final_error"] and residual == row["final_residual"]
            path, success = greedy_path(world, q, experiment["start"], settings["max_steps"])
            assert success == row["greedy_success"] and len(path)-1 == row["greedy_steps"]
            assert " → ".join(path) == row["greedy_path"]
            for metric, key in [("max_abs_error", "error_threshold_episode"), ("delta_q", "delta_threshold_episode")]:
                computed = sustained_threshold_episode(trace, metric, settings["error_threshold"], settings["stability_window"])
                assert computed == row[key]
            if experiment["id"] != "no_exploration":
                assert row["error_threshold_episode"] is not None and error < .001
            for metric in all_metrics:
                all_metrics[metric].append([r[metric] for r in trace])
            if replay and seed == 0 and experiment["id"] in {"original", "modified"}:
                reproduced = train(world, experiment["start"], settings, seed)
                np.testing.assert_array_equal(reproduced["q"], q)
                for generated, saved in zip(reproduced["trace"], trace):
                    assert generated == saved, (folder, generated["episode"])
            checked += 1
        aggregates = read_rows(ROOT / f'results/{experiment["id"]}/aggregate.csv')
        for metric, histories in all_metrics.items():
            for label, quantile in [("p10", .1), ("median", .5), ("p90", .9)]:
                recomputed = np.quantile(np.asarray(histories), quantile, axis=0)
                actual = np.array([float(r[f"{metric}_{label}"]) for r in aggregates])
                np.testing.assert_allclose(actual, recomputed, rtol=1e-14, atol=1e-14)
        print(f'Verified {experiment["id"]}: {len(config["seeds"])} saved runs and all aggregate series', flush=True)
    parser = OfflineHTMLCheck()
    report_text = (ROOT / "report/index.html").read_text()
    parser.feed(report_text)
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate HTML IDs"
    assert parser.images and all(img.get("alt") for img in parser.images)
    for reference in parser.references:
        parts = urlsplit(reference)
        if parts.scheme or parts.netloc:
            # External citations/downloads are allowed; external runtime assets are not.
            assert reference not in parser.scripts
            continue
        if reference.startswith("#route-"):
            assert reference[1:] in parser.ids
            continue
        if parts.path:
            local = (ROOT / "report" / unquote(parts.path)).resolve()
            assert local.is_relative_to(ROOT / "report") and local.is_file(), reference
        elif parts.fragment:
            assert parts.fragment in parser.ids, reference
    assert "50068179" in report_text and "Chenglong Zhang" in report_text
    for name in ["original", "modified"]:
        for filename in ["initial_q.csv", "final_q.csv", "visits.csv"]:
            assert (ROOT / f"report/data/{name}-{filename}").read_bytes() == (ROOT / f"results/{name}/seed_00/{filename}").read_bytes()
        assert (ROOT / f"report/data/{name}-aggregate.csv").read_bytes() == (ROOT / f"results/{name}/aggregate.csv").read_bytes()
    result = {"saved_runs_verified": checked, "aggregate_series_verified": len(config["experiments"])*18,
              "required_seed_0_full_replay": replay, "offline_local_references_checked": True}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional JSON verification record")
    args = parser.parse_args()
    result = verify(args.replay)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
