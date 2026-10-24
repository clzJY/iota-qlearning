# Experimental data dictionary

The main evidence is in `results/`. Each case has 20 seed folders and one ensemble
CSV. The complete specification is `configs/experiments.json`; `results/config.json`
is the exact configuration used for the main runs. The retained pilot follows the
same schema in `experiments/pilot_3000/`.

## Per-run files

| File | Meaning |
| --- | --- |
| `initial_q.csv` | Zero table at episode 0, with legal actions explicit |
| `final_q.csv` | Table after the complete episode budget |
| `visits.csv` | Number of updates to each valid state-action pair |
| `snapshots.csv` | Full tables at recorded checkpoints, including episode 0 and the final episode |
| `trace.csv.gz` | Gzip-compressed CSV with one row per episode plus initialization |
| `metadata.json` | Configuration, settings, seed, RNG, versions, code/config hashes, summary, all-start greedy evaluation |

Q-table rows name the current room, and columns name the destination action.
An empty cell means the action is unavailable. The target row is entirely empty
because episodes end there. Numeric zero means a valid pair whose current estimate
or visit count is zero. Empty cells must not be interpreted as numeric estimates.

Snapshots are recorded at episodes 0, 1, 10, 50, 100, 300, 1,000, and the final
episode. The interactive report uses seed 0 snapshots from saved CSVs.

## Trace fields

| Field | Definition |
| --- | --- |
| `episode` | Completed episode count; 0 is initialization |
| `steps` | Number of transitions in this episode |
| `return` | Undiscounted sum of observed rewards, 1 for goal entry and 0 otherwise in this model |
| `terminated` | 1 if the goal was reached, 0 otherwise |
| `truncated` | 1 if the step cap stopped a nonterminal episode |
| `total_steps` | Cumulative training transitions through this episode |
| `delta_q` | Maximum absolute change between this episode's start and end Q-tables over valid pairs |
| `max_abs_error` | Maximum absolute difference from exact Q* over all valid pairs |
| `bellman_residual` | Maximum absolute difference between Q and its optimal Bellman backup over valid pairs |
| `min_visits` | Smallest cumulative update count among valid pairs |
| `unvisited_pairs` | Number of valid pairs with zero cumulative updates |
| `start_value` | Maximum current Q-value over legal actions at the configured start |

The `return` field measures undiscounted reward and does not distinguish successful
routes of different lengths. The objective represented by Q discounts future rewards;
the report therefore also evaluates greedy path lengths against graph distances.

For an ordinary move, the Bellman target is `gamma * max_legal Q(next, action)`.
For target entry, it is 1. These diagnostics use the known model but never supply
training actions or learning targets to the learner. Training uses only sampled
transitions, rewards, and its own Q-table.

## Ensemble and summary files

`aggregate.csv` has episode plus the 10th percentile, median, and 90th percentile
across seeds for six metrics: `max_abs_error`, `delta_q`, `bellman_residual`,
`min_visits`, `total_steps`, and `start_value`. NumPy's default linear quantile
interpolation is used. Every episode is retained. Seed bands are descriptive
variation, not confidence intervals for a population mean.

`summary.csv` and `summary.json` have one record per case and seed. They include
final diagnostics, coverage, transition count, time-limit count, greedy route,
shortest-path distance, and threshold episodes. Greedy evaluation breaks exact
ties alphabetically; it consumes none of the training RNG stream.

`error_threshold_episode` is the first episode in the final contiguous suffix for
which full-table error stays strictly below 0.001, provided the suffix contains at
least 100 training episodes. `delta_threshold_episode` applies the same rule to
episode changes. Episode 0 is excluded. A null value means the run did not satisfy
the suffix criterion within its budget; it is censored, not zero. The threshold
is retrospective and is not used for early stopping.

Each case also includes `reference_q.csv`, the exact distance-based reference.
There is no rounding before saving CSVs. The main report tables round to three decimals (zero is shown as 0); the checkpoint viewer shows four decimals;
figures floor logarithmic error/change values at 1e-12 only for display.

## Provenance and reproduction

Each metadata file hashes the exact experiment config, `code/qlearning.py`, and
`code/run_experiments.py`. These source files remained unchanged between pilot and
main runs; only configuration settings changed. Pilot source copies preserve the
recorded implementation. The report is regenerated from these saved outputs and
explicit configuration, without running training. Its local CSV downloads duplicate
their canonical result files byte for byte.
