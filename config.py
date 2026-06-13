"""Business configuration for the Sunzone lead-scraping workflow."""

SHEET_ID = "1p48H_6PpWgYFyaAtPXijyeAlk1Tgq5kUUQORMBgG8eM"
NOTIFY_EMAIL = "hmehta4851@gmail.com"

LEADS_PER_PRODUCT = 50
KEYWORDS_PER_PRODUCT_PER_RUN = 1
SOURCE_RESULT_LIMIT = 20
SOURCE_LEAD_CAP = 20

TIER1_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Hyderabad", "Pune", "Kolkata", "Ahmedabad",
]

TIER2_CITIES = [
    "Jaipur", "Lucknow", "Surat", "Nagpur", "Indore",
    "Vadodara", "Bhopal", "Visakhapatnam", "Patna", "Coimbatore",
    "Gurgaon", "Noida", "Chandigarh", "Kochi", "Guwahati",
    "Bhubaneswar", "Thiruvananthapuram", "Nashik", "Aurangabad", "Rajkot",
]

# Brand, supplier, manufacturer, and direct sports-flooring competitors.
# Matching is applied to company names, email domains, and website domains.
COMPETITOR_BRANDS = [
    "domo sports", "mondo india", "polytan", "tarkett", "tigerturf",
    "fieldturf", "ace turf", "wuxi", "durabilt", "matsports",
    "sport group", "polyturf", "grassman", "astroturf india",
    "ccgrass", "greenfields", "limonta sport", "ten cate",
    "shaw sports turf", "sprinturf", "sporturf", "greenfield",
    "mafatlal", "sportmaster", "laykold", "plexipave",
    "unidus", "tapas acoustics", "tap acoustics",
]

# These are the eight commercial verticals used by Sunzone's workbook and
# website structure. Each vertical has one Google Sheet tab; Product remains a
# separate column so sales teams can filter without maintaining 18 tabs.
VERTICALS = {
    "Playful": {
        "tab": "Playful Leads",
        "products": {
            "EPDM Playground / Wet Pour Flooring": [
                "EPDM playground flooring contractor",
                "wet pour flooring contractor",
            ],
            "EPDM Granules / SBR Granules / PU Binder": [
                "EPDM granules buyer",
                "PU binder buyer",
            ],
        },
    },
    "Graceful": {
        "tab": "Graceful Leads",
        "products": {
            "Football Turf / Box Cricket Turnkey": [
                "football turf project",
                "box cricket turnkey project",
            ],
            "Artificial Cricket Pitch / Cricket Turf": [
                "artificial cricket pitch project",
                "cricket turf project",
            ],
            "Artificial Grass / Landscape Turf": [
                "artificial grass landscaping project",
                "landscape turf buyer",
            ],
            "FIH Hockey Turf": [
                "hockey turf project",
                "FIH hockey turf requirement",
            ],
            "Multi-Sport Turf / Tennis Turf / Padel Turf": [
                "multi sport turf project",
                "padel turf project",
            ],
            "Turf Accessories": [
                "artificial turf accessories buyer",
                "turf installation accessories",
            ],
        },
    },
    "Powerful": {
        "tab": "Powerful Leads",
        "products": {
            "Gym Astro Turf / Sled Track Turf": [
                "gym astro turf requirement",
                "sled track turf buyer",
            ],
            "Gym PVC Sports Flooring": [
                "gym PVC flooring project",
                "gym vinyl flooring buyer",
            ],
            "Gym Rubber Roll Flooring": [
                "gym rubber roll flooring project",
                "rubber roll flooring buyer",
            ],
            "Gym Rubber Tiles / Laminate Tiles / Mats": [
                "gym rubber tiles requirement",
                "gym flooring mats buyer",
            ],
        },
    },
    "Joyful": {
        "tab": "Joyful Leads",
        "products": {
            "PVC / Vinyl Badminton Flooring": [
                "badminton PVC flooring project",
                "vinyl badminton court flooring buyer",
            ],
        },
    },
    "Acryplay": {
        "tab": "Acryplay Leads",
        "products": {
            "Acrylic Sports Court Systems": [
                "acrylic sports court project",
                "acrylic court flooring buyer",
            ],
            "PP Modular Sports Court Tiles": [
                "PP modular sports tiles project",
                "interlocking court tiles buyer",
            ],
        },
    },
    "Track & Field": {
        "tab": "Track & Field Leads",
        "products": {
            "Synthetic Athletic Track Systems": [
                "synthetic athletic track project",
                "running track construction requirement",
            ],
        },
    },
    "Sports Equipment": {
        "tab": "Sports Equipment Leads",
        "products": {
            "Sports Equipment / Turnkey Facility": [
                "sports equipment procurement",
                "turnkey sports facility project",
            ],
        },
    },
    "Woodplay": {
        "tab": "Woodplay Leads",
        "products": {
            "Maple / Hevea Wooden Sports Flooring": [
                "wooden sports flooring project",
                "maple basketball flooring buyer",
            ],
        },
    },
}

SHEET_HEADERS = [
    "Date", "City", "Vertical", "Product", "Search Keyword",
    "Company Name", "Contact Person", "Phone", "Email", "Designation",
    "Source", "Website", "Lead Score",
]


def iter_products():
    """Yield (vertical, tab, product, fallback_keywords) in stable order."""
    for vertical, vertical_cfg in VERTICALS.items():
        for product, keywords in vertical_cfg["products"].items():
            yield vertical, vertical_cfg["tab"], product, keywords


# Compatibility view for scripts that only need tab discovery.
PRODUCTS = {
    product: {
        "vertical": vertical,
        "tab": tab,
        "keywords": keywords,
    }
    for vertical, tab, product, keywords in iter_products()
}
