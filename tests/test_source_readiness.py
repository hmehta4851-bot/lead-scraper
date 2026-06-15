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
        self.assertEqual(len(attempted), 4)
        self.assertEqual(report["sources"][0]["status"], "failed")
        self.assertTrue(report["ready"])


if __name__ == "__main__":
    unittest.main()
