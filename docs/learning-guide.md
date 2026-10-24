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

Starting at C, the shortest route C → D → B → F takes three transitions. Its first
action therefore has value 0 + 0.9 × 0 + 0.9² × 1 = 0.81. The exponent is two,
not three: the immediate reward is discounted by gamma to the power zero.

## Work through one update

For a nonterminal transition, suppose current Q is 0.2, reward is 0, and the best
legal next Q is 0.6. With alpha 0.1 and gamma 0.9:

```text
target = 0 + 0.9 × 0.6 = 0.54
TD error = 0.54 − 0.2 = 0.34
new Q = 0.2 + 0.1 × 0.34 = 0.234
```

If that transition instead enters the target, the observed reward is 1 and there
is no future action. The target is 1, so the same current Q becomes 0.28. Explain
why adding a discounted future value in this terminal case would change the model.
These are illustrative calculations, not a claim about a particular saved episode.

The first two tests in `code/test_qlearning.py` check these numerical principles.
One deliberately fills invalid or terminal cells with a large number to ensure
they cannot contaminate the update.

## Why explore when we already know a good action

Epsilon-greedy sometimes samples a legal alternative rather than the current best
estimate. Without this forced exploration, a positive-valued route can dominate
selection while other actions remain poorly estimated. Exact ties are still broken
randomly when epsilon is zero; zero epsilon does not remove all randomness.

Compare `original` and `no_exploration` in `results/summary.csv`. Both reach the goal
in three greedy steps across all 20 seeds. Only the former learns the whole table
to the specified tolerance. Explain how success, stability, and full-table accuracy
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
