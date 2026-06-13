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

# Known competitor brand names — leads matching these are excluded
# (we do not target our own competitors as sales prospects)
COMPETITOR_BRANDS = [
    "domo sports", "mondo india", "polytan", "tarkett", "tigerturf",
    "fieldturf", "ace turf", "wuxi", "durabilt", "matsports",
    "sport group", "polyturf", "grassman", "astroturf india",
    "ccgrass", "greenfields", "limonta sport", "ten cate",
    "shaw sports turf", "sprinturf", "sporturf", "greenfield",
    "mafatlal", "sportmaster", "laykold", "plexipave",
]

PRODUCTS = {
    # ── PLAYFUL ─────────────────────────────────────────────────────────────
    "EPDM Granules": {
        "tab": "EPDM Granules",
        "keywords": [
            # Contractors & Applicators
            "EPDM flooring contractor",
            "EPDM rubber flooring installer",
            "EPDM granules flooring contractor",
            "rubber safety surfacing contractor",
            "playground rubber flooring applicator",
            "EPDM surface applicator",
            "rubber flooring contractor",
            "sports flooring applicator",
            "playground flooring contractor",
            # Education & Institutional
            "school playground flooring contractor",
            "kids play area flooring contractor",
            "preschool rubber flooring contractor",
            "daycare playground flooring",
            "park rubber flooring contractor",
            "playground equipment installer",
            "kindergarten play area flooring",
            "school play area rubber flooring",
            # Hospitality & Real Estate
            "township playground flooring contractor",
            "housing society play area contractor",
            "apartment complex playground contractor",
            "residential complex play area",
            "gated community playground contractor",
            # Niche & Project
            "theme park rubber flooring contractor",
            "landscape rubber surface contractor",
            "rubber mulch flooring contractor",
            "safety surfacing playground",
            "rubber track flooring applicator",
            "soft play area contractor",
            "splash pad rubber flooring",
            # Procurement intent
            "buy EPDM granules rubber flooring",
            "EPDM granules flooring price India",
        ],
        "gmaps_types": ["general_contractor", "flooring_contractor"],
    },

    "PU Binder": {
        "tab": "PU Binder",
        "keywords": [
            # Contractors
            "running track contractor",
            "athletic track contractor",
            "PU running track builder",
            "polyurethane track contractor",
            "rubber track binder applicator",
            "synthetic track contractor",
            "sports surface contractor",
            "athletics track construction company",
            "running track surface contractor",
            # Maintenance & Repair
            "athletic track maintenance contractor",
            "sports surface repair contractor",
            "running track resurfacing",
            "track renovation contractor",
            # Institutional
            "school running track contractor",
            "college athletic track contractor",
            "university running track contractor",
            "stadium track contractor",
            "sports academy track contractor",
            # Broader
            "rubber flooring installer",
            "playground flooring applicator",
            "PU binder sports flooring",
            "polyurethane rubber flooring contractor",
            "synthetic rubber surface contractor",
            # Procurement intent
            "buy PU binder running track",
            "PU binder sports flooring price",
        ],
        "gmaps_types": ["general_contractor"],
    },

    # ── GRACEFUL ─────────────────────────────────────────────────────────────
    "Artificial Football Turf": {
        "tab": "Artificial Football Turf",
        "keywords": [
            # Direct Buyers
            "football turf owner",
            "box turf owner",
            "futsal turf owner",
            "football academy owner",
            "indoor football academy",
            "outdoor football academy",
            # Contractors & Installers
            "football turf contractor",
            "football turf installer",
            "artificial grass football field contractor",
            "turf installation contractor",
            "synthetic grass football field",
            "artificial turf football ground",
            # Institutional
            "school football ground contractor",
            "college football ground contractor",
            "sports ground contractor",
            "football ground construction company",
            # Municipal & PSU
            "municipal sports ground contractor",
            "sports complex football turf",
            "football ground developer",
            "government sports contractor",
            # Hospitality & Real Estate
            "resort football turf",
            "hotel sports facility contractor",
            "township football ground contractor",
            "housing society football turf",
            # Project & Procurement
            "artificial football turf installation India",
            "buy artificial football turf India",
            "football turf price per sqft India",
            "Khelo India football turf contractor",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },

    "Hockey Turf": {
        "tab": "Hockey Turf",
        "keywords": [
            # Direct Buyers & Contractors
            "hockey turf contractor",
            "synthetic hockey turf installer",
            "astroturf hockey contractor",
            "hockey ground contractor",
            "artificial hockey turf installation",
            # Academies & Clubs
            "hockey academy",
            "hockey club ground contractor",
            "hockey stadium contractor",
            "hockey astroturf developer",
            # Institutional
            "sports complex hockey turf",
            "hockey ground developer",
            "school hockey ground contractor",
            "college hockey ground contractor",
            # Government & PSU
            "government sports contractor hockey",
            "sports authority hockey contractor",
            "state hockey association ground",
            "Khelo India hockey turf",
            "hockey federation ground contractor",
            # Broader Infrastructure
            "EPC sports contractor hockey",
            "sports infrastructure contractor",
            "sports complex developer",
            "hockey field irrigation contractor",
            # Procurement
            "buy hockey turf India",
            "synthetic hockey turf price India",
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
            "multi purpose court contractor",
            "multi sport ground contractor",
            # Rooftop & Terrace
            "rooftop turf contractor",
            "terrace sports turf contractor",
            "rooftop sports court contractor",
            "terrace sports court installer",
            # Residential & Housing
            "housing society sports turf",
            "residential complex sports court",
            "apartment sports amenity contractor",
            "gated community sports court",
            "clubhouse sports ground contractor",
            "township amenity sports contractor",
            # Commercial & Corporate
            "corporate campus sports turf",
            "office campus sports court",
            "commercial sports facility contractor",
            # Institutional
            "school multi sport ground contractor",
            "sports academy ground contractor",
            "university multi sport court",
            # Real Estate Developers
            "real estate sports amenity contractor",
            "sports complex developer",
            "multi sport complex builder",
            # Procurement
            "buy multi sport turf India",
            "multi sport court price India",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },

    "Cricket Turf": {
        "tab": "Cricket Turf",
        "keywords": [
            # Direct Buyers
            "box cricket turf owner",
            "indoor cricket turf owner",
            "cricket net owner",
            "cricket batting cage owner",
            # Academies & Clubs
            "cricket academy flooring",
            "cricket coaching academy",
            "cricket club ground contractor",
            "indoor cricket facility",
            # Contractors
            "cricket turf contractor",
            "artificial cricket pitch contractor",
            "cricket practice net contractor",
            "cricket turf installer",
            "synthetic cricket pitch installer",
            # Institutional & Developers
            "school cricket ground contractor",
            "college cricket ground contractor",
            "cricket ground developer",
            "cricket stadium contractor",
            "sports ground maintenance company",
            "sports academy cricket ground",
            # Government
            "government cricket ground contractor",
            "Khelo India cricket ground",
            "municipal cricket ground contractor",
            # Procurement
            "buy artificial cricket turf India",
            "cricket turf price per sqft India",
            "cricket pitch mat contractor",
        ],
        "gmaps_types": ["sports_complex", "stadium"],
    },

    "Padel Court Turf": {
        "tab": "Padel Court Turf",
        "keywords": [
            # Direct Buyers & Contractors
            "padel court contractor",
            "padel court builder",
            "padel court installer",
            "padel court construction company",
            "padel court developer",
            # Clubs & Owners
            "padel club owner",
            "padel tennis court owner",
            "padel sport club India",
            "padel tennis India",
            # Sports Clubs
            "sports club padel court",
            "tennis club padel court",
            "squash club padel court",
            "fitness club padel court",
            # Hospitality
            "hotel padel court contractor",
            "resort padel court",
            "luxury resort sports contractor",
            "club house padel court",
            # Real Estate
            "township padel court developer",
            "housing society padel court",
            "gated community padel court",
            # Procurement
            "padel court turf India",
            "padel court price India",
            "buy padel court surface India",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── JOYFUL ───────────────────────────────────────────────────────────────
    "Badminton PVC Flooring": {
        "tab": "Badminton PVC Flooring",
        "keywords": [
            # Direct Buyers
            "badminton academy owner",
            "badminton court owner",
            "badminton club owner",
            "indoor sports complex owner",
            # Contractors
            "badminton court flooring contractor",
            "indoor sports flooring contractor",
            "PVC sports flooring contractor",
            "synthetic badminton court contractor",
            "indoor court PVC flooring contractor",
            "badminton court surface contractor",
            "sports hall flooring contractor",
            # Renovation
            "sports hall renovation contractor",
            "badminton court renovation",
            "indoor sports court renovation",
            # Institutional
            "school badminton court contractor",
            "college badminton court contractor",
            "university sports hall contractor",
            "government badminton court contractor",
            # Corporate & Hospitality
            "corporate badminton court",
            "hotel badminton court contractor",
            "club house badminton court",
            "township badminton court contractor",
            # Procurement
            "buy PVC badminton court flooring India",
            "badminton court flooring price India",
            "PVC sports flooring price India",
        ],
        "gmaps_types": ["sports_complex"],
    },

    # ── POWERFUL ─────────────────────────────────────────────────────────────
    "Gym Rubber Roll Flooring": {
        "tab": "Gym Rubber Roll Flooring",
        "keywords": [
            # Contractors & Setup
            "gym setup contractor",
            "gym interior contractor",
            "commercial gym setup contractor",
            "gym renovation contractor",
            "fitness center setup company",
            "gym flooring contractor",
            # Direct Buyers
            "gym owner",
            "commercial gym owner",
            "fitness center owner",
            "gym franchise owner",
            # Fitness Segments
            "CrossFit box setup contractor",
            "CrossFit gym flooring",
            "martial arts gym flooring contractor",
            "boxing gym flooring",
            "weightlifting gym rubber floor",
            "functional fitness gym contractor",
            # Hospitality & Corporate
            "hotel gym flooring contractor",
            "corporate gym setup contractor",
            "office gym flooring",
            "apartment gym contractor",
            "housing society gym contractor",
            # Rehab & Wellness
            "physiotherapy clinic flooring",
            "rehabilitation centre flooring",
            "yoga studio rubber flooring",
            # Procurement
            "buy gym rubber flooring India",
            "rubber gym flooring price India",
            "commercial gym flooring price per sqft",
        ],
        "gmaps_types": ["gym"],
    },

    "Gym Astro Turf": {
        "tab": "Gym Astro Turf",
        "keywords": [
            # Direct Buyers
            "CrossFit box owner",
            "crossfit gym owner",
            "functional training gym owner",
            "performance gym owner",
            "strength conditioning gym owner",
            # Contractors
            "functional training turf contractor",
            "gym turf flooring contractor",
            "gym astro turf installer",
            "fitness turf contractor",
            "sports performance facility contractor",
            "gym interior contractor",
            # Segments
            "CrossFit gym setup contractor",
            "sports performance centre contractor",
            "obstacle course gym contractor",
            "functional fitness area contractor",
            # Hospitality
            "hotel gym astro turf contractor",
            "resort fitness center contractor",
            "club gym astro turf",
            # Procurement
            "buy gym turf India",
            "gym astro turf price India",
            "functional turf flooring price",
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
            "maple wood sports flooring contractor",
            "indoor sports hall contractor",
            "sprung floor contractor",
            "wood flooring sports court",
            # Sport-Specific
            "maple basketball court contractor",
            "wooden basketball floor contractor",
            "indoor basketball wooden floor",
            "squash court wooden floor contractor",
            "badminton wooden court contractor",
            "volleyball court wooden flooring",
            # Niche
            "dance studio wooden floor contractor",
            "aerobics room wooden flooring",
            "multipurpose hall wooden flooring",
            # Institutional & Hospitality
            "school sports hall flooring contractor",
            "university sports hall wooden floor",
            "college gymnasium wooden floor",
            "club house sports flooring contractor",
            "hotel sports hall flooring",
            # Procurement
            "buy wooden sports flooring India",
            "hardwood basketball court price India",
            "maple sports floor price per sqft",
        ],
        "gmaps_types": ["sports_complex", "gym"],
    },

    # ── TRACK & FIELD ────────────────────────────────────────────────────────
    "Athletic Running Track": {
        "tab": "Athletic Running Track",
        "keywords": [
            # Contractors
            "running track contractor",
            "athletic track construction company",
            "PU running track installer",
            "synthetic running track contractor",
            "prefabricated running track installer",
            "rubber running track contractor",
            "athletic track laying contractor",
            # Institutional Education
            "school running track contractor",
            "college athletic track contractor",
            "university running track contractor",
            "school stadium track contractor",
            "sports school running track",
            # Government & Institutional
            "sports authority track contractor",
            "municipal stadium running track contractor",
            "Khelo India track contractor",
            "SAI running track contractor",
            "government athletics track contractor",
            # Defence & Paramilitary
            "army sports track contractor",
            "police academy running track",
            "CRPF sports ground contractor",
            # Broader
            "stadium track construction",
            "athletics field contractor",
            "synthetic track resurfacing",
            # Procurement
            "buy synthetic running track India",
            "PU athletic track price India",
            "running track price per sqft India",
        ],
        "gmaps_types": ["stadium", "sports_complex"],
    },

    # ── ACRYPLAY ─────────────────────────────────────────────────────────────
    "Acrylic Sports Flooring": {
        "tab": "Acrylic Sports Flooring",
        "keywords": [
            # Contractors
            "acrylic sports flooring contractor",
            "acrylic court coating contractor",
            "hard court resurfacing contractor",
            "sports court resurfacing contractor",
            "outdoor court flooring contractor",
            "acrylic court surface contractor",
            # Sport-Specific
            "tennis court acrylic flooring contractor",
            "acrylic basketball court contractor",
            "acrylic volleyball court",
            "acrylic badminton court contractor",
            "multisport acrylic court contractor",
            # Direct Buyers
            "tennis court owner",
            "tennis club contractor",
            "lawn tennis court contractor",
            # Hospitality
            "hotel tennis court contractor",
            "resort sports court contractor",
            "club tennis court contractor",
            # Housing
            "housing society tennis court contractor",
            "gated community tennis court",
            "clubhouse tennis court contractor",
            "township tennis court contractor",
            # Procurement
            "buy acrylic sports flooring India",
            "acrylic tennis court price India",
            "hard court sports flooring price",
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
            "outdoor basketball court contractor",
            "indoor basketball court contractor",
            "sports court contractor",
            "basketball court construction company",
            # Direct Buyers
            "basketball academy owner",
            "basketball club owner",
            "indoor basketball court owner",
            # Institutional
            "school basketball court contractor",
            "college basketball court contractor",
            "university basketball court contractor",
            "government school basketball court",
            "sports school basketball court",
            # Residential & Corporate
            "clubhouse basketball court contractor",
            "housing society basketball court",
            "township basketball court contractor",
            "gated community basketball court",
            "corporate campus basketball court",
            # Sports Infrastructure
            "sports hall construction company",
            "indoor sports hall contractor",
            "basketball arena contractor",
            # Procurement
            "buy basketball court flooring India",
            "basketball court flooring price India",
            "outdoor basketball court price per sqft",
        ],
        "gmaps_types": ["sports_complex", "school"],
    },

    # ── COURT TILES ─────────────────────────────────────────────────────────
    "PP Interlocking Court Tiles": {
        "tab": "PP Interlocking Tiles",
        "keywords": [
            # Contractors & Buyers
            "interlocking sports tiles contractor",
            "modular sports flooring contractor",
            "PP sports tiles installer",
            "outdoor court tiles contractor",
            "outdoor sports court contractor",
            "modular court contractor",
            # Rooftop & Terrace
            "rooftop court tiles contractor",
            "terrace sports tiles contractor",
            "rooftop sports court contractor",
            "terrace multisport court",
            # Residential
            "housing society court tiles contractor",
            "residential sports court tiles",
            "apartment sports amenity contractor",
            "gated community sports court contractor",
            "residential sports court developer",
            # Institutional
            "school outdoor court tiles",
            "school playground tiles contractor",
            # Commercial
            "commercial sports facility contractor",
            "multi sport complex builder",
            "sports club court tiles",
            # Procurement
            "buy PP interlocking tiles India",
            "interlocking court tiles price India",
            "modular sports tiles price per sqft",
        ],
        "gmaps_types": ["sports_complex"],
    },
}

SHEET_HEADERS = [
    "Date", "City", "Product", "Company Name",
    "Contact Person", "Phone", "Email", "Designation", "Source", "Website"
]
