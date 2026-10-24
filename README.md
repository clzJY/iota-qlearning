# How do robots find the goal?

**Chenglong Zhang · 50068179 · IOTA 5201 · Fall 2026**

A six-room Q-learning study with a self-contained technical report, reproducible
experiments, controlled comparisons, and an exploration ablation.

- Website: https://clzJY.github.io/iota-qlearning/
- Personal repository: https://github.com/clzJY/iota-qlearning
- Downloadable submission ZIP: https://github.com/clzJY/iota-qlearning/releases/latest
- Offline report: `report/index.html`
- PDF: `report/Qlearning_Report_Chenglong_Zhang_50068179.pdf`

The current report and evidence use the corrected B–C doorway. The original C → F
route has two moves and value 0.9; A → C has three moves and value 0.81. Student
review and understanding remain necessary before submission; the AI-use statement
explicitly records that distinction. The repository belongs to the personal `clzJY`
account. No organization repository or existing personal website source is used.

## The main file and editable source

This is one technical HTML report, published as a website. The PDF is exported
from the report for printing; it is a companion rather than a separate narrative.

| Purpose | Main file |
| --- | --- |
| Read the report or open the website locally | `report/index.html` |
| Revise the written explanation and page structure | `code/report_template.html` |
| Revise styling | `report/assets/style.css` |
| Insert saved results and regenerate the report/figures | `scripts/build_report.py` |
| Understand the learning implementation | `code/qlearning.py` |

Edit the template, then run `python scripts/build_report.py`. Direct edits to the
built `report/index.html` would be replaced by the next generation. Both conceptual floorplans use the same corrected walls and doorways: the opening
shows C → F and Experiment 2 shows A → C. Each has fixed robot/dock markers and
three illustrative legal route traces. Traces are not recorded runs. A single row of five quick links at the bottom of The Problem jumps to the named
report parts. A sticky reading indicator shows the current part and experiment
while scrolling. References and AI use appear with the Part 5 takeaways; conclusions
for both additional questions remain visible before their expandable evidence.
The required C-to-F and A-to-C experiments come before the expandable extensions.

## Read the report

Open `report/index.html` directly in a browser. All essential text, Q-tables, figures,
styles, scripts, and saved interactive checkpoints are local. JavaScript enhances
explanation; it is not required to read the main results. Alternatively:

```bash
python -m http.server 8000 --directory report
```

Visit http://localhost:8000. External references and GitHub download links require
internet access; the local report does not.

## What was run

All runs train from a fresh zero table. Main parameters are α = 0.1, γ = 0.9,
ε = 0.5, 20,000 episodes, a 100-transition cap, and seeds 0–19.

| Experiment ID | Start → target | Role |
| --- | --- | --- |
| `original` | C → F | Original pair inferred from the supplied figure |
| `modified` | A → C | Required modified case |
| `start_control` | A → F | Hold the target fixed |
| `factorial_bf` | B → F | Controlled A/B × C/F comparison |
| `factorial_bc` | B → C | Controlled A/B × C/F comparison |
| `no_exploration` | C → F | Same protocol with ε = 0 |

The A/B × C/F comparison comprises `start_control`, `factorial_bf`, `modified`,
and `factorial_bc`. No goal self-loop is used. Entering the goal yields +1 and
terminates; other legal moves yield 0. Illegal actions are unavailable. The room
graph and every setting are in `configs/experiments.json`.

All 100 main runs with ε = 0.5 reached full-table error below 0.001 for a suffix
of at least 100 episodes through run end, and found shortest greedy routes. The
20 no-forced-exploration runs retained full-table errors of 0.9–1.0; 14 found a
shortest route and six kept a longer one. The report analyses why these are different outcomes.

## Map correction and preserved history

The B–C connection is available in both directions: C has actions B/D; B has
C/D/F when it is nonterminal. All diagrams, every current main/pilot experiment,
and all derived values use these seven doorway pairs:
A–E, B–C, B–D, B–F, C–D, D–E, E–F.

Releases v1.0.0 and v1.1.0 used an incomplete graph. Their exact main/pilot evidence
and verification records are retained in `experiments/superseded_missing_bc_20261024/`
with a relocation notice; their results are not used in the current report. That
historical directory remains in the repository and is excluded from the current
submission ZIP. The ZIP contains the corrected main results and corrected pilot.
See `docs/revisions/20261024_bc_doorway.md` for the correction record.

## Reproduce from a clean environment

