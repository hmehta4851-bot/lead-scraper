import smtplib
import os
from email.mime.text import MIMEText


def send_notification(subject, body):
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    to_email = os.environ.get("NOTIFY_EMAIL", "hmehta4851@gmail.com")

    if not gmail_user or not gmail_pass:
        raise RuntimeError(
            "Email notification required but GMAIL_USER / GMAIL_APP_PASSWORD not set. "
            "Add both as GitHub repository secrets to enable daily lead reports."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, [to_email], msg.as_string())
        print(f"[NOTIFY SENT] {subject}")
    except Exception as e:
        print(f"[NOTIFY ERROR] {e}")


def notify_tier1_exhausted():
    send_notification(
        subject="[Lead Scraper] Tier 1 cities exhausted — moving to Tier 2",
        body=(
            "All Tier 1 cities have been fully cycled through.\n\n"
            "The scraper is now moving to Tier 2 cities.\n\n"
            "Tier 2 cities: Jaipur, Lucknow, Surat, Nagpur, Indore, Vadodara, "
            "Bhopal, Visakhapatnam, Patna, Coimbatore, Gurgaon, Noida, Chandigarh, "
            "Kochi, Guwahati, Bhubaneswar, Thiruvananthapuram, Nashik, Aurangabad, Rajkot\n\n"
            "Leads will continue adding to the same Google Sheet."
        ),
    )


def notify_tier2_exhausted():
    send_notification(
        subject="[Lead Scraper] Tier 2 cities exhausted — restarting cycle",
        body=(
            "All Tier 1 and Tier 2 cities have been cycled through.\n\n"
            "The scraper is restarting from Tier 1 cities again.\n\n"
            "Duplicate leads are automatically skipped (phone number dedup)."
        ),
    )


def notify_scraper_started(city, total_products):
    send_notification(
        subject=f"[Lead Scraper] STARTED — {city}",
        body=(
            f"Lead scraper has started.\n\n"
            f"City: {city}\n"
            f"Products to scrape: {total_products}\n\n"
            f"You will receive a progress update every 15 minutes and a final summary when done."
        ),
    )


def notify_progress_update(city, completed, total, leads_so_far, elapsed_min):
    send_notification(
        subject=f"[Lead Scraper] Progress — {city} ({completed}/{total} products)",
        body=(
            f"Scraper is still running.\n\n"
            f"City: {city}\n"
            f"Products completed: {completed} of {total}\n"
            f"Leads collected so far: {leads_so_far}\n"
            f"Time elapsed: {elapsed_min} minutes\n\n"
            f"Next update in 15 minutes (or final summary when done)."
        ),
    )


def notify_daily_summary(
    city,
    total_leads,
    per_product,
    per_source=None,
    quality=None,
    duration_min=None,
    source_failures=None,
):
    sep = "─" * 42

    # Product breakdown
    product_lines = []
    for product, count in per_product.items():
        bar = "█" * min(count // 5, 10)
        product_lines.append(f"  {product:<30} {count:>3} leads  {bar}")

    # Source breakdown
    source_lines = []
    if per_source:
        for src, count in sorted(per_source.items(), key=lambda x: -x[1]):
            bar = "█" * min(count // 5, 10)
            source_lines.append(f"  {src:<20} {count:>4} leads  {bar}")

    # Quality stats
    quality_lines = []
    if quality and total_leads > 0:
        pct = lambda n: f"{n} ({int(n/total_leads*100)}%)"
        quality_lines = [
            f"  With phone number   : {pct(quality.get('with_phone', total_leads))}",
            f"  With email          : {pct(quality.get('with_email', 0))}",
            f"  With contact person : {pct(quality.get('with_contact', 0))}",
            f"  With website        : {pct(quality.get('with_website', 0))}",
        ]

    duration_str = f"{duration_min} minutes" if duration_min else "—"
    failure_lines = []
    for source, count in sorted((source_failures or {}).items()):
        failure_lines.append(f"  {source:<20} {count:>4} failed attempts")

    body = f"""
╔══════════════════════════════════════════╗
  SUNZONE PROSPECT FLOW — DAILY REPORT
╚══════════════════════════════════════════╝

  City           : {city}
  Total Leads    : {total_leads}
  Duration       : {duration_str}
  Sheet          : https://docs.google.com/spreadsheets/d/1p48H_6PpWgYFyaAtPXijyeAlk1Tgq5kUUQORMBgG8eM

{sep}
  LEADS BY PRODUCT
{sep}
{chr(10).join(product_lines)}

  TOTAL: {total_leads} leads across {len(per_product)} products

{sep}
  LEADS BY SOURCE
{sep}
{chr(10).join(source_lines) if source_lines else "  (source data unavailable)"}

{sep}
  DATA QUALITY
{sep}
{chr(10).join(quality_lines) if quality_lines else "  (quality data unavailable)"}

{sep}
  SOURCES USED (9 total)
{sep}
  1. Google Maps      6. DuckDuckGo
  2. Sulekha          7. Bing
  3. ExportersIndia   8. YellowPages India
  4. IndiaMART        9. JustDial
  5. TradeIndia

{sep}
  SOURCE HEALTH
{sep}
{chr(10).join(failure_lines) if failure_lines else "  All source attempts completed without uncaught errors"}

{sep}
Sunzone Prospect Flow Automation
Built for Sunzone Sports & Play
""".strip()

    send_notification(
        subject=f"[Sunzone Prospect Flow] DONE — {city} — {total_leads} leads",
        body=body,
    )
