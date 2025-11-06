import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

# === CONFIGURATION ===
KEYWORDS = [
    r"nvcc",
    r"nova community college",
    r"northern virginia community college",
    r"northern va community college",
    r"nova (college|education|community)"
]

JURISDICTIONS = {
    "Fairfax County": "https://www.fairfaxcounty.gov/boardofsupervisors/meetings",
    "Loudoun County": "https://lfportal.loudoun.gov/LFPortalOnline/",
    "Prince William County": "https://www.pwcva.gov/department/board-county-supervisors",
    "Arlington County": "https://www.arlingtonva.us/Government/County-Board/Meetings",
    "City of Alexandria": "https://www.alexandriava.gov/CityCouncil",
    "City of Manassas": "https://www.manassasva.gov/council/meeting_agendas.php",
    "City of Falls Church": "https://www.fallschurchva.gov/Agendas-Minutes",
    "City of Manassas Park": "https://www.manassasparkva.gov/government/agenda_center.php"
}

# === EMAIL CONFIG (optional) ===
SEND_EMAIL = False  # Change to True if you configure email below
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = ""   # your email (store safely in GitHub Secrets later)
EMAIL_PASS = ""   # your app password (store safely in GitHub Secrets later)
TO_EMAIL = ""     # where alerts should go

# === END CONFIG ===

def fetch_page_text(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def find_mentions(text):
    text_lower = text.lower()
    hits = []
    for pattern in KEYWORDS:
        for match in re.finditer(pattern, text_lower):
            snippet = text_lower[max(0, match.start()-50):match.end()+50]
            hits.append((pattern, snippet))
    return hits

def main():
    found_hits = []
    for name, url in JURISDICTIONS.items():
        text = fetch_page_text(url)
        if not text:
            continue
        hits = find_mentions(text)
        if hits:
            for pattern, snippet in hits:
                found_hits.append((name, url, pattern, snippet))

    if found_hits:
        report_lines = []
        for name, url, pattern, snippet in found_hits:
            report_lines.append(f"{name}: {url}\nMatch: {pattern}\nSnippet: ...{snippet}...\n")

        report = "\n\n".join(report_lines)
        print("Mentions found:\n", report)

        # Save to file
        Path("results").mkdir(exist_ok=True)
        filename = f"results/nvcc_hits_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, "w") as f:
            f.write(report)

        if SEND_EMAIL:
            msg = MIMEText(report)
            msg["Subject"] = "NVCC Mention Alert"
            msg["From"] = EMAIL_USER
            msg["To"] = TO_EMAIL
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
    else:
        print("No NVCC mentions found this week.")

if __name__ == "__main__":
    main()