The recorded training environment is Python 3.13.12 and NumPy 2.5.3. Figures use
Matplotlib 3.10.8. `requirements-lock.txt` records all plotting dependency versions.
No GPU or training framework is needed.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m unittest discover -s code -p 'test_*.py' -v
python code/run_experiments.py
python scripts/build_report.py
python scripts/verify_project.py --replay --output docs/verification.json
python scripts/package_submission.py
```

`run_experiments.py` regenerates the canonical `results/` files. To retain the
submitted evidence while rerunning, choose a separate output directory:

```bash
python code/run_experiments.py --output reruns/main
```

The report generator always reads canonical `results/`. For either required
configuration alone (20 seeds, with the other settings unchanged):

```bash
python code/run_experiments.py --only original --output reruns/original
python code/run_experiments.py --only modified --output reruns/modified
```

The full CPU-only suite may take several minutes. Its saved traces include every
episode, not just plotted checkpoints. The checker verifies all 120 saved runs and
all 108 ensemble series. `--replay` additionally reruns seed 0 in both required
configurations and requires exact equality of every saved trace field and Q-value.

## Pilot evidence

`experiments/pilot_3000/` retains all 120 preliminary runs using ε = 0.2 and 3,000
episodes. Its copied learner and runner match the source hashes in its metadata.
This pilot was rerun on the corrected seven-doorway graph. It motivates the larger
main budget; it is not mixed with the historical pilot from the incomplete graph.
To reproduce it separately:

```bash
python code/run_experiments.py \
  --config experiments/pilot_3000/config.json \
  --output reruns/pilot_3000
```

Because the learner and runner remained unchanged, this uses the same numerical
implementation as the pilot. Both the exploration rate and budget changed between
pilot and main protocols; no single-variable causal claim is made from that change.

## Optional browser checks and PDF export

The saved PDF is included, so reading and reproducing the numerical experiments
do not require a browser automation setup. To regenerate the PDF and browser checks
on a machine with Firefox, geckodriver, and Node installed:

```bash
python scripts/browser_check.py --export-pdf
```

The script starts its own local server and isolated headless browser, checks the
fixed landmarks, route playback/fading, the annotated update, AI-use navigation, and saved snapshots, verifies real CSS viewports at 390/768/1440 px,
tests direct file opening, exports the PDF, and stops its own processes. It uses
standard WebDriver HTTP and BiDi. Node 22+ provides WebSocket; Node 18 needs the
`undici` module (already available on the development host). Firefox Snap restricts
`/data/private`, so direct-file QA uses a temporary byte-identical report copy in
its permitted directory. No production files are moved for that check.

`docs/browser-verification.json` and `docs/preview/` contain the recorded checks
and representative desktop/mobile screenshots. `docs/verification.json` records
the numerical artifact verification. The PDF was also rendered and inspected.

## Package the submission

```bash
python scripts/package_submission.py
```

Output: `dist/Chenglong_Zhang_50068179_IOTA_Qlearning.zip`, plus `dist/SHA256SUMS`.
The ZIP contains an `IOTA-RL/` project folder and `SUBMISSION_SHA256.json` mapping
included files to hashes. It excludes `.git/`, virtual environments, caches, and
prior ZIPs, and superseded results from the earlier graph without B–C. The original course PDF is retained locally and attributed in the
report; it is not needed for reproduction and is excluded from Git and the ZIP.
The ZIP includes the optional PDF when present. Packaging verifies archive integrity
and every embedded file hash.

Rebuilding the report does not regenerate the optional PDF. After editing report
content, regenerate the PDF before packaging if it is to be included.

## GitHub Pages

`.github/workflows/pages.yml` validates the learner and saved artifacts, then
publishes `report/` as the Pages artifact on pushes to `main`. There is no separate
online report source. Repository Pages settings must use GitHub Actions. Hosting
requires no server-side Python and does not run training on page load.

## Project map

```text
code/           Learner, experiment runner, numerical checks, editable HTML template
configs/        Complete main experimental specification
results/        120 main-run outputs, exact references, and ensemble plot data
experiments/    Corrected pilot plus clearly marked superseded historical evidence
report/         Offline/online report, local evidence downloads, figures, and PDF
scripts/        Report generation, verification, browser checks, ZIP packaging
docs/           Requirements, data dictionary, learning guide, and QA records
.github/        Pages deployment workflow
```

Start with `docs/learning-guide.md` for a guided explanation, and
`docs/data-dictionary.md` to connect files to the report. `docs/requirements.md`
tracks the assignment deliverables. Graph connectivity is an explicit interpretation
of Figure 1; we abstract rooms rather than impose an undocumented rectangular grid.

## Attribution and AI use

The report cites Sutton and Barto, Watkins and Dayan, the course assignment, and
GitHub's hosting documentation. The implementation and diagrams were written for
this project, with OpenAI Codex assistance. Full scope and verification are disclosed
in the report. No AI-generated numerical result is presented as experiment output.
