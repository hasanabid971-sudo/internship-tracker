# Internship Tracker

Checks a list of company career pages every day for lines mentioning
internship/EEE-related keywords, and sends you a Telegram message when
something new shows up. Runs for free on GitHub Actions.

## How it works

- `sites.json` — the list of career pages to check + keywords to match
- `scraper.py` — fetches each page, extracts lines matching the keywords,
  compares against the last run (`state.json`), and messages you anything new
- `.github/workflows/scrape.yml` — runs `scraper.py` automatically once a day

## Setup (about 15–20 minutes)

### 1. Create a GitHub repo
- Go to github.com → New repository → name it e.g. `internship-tracker`
  (Public is fine and keeps you well within the free Actions minutes; Private
  also works, just uses your monthly quota.)
- Upload all the files in this folder to the repo (drag-and-drop on GitHub's
  web UI works, or use `git push` if you're comfortable with git).

### 2. Create a Telegram bot (this is how you'll get notified)
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, give it a name and username (anything, e.g.
   `foysal_internship_bot`).
3. BotFather will give you a **bot token** — looks like
   `123456789:AAExampleTokenHere`. Save it.
4. Send your new bot any message (e.g. "hi") so it can message you back.
5. In your browser, visit:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   (replace `<YOUR_TOKEN>` with your actual token). Look for `"chat":{"id":`
   in the response — that number is your **chat ID**. Save it.

### 3. Add secrets to your GitHub repo
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
- Add `TELEGRAM_BOT_TOKEN` = the token from step 2
- Add `TELEGRAM_CHAT_ID` = the chat ID from step 2

### 4. Run it once manually to set the baseline
- Go to the **Actions** tab in your repo → select "Internship Tracker" →
  **Run workflow** (button on the right).
- First run just records what's currently on each page — it won't send an
  alert (nothing "new" yet, since there's nothing to compare against).
- After that, it runs automatically every day at 03:00 UTC (~9 AM Dhaka
  time), and you'll get a Telegram message only when something new appears.

## Customizing

- **Add/remove companies**: edit `sites.json`, add a `{"name": "...", "url": "..."}`
  entry. Double check the URL still loads the actual careers content (some
  sites load listings via JavaScript and won't scrape well with this simple
  approach — LinkedIn is a known example that won't work here).
- **Change keywords**: edit the `keywords` list in `sites.json`.
- **Change schedule**: edit the `cron` line in
  `.github/workflows/scrape.yml` (uses standard cron syntax, in UTC).

## Known limitations

- Pages that load content via JavaScript (heavy React/Vue sites) may not
  scrape correctly with this simple requests+BeautifulSoup approach — if a
  company page consistently shows no results, it's likely this.
- LinkedIn specifically blocks this kind of scraping — keep using LinkedIn's
  own job alerts for that one.
- This detects *changes in page text*, not a structured "new job posted"
  event — so a page that gets reworded without new postings could
  occasionally trigger a false alert. Not a big deal, just means you'll
  sometimes get a notification worth a 10-second glance and a shrug.
