# Problem first report revision

The opening now asks how a robot can find a goal, before introducing Q-learning.
The numerical statistics strip was removed. A generated conceptual illustration
replaces the opening graph; a separate exact room map appears after the navigation
problem has been explained.

The required C-to-F and A-to-C experiments form the main narrative. Each table is
introduced with what its rows, columns, values, and unavailable actions mean. A
worked row connects the values to a learned route. Each convergence figure is
preceded by an explanation of its measures and followed by the result it supports.
The start-value panel now comes before the full-table error panel. Numerical plot
data have not changed. Main Q-tables display three decimals, with full-precision
CSV downloads retained.

The two required configurations are compared before extra experiments appear.
Controlled comparisons, exploration diagnostics, and the retained pilot are placed
in expandable sections after the required results. The printable report includes
their full content. Essential assignment results remain visible without interaction.

The original wording about what the prose did not specify was replaced with a
direct explanation: C and F are read from the robot and dock in Figure 1; A-to-C
is the explicitly required modified configuration.

## Main files

- `report/index.html` is the report that readers open and the file published online.
- `code/report_template.html` is the editable narrative and page structure.
- `scripts/build_report.py` inserts saved results and generates the figures/HTML.
- `report/assets/style.css` controls layout and print presentation.
- `report/Qlearning_Report_Chenglong_Zhang_50068179.pdf` is the printable companion.

## Illustration provenance

The built-in image-generation tool produced the conceptual scene. The final image
is `report/assets/illustrations/robot-navigation-v2.png`; its exact prompt is
`report/assets/illustrations/hero-navigation-v2.prompt.txt`. It does not specify the
experimental topology or claim an observed route. The AI-use statement identifies
this image separately from numerical evidence.

The learner, runner, configurations, main results, and pilot evidence remain
unchanged from the verified first version. Browser checks cover the new opening,
visible required tables, calculator, saved checkpoints, responsive layouts, direct
file opening, and PDF export. Numerical artifact checks continue to verify the
saved evidence and plot summaries.
