"""
Internship Tracker Scraper
--------------------------
Checks a list of company career pages for lines of text that mention
internship/EEE-related keywords, compares them against the previous run
(stored in state.json), and sends a Telegram message for anything new.

Designed to be run on a schedule by GitHub Actions (see
.github/workflows/scrape.yml), but works fine run locally too.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
SITES_FILE = BASE_DIR / "sites.json"
STATE_FILE = BASE_DIR / "state.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_matching_lines(html, keywords):
    """Pull out short visible-text lines/snippets that mention any keyword."""
    soup = BeautifulSoup(html, "html.parser")

    # Strip script/style/nav/footer noise
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    matches = set()
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in keywords):
            # Keep snippets short and de-duplicatable
            snippet = line[:200]
            matches.add(snippet)
    return matches


def fetch(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [!] Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials not set, skipping notification.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Telegram messages are capped at 4096 chars; trim just in case.
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message[:4000],
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, data=payload, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] Failed to send Telegram message: {e}", file=sys.stderr)


def main():
    config = load_json(SITES_FILE, {"keywords": [], "sites": []})
    keywords = [k.lower() for k in config.get("keywords", [])]
    sites = config.get("sites", [])

    state = load_json(STATE_FILE, {})
    new_state = dict(state)  # carry forward anything not re-checked

    all_new_findings = []

    for site in sites:
        name = site["name"]
        url = site["url"]
        print(f"Checking: {name} ({url})")

        html = fetch(url)
        if html is None:
            continue

        current_matches = extract_matching_lines(html, keywords)
        previous_matches = set(state.get(url, []))

        newly_found = current_matches - previous_matches

        # First-ever run for a site: just record baseline, don't spam
        # with every existing line as "new".
        if url not in state:
            print(f"  First run for this site — saving baseline "
                  f"({len(current_matches)} lines), no alert sent.")
        elif newly_found:
            print(f"  {len(newly_found)} new matching line(s) found.")
            all_new_findings.append((name, url, sorted(newly_found)))
        else:
            print("  No changes.")

        new_state[url] = sorted(current_matches)

    save_json(STATE_FILE, new_state)

    if all_new_findings:
        lines = ["\U0001F514 New internship-related updates found:\n"]
        for name, url, snippets in all_new_findings:
            lines.append(f"\n\U0001F4CC {name}\n{url}")
            for s in snippets[:8]:  # cap per-site to keep message readable
                lines.append(f"  • {s}")
        message = "\n".join(lines)
        send_telegram(message)
        print("\nNotification sent.")
    else:
        print("\nNo new updates this run.")


if __name__ == "__main__":
    main()
