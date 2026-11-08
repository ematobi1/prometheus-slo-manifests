import unittest

import exporter


class ParseErrorRateTest(unittest.TestCase):
    def test_accepts_bounds(self):
        self.assertEqual(exporter.parse_error_rate("0"), 0.0)
        self.assertEqual(exporter.parse_error_rate("1"), 1.0)

    def test_rejects_out_of_range(self):
        for raw in ("-0.1", "1.5"):
            with self.assertRaises(ValueError):
                exporter.parse_error_rate(raw)

    def test_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            exporter.parse_error_rate("abc")


class RenderMetricsTest(unittest.TestCase):
    def setUp(self):
        self.saved_counts = dict(exporter.request_counts)
        for key in exporter.request_counts:
            exporter.request_counts[key] = 0

    def tearDown(self):
        exporter.request_counts.clear()
        exporter.request_counts.update(self.saved_counts)

    def test_renders_counter_per_service_and_code(self):
        exporter.request_counts[("reservations", "500")] = 7
        output = exporter.render_metrics()
        self.assertIn("# TYPE http_requests_total counter", output)
        self.assertIn('http_requests_total{service="reservations",code="500"} 7', output)
        self.assertIn('http_requests_total{service="licensing",code="200"} 0', output)
        self.assertTrue(output.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
