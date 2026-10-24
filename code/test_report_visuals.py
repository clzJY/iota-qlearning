"""Check that the illustrated routes obey the experimental map and physical walls."""
import copy
import json
import unittest
from pathlib import Path

from report_visuals import validate_scene

ROOT = Path(__file__).resolve().parents[1]


class RouteIllustrationChecks(unittest.TestCase):
    def test_paths_use_the_corrected_doorways_and_do_not_cross_walls(self):
        graph = json.loads((ROOT / "configs/experiments.json").read_text())["graph"]
        scene = json.loads((ROOT / "configs/floorplan.json").read_text())
        self.assertTrue(validate_scene(graph, scene))
        bad_scene = copy.deepcopy(scene)
        # Moving vertically from C to D here would pass through the solid wall.
        bad_scene["routes"][1]["points"] = [[500,420],[500,300],[375,370],[320,290],[95,260],[370,140]]
        with self.assertRaises(ValueError):
            validate_scene(graph, bad_scene)
