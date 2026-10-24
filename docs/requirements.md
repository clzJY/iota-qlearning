# Assignment requirements

Source: `../IOTA_Assignment-1.pdf`, four pages, reviewed on 24 October 2026.
The brief states a due date of 24 October 2026; it does not specify a time of day.
This checklist paraphrases the requirements and distinguishes them from proposed
project choices.

## Implementation and evidence

- [x] Implement tabular Q-learning and support different states and actions.
- [x] Define states, legal actions, transitions, rewards, and termination conditions.
- [x] Identify the original start and target configuration explicitly.
- [x] Run the modified configuration with start A and target C.
- [x] State Q initialization, learning rate, discount factor, exploration strategy,
      episode budget, and random seeds.
- [x] Save and show initial and final Q-tables for both configurations.
- [x] Save numerical training traces and generate convergence plots for both cases.
- [x] Explain the metric in each plot and the criterion used to judge convergence.
- [x] Distinguish observed stabilization from an optimality guarantee.
- [x] Compare learned values, policies, and learning behaviour using evidence.
- [x] Discuss limitations and unexpected observations; use repeated runs where
      reliability claims require them.
- [x] Separate effects of changed configuration from stochastic variation.

## Technical report

- [x] Write for a postgraduate reader with basic reinforcement learning knowledge.
- [x] Explain the learning problem, update rule, implementation, and action selection.
- [x] Build a narrative connecting questions, experiments, evidence, and conclusions.
- [x] Keep key tables, plots, and conclusions visible without interaction.
- [x] Give plots labeled axes and captions; provide text alternatives for key visuals.
- [x] Label illustrative demonstrations separately from experimental evidence.
- [x] Include takeaways and references for external sources, adapted code, and assets.
- [x] Include author name and student ID.
- [x] Include a short AI-use statement naming tools, their contributions, and checks.
- [x] Ensure every reported experimental result is backed by a verified run.

## Submission and reproducibility

- [x] Prepare one clearly organized ZIP archive. Submission to the course portal remains a student action.
- [x] Include `report/index.html` with every required local asset.
- [x] Ensure the report is readable without an account, paid service, or AI tool.
- [x] Document direct browser opening or a simple local-server command.
- [x] Include editable report source and build instructions if a generator is used.
- [x] Include dependency versions, configurations, seeds, and exact commands for
      both experiments and figure regeneration.
- [x] Save initial and final Q-tables and plot data in machine-readable form.
- [x] Connect report claims to identifiable experiment outputs.
- [x] Include the public URL if hosting is used, alongside the offline HTML export.

## Grading weights

| Area | Weight |
| --- | ---: |
| Q-learning implementation | 30% |
| Experimental evidence and analysis | 30% |
| Technical communication and visual explanation | 20% |
| Creativity and insight | 10% |
| Reproducibility and transparency | 10% |

## Requirements versus choices

HTML and a reproducible ZIP are required. Public hosting, interactivity, Python,
and a particular website framework are optional. A PDF alone does not satisfy the
report requirement. The user prefers GitHub hosting and iterative website refinement;
this project will support those preferences while retaining an offline report.

## Student review

- [ ] Chenglong Zhang has reviewed and understood the implementation, modelling assumptions, evidence, and AI-use statement before course submission.

The technical checklist records the prepared project deliverables; it does not claim that the student has performed this review or submitted the archive.
