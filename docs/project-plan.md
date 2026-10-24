# Q-learning project plan

The aim is to make the algorithm, evidence, and explanation understandable together.
We will use a small Python implementation for experiments and a static HTML report
for reading, sharing, and submission. Numerical results will come from saved runs;
browser interactions will explain them without being needed to see the evidence.

## Environment interpretation

The supplied figure depicts six connected regions labeled A through F, rather than
a fully specified rectangular grid. A room graph is a natural model: a state is the
current room and an action selects an adjacent room through an opening.

Reading the openings in the figure suggests the following undirected connections:

| Room | Adjacent rooms |
| --- | --- |
| A | E |
| B | C, D, F |
| C | B, D |
| D | B, C, E |
| E | A, D, F |
| F | B, E |

This adjacency includes the B–C doorway clarified by the user from Figure 1; all current experiments were rerun with it.
We should redraw it ourselves for the report and explain that the graph preserves
room connectivity rather than physical distances.

The robot appears in C and its dock appears in F. The proposed original configuration
is therefore C to F, but the prose does not explicitly prescribe that pair. The
modified configuration A to C is explicit. We will label the original interpretation
as our assumption unless additional course information confirms it.

The brief does not prescribe rewards, learning parameters, legal-action handling,
or the exact termination model. These must be explicit project choices, rather than
unstated assumptions copied from another six-room tutorial.

## Implemented learning model

The first complete version uses these explicit choices:

- Use deterministic movement along legal edges; mask unavailable actions.
- Give reward 1 on entering the target and 0 on other legal moves.
- End the episode immediately on entering the target. Do not bootstrap from a
  terminal state, and do not introduce an undocumented goal self-loop.
- Initialize valid Q-values to zero; display invalid actions distinctly.
- Use epsilon-greedy exploration with random tie breaking among greedy actions.
- Use discount 0.9, learning rate 0.1, epsilon 0.5, a 100-step episode cap,
  and 20,000 episodes per main run. The retained pilot used epsilon 0.2 and 3,000 episodes.
- Keep time-limit truncation distinct from reaching the terminal goal. The cap is
  a sampling limit, so its final transition still bootstraps if nonterminal.

The terminal update target is the reward alone. Otherwise it is the reward plus
the discounted maximum over legal actions in the next state. Changing the target
changes the reward/termination model; changing only the initial state changes where
training trajectories begin. We will explain this distinction with actual results.

## Experimental evidence

Save one identified illustrative run and repeated runs for each configuration, using
the same declared seed list and hyperparameters. The implemented repeated-run budget is
20 seeds per configuration. Record the final budget, package versions, and exact commands with outputs.

Convergence evidence should combine:

1. Changes in the Q-table over episodes, with the precise aggregation stated.
2. Error against an independently computed reference solution for this small model,
   or a Bellman residual over all valid nonterminal state-action pairs.
3. State-action visit counts, since small updates can also indicate missing coverage.
4. Greedy policy paths, success, and path lengths, with tie handling specified.

Repeated-run plots should show both a central statistic and variation across seeds.
The two required configurations change start and target together, so their comparison
alone cannot isolate the causal effect of each. The implemented start-only control
A to F, B-to-F/B-to-C comparisons, and epsilon-zero ablation investigate that distinction.
These extra experiments are labeled separately from the required cases.

Finite-run stability is empirical evidence, not a proof of the asymptotic Q-learning
convergence conditions. Constant learning rate and a finite sampling budget must be
discussed honestly. A known-model reference is a validation tool; the learner itself
must learn from sampled transitions.

## Website and report

Use plain HTML, CSS, and small JavaScript enhancements initially. This keeps the
offline report portable and allows the same directory to be deployed to GitHub Pages.
All essential content and figures will be local, with relative asset paths and no
runtime dependency on a CDN, external API, or training process.

Suggested reading sequence:

1. The question and a concise overview of the six-room world.
2. A fixed, annotated update sequence showing how goal reward propagates back to C.
3. The exact environment and experiment settings.
4. Original configuration: initial/final tables, convergence plot, and policy.
5. Modified configuration: the same evidence in the same format.
6. Comparison across seeds, coverage diagnostics, and limits of the conclusions.
7. Lessons, reproduction instructions, references, and AI-use statement.

Potential interactions include a policy stepper, a Q-table action inspector, and illustrative route traces. They should each answer a learning question. Static captions and
summaries must remain available without using them. Design and accessibility can be
refined after the numerical story is sound. A print stylesheet can support a PDF
export from the same report.

## Development stages

| Stage | Concrete review point |
| --- | --- |
| 1. Model | Confirm room connections, original configuration, rewards, and terminal handling |
| 2. Learner | Walk through a hand-calculated update and check the implementation |
| 3. Experiments | Inspect saved tables, plots, coverage, and repeated-run variation |
| 4. Report | Read the complete static narrative and verify every numerical claim |
| 5. Website refinement | Improve layout, mobile reading, accessibility, and useful interactions |
| 6. Release | Verify offline assets, reproduction commands, GitHub Pages URL, and ZIP contents |

The author is Chenglong Zhang, student ID 50068179. All development stays within
this project directory. The source PDF is retained locally as the assignment brief.
The complete first version includes a static report, an optional PDF export, saved
main and pilot evidence, verification tools, and a submission packager. Publication
uses the personal clzJY/iota-qlearning repository. Student understanding and review
remain the next collaborative step; automated checks do not replace that review.
