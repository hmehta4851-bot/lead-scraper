import json
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import main
import preflight
from config import (
    MAX_CITIES_PER_DAY,
    MAX_LEADS_PER_SOURCE_PER_VERTICAL,
    MAX_SAME_CITY_ROUNDS,
    SOURCE_ATTEMPTS,
    TARGET_LEADS_PER_VERTICAL,
    VERTICALS,
    iter_products,
)
from keyword_library import (
    add_buyer_intent,
    load_keyword_library,
    select_buyer_signal,
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
    def test_preflight_repairs_only_small_header_label_drift(self):
        headers = list(preflight.SHEET_HEADERS)
        headers[3] = "UPDATE "
        self.assertTrue(preflight._repairable_header_drift(headers))

        reordered = list(preflight.SHEET_HEADERS)
        reordered[2], reordered[3] = reordered[3], reordered[2]
        self.assertFalse(preflight._repairable_header_drift(reordered))

        structurally_changed = list(preflight.SHEET_HEADERS[:-1])
        self.assertFalse(
            preflight._repairable_header_drift(structurally_changed)
        )

    def test_management_columns_can_follow_automation_headers(self):
        headers = [*preflight.SHEET_HEADERS, "Comments"]
        self.assertEqual(
            headers[:len(preflight.SHEET_HEADERS)],
            preflight.SHEET_HEADERS,
        )

    def test_workflow_has_early_missed_schedule_recovery(self):
        repo_root = Path(__file__).resolve().parents[1]
        daily = (repo_root / ".github/workflows/daily.yml").read_text()
        watchdog = (
            repo_root / ".github/workflows/watchdog.yml"
        ).read_text()
        morning_kickoff = (
            repo_root / ".github/workflows/morning-kickoff.yml"
        ).read_text()
        readiness = (
            repo_root / ".github/workflows/readiness-patrol.yml"
        ).read_text()

        self.assertIn('cron: "17 2 * * 1-6"', daily)
        self.assertIn('cron: "10 2 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "25 2 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "40 2 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "55 2 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "10 3 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "25 3 * * 1-6"', morning_kickoff)
        self.assertIn('cron: "47 2 * * 1-6"', watchdog)
        self.assertIn('cron: "17 3 * * 1-6"', watchdog)
        self.assertIn('cron: "17 5 * * 1-6"', watchdog)
        self.assertIn('cron: "17 9 * * 1-6"', watchdog)
        self.assertIn('cron: "7 15 * * 0-5"', readiness)
        self.assertIn('cron: "37 0 * * 1-6"', readiness)
        self.assertIn("python source_readiness.py", readiness)
        self.assertIn("pip-audit -r requirements.txt", readiness)
        self.assertIn(
            "Probe all 11 sources without writing leads",
            readiness,
        )
        self.assertIn("gh workflow run daily.yml", morning_kickoff)
        self.assertIn("already_active", morning_kickoff)
        self.assertIn("already_success", morning_kickoff)
        self.assertIn("gh workflow run daily.yml", watchdog)
        self.assertIn('"cancelled"', watchdog)
        self.assertIn("genuine_failures", watchdog)
        self.assertIn(
            "Latest run was manually cancelled — staying stopped today.",
            watchdog,
        )

    def test_all_workflows_opt_in_to_node24_runtime(self):
        repo_root = Path(__file__).resolve().parents[1]
        workflows = sorted((repo_root / ".github/workflows").glob("*.yml"))

        self.assertTrue(workflows)
        for workflow in workflows:
            with self.subTest(workflow=workflow.name):
                self.assertIn(
                    "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true",
                    workflow.read_text(),
                )

    def test_daily_collection_has_bounded_low_yield_city_fallback(self):
        self.assertEqual(MAX_CITIES_PER_DAY, 20)

    def test_preflight_locks_business_policy(self):
        checks = preflight.check_static_configuration()
        self.assertIn(
            "50-lead target with 25-lead city expansion floor",
            checks,
        )
        self.assertIn(
            "8 complete keyword rounds before any town expansion",
            checks,
        )
        self.assertIn(
            "strict buyer, supplier and competitor qualification rules",
            checks,
        )
        workflow_checks = preflight.check_workflow_policy()
        self.assertIn(
            "7:47 AM IST Mon-Sat automatic collection",
            workflow_checks,
        )
        self.assertIn(
            "four same-day missed-run and failure recovery checks",
            workflow_checks,
        )
        self.assertIn(
            "three-attempt API, dispatch, email and state synchronization",
            workflow_checks,
        )
        self.assertIn(
            "evening and pre-run 11-source readiness patrols",
            workflow_checks,
        )
        daily = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/daily.yml"
        ).read_text()
        preflight_workflow = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/preflight.yml"
        ).read_text()
        self.assertIn("Run automated safety tests", daily)
        self.assertIn("Run automated safety tests", preflight_workflow)

    def test_status_workflow_is_read_only_and_aggregate_only(self):
        repo_root = Path(__file__).resolve().parents[1]
        status = (
            repo_root / ".github/workflows/status.yml"
        ).read_text()

        self.assertIn("contents: read", status)
        self.assertNotIn("contents: write", status)
        self.assertIn("load_daily_snapshot", status)
        self.assertIn("VERTICAL_COUNTS", status)
        self.assertIn("SOURCE_COUNTS", status)
        self.assertNotIn("append_leads", status)

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
        self.assertEqual(len(attempted), 11 + SOURCE_ATTEMPTS - 1)
        self.assertEqual(len(telemetry["attempted"]), 11)
        self.assertEqual(list(telemetry["failed"]), ["Source 3"])
        self.assertEqual(
            telemetry["attempt_counts"]["Source 3"],
            SOURCE_ATTEMPTS,
        )

    def test_source_recovers_on_second_attempt_without_blocking_others(self):
        calls = Counter()

        def flaky(keyword, city, max_results):
            calls["Flaky"] += 1
            if calls["Flaky"] == 1:
                raise TimeoutError("temporary block")
            return [{"company": "Recovered Gym", "phone": "9876543210"}]

        def stable(keyword, city, max_results):
            calls["Stable"] += 1
            return []

        with patch("main.time.sleep", return_value=None):
            leads, telemetry = main.run_all_sources(
                "gym",
                "Mumbai",
                source_registry=(("Flaky", flaky), ("Stable", stable)),
            )

        self.assertEqual(calls, Counter({"Flaky": 2, "Stable": 1}))
        self.assertEqual([lead["source"] for lead in leads], ["Flaky"])
        self.assertEqual(telemetry["failed"], {})
        self.assertEqual(telemetry["attempt_counts"]["Flaky"], 2)

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

    def test_city_is_never_abandoned_before_all_keyword_rounds(self):
        self.assertFalse(
            main.should_add_next_town(
                city_offset=0,
                round_number=MAX_SAME_CITY_ROUNDS - 1,
                no_progress_rounds=1,
                fresh_leads=0,
            )
        )
        self.assertTrue(
            main.should_add_next_town(
                city_offset=0,
                round_number=MAX_SAME_CITY_ROUNDS,
                no_progress_rounds=0,
                fresh_leads=0,
            )
        )

    def test_city_expansion_requires_a_vertical_below_25(self):
        self.assertTrue(
            main.city_expansion_needed(
                {vertical: 25 for vertical in VERTICALS} | {"Joyful": 15},
                VERTICALS,
            )
        )
        self.assertFalse(
            main.city_expansion_needed(
                {vertical: 25 for vertical in VERTICALS},
                VERTICALS,
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

    def test_buyer_signal_rotates_within_vertical(self):
        self.assertEqual(select_buyer_signal("Playful", 0), "school")
        self.assertEqual(select_buyer_signal("Powerful", 0), "gym")
        self.assertNotEqual(
            select_buyer_signal("Powerful", 0),
            select_buyer_signal("Powerful", 1),
        )

    def test_directory_uses_buyer_query_and_marketplace_uses_product_query(self):
        calls = []

        def search(query, city, max_results):
            calls.append(query)
            return []

        registry = (
            ("Google Maps", search),
            ("TradeIndia", search),
        )
        with patch("main.time.sleep", return_value=None):
            main.run_all_sources(
                "football turf 11000 dtex",
                "Mumbai",
                source_registry=registry,
                buyer_keyword="football academy",
            )

        self.assertEqual(
            calls,
            ["football academy", "football turf 11000 dtex"],
        )

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

    def test_source_cap_requires_multiple_sources_for_full_quota(self):
        self.assertLessEqual(
            MAX_LEADS_PER_SOURCE_PER_VERTICAL * 2,
            TARGET_LEADS_PER_VERTICAL,
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

    def test_obvious_buyer_skips_prequalification_enrichment(self):
        lead = {
            "company": "Iron House Fitness Gym",
            "phone": "9876543210",
            "website": "https://ironhouse.example",
        }
        with patch("main._enrich") as enrich:
            qualified = main._qualify_candidates(
                [lead],
                "Powerful",
                {"9876543210"},
            )

        self.assertEqual(qualified, [lead])
        enrich.assert_not_called()

    def test_ambiguous_website_is_enriched_then_strictly_qualified(self):
        lead = {
            "company": "Iron House",
            "phone": "",
            "website": "https://ironhouse.example",
        }

        def enrich(leads, seen_phones, limit):
            self.assertEqual(leads, [lead])
            self.assertEqual(limit, 25)
            lead["phone"] = "9876543210"
            lead["website_text"] = "fitness gym and health club"

        with patch("main._enrich", side_effect=enrich):
            qualified = main._qualify_candidates(
                [lead],
                "Powerful",
                set(),
            )

        self.assertEqual(qualified, [lead])
        self.assertGreaterEqual(lead["lead_score"], 80)

    def test_parallel_enrichment_merges_contact_data_safely(self):
        leads = [
            {
                "company": "Gym One",
                "phone": "",
                "website": "https://one.example",
            },
            {
                "company": "Gym Two",
                "phone": "",
                "website": "https://two.example",
            },
        ]

        def enrich(url, max_pages):
            suffix = "1" if "one." in url else "2"
            return {
                "phone": f"987654321{suffix}",
                "email": f"sales{suffix}@example.com",
                "contact_person": "",
                "designation": "",
                "website_text": "fitness gym",
            }

        with patch("main.enrich_website", side_effect=enrich):
            main._enrich(leads, set(), limit=2)

        self.assertEqual(
            {lead["phone"] for lead in leads},
            {"9876543211", "9876543212"},
        )
        self.assertTrue(all(lead["email"] for lead in leads))
        self.assertTrue(all(lead["website_text"] == "fitness gym" for lead in leads))

    def test_supplier_is_rejected_without_wasting_enrichment_time(self):
        lead = {
            "company": "Unknown Sports Flooring Manufacturer",
            "phone": "9876543210",
            "website": "https://supplier.example",
        }
        with patch("main._enrich") as enrich:
            qualified = main._qualify_candidates(
                [lead],
                "Powerful",
                {"9876543210"},
            )

        self.assertEqual(qualified, [])
        enrich.assert_not_called()

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
