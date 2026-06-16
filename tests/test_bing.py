import unittest

from scrapers.bing import _rss_results


class BingTests(unittest.TestCase):
    def test_rss_fallback_extracts_independent_business_results(self):
        xml = """<?xml version="1.0"?>
        <rss><channel>
          <item>
            <title>Acme Fitness Gym - Mumbai</title>
            <link>https://acmefitness.example/contact</link>
            <description>Call 98765 43211 for membership.</description>
          </item>
          <item>
            <title>LinkedIn</title>
            <link>https://linkedin.com/company/acme</link>
            <description>Skip social directory.</description>
          </item>
        </channel></rss>
        """
        leads = _rss_results(xml, max_results=5)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["company"], "Acme Fitness Gym")
        self.assertEqual(leads[0]["phone"], "9876543211")
        self.assertEqual(leads[0]["source"], "Bing")


if __name__ == "__main__":
    unittest.main()
