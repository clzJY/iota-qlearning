# Understanding this Q-learning project

Work through these questions in order. The report is a complete first version, but
understanding its modelling choices and evidence is part of the assignment.

## What is a state and what is an action

A state is a room label, such as D. An action names a neighboring room: from D,
the legal actions are B, C, and E. We do not define actions such as moving through
a wall, and we do not treat their absent Q-values as zeros when taking a maximum.

Find `RoomWorld.actions` and `RoomWorld.mask` in `code/qlearning.py`. Explain why
the row for the current target is empty even though that room has physical neighbors.
Episodes stop on goal entry, so an outgoing action there is never part of a trajectory.

## What a Q-value means

Q(D, B) estimates discounted future reward if we move from D to B now and then act
optimally. It is not a probability, a distance, or an immediate reward. With goal F,
moving D → B → F takes two transitions. Only the second transition gives reward 1,
so the exact value of D → B is 0 + 0.9 × 1 = 0.9.

With the corrected B–C doorway, the shortest route from C is C → B → F.
Its first-action value is 0 + 0.9 × 1 = 0.9. Taking C → D first can still reach F,
but the best continuation then takes two more moves, giving Q(C,D) = 0.9² = 0.81.
The modified A → E → D → C route has three moves and first-action value 0.81.

## Follow one reward back to an earlier move

Imagine the first episode follows C → B → F, starting with every Q-value at zero.
The first C → B move earns zero and initially sees no learned future value, so its
estimate stays zero. Entering F then gives reward 1:

```text
Q(B,F) = 0 + 0.1 × (1 − 0) = 0.100
```

On a later attempt, choosing C → B still gives no immediate reward. But B now has
an action worth 0.1, so the update to the earlier move becomes:

```text
target = 0 + 0.9 × 0.1 = 0.09
Q(C,B) = 0 + 0.1 × (0.09 − 0) = 0.009
```

This is the point of the worked example: a move can become useful without receiving
a reward immediately. Repeated experience propagates the goal reward back towards
the start. The 0.009 value is an early estimate; the correct final Q(C,B) is 0.9.
The example is an explicitly illustrative sequence, not a claim about a particular
saved run. The goal update has no discounted future term because the episode ends.

The numerical tests check this exact sequence and the corrected B–C connection.

## Why explore when we already know a good action

Epsilon-greedy sometimes samples a legal alternative rather than the current best
estimate. Without this forced exploration, a positive-valued route can dominate
selection while other actions remain poorly estimated. Exact ties are still broken
randomly when epsilon is zero; zero epsilon does not remove all randomness.

Compare `original` and `no_exploration` in `results/summary.csv`. All 20 exploratory runs learn the two-move route. Without forced exploration,
14 of 20 runs learn that shortest route and the remaining runs keep a longer route.
None learns the full table to the specified tolerance. Explain how success, stability, and full-table accuracy
can give different answers without contradicting one another.

## Why the start and the goal have different roles

Changing only the start changes the training distribution. It does not change the
Bellman optimality equations for a fixed environment and target. Changing the goal
changes which transition receives reward and where episodes terminate, so it changes
the value function itself. Both required configurations are trained from scratch.

Use `start_control` versus `original` to hold target F fixed. Then compare
`factorial_bf` versus `factorial_bc` to hold start B fixed. The added A/B × C/F
design avoids starting at the goal, which would produce a zero-action episode.

## How to read convergence evidence

Episode change asks how much Q changed during an episode. Reference error asks how
wrong Q is after that episode. A small update can happen because a value is accurate
or because a rarely visited action is barely being revised. Visit counts help tell
these cases apart.

The exact reference is available only because this world is tiny and deterministic.
The learner does not read it. Locate `reference_q`, then see the independent
value-iteration test. Explain why using that reference for validation does not make
the sampled Q-learning algorithm a model-based planner.

Our suffix threshold is a finite-run accuracy criterion. Constant alpha and a finite
budget are not the classical asymptotic convergence theorem. State that limitation
before describing the results as converged.

## Review before submission

Check the room connections against Figure 1 and any additional course guidance.
Walk through the learner and update tests, reproduce at least the required seed-0
runs, inspect the saved final tables and figures, and read the AI-use statement.
Confirm that every conclusion describes the actual evidence and that you can explain
the distinction between a route and the complete value function in your own words.

## Why the former sliders were replaced

The sliders changed hypothetical input numbers, not the saved experiments. The report now uses a fixed sequence: after B → F, Q(B,F) becomes 0.1; on a later C → B move, that future value makes Q(C,B) become 0.009. This makes the teaching point explicit: reward can influence an earlier move even when that move itself earns zero.

## Read the opening animation

The solid robot stays in C and the dock stays in F. Teal illustrates C → B → F,
orange C → D → B → F, and blue C → D → E → F. Faint robot echoes show possible
choices and fade as they reach F. The animation uses valid doorways, but it is not
a playback of a recorded training trajectory. The reported policies and plots below
it come from the saved experiments.


## Experiment 2 and the report guide

Experiment 2 reuses the exact room geometry, with the static robot in A and the
destination in C. Teal shows A → E → D → C (3 moves), orange A → E → F → B → C
(4 moves), and blue A → E → D → B → C (4 moves). These are legal conceptual
alternatives; the reported learned policy still comes from the saved evaluation.
Each figure has its own pause control.

The five quick links at the bottom of The Problem jump to the five named report
parts. They stay in one row and scroll horizontally on narrow screens. The sticky
reading indicator follows the current part, including which experiment is being
read. References and the AI statement are grouped with Part 5. The two Going Further questions are additional
investigations. Their visible answers are: equal route lengths do not imply equal
whole-table learning times in this protocol; and a good route can coexist with
inaccurate unvisited actions (14/20 shortest without exploration, 0/20 accurate
tables). Expand the corresponding evidence for seed summaries and plots.
