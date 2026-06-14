from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = Path(
    "/Users/admin/Desktop/"
    "Sunzone-Prospect-Flow-Detailed-Build-Report.pdf"
)
LOGO = Path("/Users/admin/lead-scraper/sunzone-logo-hd.png")

ORANGE = colors.HexColor("#F04423")
NAVY = colors.HexColor("#17242D")
INK = colors.HexColor("#27343B")
MUTED = colors.HexColor("#617078")
PALE = colors.HexColor("#FFF4EF")
PALE_GREEN = colors.HexColor("#EDF8F3")
LINE = colors.HexColor("#E3E8EA")
GREEN = colors.HexColor("#16845B")
WHITE = colors.white

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    "CoverTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=28,
    leading=33,
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=7 * mm,
))
styles.add(ParagraphStyle(
    "CoverSub",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=12.5,
    leading=18,
    textColor=MUTED,
    alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "H1x",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=21,
    leading=26,
    textColor=NAVY,
    spaceAfter=4.5 * mm,
))
styles.add(ParagraphStyle(
    "H2x",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    textColor=NAVY,
    spaceBefore=3.5 * mm,
    spaceAfter=2 * mm,
))
styles.add(ParagraphStyle(
    "Bodyx",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.8,
    leading=14.7,
    textColor=INK,
    spaceAfter=2.8 * mm,
))
styles.add(ParagraphStyle(
    "Smallx",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8.3,
    leading=12,
    textColor=INK,
))
styles.add(ParagraphStyle(
    "Tinyx",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=7.5,
    leading=10.5,
    textColor=MUTED,
))
styles.add(ParagraphStyle(
    "Callout",
    parent=styles["BodyText"],
    fontName="Helvetica-Bold",
    fontSize=10.8,
    leading=16,
    textColor=NAVY,
    alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    "Bulletx",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.6,
    leading=14.3,
    textColor=INK,
    leftIndent=5 * mm,
    firstLineIndent=-3.5 * mm,
    bulletIndent=0,
    spaceAfter=1.7 * mm,
))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 7.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        18 * mm,
        9 * mm,
        "SUNZONE PROSPECT FLOW | DETAILED BUILD REPORT",
    )
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=18 * mm,
    rightMargin=18 * mm,
    topMargin=17 * mm,
    bottomMargin=20 * mm,
    title="Sunzone Prospect Flow Detailed Build Report",
    author="Sunzone Sports & Play",
    subject="How Sunzone Prospect Flow was designed, built and verified",
)
frame = Frame(
    doc.leftMargin,
    doc.bottomMargin,
    doc.width,
    doc.height,
    leftPadding=0,
    rightPadding=0,
    topPadding=0,
    bottomPadding=0,
)
doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=footer))


def p(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def bullet(text):
    return Paragraph(f"&bull;&nbsp; {text}", styles["Bulletx"])


def callout(text, background=PALE, border=ORANGE):
    result = Table([[p(text, "Callout")]], colWidths=[doc.width])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5 * mm),
    ]))
    return result


def table(data, widths, header=True, tiny=False):
    wrapped = []
    for row_index, row in enumerate(data):
        style = "Tinyx" if tiny else "Smallx"
        if row_index == 0 and header:
            style = "Smallx"
        wrapped.append([p(str(value), style) for value in row])
    result = Table(
        wrapped,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.3 * mm),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [WHITE, colors.HexColor("#F8FAFA")],
        ),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    result.setStyle(TableStyle(commands))
    return result


def section(title, intro=None):
    items = [p(title, "H1x")]
    if intro:
        items.append(p(intro))
    return items


story = [Spacer(1, 14 * mm)]
if LOGO.exists():
    logo = Image(str(LOGO))
    logo._restrictSize(85 * mm, 30 * mm)
    logo.hAlign = "CENTER"
    story.extend([logo, Spacer(1, 11 * mm)])

