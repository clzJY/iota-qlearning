# Corrected B to C doorway and explanatory route animation

Figure 1 includes an opening between B and C. The earlier graph omitted it.
The corrected adjacency is A: E; B: C/D/F; C: B/D; D: B/C/E; E: A/D/F;
F: B/E. All main and pilot experiments were rerun from zero tables with this
seven-edge graph, preserving seeds, rewards, hyperparameters, and budgets.

## Effect on the required results

The original C-to-F shortest route is now C → B → F: two moves, with exact
first-action value 0.9. C → D first has value 0.81 and is less direct. The modified
A → E → D → C route still has three moves and exact first-action value 0.81.
The final tables, convergence plots, snapshots, repeated-run comparisons, and
narrative were regenerated from corrected runs. In the exploration ablation,
14/20 seeds learn a shortest route; the remaining six keep longer routes. These
counts replace the earlier graph's ablation findings.

## Preservation of superseded evidence

The former main results and pilot were relocated to
`experiments/superseded_missing_bc_20261024/main/` and `pilot_3000/`.
The archive README records their original locations and superseded status.
Recorded configs, metadata, hashes, numerical CSVs, traces, and source copies
were preserved. Previous numerical/browser verification records were also copied
there. Releases v1.0.0 and v1.1.0 retain the earlier report and packaged evidence.
Current canonical results are `results/` and `experiments/pilot_3000/`.

The current submission ZIP includes only the corrected main and pilot evidence;
the superseded archive remains available in the personal GitHub repository.

## Explanatory and visual changes

The opening floorplan follows the assignment's wall layout, including B–C.
`configs/floorplan.json` declares walls, doorway points, labels, and three legal
routes: C–B–F, C–D–B–F, and C–D–E–F. A geometry validator requires exact agreement
with the experiment graph and rejects route segments crossing solid walls.
The routes are illustrative alternatives, not recorded experimental trajectories.

The solid robot and dock remain fixed. Three translucent robot echoes follow the
coloured traces and fade near the destination. A pause control and reduced-motion
support are included. Print uses static full routes. Robot/dock cutouts came from
built-in image generation with transparency; exact prompts are included beside the
assets. Floorplan geometry and animation are implemented in editable SVG/CSS/JS.

The unexplained sliders were replaced by an annotated hand calculation: after
B → F, Q(B,F) becomes 0.1; on a later C → B move, Q(C,B) becomes 0.009. The teaching
point is reward propagation, with the same fixed learning settings as the runs.
A numerical check validates these two update values. AI use has a dedicated top-menu link.
