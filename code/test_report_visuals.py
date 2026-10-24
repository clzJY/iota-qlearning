"""Check that the illustrated routes obey the experimental map and physical walls."""
import copy
import json
import unittest
from pathlib import Path

from report_visuals import load_scene, route_scene, validate_scene

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

    def test_modified_figure_reuses_geometry_and_stops_in_c(self):
        graph = json.loads((ROOT / "configs/experiments.json").read_text())["graph"]
        original, modified = load_scene(), load_scene("modified")
        for key in ["bounds", "walls", "doorways", "viewbox"]:
            self.assertEqual(original[key], modified[key])
        self.assertTrue(validate_scene(graph, modified))
        self.assertEqual((modified["start"], modified["goal"]), ("A", "C"))
        for route in modified["routes"]:
            self.assertEqual(route["states"][0], "A")
            self.assertEqual(route["states"][-1], "C")
            self.assertNotIn("C", route["states"][:-1])
        # Ensure both inline figures can coexist without duplicate animation IDs.
        from html.parser import HTMLParser
        class Ids(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
            def handle_starttag(self, tag, attrs):
                self.ids.extend(value for key,value in attrs if key == "id")
        parser = Ids()
        parser.feed(route_scene(graph) + route_scene(graph, "modified"))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