story.extend([
    p("SUNZONE PROSPECT FLOW", "CoverTitle"),
    p("Detailed Build and Engineering Journey", "CoverSub"),
    Spacer(1, 8 * mm),
    callout(
        "A management-friendly explanation of what it took to turn a broad "
        "lead-generation idea into an automatic, product-aware prospecting "
        "system for Sunzone Sports & Play."
    ),
    Spacer(1, 14 * mm),
    table([
        ["Purpose", "Build a repeatable daily pipeline of qualified B2B prospects"],
        ["Product scope", "170 SKU/system records routed through 18 buying families and 8 verticals"],
        ["Search scope", "11 independent public lead sources"],
        ["Keyword intelligence", "20,166 validated product-specific search phrases"],
        ["Geographic scope", "7,705 Indian cities and towns"],
        ["Delivery", "8 organised Google Sheet tabs for the sales team"],
        ["Operation", "Cloud scheduled Monday to Saturday with automatic recovery"],
        ["Current release", "Maharashtra-first, beginning with Mumbai"],
    ], [49 * mm, 125 * mm], header=False),
    Spacer(1, 16 * mm),
    p("Prepared 14 June 2026", "CoverSub"),
    PageBreak(),
])

story.extend(section(
    "1. Executive Summary",
    "Sunzone Prospect Flow was not built as a single scraper or a list of "
    "search terms. It is a connected operating system for prospect discovery, "
    "qualification, organisation and recovery. Each layer was added because "
    "a raw list of internet results is not reliable enough for a sales team."
))
story.extend([
    p("The business problem", "H2x"),
    bullet("Salespeople need a regular supply of prospects arranged by product vertical."),
    bullet("Search results often contain competitors, suppliers, duplicates and irrelevant businesses."),
    bullet("One search website can fail, block access or produce weak results without warning."),
    bullet("Small towns may not contain enough qualified buyers to meet a daily target."),
    bullet("The owner should not have to start, monitor or repair the process every day."),
    p("The resulting solution", "H2x"),
    table([
        ["Layer", "Why it was required"],
        ["Product intelligence", "Keep every search aligned with an exact Sunzone product and vertical."],
        ["Multi-source discovery", "Reduce dependence on any single directory or map provider."],
        ["Qualification", "Reject competitors, suppliers, weak matches and unusable records."],
        ["Deduplication", "Prevent salespeople from receiving the same phone number repeatedly."],
        ["Geographic rotation", "Cover India systematically without repeatedly searching only major cities."],
        ["Cloud operation", "Run even when the office Mac is switched off."],
        ["Recovery and reporting", "Retry failures, preserve progress and report honest shortfalls."],
    ], [47 * mm, 127 * mm]),
    Spacer(1, 6 * mm),
    callout(
        "The automation is called an AI prospecting system because it applies "
        "structured product intelligence and decision rules throughout the "
        "journey. It does not depend on a paid generative-AI API to operate."
    ),
    PageBreak(),
])

story.extend(section(
    "2. Requirements and Design Decisions",
    "The build began by converting business expectations into rules the "
    "software could enforce consistently."
))
story.extend([
    table([
        ["Business requirement", "Engineering decision"],
        ["50 quality leads per vertical", "A separate quota counter for each of 8 verticals; success only when every counter reaches 50."],
        ["No competitor leads", "Competitor names, domains and identity text are checked before acceptance."],
        ["No supplier-heavy results", "Supplier, manufacturer, exporter, distributor and installer signals are rejected."],
        ["Do not rely on Google Maps", "All 11 sources are attempted in the first round and each source is isolated from the others."],
        ["Correct product targeting", "Keywords carry compulsory product and vertical labels and are validated before use."],
        ["One region at a time", "Mumbai begins the rotation and all 509 Maharashtra towns come before the rest of India."],
        ["No daily manual work", "GitHub Actions schedules the run and securely authenticates to Google."],
        ["No invented data", "Quota shortages return a shortfall status and trigger recovery; filters are not relaxed."],
    ], [55 * mm, 119 * mm]),
    Spacer(1, 6 * mm),
    p("Important design principle", "H2x"),
    p(
        "The system is fail-closed. If a record cannot prove that it is useful "
        "enough, it is excluded. If one vertical is below target, the complete "
        "run is not reported as successful. This makes the numbers more honest, "
        "although it also means the system cannot promise that the public web "
        "will always contain 50 suitable, reachable prospects for every vertical."
    ),
    PageBreak(),
])

