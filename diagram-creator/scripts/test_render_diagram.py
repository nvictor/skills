import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import render_diagram as r


def node(name, x, y, width=40, height=40):
    return r.NodeLayout(name, name, 'process', False, None, 'bottom', x, y,
                        width, height, 'section', 'lane')


class EdgeGeometryTests(unittest.TestCase):
    def setUp(self):
        self.source = node('source', 100, 200)
        self.target = node('target', 400, 200)
        self.nodes = {n.node_id: n for n in (self.source, self.target)}

    def obstacles(self):
        return [(key, n.rect.inflate(r.EDGE_CLEARANCE)) for key, n in self.nodes.items()]

    def check(self, points, extra=()):
        return r.checked_edge_path(points, self.source, self.target,
                                   self.obstacles() + list(extra), self.nodes)

    def route(self, extra=()):
        return r.route_connection_points({'from': 'source', 'to': 'target', 'route': 'direct'},
                                         self.nodes, self.obstacles() + list(extra), 600, 600)

    def test_clear_straight_route(self):
        points = self.route()
        self.assertTrue(all(y == 220 for x, y in points))
        self.assertIn('399.0 220.0', self.check(points))

    def test_adjacent_nodes_stay_straight(self):
        self.target.x = 158
        self.assertEqual(self.route(), [(140,220),(158,220)])
        self.target.x = 100
        self.target.y = 258
        self.assertEqual(self.route(), [(120,240),(120,258)])

    def test_intervening_node_routes_around(self):
        self.nodes['blocker'] = node('blocker', 250, 190)
        points = self.route()
        self.check(points)
        self.assertTrue(any(y != 220 for x, y in points))

    def test_source_and_target_reentry_rejected(self):
        for points in (
            [(140,220),(158,220),(120,220),(382,220),(400,220)],
            [(140,220),(158,220),(420,220),(382,220),(400,220)],
        ):
            with self.subTest(points=points), self.assertRaises(r.DiagramError):
                self.check(points)

    def test_endpoint_label_is_obstacle(self):
        label = [('node_label:source', r.Rect(148,205,180,235).inflate(6))]
        points = self.route(label)
        self.check(points, label)
        self.assertNotEqual(points[0], (140,220))

    def test_port_segment_collision_rejected(self):
        self.nodes['tiny'] = node('tiny', 147, 219, 2, 2)
        with self.assertRaisesRegex(r.DiagramError, 'tiny'):
            self.check([(140,220),(158,220),(382,220),(400,220)])

    def test_arrowhead_collision_rejected(self):
        # Centerline clears this text, but the marker's wing does not.
        extra = [('text', r.Rect(390,223,396,225).inflate(6))]
        with self.assertRaisesRegex(r.DiagramError, 'Arrowhead.*text'):
            r.final_edge_path([(140,220),(158,220),(382,220),(400,220)],
                              self.source, self.obstacles() + extra, self.nodes)

    def test_unsafe_rounding_falls_back_to_square(self):
        points = [(140,220),(158,220),(200,220),(200,300),
                  (382,300),(382,220),(400,220)]
        extra = [('text', r.Rect(193,224,195,226).inflate(6))]
        # Isolate final-path validation from clearance-route validation.
        path = r.final_edge_path(points, self.source, self.obstacles() + extra, self.nodes)
        self.assertIn('Q 200.0 220.0 200.0 220.0', path)
        self.assertIn('Q 200.0 300.0 210.0 300.0', path)

    def test_stroke_collision_rejected(self):
        extra = [('text', r.Rect(250,220.5,260,223).inflate(6))]
        with self.assertRaisesRegex(r.DiagramError, 'Stroke.*text'):
            r.final_edge_path([(140,220),(158,220),(382,220),(400,220)],
                              self.source, self.obstacles() + extra, self.nodes)

    def test_simplification_preserves_reversal(self):
        points = [(0,0),(10,0),(0,0),(0,10)]
        self.assertEqual(r.simplify_points(points), points)

    def test_impossible_cli_preserves_output(self):
        spec = {'diagram': {'title': 'Blocked', 'sections': [{
            'id':'s', 'title':'S', 'layout':{'type':'flow','direction':'horizontal'},
            'lanes':[{'id':'l','direction':'horizontal','groups':[{'type':'sequential','nodes':['a']}]}],
            'nodes':[{'id':'a','label':'A','type':'process'}]}],
            'connections':[{'from':'a','to':'a'}]}}
        section = spec['diagram']['sections'][0]
        section['nodes'].append({'id':'b','label':'B','type':'process'})
        section['lanes'].append({'id':'second','direction':'horizontal',
                                 'groups':[{'type':'sequential','nodes':['b']}]})
        spec['diagram']['connections'] = [{'from':'a','to':'b'}]
        normalized = r.validate_spec(spec)
        _, nodes, _, _ = r.layout_diagram(normalized['diagram'])
        section['lanes'][1]['x_offset'] = nodes['a'].x - nodes['b'].x
        section['lanes'][1]['y_offset'] = nodes['a'].y - nodes['b'].y
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)/'spec.json'; src.write_text(json.dumps(spec))
            validation = subprocess.run([sys.executable, r.__file__, str(src), '--validate-only'],
                                        capture_output=True, text=True)
            self.assertNotEqual(validation.returncode, 0)
            self.assertIn('a->b', validation.stdout)
            out = Path(folder)/'diagram.svg'
            for existing in (False, True):
                if existing:
                    out.write_text('keep me')
                result = subprocess.run([sys.executable, r.__file__, str(src), '--output', str(out)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                if existing:
                    self.assertEqual(out.read_text(), 'keep me')
                else:
                    self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
