"""Independent numerical checks for the modelling choices that matter."""
import json
import unittest
from pathlib import Path

import numpy as np

from qlearning import RoomWorld, bellman_residual, choose_action, reference_q, sustained_threshold_episode, train, update

CONFIG = json.loads((Path(__file__).resolve().parents[1] / "configs/experiments.json").read_text())


class QLearningChecks(unittest.TestCase):
    def setUp(self):
        self.world = RoomWorld(CONFIG["graph"], "F")

    def test_terminal_update_never_bootstraps(self):
        q = np.full((6, 6), 999.0)
        q[1, 5] = 0
        target = update(q, 1, 5, 1, 5, True, [], .1, .9)
        self.assertEqual(target, 1)
        self.assertAlmostEqual(q[1, 5], .1)

    def test_nonterminal_update_uses_legal_maximum(self):
        q = np.full((6, 6), 999.0)
        q[2, 3], q[3, 1], q[3, 2], q[3, 4] = .2, .4, .6, .3
        target = update(q, 2, 3, 0, 3, False, self.world.actions[3], .1, .9)
        self.assertAlmostEqual(target, .54)
        self.assertAlmostEqual(q[2, 3], .234)

    def test_legal_actions_and_terminal_state(self):
        with self.assertRaises(ValueError):
            self.world.step(self.world.index["A"], self.world.index["F"])
        with self.assertRaises(ValueError):
            self.world.step(self.world.index["F"], self.world.index["B"])
        self.assertEqual(self.world.step(1, 5), (5, 1, True))

    def test_random_ties_and_exploration_ignore_invalid_cells(self):
        q = np.full((6, 6), 999.0)
        q[3, self.world.actions[3]] = 0
        rng = np.random.default_rng(100)
        observed = {choose_action(q, 3, self.world.actions[3], 0, rng) for _ in range(200)}
        self.assertEqual(observed, set(self.world.actions[3]))

    def test_oracle_matches_independent_value_iteration_for_all_goals(self):
        # This independent iterative solution does not use graph distances.
        for goal in CONFIG["graph"]:
            world = RoomWorld(CONFIG["graph"], goal)
            values = np.zeros(6)
            for _ in range(100):
                previous = values.copy()
                for s, actions in enumerate(world.actions):
                    values[s] = max((1.0 if a == world.goal_index else .9 * previous[a] for a in actions), default=0)
            expected = np.zeros((6, 6))
            for s, actions in enumerate(world.actions):
                for a in actions:
                    expected[s, a] = 1 if a == world.goal_index else .9 * values[a]
            np.testing.assert_allclose(reference_q(world, .9), expected, atol=1e-12)
            self.assertLess(bellman_residual(world, expected, .9), 1e-12)

    def test_time_limit_remains_nonterminal(self):
        # A has only E as an action; after one step A-to-F is truncated, not terminal.
        settings = {**CONFIG["defaults"], "episodes": 1, "max_steps": 1}
        result = train(self.world, "A", settings, 0)
        self.assertEqual(result["trace"][-1]["truncated"], 1)
        self.assertEqual(result["trace"][-1]["terminated"], 0)
        self.assertEqual(result["visits"][0, 4], 1)

    def test_seed_replay_and_initial_zero_table(self):
        settings = {**CONFIG["defaults"], "episodes": 40}
        first, second = [train(self.world, "C", settings, 7) for _ in range(2)]
        np.testing.assert_array_equal(first["q"], second["q"])
        self.assertEqual(first["trace"], second["trace"])
        self.assertTrue((first["initial"] == 0).all())

    def test_stability_requires_a_sustained_suffix(self):
        trace = [{"episode": i, "error": v} for i, v in enumerate([1, .1, .8, .1, .1, .1])]
        self.assertEqual(sustained_threshold_episode(trace, "error", .5, 3), 3)
        self.assertIsNone(sustained_threshold_episode(trace, "error", .5, 4))

    def test_start_at_goal_has_no_updates(self):
        run = train(self.world, "F", {**CONFIG["defaults"], "episodes": 2}, 0)
        self.assertEqual(run["visits"].sum(), 0)
        self.assertEqual(run["trace"][-1]["steps"], 0)
        self.assertEqual(run["trace"][-1]["terminated"], 1)


if __name__ == "__main__":
    unittest.main()
