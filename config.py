SHEET_ID = "1p48H_6PpWgYFyaAtPXijyeAlk1Tgq5kUUQORMBgG8eM"
NOTIFY_EMAIL = "hmehta4851@gmail.com"
LEADS_PER_PRODUCT = 50

TIER1_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Hyderabad", "Pune", "Kolkata", "Ahmedabad"
]

TIER2_CITIES = [
    "Jaipur", "Lucknow", "Surat", "Nagpur", "Indore",
    "Vadodara", "Bhopal", "Visakhapatnam", "Patna", "Coimbatore",
    "Gurgaon", "Noida", "Chandigarh", "Kochi", "Guwahati",
    "Bhubaneswar", "Thiruvananthapuram", "Nashik", "Aurangabad", "Rajkot"
]

PRODUCTS = {
    # ── PLAYFUL ─────────────────────────────────────────────────────────────
    "EPDM Granules": {
        "tab": "EPDM Granules",
        "keywords": [
            "EPDM flooring contractor",
            "playground flooring contractor",
            "rubber flooring contractor",
            "EPDM granules supplier",
            "rubber granules supplier",
            "kids play area flooring contractor",
            "sports flooring applicator",
        ],
        "gmaps_types": ["general_contractor", "flooring_contractor"],
    },
    "PU Binder": {
        "tab": "PU Binder",
        "keywords": [
            "PU binder supplier",
            "EPDM PU binder dealer",
            "running track contractor",
            "rubber flooring installer",
            "athletic track contractor",
            "playground flooring applicator",
            "sports surface contractor",
        ],
        "gmaps_types": ["general_contractor"],
    },

    # ── GRACEFUL ─────────────────────────────────────────────────────────────
    "Artificial Football Turf": {
        "tab": "Artificial Football Turf",
        "keywords": [
            "football turf contractor",
            "football turf installer",
            "box turf owner",
            "football academy",
            "futsal turf contractor",
            "sports ground contractor",
            "artificial grass football",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },
    "Hockey Turf": {
        "tab": "Hockey Turf",
        "keywords": [
            "hockey turf contractor",
            "FIH hockey turf supplier",
            "hockey academy",
            "hockey stadium contractor",
            "synthetic hockey turf installer",
            "sports complex hockey",
            "astroturf hockey contractor",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },
    "Multi-Sport Turf": {
        "tab": "Multi-Sport Turf",
        "keywords": [
            "multi sports turf contractor",
            "multi sport court installer",
            "school sports ground contractor",
            "sports academy flooring",
            "housing society sports turf",
            "clubhouse sports ground",
            "synthetic grass multi sport",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },
    "Cricket Turf": {
        "tab": "Cricket Turf",
        "keywords": [
            "cricket turf contractor",
            "artificial cricket pitch",
            "cricket practice net contractor",
            "cricket academy flooring",
            "indoor cricket turf",
            "box cricket turf owner",
            "cricket club flooring",
        ],
        "gmaps_types": ["sports_complex", "stadium"],
    },
    "Padel Court Turf": {
        "tab": "Padel Court Turf",
        "keywords": [
            "padel court contractor",
            "padel court builder",
            "padel tennis court India",
            "padel club owner",
            "sports club padel",
            "padel court installer",
            "padel court construction",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── JOYFUL ───────────────────────────────────────────────────────────────
    "Badminton PVC Flooring": {
        "tab": "Badminton PVC Flooring",
        "keywords": [
            "badminton court flooring contractor",
            "badminton academy owner",
            "PVC badminton flooring supplier",
            "indoor sports flooring contractor",
            "badminton court contractor",
            "synthetic badminton court",
            "indoor court PVC flooring",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── POWERFUL ─────────────────────────────────────────────────────────────
    "Gym Rubber Roll Flooring": {
        "tab": "Gym Rubber Roll Flooring",
        "keywords": [
            "gym rubber flooring dealer",
            "gym rubber roll supplier",
            "fitness center flooring contractor",
            "gym setup contractor",
            "CrossFit flooring dealer",
            "gym flooring supplier",
            "commercial gym flooring",
        ],
        "gmaps_types": ["gym"],
    },
    "Gym Astro Turf": {
        "tab": "Gym Astro Turf",
        "keywords": [
            "gym astro turf supplier",
            "sled push turf dealer",
            "functional training turf",
            "CrossFit box owner",
            "gym turf flooring",
            "fitness turf contractor",
            "turf gym flooring",
        ],
        "gmaps_types": ["gym"],
    },

    # ── WOODPLAY ─────────────────────────────────────────────────────────────
    "Wooden Sports Flooring": {
        "tab": "Wooden Sports Flooring",
        "keywords": [
            "wooden sports flooring contractor",
            "maple wooden basketball court",
            "hardwood court contractor",
            "wooden court installer",
            "sports wooden flooring supplier",
            "basketball wooden floor contractor",
            "indoor sports wooden floor",
        ],
        "gmaps_types": ["sports_complex", "gym"],
    },

    # ── TRACK & FIELD ────────────────────────────────────────────────────────
    "Athletic Running Track": {
        "tab": "Athletic Running Track",
        "keywords": [
            "running track contractor",
            "athletic track construction",
            "PU running track installer",
            "synthetic running track",
            "sports authority track contractor",
            "school running track contractor",
            "prefabricated track system",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },

    # ── ACRYPLAY ─────────────────────────────────────────────────────────────
    "Acrylic Sports Flooring": {
        "tab": "Acrylic Sports Flooring",
        "keywords": [
            "acrylic sports flooring contractor",
            "tennis court acrylic flooring",
            "acrylic basketball court",
            "hard court sports flooring",
            "acrylic court coating contractor",
            "sports court resurfacing",
            "outdoor court flooring contractor",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── BASKETBALL ───────────────────────────────────────────────────────────
    "Basketball Flooring": {
        "tab": "Basketball Flooring",
        "keywords": [
            "basketball court flooring contractor",
            "basketball court contractor",
            "sports court contractor",
            "school basketball court",
            "indoor basketball court",
            "outdoor basketball court contractor",
            "clubhouse basketball court",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },

    # ── COURT TILES ─────────────────────────────────────────────────────────
    "PP Interlocking Court Tiles": {
        "tab": "PP Interlocking Tiles",
        "keywords": [
            "interlocking court tiles dealer",
            "PP sports tiles supplier",
            "modular sports flooring",
            "interlocking sports tiles India",
            "outdoor court tiles contractor",
            "multi purpose court tiles",
            "sports tiles dealer",
        ],
        "gmaps_types": ["sports_complex"],
    },
}

SHEET_HEADERS = [
    "Date", "City", "Product", "Company Name",
    "Contact Person", "Phone", "Email", "Designation", "Source", "Website"
]
