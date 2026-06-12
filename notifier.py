import smtplib
import os
from email.mime.text import MIMEText


def send_notification(subject, body):
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    to_email = os.environ.get("NOTIFY_EMAIL", "hmehta4851@gmail.com")

    if not gmail_user or not gmail_pass:
        print(f"[NOTIFY SKIP] No Gmail credentials. Subject: {subject}")
        return

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


def notify_daily_summary(city, total_leads, per_product):
    lines = [f"  {product}: {count} leads" for product, count in per_product.items()]
    body = (
        f"Daily lead scraping complete.\n\n"
        f"City: {city}\n"
        f"Total leads added: {total_leads}\n\n"
        f"Breakdown:\n" + "\n".join(lines)
    )
    send_notification(
        subject=f"[Lead Scraper] {city} — {total_leads} leads added",
        body=body,
    )
