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
            # Contractors & Installers
            "EPDM flooring contractor",
            "playground flooring contractor",
            "rubber flooring contractor",
            "sports flooring applicator",
            "rubber safety surfacing contractor",
            # Education & Institutional
            "school playground flooring contractor",
            "kids play area flooring contractor",
            "preschool rubber flooring",
            "park flooring contractor",
            "playground equipment contractor",
            # Hospitality & Real Estate
            "township playground contractor",
            "housing society play area contractor",
            # Niche
            "theme park rubber flooring",
            "landscape rubber surface contractor",
        ],
        "gmaps_types": ["general_contractor", "flooring_contractor"],
    },
    "PU Binder": {
        "tab": "PU Binder",
        "keywords": [
            # Contractors
            "running track contractor",
            "athletic track contractor",
            "rubber flooring installer",
            "sports surface contractor",
            "playground flooring applicator",
            "athletic track maintenance contractor",
            "sports surface repair contractor",
            # Broader track & field
            "synthetic track contractor",
            "PU running track builder",
            "athletics track construction",
            # Institutional
            "school running track contractor",
            "college athletic track contractor",
            "stadium track contractor",
        ],
        "gmaps_types": ["general_contractor"],
    },

    # ── GRACEFUL ─────────────────────────────────────────────────────────────
    "Artificial Football Turf": {
        "tab": "Artificial Football Turf",
        "keywords": [
            # Direct buyers
            "football turf owner",
            "box turf owner",
            "futsal turf owner",
            "football academy",
            # Contractors
            "football turf contractor",
            "football turf installer",
            "artificial grass football",
            "turf installation contractor",
            # Institutional
            "school football ground contractor",
            "sports ground contractor",
            # Municipal & PSU
            "municipal sports ground contractor",
            "sports complex football turf",
            "football ground developer",
            "sports ground construction company",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },
    "Hockey Turf": {
        "tab": "Hockey Turf",
        "keywords": [
            # Direct buyers & contractors
            "hockey turf contractor",
            "synthetic hockey turf installer",
            "hockey academy",
            "hockey stadium contractor",
            # Institutional
            "astroturf hockey contractor",
            "sports complex hockey",
            "hockey ground developer",
            # Government
            "government sports contractor",
            "sports authority hockey contractor",
            "state hockey association",
            # Broader
            "EPC sports contractor",
            "sports infrastructure contractor",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },
    "Multi-Sport Turf": {
        "tab": "Multi-Sport Turf",
        "keywords": [
            # Contractors
            "multi sports turf contractor",
            "multi sport court installer",
            "synthetic grass multi sport",
            "rooftop turf contractor",
            "terrace sports turf",
            # Buyers - residential & commercial
            "housing society sports turf",
            "residential complex sports court",
            "clubhouse sports ground",
            "township amenity contractor",
            # Institutional
            "school sports ground contractor",
            "sports academy flooring",
            # Corporate & developers
            "corporate campus sports turf",
            "real estate sports amenity contractor",
            "sports complex developer",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },
    "Cricket Turf": {
        "tab": "Cricket Turf",
        "keywords": [
            # Direct buyers
            "box cricket turf owner",
            "cricket academy flooring",
            "indoor cricket turf",
            "cricket club flooring",
            # Contractors
            "cricket turf contractor",
            "artificial cricket pitch",
            "cricket practice net contractor",
            # Institutional & developers
            "school cricket ground contractor",
            "cricket ground developer",
            "sports ground maintenance company",
            "sports academy cricket",
            "cricket turf installer",
        ],
        "gmaps_types": ["sports_complex", "stadium"],
    },
    "Padel Court Turf": {
        "tab": "Padel Court Turf",
        "keywords": [
            # Direct buyers & contractors
            "padel court contractor",
            "padel court builder",
            "padel court installer",
            "padel court construction",
            # Owners & clubs
            "padel club owner",
            "sports club padel",
            # Geographic & market
            "padel tennis court India",
            "padel court management company",
            # Hospitality crossover
            "hotel padel court",
            "resort padel court",
            "padel court developer",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── JOYFUL ───────────────────────────────────────────────────────────────
    "Badminton PVC Flooring": {
        "tab": "Badminton PVC Flooring",
        "keywords": [
            # Direct buyers
            "badminton academy owner",
            "badminton court owner",
            "indoor sports complex owner",
            # Contractors
            "badminton court flooring contractor",
            "indoor sports flooring contractor",
            "synthetic badminton court",
            "indoor court PVC flooring",
            "indoor sports court contractor",
            "sports hall renovation contractor",
            # Institutional
            "school badminton court contractor",
            "college badminton court",
            # Corporate & hospitality
            "corporate badminton court",
            "hotel badminton court contractor",
            "sports complex renovation contractor",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── POWERFUL ─────────────────────────────────────────────────────────────
    "Gym Rubber Roll Flooring": {
        "tab": "Gym Rubber Roll Flooring",
        "keywords": [
            # Contractors
            "gym setup contractor",
            "commercial gym flooring",
            "gym renovation contractor",
            "fitness center setup company",
            "commercial gym setup contractor",
            # Direct buyers
            "gym owner",
            "fitness center flooring contractor",
            "CrossFit box setup contractor",
            # Fitness segments
            "martial arts gym flooring",
            "boxing gym flooring",
            "weightlifting gym rubber floor",
            # Hospitality & corporate
            "hotel gym flooring contractor",
            "corporate gym flooring",
            # Rehab & wellness
            "physiotherapy clinic flooring",
            "rehabilitation centre flooring",
        ],
        "gmaps_types": ["gym"],
    },
    "Gym Astro Turf": {
        "tab": "Gym Astro Turf",
        "keywords": [
            # Direct buyers
            "CrossFit box owner",
            "crossfit gym owner",
            "functional training gym owner",
            # Contractors
            "functional training turf",
            "gym turf flooring",
            "turf gym flooring",
            "fitness turf contractor",
            "gym interior contractor",
            "sports performance facility contractor",
            # Hospitality
            "hotel gym astro turf",
            "sports performance centre",
            "gym interior designer",
        ],
        "gmaps_types": ["gym"],
    },

    # ── WOODPLAY ─────────────────────────────────────────────────────────────
    "Wooden Sports Flooring": {
        "tab": "Wooden Sports Flooring",
        "keywords": [
            # Contractors
            "wooden sports flooring contractor",
            "hardwood court contractor",
            "wooden court installer",
            "indoor sports hall contractor",
            # Direct buyers
            "maple wooden basketball court",
            "basketball wooden floor contractor",
            "indoor sports wooden floor",
            # Niche
            "squash court wooden floor",
            "dance studio wooden floor contractor",
            "badminton wooden court",
            # Institutional & hospitality
            "school sports hall flooring",
            "university sports hall wooden floor",
            "club house sports flooring",
        ],
        "gmaps_types": ["sports_complex", "gym"],
    },

    # ── TRACK & FIELD ────────────────────────────────────────────────────────
    "Athletic Running Track": {
        "tab": "Athletic Running Track",
        "keywords": [
            # Contractors
            "running track contractor",
            "athletic track construction",
            "PU running track installer",
            "synthetic running track",
            "prefabricated track system",
            # Institutional education
            "school running track contractor",
            "college athletic track contractor",
            "university running track",
            # Government & institutional
            "sports authority track contractor",
            "municipal stadium running track",
            "Khelo India track contractor",
            # Defence
            "army sports track contractor",
            "police academy running track",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },

    # ── ACRYPLAY ─────────────────────────────────────────────────────────────
    "Acrylic Sports Flooring": {
        "tab": "Acrylic Sports Flooring",
        "keywords": [
            # Contractors
            "acrylic sports flooring contractor",
            "sports court resurfacing",
            "outdoor court flooring contractor",
            "hard court sports flooring",
            # Sport-specific
            "tennis court acrylic flooring",
            "acrylic basketball court",
            "acrylic court coating contractor",
            # Direct buyers
            "tennis court owner",
            "tennis club contractor",
            # Hospitality
            "hotel tennis court contractor",
            "resort sports court",
            # Housing
            "housing society tennis court",
            "clubhouse tennis court contractor",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── BASKETBALL ───────────────────────────────────────────────────────────
    "Basketball Flooring": {
        "tab": "Basketball Flooring",
        "keywords": [
            # Contractors
            "basketball court flooring contractor",
            "basketball court contractor",
            "sports court contractor",
            # Direct buyers
            "basketball academy owner",
            "indoor basketball court",
            "outdoor basketball court contractor",
            # Institutional
            "school basketball court",
            "college basketball court contractor",
            "university basketball court",
            # Residential & corporate
            "clubhouse basketball court",
            "housing society basketball court",
            "township basketball court",
            "sports hall construction company",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },

    # ── COURT TILES ─────────────────────────────────────────────────────────
    "PP Interlocking Court Tiles": {
        "tab": "PP Interlocking Tiles",
        "keywords": [
            # Contractors & buyers
            "modular sports flooring",
            "interlocking sports tiles India",
            "outdoor court tiles contractor",
            "outdoor sports court contractor",
            "rooftop court tiles",
            "terrace sports tiles",
            "multi purpose court tiles",
            # Residential
            "housing society court tiles",
            "residential sports court tiles",
            "apartment sports amenity contractor",
            "residential sports court developer",
            # Institutional
            "school outdoor court tiles",
            # Commercial
            "commercial sports facility contractor",
            "multi-sport complex builder",
        ],
        "gmaps_types": ["sports_complex"],
    },
}

SHEET_HEADERS = [
    "Date", "City", "Product", "Company Name",
    "Contact Person", "Phone", "Email", "Designation", "Source", "Website"
]
