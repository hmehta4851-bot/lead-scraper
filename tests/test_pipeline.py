import json
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from config import VERTICALS, iter_products
from keyword_library import select_rotating_keywords
from state import advance_city


class PipelineTests(unittest.TestCase):
    def test_all_nine_sources_are_attempted_despite_failures(self):
        attempted = []

        def successful(keyword, city, max_results):
            attempted.append("ok")
            return []

        def failed(keyword, city, max_results):
            attempted.append("failed")
            raise TimeoutError("blocked")

        registry = tuple(
            (f"Source {index}", failed if index == 3 else successful)
            for index in range(9)
        )
        with patch.object(main, "SOURCE_REGISTRY", registry), patch(
            "main.time.sleep", return_value=None
        ):
            leads, telemetry = main.run_all_sources("turf", "Mumbai")

        self.assertEqual(leads, [])
        self.assertEqual(len(attempted), 9)
        self.assertEqual(len(telemetry["attempted"]), 9)
        self.assertEqual(list(telemetry["failed"]), ["Source 3"])

    def test_competitor_is_blocked_by_company_or_domain(self):
        self.assertTrue(
            main.is_competitor(
                {"company": "Mondo India Sports Pvt Ltd", "website": ""}
            )
        )
        self.assertTrue(
            main.is_competitor(
                {
                    "company": "Example Projects",
                    "website": "https://www.polytan.example/contact",
                }
            )
        )
        self.assertFalse(
            main.is_actionable_lead(
                {
                    "company": "Sunzone Sports",
                    "phone": "9876543210",
                    "website": "https://sunzone.in",
                }
            )
        )

    def test_vertical_catalog_is_complete(self):
        self.assertEqual(
            set(VERTICALS),
            {
                "Playful",
                "Graceful",
                "Powerful",
                "Joyful",
                "Acryplay",
                "Track & Field",
                "Sports Equipment",
                "Woodplay",
            },
        )
        products = list(iter_products())
        self.assertEqual(len(products), 18)
        self.assertEqual(len({product for _, _, product, _ in products}), 18)

    def test_keyword_library_is_globally_unique_and_complete(self):
        data = json.loads(Path("keyword_library.json").read_text())
        keywords = [
            keyword
            for products in data.values()
            for product_keywords in products.values()
            for keyword in product_keywords
        ]
        self.assertEqual(len(data), 8)
        self.assertEqual(sum(map(len, data.values())), 18)
        self.assertGreaterEqual(len(keywords), 29373)
        self.assertEqual(len(keywords), len({k.casefold() for k in keywords}))

    def test_keyword_rotation_uses_independent_product_cursor(self):
        selected, next_cursor = select_rotating_keywords(
            "Joyful",
            "PVC / Vinyl Badminton Flooring",
            [],
            {"Joyful::PVC / Vinyl Badminton Flooring": 1},
            count=2,
        )
        self.assertEqual(len(selected), 2)
        self.assertEqual(next_cursor, 3)

    def test_keyword_rotation_falls_back_if_library_is_unavailable(self):
        with patch(
            "keyword_library.load_keyword_library",
            side_effect=FileNotFoundError,
        ):
            selected, next_cursor = select_rotating_keywords(
                "Example",
                "Product",
                ["first", "second"],
            {},
            count=1,
            city="Mumbai",
        )
        self.assertEqual(selected, ["first"])
        self.assertEqual(next_cursor, 1)

    def test_city_placeholder_is_replaced_before_search(self):
        with patch(
            "keyword_library.load_keyword_library",
            return_value={"Example": {"Product": ["installer in [city]"]}},
        ):
            selected, _ = select_rotating_keywords(
                "Example",
                "Product",
                [],
                {},
                city="Pune",
            )
        self.assertEqual(selected, ["installer in Pune"])

    def test_phone_dedup_normalizes_indian_formats(self):
        leads = main._deduplicate(
            [
                {"company": "Acme Sports", "phone": "+91 98765 43210"},
                {"company": "Acme Sports Pvt Ltd", "phone": "09876543210"},
            ]
        )
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["phone"], "9876543210")

    def test_source_balancing_keeps_smaller_sources_visible(self):
        raw = []
        for index in range(8):
            raw.append(
                {
                    "company": f"Large {index}",
                    "phone": f"98765432{index:02d}",
                    "source": "Large Source",
                }
            )
        raw.append(
            {
                "company": "Specialist",
                "phone": "9123456789",
                "source": "Small Source",
            }
        )
        registry = (
            ("Large Source", lambda *args, **kwargs: raw[:-1]),
            ("Small Source", lambda *args, **kwargs: raw[-1:]),
        )
        with patch.object(main, "SOURCE_REGISTRY", registry), patch(
            "main.time.sleep", return_value=None
        ), patch("main.resolve_contact_names", return_value=None):
            leads, _ = main.scrape_product(["test"], "Mumbai", target=3)
        self.assertEqual(
            [lead["source"] for lead in leads],
            ["Large Source", "Small Source", "Large Source"],
        )

    def test_city_cycle_records_each_transition(self):
        state = {
            "tier": 1,
            "city_index": 0,
            "exhausted_tier1": False,
            "exhausted_tier2": False,
            "keyword_cursors": {},
            "last_transition": "",
        }
        with patch("state.save_state", return_value=None):
            advance_city(state, ["Mumbai"], ["Jaipur"])
            self.assertEqual(state["last_transition"], "tier1_to_tier2")
            advance_city(state, ["Mumbai"], ["Jaipur"])
            self.assertEqual(state["last_transition"], "tier2_to_tier1")


if __name__ == "__main__":
    unittest.main()