story.extend(section(
    "3. Product and Keyword Intelligence",
    "A large keyword list alone is dangerous: the same phrase can mean "
    "different products, attract suppliers, or send a lead to the wrong sales "
    "team. The keyword layer therefore required extensive cleaning and routing."
))
story.extend([
    table([
        ["Verified component", "Current production quantity"],
        ["Sunzone product verticals", "8"],
        ["Buyer-search families", "18"],
        ["Routed SKU and named system records", "170"],
        ["Approved unique keyword phrases", "20,166"],
        ["Ambiguous phrases removed during validation", "9,207"],
        ["Minimum validated phrases available to each product", "356"],
    ], [77 * mm, 97 * mm]),
    Spacer(1, 5 * mm),
    p("What happens to a search phrase", "H2x"),
    bullet("It is attached to one exact product and one exact Sunzone vertical."),
    bullet("The phrase is checked against product-specific rules before production use."),
    bullet("A rotating cursor selects fresh phrases rather than repeating the same search every day."),
    bullet("The city placeholder is replaced with the active city or town."),
    bullet("A buyer type such as school, gym, academy, resort or institution is added according to the vertical."),
    bullet("The phrase used to find the lead is stored in the Google Sheet for traceability."),
    p("Why keyword rotation matters", "H2x"),
    p(
        "Public search engines return different results for different wording. "
        "Using several validated phrases and buyer combinations increases "
        "coverage while preserving relevance. The saved cursor allows the next "
        "run to continue from where the previous run stopped."
    ),
    callout(
        "The keyword engine is product-aware, city-aware, buyer-aware and "
        "stateful. This is substantially different from repeatedly searching "
        "a generic phrase such as 'sports flooring'.",
        PALE_GREEN,
        GREEN,
    ),
    PageBreak(),
])

story.extend(section(
    "4. The 11-Source Discovery Network",
    "The discovery layer was built around independent sources. A source is "
    "allowed to fail without stopping the complete run."
))
story.extend([
    table([
        ["Source", "Role in the network"],
        ["Sulekha", "Local-service and business discovery"],
        ["ExportersIndia", "Marketplace discovery used in the broad first round"],
        ["TradeIndia", "Marketplace discovery used in the broad first round"],
        ["DuckDuckGo", "Independent web-search results"],
        ["Bing", "Independent web-search results"],
        ["Yellow Pages", "Business-directory discovery"],
        ["OpenStreetMap", "Open geographic business data"],
        ["Yahoo", "Additional web-search coverage"],
        ["IndiaMART", "Marketplace discovery used in the broad first round"],
        ["JustDial", "Local business-directory discovery"],
        ["Google Maps", "One geographic source among the complete network"],
    ], [47 * mm, 127 * mm], tiny=True),
    Spacer(1, 5 * mm),
    p("How dependency is controlled", "H2x"),
    bullet("All 11 configured sources are attempted during the first search round."),
    bullet("If one source throws an error, its failure is recorded and the other sources continue."),
    bullet("Later recovery rounds use 8 buyer-focused sources and exclude supplier-heavy marketplaces."),
    bullet("No source may contribute more than 25 accepted leads to one vertical in one day."),
    bullet("Google Maps therefore cannot independently satisfy a 50-lead vertical target."),
    bullet("Smaller sources are kept visible through balanced result selection."),
    callout(
        "The system is not Google-Maps-dependent. However, public sources can "
        "change their pages or block automation, so source health is monitored "
        "and failures are isolated rather than ignored."
    ),
    PageBreak(),
])

story.extend(section(
    "5. Lead Qualification and Data Cleaning",
    "Finding a business is only the beginning. The most important engineering "
    "work happens between discovery and the Google Sheet."
))
story.extend([
    table([
        ["Quality gate", "What it prevents"],
        ["Own-brand protection", "Sunzone's own company, website or email returning as a prospect."],
        ["Competitor screening", "Known sports-flooring brands and competitor identity signals."],
        ["Supplier screening", "Manufacturers, exporters, distributors, dealers and flooring contractors."],
        ["Buyer relevance", "Businesses that do not match the expected buyer profile for the vertical."],
        ["Phone normalisation", "The same Indian number appearing in +91, leading-zero or spaced formats."],
        ["Company normalisation", "Duplicate company names hidden behind Pvt Ltd, LLP or punctuation variants."],
        ["Minimum contact usability", "Records without a usable identity or contact route."],
        ["Cross-sheet deduplication", "A phone already delivered in another vertical tab."],
        ["Source cap", "One directory dominating the sales team's complete daily list."],
    ], [55 * mm, 119 * mm], tiny=True),
    Spacer(1, 5 * mm),
    p("What the salesperson receives", "H2x"),
    bullet("Date, city, vertical, exact product and exact search phrase."),
    bullet("Company name, contact person when available, phone, email and website."),
    bullet("The originating source, lead score and a plain qualification reason."),
    p("What the system deliberately does not do", "H2x"),
    bullet("It does not invent missing phone numbers, emails or companies."),
    bullet("It does not lower filters merely to make a target appear complete."),
    bullet("It does not silently classify a supplier as a buyer."),
    PageBreak(),
])

