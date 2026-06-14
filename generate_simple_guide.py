"""Sunzone Prospect Flow simple non-technical guide PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import date

OUTPUT = "/Users/admin/lead-scraper/SUNZONE_SIMPLE_GUIDE.pdf"

RED    = colors.HexColor("#EF3B24")
NAVY   = colors.HexColor("#17223B")
LIGHT  = colors.HexColor("#F7F9FC")
BORDER = colors.HexColor("#D9DEE5")
GREEN  = colors.HexColor("#16835F")
WHITE  = colors.white

LM, RM = 18 * mm, 18 * mm
PW = A4[0] - LM - RM  # 174mm usable

def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9, leading=14,
                textColor=colors.HexColor("#20252B"), spaceAfter=4)
    base.update(kw)
    return ParagraphStyle(name, **base)

H1    = S("H1",  fontSize=14, fontName="Helvetica-Bold", textColor=NAVY, leading=18, spaceAfter=8, spaceBefore=4)
H2    = S("H2",  fontSize=13, fontName="Helvetica-Bold", textColor=NAVY, leading=18, spaceBefore=14, spaceAfter=6)
H3    = S("H3",  fontSize=10, fontName="Helvetica-Bold", textColor=RED,  leading=14, spaceBefore=8, spaceAfter=4)
BODY  = S("BD",  fontSize=9,  leading=14, spaceAfter=6)
CELL  = S("CL",  fontSize=8,  leading=12)
BRAND = S("BR",  fontSize=9,  fontName="Helvetica-Bold", textColor=RED, letterSpacing=2, spaceAfter=6)
SUB   = S("SB",  fontSize=10, textColor=colors.HexColor("#4B5563"), spaceAfter=6, leading=15)
LBL   = S("LB",  fontSize=8,  fontName="Helvetica-Bold", textColor=colors.HexColor("#6B7280"))
BIG   = S("BG",  fontSize=18, fontName="Helvetica-Bold", textColor=RED, alignment=TA_CENTER, leading=22)
MED   = S("MD",  fontSize=7,  textColor=colors.HexColor("#4B5563"), alignment=TA_CENTER, leading=11)
TH    = S("TH",  fontSize=8,  fontName="Helvetica-Bold", textColor=WHITE, leading=12)
CALLB = S("CB",  fontSize=9,  leading=14, textColor=NAVY, leftIndent=4)

def rule():
    return HRFlowable(width="100%", thickness=2, color=RED, spaceAfter=8)

def thin_rule():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=5)

def p(text, style=None):
    return Paragraph(text, style or CELL)

def th(text):
    return Paragraph(text, TH)

BASE_TBL = TableStyle([
    ("BACKGROUND",     (0, 0), (-1, 0),   NAVY),
    ("FONTNAME",       (0, 0), (-1, 0),   "Helvetica-Bold"),
    ("FONTSIZE",       (0, 0), (-1, 0),   8),
    ("TEXTCOLOR",      (0, 0), (-1, 0),   WHITE),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1),  [WHITE, LIGHT]),
    ("GRID",           (0, 0), (-1, -1),  0.4, BORDER),
    ("VALIGN",         (0, 0), (-1, -1),  "TOP"),
    ("TOPPADDING",     (0, 0), (-1, -1),  5),
    ("BOTTOMPADDING",  (0, 0), (-1, -1),  5),
    ("LEFTPADDING",    (0, 0), (-1, -1),  6),
    ("RIGHTPADDING",   (0, 0), (-1, -1),  6),
])

def tbl(rows, widths, extra_style=None):
    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = list(BASE_TBL._cmds)
    if extra_style:
        style += extra_style
    t.setStyle(TableStyle(style))
    return t

def box(text, bg=colors.HexColor("#FFF4F1"), border=RED):
    inner = Table([[p(text, CALLB)]], colWidths=[PW - 4])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("BOX",           (0,0),(-1,-1), 1.5, border),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    return inner

def green_box(text):
    return box(text, bg=colors.HexColor("#EFFAF6"), border=GREEN)


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
                            leftMargin=LM, rightMargin=RM,
                            topMargin=18*mm, bottomMargin=18*mm)
    story = []

    # Cover
    story += [
        Spacer(1, 8*mm),
        p("SUNZONE SPORTS &amp; PLAY", BRAND),
        Spacer(1, 4*mm),
        p("Sunzone Prospect Flow", H1),
        Spacer(1, 6*mm),
        p("How our automatic buyer prospect system works — a plain-English "
          "guide for the sales &amp; management team", SUB),
        Spacer(1, 3*mm),
        p(f"Last updated: {date.today().strftime('%B %d, %Y')}", LBL),
        Spacer(1, 4*mm),
        rule(),
        Spacer(1, 2*mm),
        box("📌  <b>What this document is:</b>  A simple explanation of what our automatic "
            "lead-finding system does, how it finds buyers, what it puts in the spreadsheet, "
            "and what is new. No technical knowledge needed."),
        Spacer(1, 6*mm),
    ]

    # What is it?
    story += [
        p("What Is Sunzone Prospect Flow?", H2), rule(),
        p("Think of it as a <b>robot sales researcher</b> that works every day — Monday to "
          "Saturday — while you sleep. Every morning at 8 AM, it automatically searches the "
          "internet for businesses that are likely to <b>buy</b> Sunzone products.", BODY),
        p("It searches 11 different websites at once — Google Maps, Sulekha, IndiaMART, "
          "JustDial, TradeIndia, and more. For each business it finds, it tries to collect "
          "the company name, phone number, email, and contact person.", BODY),
        p("By the end of its run, it adds the best leads directly into your "
          "<b>Google Sheet</b> — automatically, no human needed.", BODY),
        Spacer(1, 3*mm),
        green_box("✅  <b>Result:</b>  Every morning you wake up to fresh, verified buyer "
                  "leads already in your spreadsheet — sorted from best to lowest quality."),
        Spacer(1, 6*mm),
    ]

    # Stat row
    c1 = PW / 4
    stat_rows = [
        [p("11", BIG),  p("170", BIG),   p("20,166", BIG), p("7,705", BIG)],
        [p("websites searched<br/>every single day", MED),
         p("SKU and named systems<br/>in 8 verticals", MED),
         p("validated search terms<br/>in keyword library", MED),
         p("cities covered<br/>across India", MED)],
    ]
    st = Table(stat_rows, colWidths=[c1]*4)
    st.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",    (0,0),(-1,-1), 0.5, BORDER),
        ("BACKGROUND",   (0,0),(-1,-1), LIGHT),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [st, Spacer(1, 8*mm)]

    # Keeps vs Skips
    story += [
        p("How Does It Find the Right Buyers?", H2), rule(),
        p("The system only looks for <b>buyers</b> — companies likely to purchase a "
          "Sunzone product. It automatically skips the wrong types:", BODY),
    ]
    W1, W2 = PW * 0.50, PW * 0.50
    keeps_skips = [
        [th("✅  It KEEPS"), th("❌  It SKIPS")],
        [p("Schools, colleges, universities"),   p("Other flooring companies (competitors)")],
        [p("Gyms and fitness centres"),           p("Manufacturers, suppliers, dealers")],
        [p("Real estate developers, builders,<br/>housing societies, townships"),
         p("Sunzone itself (own company name)")],
        [p("Sports academies, football clubs,<br/>cricket academies, padel clubs"),
         p("Companies with no phone number")],
        [p("Hotels, resorts, corporate offices"),
         p("Competitor brands: Domo Sports, Polytan,<br/>TigerTurf, FieldTurf, etc.")],
        [p("Government projects, stadiums,<br/>municipal contracts"), p("")],
    ]
    kt = Table(keeps_skips, colWidths=[W1, W2], repeatRows=1)
    kt.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(0,0),  GREEN),
        ("BACKGROUND",   (1,0),(1,0),  RED),
        ("TEXTCOLOR",    (0,0),(-1,0), WHITE),
        ("FONTNAME",     (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,-1),8),
        ("FONTNAME",     (0,1),(-1,-1),"Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT]),
        ("GRID",         (0,0),(-1,-1),0.4, BORDER),
        ("VALIGN",       (0,0),(-1,-1),"TOP"),
        ("TOPPADDING",   (0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",  (0,0),(-1,-1),6),
        ("RIGHTPADDING", (0,0),(-1,-1),6),
    ]))
    story += [kt, Spacer(1, 6*mm)]

    story.append(PageBreak())

    # 8 Categories
    story += [
        p("The 8 Business Categories It Searches", H2), rule(),
        p("Leads are organised into <b>8 categories</b> (verticals). Each has its own "
          "tab in the Google Sheet so your sales team can focus on relevant products.", BODY),
    ]
    cats = [
        [th("Category"), th("Sheet Tab"), th("Products Covered")],
        [p("🎠  Playful"),       p("Playful Leads"),         p("EPDM playground flooring, rubber granules for play areas")],
        [p("⚽  Graceful"),      p("Graceful Leads"),        p("Football turf, cricket pitch, hockey turf, padel turf, landscape grass")],
        [p("💪  Powerful"),      p("Powerful Leads"),        p("Gym rubber flooring, gym PVC flooring, gym astro turf")],
        [p("🏸  Joyful"),        p("Joyful Leads"),          p("Badminton PVC / vinyl flooring")],
        [p("🎾  Acryplay"),      p("Acryplay Leads"),        p("Acrylic sports courts, PP interlocking court tiles")],
        [p("🏃  Track &amp; Field"), p("Track &amp; Field Leads"), p("Synthetic athletic running tracks")],
        [p("🏆  Sports Equipment"), p("Sports Equipment Leads"), p("Sports equipment, turnkey facility setup")],
        [p("🪵  Woodplay"),      p("Woodplay Leads"),        p("Maple / Hevea wooden sports flooring")],
    ]
    story += [tbl(cats, [PW*0.19, PW*0.22, PW*0.59]), Spacer(1, 6*mm)]

    # 14 Sheet Columns
    story += [
        p("What Information Goes Into the Google Sheet?", H2), rule(),
        p("Each lead row contains <b>14 pieces of information</b>. "
          "Four columns are brand new — marked with ⭐:", BODY),
    ]
    cols = [
        [th("#"), th("Column"), th("What It Means")],
        [p("1"),  p("Date"),               p("The date this lead was found")],
        [p("2"),  p("City"),               p("Which city was searched that day")],
        [p("3"),  p("Vertical  ⭐ NEW"),   p("Which business category — e.g. Graceful, Playful, Powerful")],
        [p("4"),  p("Product  ⭐ NEW"),    p("The exact Sunzone product this lead is relevant to")],
        [p("5"),  p("Search Keyword  ⭐ NEW"), p("The exact phrase typed into the search engine to find this company")],
        [p("6"),  p("Company Name"),       p("Name of the business")],
        [p("7"),  p("Contact Person"),     p("Name of the owner / director / manager (if found online)")],
        [p("8"),  p("Phone"),              p("10-digit mobile or landline number")],
        [p("9"),  p("Email"),              p("Company email address (if found online)")],
        [p("10"), p("Designation"),        p("Job title of the contact — e.g. Director, Proprietor")],
        [p("11"), p("Source"),             p("Which website found this lead — e.g. Google Maps, Sulekha")],
        [p("12"), p("Website"),            p("Company website address")],
        [p("13"), p("Lead Score  ⭐ NEW"), p("Score from 65–100. Higher = more complete data and stronger buyer match. Sort by this column to call best leads first.")],
        [p("14"), p("Qualification Reason  ⭐ NEW"), p("Why this company was included — e.g. 'sports academy buyer signal'")],
    ]
    story += [tbl(cols, [PW*0.06, PW*0.25, PW*0.69]), Spacer(1, 6*mm)]

    story.append(PageBreak())

    # Cities
    story += [
        p("Which Cities Does It Cover?", H2), rule(),
        p("The system covers <b>7,705 Census-recognized statutory and census towns "
          "across India</b>. Major commercial cities are searched first. It then moves "
          "through the complete national town list and restarts from Mumbai only after "
          "the full list has been covered.", BODY),
        p("<b>How small towns are handled:</b>", H3),
        p("A large city can form one daily batch. If a smaller town cannot produce enough "
          "genuine buyers, the system automatically adds the next town or towns to the same "
          "day's batch. Their qualified leads are combined toward the target of at least "
          "50 leads in each vertical. Every spreadsheet row still shows the exact town "
          "where that lead was found.", BODY),
        p("<b>Schedule:</b>", H3),
        p("The automation runs Monday to Saturday at 8:00 AM. Sunday is kept free. "
          "Each scheduled day starts with the next unprocessed town in the national rotation.", BODY),
        Spacer(1, 4*mm),
    ]

    # 11 Websites
    story += [
        p("Which 11 Websites Does It Search?", H2), rule(),
        p("Searching multiple websites means if one is blocked or gives no results, "
          "the others still work. It never relies on just one source.", BODY),
    ]
    sites = [
        [th("#"), th("Website"), th("Why It Is Useful")],
        [p("1"),  p("Sulekha"),          p("India's top service directory — great for local contractors")],
        [p("2"),  p("ExportersIndia"),   p("B2B marketplace — shows full phone numbers without login")],
        [p("3"),  p("TradeIndia"),       p("B2B marketplace — suppliers and project companies")],
        [p("4"),  p("DuckDuckGo"),       p("Private search engine — finds company websites with contact info")],
        [p("5"),  p("Bing"),             p("Microsoft search engine — different results from Google")],
        [p("6"),  p("Yahoo Search  ⭐"), p("Another search engine — third independent set of results (new)")],
        [p("7"),  p("YellowPages India"),p("Business directory — good coverage of small and medium businesses")],
        [p("8"),  p("OpenStreetMap  ⭐"),p("Global map database — finds venues like gyms, schools, stadiums (new)")],
        [p("9"),  p("IndiaMART"),        p("India's largest B2B platform (some phone numbers may be hidden behind login)")],
        [p("10"), p("JustDial"),         p("Popular Indian directory (sometimes blocks automated searches)")],
        [p("11"), p("Google Maps"),      p("Searched last — fills any gaps the other 10 sources missed")],
    ]
    story += [tbl(sites, [PW*0.06, PW*0.20, PW*0.74]), Spacer(1, 6*mm)]

    # What's new
    story += [
        p("What Is New in the Latest Update?", H2), rule(),
    ]
    news = [
        [th("Improvement"), th("What It Means for You")],
        [p("Lead Score column"),
         p("Each lead now gets a score from 65–100. Higher = more complete contact details "
           "and stronger match to your product. Sort by this column to call the best leads first.")],
        [p("Qualification Reason column"),
         p("Tells you WHY this company was included — e.g. 'sports academy buyer signal'. "
           "Quick way to understand a lead at a glance.")],
        [p("Vertical and Product columns"),
         p("Every lead now shows which of the 8 business categories it belongs to and the "
           "exact product it is relevant for. Sales reps can filter the sheet by their area.")],
        [p("Search Keyword column"),
         p("Shows exactly what search phrase found this lead — useful for understanding "
           "context, e.g. 'gym rubber flooring project hotel' shows a hotel buying gym flooring.")],
        [p("20,166 validated search terms"),
         p("The checked keyword library rotates fresh phrases while the matching SKU target "
           "also rotates inside its correct product family and vertical.")],
        [p("OpenStreetMap and Yahoo added"),
         p("Two new search sources. OpenStreetMap finds physical venues (gyms, schools, "
           "stadiums). Yahoo adds a third independent search engine for different results.")],
        [p("No duplicate leads"),
         p("Before writing to the sheet, the system checks phone numbers against ALL "
           "existing leads across ALL tabs. Same company never appears twice.")],
        [p("Archived before clearing"),
         p("When the Clear Sheet option is used, the system first saves a backup copy "
           "of all existing data. No data is ever permanently lost.")],
        [p("Smarter scheduling"),
         p("If the system somehow starts twice at the same time, one run automatically "
           "waits for the other to finish first — no duplicate data.")],
    ]
    story += [tbl(news, [PW*0.26, PW*0.74]), Spacer(1, 6*mm)]

    story.append(PageBreak())

    # Step by step
    story += [
        p("What Happens Every Morning — Step by Step", H2), rule(),
    ]
    steps = [
        [th("Step"), th("When"), th("What Happens")],
        [p("1"),  p("8:00 AM"),      p("System wakes up automatically on GitHub servers")],
        [p("2"),  p("8:01 AM"),      p("Picks today's starting town from the national rotation")],
        [p("3"),  p("8:02 AM"),      p("Selects fresh phrases from 20,166 validated keywords and rotates the matching SKU target")],
        [p("4"),  p("8:03 AM"),      p("Starts searching all 11 websites simultaneously with those phrases")],
        [p("5"),  p("During run"),   p("For each company found, visits their website to collect phone, email, and contact name")],
        [p("6"),  p("During run"),   p("Removes duplicate companies — same phone number across different sources")],
        [p("7"),  p("During run"),   p("Removes competitors, suppliers, and own-brand results automatically")],
        [p("8"),  p("During run"),   p("Scores each lead 65–100 based on data completeness and buyer relevance")],
        [p("9"),  p("During run"),   p("Sorts best leads to the top")],
        [p("10"), p("End of run"),   p("Checks sheet — skips any phone number already there to avoid duplicates")],
        [p("11"), p("End of run"),   p("Writes new leads into the correct vertical tab in Google Sheets")],
        [p("12"), p("During run"),   p("If a small town has too few genuine buyers, adds the next town to the same daily batch")],
        [p("13"), p("End of run"),   p("Sends a quota report showing each vertical's actual count against the target of 50")],
        [p("14"), p("Next morning"), p("Starts with the next town not already used in the previous day's batch")],
    ]
    story += [tbl(steps, [PW*0.08, PW*0.16, PW*0.76]), Spacer(1, 6*mm)]

    # FAQ
    story += [p("Common Questions", H2), rule()]
    faqs = [
        ("Do I need to do anything to make it run?",
         "No. It runs automatically every morning. Just open the Google Sheet to see new leads."),
        ("Can I run it manually for fresh leads right now?",
         "Yes, but this is optional. Go to GitHub → Actions → Sunzone Prospect Flow - "
         "Daily Collection → click Run workflow. Normal daily operation needs no action from you."),
        ("What happens when a small town has fewer than 50 leads?",
         "The system combines that town with the next town or towns during the same daily "
         "run. It keeps adding genuine leads until each vertical reaches 50 or the safe "
         "cloud runtime ends. It never invents leads or accepts competitors just to reach a number."),
        ("Why do some leads have no email or contact person?",
         "Not all companies publish their email or owner's name online. The system tries its "
         "best to find these but some simply do not have it publicly available."),
        ("How do I know if a lead is good?",
         "Look at the Lead Score column. 85–100 = excellent (phone + email + contact found). "
         "65–75 = basic (phone only). Also check Qualification Reason to see the buyer type."),
        ("Will the same company appear twice?",
         "No. The system checks every phone number against the entire sheet before adding "
         "anything. If a company already exists, it is skipped."),
        ("What if the system fails one day?",
         "You receive an automatic failure alert by email. There is also a watchdog program "
         "that checks every 6 hours and restarts the system if it stops unexpectedly."),
        ("How do I clear old data and start fresh?",
         "Go to GitHub → Actions → Clear Sheet → Run workflow. It automatically backs up "
         "all existing data first, then clears the sheet for a fresh start."),
    ]
    for q, a in faqs:
        story += [
            KeepTogether([
                p(f"❓  {q}", H3),
                p(a, BODY),
                thin_rule(),
            ])
        ]

    # Footer
    story += [
        Spacer(1, 4*mm),
        HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=3),
        p(f"Sunzone Sports &amp; Play — Prospect Flow Simple Guide  |  "
          f"{date.today().strftime('%B %d, %Y')}  |  "
          "For technical details see: SUNZONE_SCRAPER_REPORT.pdf",
          S("FTR", fontSize=7, textColor=colors.HexColor("#9CA3AF"), alignment=TA_CENTER)),
    ]

    doc.build(story)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build()
