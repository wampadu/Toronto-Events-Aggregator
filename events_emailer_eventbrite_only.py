import os
import asyncio
import html
import random
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import smtplib

# ===================== Config =====================
HEADLESS = os.getenv("CI", "").lower() == "true" or os.getenv("HEADLESS", "1") == "1"
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "90000"))
RETRIES = int(os.getenv("NAV_RETRIES", "4"))
SLOW_MO = int(os.getenv("SLOW_MO_MS", "0"))

# A few realistic desktop UAs
UAS = [
    # Chrome 119–122 desktop Windows/macOS
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# ===================== Dates ======================
def get_upcoming_weekend_dates():
    """
    Keep your previous behavior (today+10, today+17) so your pipeline output matches.
    """
    today = datetime.today()
    return [today + timedelta(days=10), today + timedelta(days=17)]

# ===================== HTML =======================
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    html_output = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <title>{title}</title>
        <style>
            body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; }}
            h1 {{ margin-bottom: 16px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; }}
            img {{ max-width: 140px; border-radius: 6px; }}
            th {{ background: #f7f7f7; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table>
            <thead>
                <tr>
                    <th>Image</th>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Price</th>
                    <th>Description</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
    """
    for e in events:
        if not e.get('title') or not e.get('url'):
            continue
        html_output += f"""
            <tr>
                <td>{f'<img src="{html.escape(e["image"])}">' if e.get('image', '').startswith('http') else ''}</td>
                <td><a href="{html.escape(e['url'])}" target="_blank">{html.escape(e['title'])}</a></td>
                <td>{html.escape(e.get('date', ''))}</td>
                <td>{html.escape(e.get('price', ''))}</td>
                <td>{html.escape(e.get('description', ''))}</td>
                <td>{html.escape(e.get('source', ''))}</td>
            </tr>
        """
    html_output += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_output

# ===================== Helpers ====================
async def maybe_dismiss_cookie_banner(page):
    """
    Best-effort cookie/consent accept. Won't fail the run if not present.
    """
    selectors = [
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('I Accept')",
        "[data-testid*='accept']:not([disabled])",
        "button[mode='primary'] >> text=Accept",  # generic
    ]
    for sel in selectors:
        try:
            btn = await page.wait_for_selector(sel, timeout=2000, state="visible")
            if btn:
                await btn.click()
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue

async def safe_goto(page, url, retries=RETRIES, base_timeout=NAV_TIMEOUT_MS):
    """
    Robust navigation with retries/backoff and varied waitUntil strategies.
    """
    waits = ["domcontentloaded", "networkidle", "load"]
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=base_timeout, wait_until=waits[min(attempt - 1, len(waits) - 1)])
            await maybe_dismiss_cookie_banner(page)
            # Wait for either results or an empty-state to show the page settled
            await page.wait_for_selector("li [data-testid='search-event'], [data-testid*='empty'], [data-automation='empty_state']", timeout=base_timeout)
            return
        except PWTimeout as e:
            if attempt == retries:
                raise
            backoff = 1.5 ** attempt
            print(f"⏳ goto retry {attempt}/{retries} after timeout… sleeping {backoff:.1f}s")
            await asyncio.sleep(backoff)
        except Exception as e:
            if attempt == retries:
                raise
            backoff = 1.5 ** attempt
            print(f"⚠️ goto retry {attempt}/{retries} after error: {e}… sleeping {backoff:.1f}s")
            await asyncio.sleep(backoff)

# ===================== Scraper ====================
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite…")
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"

    # Navigate robustly
    await safe_goto(page, url)

    # Scroll-to-load loop
    print("🔄 Scrolling to load events on current page…")
    prev_height = 0
    retries = 0
    while retries < 6:
        await page.mouse.wheel(0, 6000)
        await asyncio.sleep(1.0)
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            retries += 1
        else:
            retries = 0
            prev_height = curr_height

    cards = await page.query_selector_all("li [data-testid='search-event']")
    print(f"🧾 Found {len(cards)} event cards on this page.")

    for card in cards:
        try:
            title_el = await card.query_selector("h3")
            title = (await title_el.inner_text()).strip() if title_el else "N/A"

            # Date/location text on search tiles (selectors can change; these work as of mid-2025)
            date_el = await card.query_selector("a + p[class*='Typography_']")
            location_el = await card.query_selector("p[class*='Typography_'].Typography_body-md__487rx, p[class*='body-md']")
            date_text = (await date_el.inner_text()).strip() if date_el else ""
            location_text = (await location_el.inner_text()).strip() if location_el else ""

            img_el = await card.query_selector("img.event-card-image, img[class*='card']")  # fallback
            img_url = await img_el.get_attribute("src") if img_el else ""

            link_el = await card.query_selector("a.event-card-link, a[href*='/e/']")
            link = await link_el.get_attribute("href") if link_el else ""

            price_el = await card.query_selector("div[class*='priceWrapper'] p, [data-testid='event-card-price']")
            price = (await price_el.inner_text()).strip() if price_el else "Free"

            events.append({
                "title": title,
                "date": date_text,
                "description": location_text,
                "image": img_url or "",
                "url": link or "",
                "price": price,
                "source": "Eventbrite"
            })
        except Exception as e:
            print("⚠️ Error extracting event:", e)

    # Some regions of Eventbrite use pagination; try Next if present
    while True:
        try:
            next_btn = await page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
            if not next_btn:
                print("🛑 No more pages.")
                break
            print("➡️ Going to next page…")
            await next_btn.click()
            await page.wait_for_timeout(1500)
            await page.wait_for_selector("li [data-testid='search-event']", timeout=NAV_TIMEOUT_MS)

            # Scroll load again
            prev_height = 0
            retries = 0
            while retries < 6:
                await page.mouse.wheel(0, 6000)
                await asyncio.sleep(1.0)
                curr_height = await page.evaluate("document.body.scrollHeight")
                if curr_height == prev_height:
                    retries += 1
                else:
                    retries = 0
                    prev_height = curr_height

            new_cards = await page.query_selector_all("li [data-testid='search-event']")
            print(f"🧾 Found {len(new_cards)} event cards on this page.")
            for card in new_cards:
                try:
                    title_el = await card.query_selector("h3")
                    title = (await title_el.inner_text()).strip() if title_el else "N/A"

                    date_el = await card.query_selector("a + p[class*='Typography_']")
                    location_el = await card.query_selector("p[class*='Typography_'].Typography_body-md__487rx, p[class*='body-md']")
                    date_text = (await date_el.inner_text()).strip() if date_el else ""
                    location_text = (await location_el.inner_text()).strip() if location_el else ""

                    img_el = await card.query_selector("img.event-card-image, img[class*='card']")
                    img_url = await img_el.get_attribute("src") if img_el else ""

                    link_el = await card.query_selector("a.event-card-link, a[href*='/e/']")
                    link = await link_el.get_attribute("href") if link_el else ""

                    price_el = await card.query_selector("div[class*='priceWrapper'] p, [data-testid='event-card-price']")
                    price = (await price_el.inner_text()).strip() if price_el else "Free"

                    events.append({
                        "title": title,
                        "date": date_text,
                        "description": location_text,
                        "image": img_url or "",
                        "url": link or "",
                        "price": price,
                        "source": "Eventbrite"
                    })
                except Exception as e:
                    print("⚠️ Error extracting event:", e)
        except Exception as e:
            print("⚠️ Pagination error:", e)
            break

    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

# ===================== Email ======================
def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")
    if not from_email or not app_password:
        print("⚠️ Missing GMAIL_USER/GMAIL_PASS — skipping email send.")
        return

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email or ""
    msg["Subject"] = subject

    msg.attach(MIMEText("Toronto Weekend Events (Eventbrite Only)", "plain"))

    with open(html_path, "rb") as f:
        part = MIMEApplication(f.read(), Name="eventbrite_events.html")
    part["Content-Disposition"] = 'attachment; filename="eventbrite_events.html"'
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg)
    print("📧 Email sent!")

# ===================== Main =======================
async def aggregate_events():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")

    launch_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--no-zygote",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            args=launch_args
        )

        context = await browser.new_context(
            locale="en-CA",
            timezone_id="America/Toronto",
            user_agent=random.choice(UAS),
            viewport={"width": 1366, "height": 768},
        )

        # Light stealth: hide webdriver flag
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        page = await context.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        page.set_default_timeout(NAV_TIMEOUT_MS)

        events = await scrape_eventbrite(page)
        await browser.close()

    # De-dupe by (title, url)
    dedup = {}
    for e in events:
        key = (e.get("title","").strip().lower(), (e.get("url","") or "").strip().lower())
        if key not in dedup:
            dedup[key] = e
    events = list(dedup.values())

    html_output = generate_html(events)
    out_path = "eventbrite_events.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"✅ File saved: {out_path}")

    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO", ""),
        subject=f"🎉 Eventbrite - Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path=out_path,
    )

if __name__ == "__main__":
    asyncio.run(aggregate_events())