story.extend(section(
    "6. Geographic Rotation and Daily Search Depth",
    "The geographic engine was expanded from a short city list into an "
    "official Census-based catalogue covering 7,705 Indian cities and towns."
))
story.extend([
    table([
        ["Rotation rule", "Production behaviour"],
        ["Starting point", "Mumbai, Maharashtra"],
        ["Maharashtra priority", "All 509 Maharashtra towns are contiguous at the beginning."],
        ["Next national city", "Delhi appears only after the complete Maharashtra block."],
        ["Mumbai search depth", "The first city receives all 8 product-keyword rounds before another town is added."],
        ["Small-town support", "Additional Maharashtra towns may be grouped when one town cannot provide enough genuine prospects."],
        ["Maximum daily town group", "Up to 20 towns, subject to the safe runtime limit."],
        ["Rotation memory", "Completed towns and keyword positions are stored for the next run."],
    ], [56 * mm, 118 * mm]),
    Spacer(1, 6 * mm),
    p("Why this required careful state management", "H2x"),
    p(
        "Changing the rotation could not erase the previous keyword positions, "
        "buyer positions, deduplication history or recovery information. The "
        "release reset only the city index to Mumbai while preserving the "
        "remaining operating state."
    ),
    callout(
        "The Maharashtra-first release is protected by code tests and a cloud "
        "preflight rule that rejects deployment unless Mumbai is first and all "
        "509 Maharashtra towns appear before every other state.",
        PALE_GREEN,
        GREEN,
    ),
    PageBreak(),
])

story.extend(section(
    "7. Google Sheet Delivery System",
    "The output was designed for sales use, not only for technical storage."
))
story.extend([
    table([
        ["Sunzone vertical tab", "Delivery status"],
        ["Playful Leads", "Production access verified"],
        ["Graceful Leads", "Production access verified"],
        ["Powerful Leads", "Production access verified"],
        ["Joyful Leads", "Production access verified"],
        ["Acryplay Leads", "Production access verified"],
        ["Track & Field Leads", "Production access verified"],
        ["Sports Equipment Leads", "Production access verified"],
        ["Woodplay Leads", "Production access verified"],
    ], [70 * mm, 104 * mm]),
    Spacer(1, 5 * mm),
    p("Delivery safeguards", "H2x"),
    bullet("Each tab is checked for accessibility and the exact required header structure before production."),
    bullet("Existing phone numbers are loaded before collection to prevent repeat delivery."),
    bullet("Rows are written only after product routing, qualification and source-cap checks."),
    bullet("A same-day recovery run reloads the existing sheet and continues without deleting good leads."),
    bullet("The Sheet remains the simple front end for the salespeople; no additional app is required."),
    p("Why the Sheet is part of the production preflight", "H2x"),
    p(
        "A scraper can work perfectly and still fail the business if it cannot "
        "write to the right destination. The preflight therefore treats Sheet "
        "access and tab structure as compulsory production dependencies."
    ),
    PageBreak(),
])

