import unittest

from source_readiness import probe_sources


class SourceReadinessTests(unittest.TestCase):
    def test_readiness_requires_multiple_sources_across_two_groups(self):
        productive = lambda *args, **kwargs: [{"company": "Buyer"}]
        empty = lambda *args, **kwargs: []
        registry = (
            ("Sulekha", productive),
            ("DuckDuckGo", productive),
            ("IndiaMART", empty),
        )
        report = probe_sources("gym", "Mumbai", registry)
        self.assertTrue(report["ready"])
        self.assertEqual(report["attempted_count"], 3)
        self.assertEqual(
            report["productive_groups"],
            ["directories", "search engines"],
        )
        marketplace = next(
            source
            for source in report["sources"]
            if source["source"] == "IndiaMART"
        )
        self.assertEqual(marketplace["keyword"], "artificial grass")

    def test_single_source_group_is_not_ready(self):
        productive = lambda *args, **kwargs: [{"company": "Buyer"}]
        registry = (
            ("DuckDuckGo", productive),
            ("Bing", productive),
            ("Yahoo", productive),
        )
        report = probe_sources("gym", "Mumbai", registry)
        self.assertFalse(report["ready"])

    def test_exception_is_isolated_and_every_source_is_attempted(self):
        attempted = []

        def failed(*args, **kwargs):
            attempted.append("failed")
            raise TimeoutError("blocked")

        def successful(*args, **kwargs):
            attempted.append("successful")
            return [{"company": "Buyer"}]

        registry = (
            ("Sulekha", failed),
            ("DuckDuckGo", successful),
            ("Bing", successful),
            ("Google Maps", successful),
        )
        report = probe_sources("gym", "Mumbai", registry)
        self.assertEqual(len(attempted), 5)
        self.assertEqual(report["sources"][0]["status"], "failed")
        self.assertEqual(report["sources"][0]["attempts"], 2)
        self.assertTrue(report["ready"])

    def test_degraded_source_is_retried_and_can_recover(self):
        calls = []

        def flaky(*args, **kwargs):
            calls.append("flaky")
            if len(calls) == 1:
                print("[Source] Error: temporary")
                return []
            return [{"company": "Recovered Buyer"}]

        productive = lambda *args, **kwargs: [{"company": "Buyer"}]
        report = probe_sources(
            "gym",
            "Mumbai",
            (
                ("Sulekha", flaky),
                ("DuckDuckGo", productive),
            ),
        )
        self.assertTrue(report["ready"])
        self.assertEqual(calls, ["flaky", "flaky"])
        self.assertEqual(report["sources"][0]["status"], "productive")
        self.assertEqual(report["sources"][0]["attempts"], 2)


if __name__ == "__main__":
    unittest.main()
