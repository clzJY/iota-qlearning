# How do robots find the goal?

**Chenglong Zhang · 50068179 · IOTA 5201 · Fall 2026**

A Q-learning study of robot navigation through six connected rooms.

- Website: https://clzjy.github.io/iota-qlearning/
- Offline report: `report/index.html`
- Printable companion: `report/Qlearning_Report_Chenglong_Zhang_50068179.pdf`
- Source: https://github.com/clzJY/iota-qlearning

## Read the report

Open `report/index.html` in a browser. All essential text, tables, figures and
scripts are local. The Jump to links include direct access to subsection tables,
plots and explanations. Evidence panels are open by default; links reopen them
if closed. The reading bar shows the subsection in the middle and the main part
on the right. Alternatively, from the project root run:

```bash
python -m http.server 8000 --directory report
```

Visit http://localhost:8000. The website and offline HTML are the same technical
report; the PDF is a companion. References and release downloads require internet
access. AI assistance and validation are disclosed in the report’s AI-use statement.

## Experiments

Rooms are states and moves through doorways are actions. The seven bidirectional
connections are A–E, B–C, B–D, B–F, C–D, D–E and E–F. Entering the goal earns 1
and terminates the episode; all other legal moves earn 0. Invalid moves are masked.

| Experiment | Start → target | Purpose |
| --- | --- | --- |
| `original` | C → F | Original case |
| `modified` | A → C | Required changed configuration |
| `start_control` | A → F | Compare starts with a fixed target |
| `factorial_bf` | B → F | Additional start/target comparison |
| `factorial_bc` | B → C | Additional start/target comparison |
| `no_exploration` | C → F | Compare with ε = 0 |

Every run starts with zero Q-values. Main settings are α = 0.1, γ = 0.9,
ε = 0.5, 20,000 episodes, a 100-move cap and seeds 0–19. The no-exploration case
changes ε to 0. All 100 runs with ε = 0.5 passed the whole-table accuracy check
and learned shortest routes. Without forced exploration, 14/20 learned a shortest
route, while none passed the whole-table accuracy check. The report explains the
criterion, plots, comparisons and limitations. Conceptual animations illustrate
legal alternatives; experimental results come from saved Python runs.

## Reproduce

The recorded numerical environment is Python 3.13.12 and NumPy 2.5.3; figures use
Matplotlib 3.10.8. Exact dependency versions are in `requirements-lock.txt`.
No GPU is needed.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m unittest discover -s code -p 'test_*.py' -v
python code/run_experiments.py
python scripts/build_report.py
python scripts/verify_project.py --replay --output docs/verification.json
```

Run either required case separately with `--only original` or `--only modified`.
To preserve the supplied results, use a separate output directory, for example:

```bash
python code/run_experiments.py --only original --output reruns/original
```

The report generator reads canonical `results/` files. It does not train the agent.
The corrected pilot uses ε = 0.2 and 3,000 episodes; its retained results support
the training-budget discussion. To rerun it:

```bash
python code/run_experiments.py --config configs/pilot.json --output reruns/pilot
```

## Files

| Path | Contents |
| --- | --- |
| `code/` | Learner, experiment runner, tests, editable HTML template and route illustrations |
| `configs/` | Main/pilot settings and conceptual floorplan |
| `results/` | All 120 main runs, initial/final tables, traces, references and aggregate plot data |
| `experiments/pilot_3000/` | Pilot evidence and source provenance |
| `report/` | HTML report, local assets, data downloads and PDF |
| `scripts/` | Report generation, verification, PDF export and packaging |
| `docs/` | Data dictionary, learning guide and verification records |

Read `docs/data-dictionary.md` to interpret the numerical files and
`docs/learning-guide.md` for the algorithm explanation. Edit
`code/report_template.html`, then rebuild with `python scripts/build_report.py`.
`report/index.html` is generated and should not be edited directly.

## PDF and submission ZIP

The PDF is already included. To regenerate it, optionally install Firefox,
geckodriver and Node, then run:

```bash
python scripts/browser_check.py --export-pdf
```

Node 22+ supplies WebSocket; Node 18 requires `undici`. The checker starts and stops
its own browser and local server, checks mobile/tablet/desktop layouts and offline
reading, and saves its verification record. Screenshots are temporary unless
`--preview-dir <directory>` is supplied. Report generation alone does not update
the PDF, so export it after content edits and before packaging.

```bash
python scripts/package_submission.py
```

**Submit `dist/Chenglong_Zhang_50068179_IOTA_Qlearning.zip`.** It contains the report,
PDF, source, settings and reproducible evidence. It also includes
`SUBMISSION_SHA256.json`; the packager verifies every embedded file hash. A PDF
alone is not the required submission. The website URL appears above and inside
the HTML report. The ZIP excludes development notes, preview screenshots,
superseded results, caches, virtual environments and previous release packages.