story.extend(section(
    "8. Cloud Scheduling and Zero-Routine-Intervention Operation",
    "The automation runs in GitHub Actions, so the office Mac does not need to "
    "remain switched on."
))
story.extend([
    table([
        ["Cloud component", "Purpose"],
        ["Scheduled workflow", "Starts at 8:00 AM IST, Monday to Saturday."],
        ["Python 3.11 environment", "Provides a repeatable supported runtime in the cloud."],
        ["Playwright browser", "Supports sources that require a real browser engine."],
        ["Private temporary directory", "Restricts temporary credential and browser files on the runner."],
        ["Google Workload Identity", "Allows Google Sheet access without storing a downloadable service-account key."],
        ["Gmail authentication", "Sends progress, completion and recovery notices."],
        ["Concurrency control", "Prevents overlapping daily collection jobs."],
        ["Six-hour job limit", "Stops an unhealthy cloud process from running indefinitely."],
    ], [57 * mm, 117 * mm]),
    Spacer(1, 6 * mm),
    p("No paid AI API dependency", "H2x"),
    p(
        "The current production flow uses deterministic Python logic, public "
        "sources, GitHub Actions, Google Sheets and Gmail authentication. It "
        "does not require OpenAI, Anthropic, Gemini or another paid generative "
        "AI API for the daily prospecting run."
    ),
    callout(
        "Zero routine intervention means Sunzone does not need to press a "
        "button every morning. Human attention can still be required if an "
        "external login is revoked, a public website changes, or a cloud "
        "provider experiences an outage."
    ),
    PageBreak(),
])

story.extend(section(
    "9. Failure Recovery and Honest Quota Handling",
    "Recovery was designed to continue useful work without corrupting or "
    "duplicating the existing sales data."
))
story.extend([
    table([
        ["Event", "Automatic response"],
        ["One source fails", "Record the failure and continue with the remaining sources."],
        ["Unexpected main-process failure", "The daily workflow retries once after a controlled delay."],
        ["One or more verticals remain below 50", "Return a verified shortfall status instead of false success."],
        ["Daily workflow remains unsuccessful", "The watchdog launches bounded same-day recovery attempts."],
        ["Recovery begins", "Reload the day's existing Sheet data and resume the original city batch."],
        ["Duplicate found during recovery", "Reject it using the existing phone and company history."],
        ["Maximum recovery reached", "Stop repeated attempts and send an alert rather than loop forever."],
    ], [58 * mm, 116 * mm]),
    Spacer(1, 6 * mm),
    p("Why the target cannot be guaranteed", "H2x"),
    p(
        "The engineering can guarantee that the system will pursue the target, "
        "use the configured search depth, enforce the filters and report the "
        "truth. It cannot guarantee that public websites contain 50 unique, "
        "reachable and relevant buyers for every product vertical in every "
        "geography on every day."
    ),
    callout(
        "A trustworthy shortfall is better than an impressive-looking list "
        "filled with competitors, suppliers, duplicates or fabricated details."
    ),
    PageBreak(),
])

story.extend(section(
    "10. Security and Production Hardening",
    "Security work focused on keeping credentials out of the codebase and "
    "making the cloud workflow predictable."
))
story.extend([
    bullet("Google authentication uses Workload Identity Federation rather than a committed key file."),
    bullet("Gmail credentials are stored as GitHub secrets and are not printed in logs."),
    bullet("Temporary runtime files use a private directory with restricted permissions."),
    bullet("GitHub workflow actions are pinned to exact commit hashes to reduce supply-chain drift."),
    bullet("Only the required GitHub permissions are granted to the daily workflow."),
    bullet("Concurrent runs are serialised so two jobs do not write competing state."),
    bullet("State updates preserve earlier work and are committed only through the controlled workflow."),
    bullet("Competitor and own-brand matching checks names, websites, hosts and email domains."),
    p("Security boundary", "H2x"),
    p(
        "No automation can make third-party public websites permanently stable "
        "or eliminate every inaccurate business listing. The security controls "
        "protect Sunzone's workflow and credentials; data-quality controls "
        "separately reduce the risk created by public information."
    ),
    PageBreak(),
])

story.extend(section(
    "11. Testing, Review and Release Verification",
    "The final system was tested at code level and then checked again inside "
    "the real cloud environment."
))
story.extend([
    table([
        ["Verification area", "Confirmed result"],
        ["Automated code tests", "38 passing"],
        ["Vertical configuration", "8 verticals"],
        ["Product configuration", "18 search families and 170 routed SKU/system records"],
        ["Source registry", "11 lead sources"],
        ["City catalogue", "7,705 unique towns"],
        ["Maharashtra-first invariant", "509 Maharashtra towns beginning with Mumbai"],
        ["Keyword catalogue", "20,166 validated phrases"],
        ["Google Sheet access", "All 8 production tabs accessible"],
        ["Gmail authentication", "Production authentication valid"],
        ["Workflow syntax", "All GitHub Actions workflow files valid"],
        ["Independent review", "Release reviewed with a GO decision before deployment"],
    ], [62 * mm, 112 * mm]),
    Spacer(1, 6 * mm),
    p("Production evidence", "H2x"),
    p(
        "The Maharashtra-first release was deployed as commit "
        "<b>f8283de</b>. GitHub Actions production preflight run "
        "<b>27501206336</b> completed successfully on 14 June 2026. "
        "The cloud log confirmed the Sheet tabs, Gmail access, sources, "
        "keywords, town catalogue and Mumbai rotation index."
    ),
    callout(
        "Testing proves that the configured system behaves as designed. It "
        "does not freeze third-party websites in time, which is why failure "
        "isolation, monitoring and bounded recovery are also part of the build.",
        PALE_GREEN,
        GREEN,
    ),
    PageBreak(),
])

