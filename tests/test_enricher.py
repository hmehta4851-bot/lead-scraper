import unittest

from bs4 import BeautifulSoup

from enricher import (
    _extract_contact_from_page,
    _extract_emails,
    _extract_phones,
    _is_person_name,
)
from main import is_actionable_lead


class EnricherTests(unittest.TestCase):
    def test_rejects_navigation_and_marketing_headings(self):
        for value in ("About Us", "Contact Us", "Perfect Surface for Every Game"):
            with self.subTest(value=value):
                self.assertFalse(_is_person_name(value))

    def test_accepts_normal_person_names(self):
        self.assertTrue(_is_person_name("Harsh Mehta"))
        self.assertTrue(_is_person_name("Ankit R. Shah"))

    def test_extracts_explicit_designation_and_name(self):
        soup = BeautifulSoup(
            "<main><p>Founder: Harsh Mehta</p></main>",
            "html.parser",
        )
        self.assertEqual(
            _extract_contact_from_page(soup),
            ("Harsh Mehta", "Founder"),
        )

    def test_extracts_person_from_json_ld(self):
        soup = BeautifulSoup(
            """
            <script type="application/ld+json">
            {"@context":"https://schema.org","@type":"Person",
             "name":"Ankit Shah","jobTitle":"Director"}
            </script>
            """,
            "html.parser",
        )
        self.assertEqual(
            _extract_contact_from_page(soup),
            ("Ankit Shah", "Director"),
        )

    def test_does_not_treat_headings_as_people(self):
        soup = BeautifulSoup(
            "<h1>About Us</h1><h2>Perfect Surface for Every Game</h2>",
            "html.parser",
        )
        self.assertEqual(_extract_contact_from_page(soup), ("", ""))

    def test_extracts_and_filters_contact_details(self):
        self.assertEqual(_extract_phones("+91 98765 43211"), ["9876543211"])
        self.assertEqual(
            _extract_emails("sales@example.com hello@sunzone.in"),
            ["hello@sunzone.in"],
        )

    def test_phone_lead_is_actionable_without_invented_person_data(self):
        self.assertTrue(
            is_actionable_lead(
                {"company": "Example Sports", "phone": "9876543211"}
            )
        )
        self.assertFalse(is_actionable_lead({"company": "Example Sports", "phone": ""}))


if __name__ == "__main__":
    unittest.main()
