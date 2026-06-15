import json
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import main
from config import MAX_LEADS_PER_SOURCE_PER_VERTICAL, VERTICALS, iter_products
from keyword_library import (
    add_buyer_intent,
    load_keyword_library,
    select_rotating_keywords,
)
from keyword_rules import validate_keyword_library, validate_product_keyword
from state import (
    complete_city_batch,
    get_batch_start_index,
    get_scheduled_city,
)
from qualification import qualify_lead
from sku_catalog import (
    format_sku_target,
    load_sku_catalog,
    select_rotating_sku,
    validate_sku_routes,
)


class PipelineTests(unittest.TestCase):
    def test_workflow_has_early_missed_schedule_recovery(self):
        repo_root = Path(__file__).resolve().parents[1]
        daily = (repo_root / ".github/workflows/daily.yml").read_text()
        watchdog = (
            repo_root / ".github/workflows/watchdog.yml"
        ).read_text()

        self.assertIn('cron: "17 2 * * 1-6"', daily)
        self.assertIn('cron: "47 2 * * 1-6"', watchdog)
        self.assertIn('cron: "17 3 * * 1-6"', watchdog)
        self.assertIn('cron: "17 5 * * 1-6"', watchdog)
        self.assertIn('cron: "17 9 * * 1-6"', watchdog)
        self.assertIn("gh workflow run daily.yml", watchdog)

    def test_all_sources_are_attempted_despite_failures(self):
        attempted = []

        def successful(keyword, city, max_results):
            attempted.append("ok")
            return []

        def failed(keyword, city, max_results):
            attempted.append("failed")
            raise TimeoutError("blocked")

        registry = tuple(
            (f"Source {index}", failed if index == 3 else successful)
            for index in range(11)
        )
        with patch.object(main, "SOURCE_REGISTRY", registry), patch(
            "main.time.sleep", return_value=None
        ):
            leads, telemetry = main.run_all_sources("turf", "Mumbai")

        self.assertEqual(leads, [])
        self.assertEqual(len(attempted), 11)
        self.assertEqual(len(telemetry["attempted"]), 11)
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
        self.assertTrue(
            main.is_own_brand(
                {
                    "company": "Gym Sports Flooring",
                    "website": "https://www.sunzonesport.com/product",
                }
            )
        )
        self.assertTrue(
            main.is_competitor(
                {"company": "CC Grass India", "phone": "9876543210"}
            )
        )
        self.assertFalse(
            main.is_competitor(
                {"company": "Garcomondo Fitness Gym", "phone": "9876543210"}
            )
        )

    def test_vertical_and_sku_catalogs_are_complete(self):
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
        skus = load_sku_catalog()
        self.assertEqual(len(skus), 170)
        self.assertEqual(
            sum(record["catalogue_type"] == "SKU" for record in skus),
            152,
        )
        self.assertEqual(
            sum(
                record["catalogue_type"] == "Website system"
                for record in skus
            ),
            18,
        )
        self.assertEqual(validate_sku_routes(VERTICALS), [])
        self.assertEqual(
            {record["vertical"] for record in skus},
            set(VERTICALS),
        )
        covered_families = {
            (record["vertical"], record["search_family"])
            for record in skus
        }
        expected_families = {
            (vertical, product)
            for vertical, config in VERTICALS.items()
            for product in config["products"]
        }
        self.assertEqual(covered_families, expected_families)

    def test_sku_rotation_stays_inside_product_family(self):
        cursors = {}
        first = select_rotating_sku(
            "Powerful",
            "Gym Astro Turf / Sled Track Turf",
            cursors,
        )
        second = select_rotating_sku(
            "Powerful",
            "Gym Astro Turf / Sled Track Turf",
            cursors,
        )
        self.assertEqual(first["vertical"], "Powerful")
        self.assertEqual(
            first["search_family"],
            "Gym Astro Turf / Sled Track Turf",
        )
        self.assertNotEqual(first["display_name"], second["display_name"])
        label = format_sku_target(first)
        self.assertIn(first["search_family"], label)
        self.assertIn(f"SKU target: {first['display_name']}", label)

    def test_rotation_completes_maharashtra_before_other_states(self):
        maharashtra = [
            city for city in main.INDIA_CITY_ROTATION
            if city.endswith(", Maharashtra")
        ]
        self.assertEqual(len(maharashtra), 509)
        self.assertEqual(
            main.INDIA_CITY_ROTATION[0],
            "Mumbai, Maharashtra",
        )
        self.assertEqual(
            main.INDIA_CITY_ROTATION[:509],
            maharashtra,
        )
        self.assertFalse(
            any(
                city.endswith(", Maharashtra")
                for city in main.INDIA_CITY_ROTATION[509:]
            )
        )

    def test_first_city_receives_every_keyword_round(self):
        for round_number in range(1, main.MAX_SAME_CITY_ROUNDS):
            self.assertFalse(
                main.should_add_next_town(
                    city_offset=0,
                    round_number=round_number,
                    no_progress_rounds=1,
                )
            )
        self.assertTrue(
            main.should_add_next_town(
                city_offset=0,
                round_number=main.MAX_SAME_CITY_ROUNDS,
                no_progress_rounds=1,
            )
        )
        self.assertTrue(
            main.should_add_next_town(
                city_offset=1,
                round_number=1,
                no_progress_rounds=1,
            )
        )

    def test_keyword_library_is_globally_unique_and_complete(self):
        data = load_keyword_library()
        keywords = [
            keyword
            for products in data.values()
            for product_keywords in products.values()
            for keyword in product_keywords
        ]
        self.assertEqual(len(data), 8)
        self.assertEqual(sum(map(len, data.values())), 18)
        self.assertGreaterEqual(len(keywords), 10000)
        self.assertEqual(len(keywords), len({k.casefold() for k in keywords}))
        self.assertEqual(validate_keyword_library(data), [])

    def test_cross_product_keywords_fail_closed(self):
        cases = [
            (
                "Powerful",
                "Gym Rubber Tiles / Laminate Tiles / Mats",
                "25mm playground rubber tile",
            ),
            (
                "Sports Equipment",
                "Sports Equipment / Turnkey Facility",
                "30mm rubber flooring",
            ),
            (
                "Joyful",
                "PVC / Vinyl Badminton Flooring",
                "badminton wooden flooring",
            ),
        ]
        for vertical, product, keyword in cases:
            valid, _ = validate_product_keyword(vertical, product, keyword)
            self.assertFalse(valid)

    def test_exact_product_keywords_are_accepted(self):
        cases = [
            (
                "Playful",
                "EPDM Playground / Wet Pour Flooring",
                "15mm EPDM playground flooring",
            ),
            (
                "Graceful",
                "Artificial Cricket Pitch / Cricket Turf",
                "artificial cricket pitch project",
            ),
            (
                "Powerful",
                "Gym Astro Turf / Sled Track Turf",
                "custom gym turf sled track",
            ),
            (
                "Sports Equipment",
                "Sports Equipment / Turnkey Facility",
                "academy basketball pole",
            ),
        ]
        for vertical, product, keyword in cases:
            valid, reason = validate_product_keyword(
                vertical,
                product,
                keyword,
            )
            self.assertTrue(valid, reason)

    def test_unknown_keyword_route_is_rejected(self):
        valid, reason = validate_product_keyword(
            "Powerful",
            "Unconfigured Product",
            "gym flooring",
        )
        self.assertFalse(valid)
        self.assertIn("no product keyword rule", reason)

        data = load_keyword_library()
        data = {
            vertical: {
                product: list(keywords)
                for product, keywords in products.items()
            }
            for vertical, products in data.items()
        }
        data["Powerful"]["Unconfigured Product"] = ["gym flooring"] * 200
        errors = validate_keyword_library(data)
        self.assertTrue(
            any("unknown route: Powerful / Unconfigured Product" in error
                for error in errors)
        )

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

    def test_product_keyword_is_paired_with_buyer_intent(self):
        queries = add_buyer_intent("Playful", ["EPDM flooring"], cursor=0)
        self.assertEqual(queries, ["EPDM flooring school"])

    def test_recovery_registry_excludes_supplier_marketplaces(self):
        recovery_sources = {name for name, _ in main.BUYER_SOURCE_REGISTRY}
        self.assertIn("Google Maps", recovery_sources)
        self.assertIn("OpenStreetMap", recovery_sources)
        self.assertNotIn("IndiaMART", recovery_sources)
        self.assertNotIn("TradeIndia", recovery_sources)
        self.assertNotIn("ExportersIndia", recovery_sources)

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
                    "company": f"Large Fitness Gym {index}",
                    "phone": f"98765432{index:02d}",
                    "source": "Large Source",
                }
            )
        raw.append(
            {
                "company": "Specialist Fitness Gym",
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
            leads, _ = main.scrape_product(
                ["test"], "Mumbai", "Powerful", target=3
            )
        self.assertEqual(
            [lead["source"] for lead in leads],
            ["Large Source", "Small Source", "Large Source"],
        )

    def test_vertical_source_cap_prevents_source_domination(self):
        counts = {"Google Maps": MAX_LEADS_PER_SOURCE_PER_VERTICAL - 1}
        leads = [
            {"company": "Gym One", "source": "Google Maps"},
            {"company": "Gym Two", "source": "Google Maps"},
            {"company": "Gym Three", "source": "Yahoo"},
        ]
        accepted = main.apply_vertical_source_caps(leads, counts)
        self.assertEqual(
            [lead["company"] for lead in accepted],
            ["Gym One", "Gym Three"],
        )

    def test_city_quota_fails_closed_if_one_vertical_is_below_50(self):
        counts = {vertical: 50 for vertical in VERTICALS}
        counts["Playful"] = 49
        self.assertFalse(main.vertical_quotas_met(counts, VERTICALS))
        counts["Playful"] = 50
        self.assertTrue(main.vertical_quotas_met(counts, VERTICALS))

    def test_product_selection_respects_existing_vertical_source_cap(self):
        raw = [
            {
                "company": "Large Fitness Gym",
                "phone": "9876543210",
                "source": "Google Maps",
            },
            {
                "company": "Independent Fitness Gym",
                "phone": "9876543211",
                "source": "Yahoo",
            },
        ]
        registry = (
            ("Google Maps", lambda *args, **kwargs: raw[:1]),
            ("Yahoo", lambda *args, **kwargs: raw[1:]),
        )
        counts = Counter({"Google Maps": MAX_LEADS_PER_SOURCE_PER_VERTICAL})
        with patch.object(main, "SOURCE_REGISTRY", registry), patch(
            "main.time.sleep", return_value=None
        ), patch("main.resolve_contact_names", return_value=None):
            leads, _ = main.scrape_product(
                ["test"],
                "Mumbai",
                "Powerful",
                target=2,
                source_counts=counts,
            )
        self.assertEqual([lead["source"] for lead in leads], ["Yahoo"])

    def test_supplier_is_rejected_even_when_brand_is_unknown(self):
        qualified, _, reason = qualify_lead(
            {
                "company": "Unknown Sports Flooring Manufacturer",
                "phone": "9876543210",
            },
            "Powerful",
        )
        self.assertFalse(qualified)
        self.assertIn("supplier signal", reason)

    def test_product_word_on_buyer_site_is_not_mistaken_for_competitor(self):
        qualified, _, reason = qualify_lead(
            {
                "company": "Iron House Fitness Gym",
                "phone": "9876543210",
                "website": "https://ironhouse.example",
                "website_text": "Our gym includes an astro turf workout zone.",
            },
            "Powerful",
        )
        self.assertTrue(qualified, reason)

    def test_buyer_page_can_describe_sports_flooring_without_rejection(self):
        qualified, _, reason = qualify_lead(
            {
                "company": "Iron House Fitness Gym",
                "phone": "9876543210",
                "website": "https://ironhouse.example",
                "website_text": (
                    "Our gym has sports flooring, an installer-managed "
                    "training zone and EPDM flooring outside."
                ),
            },
            "Powerful",
        )
        self.assertTrue(qualified, reason)

    def test_strong_supplier_claim_on_page_is_rejected(self):
        qualified, _, reason = qualify_lead(
            {
                "company": "Surface World",
                "phone": "9876543210",
                "website": "https://surfaceworld.example",
                "website_text": "We manufacture gym turf and we supply pan India.",
            },
            "Powerful",
        )
        self.assertFalse(qualified)
        self.assertIn("supplier claim", reason)

    def test_vertical_buyer_is_accepted_with_reason(self):
        qualified, score, reason = qualify_lead(
            {
                "company": "Iron House Fitness Gym",
                "phone": "9876543210",
                "website": "https://ironhouse.example",
            },
            "Powerful",
        )
        self.assertTrue(qualified)
        self.assertGreaterEqual(score, 80)
        self.assertIn("gym", reason)

    def test_irrelevant_business_fails_closed(self):
        qualified, _, reason = qualify_lead(
            {
                "company": "General Trading Company",
                "phone": "9876543210",
            },
            "Playful",
        )
        self.assertFalse(qualified)
        self.assertIn("no verified", reason)

    def test_national_city_schedule_changes_once_per_date_and_wraps(self):
        state = {
            "city_index": 0,
            "keyword_cursors": {},
            "buyer_cursors": {},
            "last_transition": "",
            "last_run_date": "",
            "last_run_city": "",
            "rotation_cycle": 1,
        }
        with patch("state.save_state", return_value=None):
            cities = ["Mumbai, Maharashtra", "Delhi, Delhi"]
            self.assertEqual(
                get_scheduled_city(state, cities, "2026-06-13"),
                "Mumbai, Maharashtra",
            )
            complete_city_batch(
                state,
                cities,
                "2026-06-13",
                ["Mumbai, Maharashtra"],
            )
            self.assertEqual(state["city_index"], 1)
            self.assertEqual(
                get_scheduled_city(state, cities, "2026-06-13"),
                "Mumbai, Maharashtra",
            )
            complete_city_batch(
                state,
                cities,
                "2026-06-13",
                ["Mumbai, Maharashtra"],
            )
            self.assertEqual(state["city_index"], 1)
            self.assertEqual(
                get_scheduled_city(state, cities, "2026-06-14"),
                "Delhi, Delhi",
            )
            complete_city_batch(
                state,
                cities,
                "2026-06-14",
                ["Delhi, Delhi"],
            )
            self.assertEqual(state["city_index"], 0)
            self.assertEqual(state["rotation_cycle"], 2)

    def test_incomplete_same_day_retry_resumes_original_batch(self):
        state = {
            "city_index": 5,
            "last_run_date": "2026-06-15",
            "last_run_city": "City 3",
            "last_run_city_count": 2,
        }
        cities = [f"City {index}" for index in range(10)]
        self.assertEqual(
            get_batch_start_index(state, cities, "2026-06-15"),
            3,
        )
        self.assertEqual(
            get_batch_start_index(state, cities, "2026-06-16"),
            5,
        )

    def test_same_day_recovery_advances_only_newly_added_towns(self):
        state = {
            "city_index": 5,
            "last_run_date": "2026-06-15",
            "last_run_city": "City 3",
            "last_run_cities": ["City 3", "City 4"],
            "last_run_city_count": 2,
            "rotation_cycle": 1,
        }
        cities = [f"City {index}" for index in range(10)]
        with patch("state.save_state", return_value=None):
            complete_city_batch(
                state,
                cities,
                "2026-06-15",
                ["City 3", "City 4", "City 5", "City 6"],
            )
        self.assertEqual(state["city_index"], 7)
        self.assertEqual(state["last_run_city_count"], 4)
        self.assertEqual(
            get_batch_start_index(state, cities, "2026-06-15"),
            3,
        )

    def test_small_town_batch_advances_past_every_used_town(self):
        state = {
            "city_index": 1,
            "last_run_date": "",
            "last_run_city": "",
            "last_run_cities": [],
            "rotation_cycle": 1,
        }
        with patch("state.save_state", return_value=None):
            cities = ["A", "B", "C", "D"]
            complete_city_batch(
                state,
                cities,
                "2026-06-13",
                ["B", "C"],
            )
        self.assertEqual(state["city_index"], 3)
        self.assertEqual(state["last_run_cities"], ["B", "C"])
        self.assertEqual(state["last_run_city_count"], 2)


if __name__ == "__main__":
    unittest.main()