story.extend(section(
    "12. What It Took to Build the Complete System",
    "The effort was spread across business analysis, data preparation, "
    "software engineering, cloud operations and quality assurance."
))
story.extend([
    table([
        ["Workstream", "Examples of completed work"],
        ["Business mapping", "Converted Sunzone's products, verticals, buyers and sales expectations into enforceable rules."],
        ["Data engineering", "Cleaned keywords, removed ambiguity, created product mappings and generated the Census town rotation."],
        ["Source engineering", "Built and integrated 11 source adapters with independent error handling."],
        ["Qualification engineering", "Added competitor, supplier, buyer-fit, identity and contact checks."],
        ["State management", "Preserved city, product-keyword and buyer-intent progress across daily and recovery runs."],
        ["Sales delivery", "Created exact Google Sheet routing, headers, deduplication and traceable lead fields."],
        ["Cloud automation", "Configured scheduling, Python, browsers, Google identity, Gmail and concurrency."],
        ["Reliability engineering", "Added time limits, retries, watchdog recovery, shortfall status and alerts."],
        ["Security hardening", "Protected secrets, restricted temporary files and pinned workflow dependencies."],
        ["Quality assurance", "Built 37 tests, static preflight rules, cloud verification and an independent release review."],
        ["Documentation", "Produced operating guides and management reports in plain language."],
    ], [47 * mm, 127 * mm], tiny=True),
    Spacer(1, 6 * mm),
    callout(
        "The final value is not one clever search. It is the combination of "
        "many smaller safeguards that makes daily use practical for the sales team."
    ),
    PageBreak(),
])

story.extend(section(
    "13. Final Operating Picture",
    "Sunzone Prospect Flow is now a production prospecting pipeline with a "
    "clear division between what is automated, what is verified, and what "
    "remains dependent on the public web."
))
story.extend([
    table([
        ["Category", "Current position"],
        ["Automatic", "Scheduling, city selection, keyword rotation, 11-source search, qualification, deduplication, Sheet delivery, notifications and recovery."],
        ["Verified", "Code tests, cloud identities, Sheet tabs, Gmail, keyword catalogue, source catalogue and Maharashtra-first rotation."],
        ["Targeted", "50 or more qualified leads for each of 8 verticals."],
        ["Quality policy", "Never fabricate leads or weaken filters to manufacture the target."],
        ["First geography", "Mumbai followed by every Maharashtra city and town."],
        ["Sales interface", "Sunzone's existing Google Sheet, ready to share with the sales team."],
        ["Routine owner work", "None under normal operating conditions."],
        ["External risk", "Public source changes, inaccurate listings, revoked credentials or cloud outages."],
    ], [49 * mm, 125 * mm]),
    Spacer(1, 8 * mm),
    HRFlowable(
        width="100%",
        thickness=1,
        color=ORANGE,
        spaceBefore=3 * mm,
        spaceAfter=5 * mm,
    ),
    p(
        "<b>Management conclusion:</b> Sunzone Prospect Flow required a full "
        "product-intelligence layer, a diversified discovery network, strict "
        "lead-quality gates, persistent geographic and keyword memory, secure "
        "cloud execution, automated recovery and production verification. "
        "It is ready to operate as Sunzone's daily prospecting assistant, with "
        "transparent reporting whenever the real market supplies fewer leads "
        "than the target.",
        "Bodyx",
    ),
    Spacer(1, 5 * mm),
    callout(
        "Built to help the sales team spend less time searching and more time "
        "speaking with relevant prospective buyers.",
        PALE_GREEN,
        GREEN,
    ),
])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story)
print(OUTPUT)
