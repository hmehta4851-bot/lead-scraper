import unittest
from collections import Counter
from datetime import date
from unittest.mock import Mock, patch

from sheets import load_daily_snapshot


class SheetSnapshotTests(unittest.TestCase):
    def test_snapshot_counts_only_same_day_and_city_but_dedupes_all_phones(self):
        headers = [
            "Date",
            "City",
            "Vertical",
            "Phone",
            "Source",
        ]
        worksheet = Mock()
        worksheet.title = "Powerful Leads"
        worksheet.get_all_values.return_value = [
            headers,
            ["2026-06-13", "Mumbai", "Powerful", "+91 98765 43210", "Bing"],
            ["2026-06-13", "Pune", "Powerful", "9123456789", "Google Maps"],
            ["2026-06-12", "Mumbai", "Powerful", "9988776655", "Yahoo"],
        ]
        spreadsheet = Mock()
        spreadsheet.worksheets.return_value = [worksheet]
        client = Mock()
        client.open_by_key.return_value = spreadsheet

        with patch("sheets.get_client", return_value=client):
            phones, counts, source_counts = load_daily_snapshot(
                "sheet-id",
                ["Powerful Leads"],
                date(2026, 6, 13),
                "Mumbai, Maharashtra",
            )

        self.assertEqual(
            phones,
            {"9876543210", "9123456789", "9988776655"},
        )
        self.assertEqual(counts, Counter({"Powerful": 1}))
        self.assertEqual(
            source_counts,
            {"Powerful": Counter({"Bing": 1})},
        )


if __name__ == "__main__":
    unittest.main()
