"""Collision regressions for the existing renderer, without changing routing.

Known defects intentionally fail: do not weaken assertions to match current
output. These checks cover routed centerlines; final SVG strokes, curves and
arrowheads still require visual inspection.
"""
import unittest

import render_diagram as r


def node(name, x, y, width=40, height=40):
    return r.NodeLayout(name, name, 'process', False, None, 'bottom',
                        x, y, width, height, 'section', 'lane')


def crosses_interior(a, b, rect):
    """Independent oracle. Boundary contact is allowed, interior overlap is not."""
    if a == b:
        return rect.left < a[0] < rect.right and rect.top < a[1] < rect.bottom
    if a[0] == b[0]:
        return (rect.left < a[0] < rect.right
                and max(min(a[1], b[1]), rect.top) < min(max(a[1], b[1]), rect.bottom))
    if a[1] == b[1]:
        return (rect.top < a[1] < rect.bottom
                and max(min(a[0], b[0]), rect.left) < min(max(a[0], b[0]), rect.right))
    raise AssertionError(f'Unexpected non-orthogonal segment: {a}->{b}')


def segment_intersection(a, b, c, d):
    """Return None, a contact point, or 'overlap' for orthogonal segments."""
    if a == b or c == d:
        return None
    horizontal_ab = a[1] == b[1]
    horizontal_cd = c[1] == d[1]
    if horizontal_ab == horizontal_cd:
        axis = 0 if horizontal_ab else 1
        other = 1 - axis
        if a[other] != c[other]:
            return None
        low = max(min(a[axis], b[axis]), min(c[axis], d[axis]))
        high = min(max(a[axis], b[axis]), max(c[axis], d[axis]))
        if low > high:
            return None
        if low < high:
            return 'overlap'
        return (low, a[1]) if horizontal_ab else (a[0], low)
    if not horizontal_ab:
        return segment_intersection(c, d, a, b)
    if min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(c[1], d[1]) <= a[1] <= max(c[1], d[1]):
        return (c[0], a[1])
    return None


def assert_edges_clear(test, first, second):
    """Each edge is (source id, target id, routed points)."""
    source_a, target_a, points_a = first
    source_b, target_b, points_b = second
    ports_a = [(source_a, points_a[0]), (target_a, points_a[-1])]
    ports_b = [(source_b, points_b[0]), (target_b, points_b[-1])]
    shared = {point_a for node_a, point_a in ports_a
              for node_b, point_b in ports_b if node_a == node_b and point_a == point_b}
    for a, b in zip(points_a, points_a[1:]):
        for c, d in zip(points_b, points_b[1:]):
            contact = segment_intersection(a, b, c, d)
            test.assertTrue(contact is None or contact in shared,
                            f'Edges {source_a}->{target_a} and {source_b}->{target_b} '
                            f'intersect at {contact}: {a}->{b}, {c}->{d}')


class EdgeGeometryTests(unittest.TestCase):
    def setUp(self):
        self.source = node('source', 100, 200)
        self.target = node('target', 400, 200)
        self.nodes = {n.node_id: n for n in (self.source, self.target)}

    def route(self, labels=()):
        obstacles = [(key, n.rect.inflate(r.EDGE_CLEARANCE)) for key, n in self.nodes.items()]
        obstacles.extend((key, rect.inflate(r.EDGE_CLEARANCE / 2)) for key, rect in labels)
        return r.route_connection_points(
            {'from': 'source', 'to': 'target', 'route': 'direct'},
            self.nodes, obstacles, 600, 600)

    def assert_clear(self, points, labels=()):
        obstacles = [(key, n.rect) for key, n in self.nodes.items()] + list(labels)
        for a, b in zip(points, points[1:]):
            for key, rect in obstacles:
                self.assertFalse(crosses_interior(a, b, rect),
                                 f'{a}->{b} crosses {key}: {rect}')

    def test_clear_straight_route(self):
        points = self.route()
        self.assert_clear(points)
        self.assertTrue(all(y == 220 for x, y in points))

    def test_adjacent_nodes_stay_straight(self):
        self.target.x = 158
        points = self.route()
        self.assert_clear(points)
        self.assertTrue(all(y == 220 for x, y in points))

    def test_intervening_node_routes_around(self):
        self.nodes['blocker'] = node('blocker', 250, 190)
        points = self.route()
        self.assert_clear(points)
        self.assertTrue(any(y != 220 for x, y in points))

    def test_endpoint_labels_remain_obstacles(self):
        for endpoint, rect in (
            ('source', r.Rect(148, 205, 180, 235)),
            ('target', r.Rect(365, 205, 392, 235)),
        ):
            with self.subTest(endpoint=endpoint):
                labels = [(f'node_label:{endpoint}', rect)]
                self.assert_clear(self.route(labels), labels)

    def test_short_port_segments_clear_other_nodes(self):
        self.nodes['tiny'] = node('tiny', 142, 219, 2, 2)
        self.assert_clear(self.route())

    def test_edges_do_not_cross_each_other(self):
        self.nodes['upper'] = node('upper', 250, 100)
        self.nodes['lower'] = node('lower', 250, 300)
        horizontal = self.route()
        obstacles = [(key, n.rect.inflate(r.EDGE_CLEARANCE)) for key, n in self.nodes.items()]
        vertical = r.route_connection_points(
            {'from': 'upper', 'to': 'lower', 'route': 'vertical'},
            self.nodes, obstacles, 600, 600)
        assert_edges_clear(self, ('source', 'target', horizontal), ('upper', 'lower', vertical))

    def test_shared_port_allows_contact_but_not_overlap(self):
        first = ('shared', 'a', [(0, 0), (20, 0)])
        assert_edges_clear(self, first, ('shared', 'b', [(0, 0), (0, 20)]))
        with self.assertRaises(AssertionError):
            assert_edges_clear(self, first, ('shared', 'b', [(0, 0), (10, 0), (10, 20)]))
        with self.assertRaises(AssertionError):
            assert_edges_clear(self, first, ('unrelated', 'b', [(0, 0), (0, 20)]))

    def test_collision_oracle_includes_endpoint_interiors(self):
        # Guard the independent oracle against accidentally exempting endpoints.
        for points in (
            [(140, 220), (158, 220), (120, 220), (400, 220)],
            [(140, 220), (420, 220), (382, 220), (400, 220)],
        ):
            with self.subTest(points=points), self.assertRaises(AssertionError):
                self.assert_clear(points)


if __name__ == '__main__':
    unittest.main()
