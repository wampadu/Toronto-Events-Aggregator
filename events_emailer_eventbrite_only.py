# events_emailer_eventbrite_only.py

import os
import asyncio
import html
import random
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Block noisy trackers/analytics to speed up load (enabled only AFTER first paint)
BLOCK_URL_PARTS = [
    "googletagmanager", "google-analytics", "doubleclick",
    "hotjar", "segment", "optimizely", "braze", "mixpanel",
    "facebook", "snap", "tiktok", "bing.com/collect", "bat.bing",
    "scorecardresearch", "app.link"
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
            a {{ color: #0a58ca; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
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
    Covers OneTrust variants commonly seen on Eventbrite.
    """
    selectors = [
        "#onetrust-accept-btn-handler",
        "[data-testid='onetrust-accept-btn-handler']",
        "button:has-text('Accept all')",
        "button:has-text('Accept All')",
        "button:has-text('I Accept')",
        "button[aria-label='Accept All']",
        "button[mode='primary'] >> text=Accept",
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
    Robust navigation with retries/backoff, permissive 'attached' waits,
    WAF/interstitial detection, and warm-up hops.
    """
    waits = ["domcontentloaded", "networkidle", "load"]
    waf_signals = [
        "Just a moment", "Access denied", "Verify you are human",
        "unusual traffic", "are you a robot", "temporarily blocked"
    ]

    for attempt in range(1, retries + 1):
        try:
            await page.goto(
                url,
                timeout=base_timeout,
                wait_until=waits[min(attempt - 1, len(waits) - 1)]
            )

            # Quick cookie banner attempt
            await maybe_dismiss_cookie_banner(page)

            # Let scripts settle a touch
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

            # Detect WAF/interstitial
            try:
                title = (await page.title()) or ""
            except Exception:
                title = ""
            try:
                body_snip = (await page.text_content("body")) or ""
            except Exception:
                body_snip = ""

            if any(s.lower() in title.lower() for s in waf_signals) or \
               any(s.lower() in body_snip.lower() for s in waf_signals):
                raise PWTimeout("WAF/interstitial detected")

            # Do not require visible yet; overlays can hide the list
            try:
                await page.wait_for_selector(
                    "li [data-testid='search-event'], "
                    "[data-testid='search-event-card'], "
                    "ul[data-spec='search-results'], "
                    "[data-testid*='empty'], [data-automation='empty_state']",
                    timeout=12000,
                    state="attached"
                )
            except Exception:
                # small scroll to trigger lazy mount
                try:
                    await page.evaluate("window.scrollBy(0, 1200)")
                except Exception:
                    pass
                await page.wait_for_selector(
                    "li [data-testid='search-event'], "
                    "[data-testid='search-event-card'], "
                    "ul[data-spec='search-results'], "
                    "[data-testid*='empty'], [data-automation='empty_state']",
                    timeout=8000,
                    state="attached"
                )

            return  # success

        except Exception as e:
            if attempt == retries:
                # Dump artifacts for debugging
                try:
                    html_dump = await page.content()
                    with open("debug_eventbrite.html", "w", encoding="utf-8") as f:
                        f.write(html_dump)
                    await page.screenshot(path="debug_eventbrite.png", full_page=True)
                    print("🧪 Wrote debug_eventbrite.html and debug_eventbrite.png")
                except Exception:
                    pass
                raise

            backoff = min(2.0 * attempt, 6.0)
            print(f"⏳ goto retry {attempt}/{retries} after error: {e}… sleeping {backoff:.1f}s")

            # Warm-up hops to seed cookies/geo/session
            try:
                if attempt == 1:
                    await page.goto("https://www.eventbrite.ca", timeout=base_timeout, wait_until="domcontentloaded")
                    await maybe_dismiss_cookie_banner(page)
                    await page.wait_for_timeout(1000)
                elif attempt == 2:
                    await page.goto("https://www.eventbrite.ca/d/canada--toronto/free--events/",
                                    timeout=base_timeout, wait_until="domcontentloaded")
                    await page.wait_for_timeout(800)
            except Exception:
                pass

            await asyncio.sleep(backoff)

async def infinite_scroll(page, max_idle_rounds=6, wheel_px=6000, max_total_rounds=40):
    """
    Scrolls until the page stops growing or caps out to avoid hanging.
    Uses mouse.wheel where available; falls back to window.scrollBy in headless.
    """
    prev_height = 0
    idle_rounds = 0
    total_rounds = 0
    while idle_rounds < max_idle_rounds and total_rounds < max_total_rounds:
        try:
            await page.mouse.wheel(0, wheel_px)
        except Exception:
            try:
                await page.evaluate("window.scrollBy(0, 6000)")
            except Exception:
                pass
        await asyncio.sleep(1.0)
        try:
            curr_height = await page.evaluate("document.body.scrollHeight")
        except Exception:
            break
        if curr_height == prev_height:
            idle_rounds += 1
        else:
            idle_rounds = 0
            prev_height = curr_height
        total_rounds += 1

def normalize_link(href: str) -> str:
    if not href:
        return ""
    if href.startswith("/"):
        return "https://www.eventbrite.ca" + href
    return href

async def enable_blocking_after_first_paint(context):
    """
    Enable network blocking of heavy analytics/trackers AFTER the first successful paint,
    to avoid breaking scripts needed to mount the results list.
    """
    async def route_handler(route):
        url = route.request.url
        if any(part in url for part in BLOCK_URL_PARTS):
            return await route.abort()
        return await route.continue_()
    await context.route("**/*", route_handler)

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

    # Now that first paint succeeded, enable tracker blocking for the rest
    await enable_blocking_after_first_paint(page.context)

    # Early probe: ensure list nodes exist (even if overlayed)
    try:
        await page.wait_for_selector(
            "li [data-testid='search-event'], [data-testid='search-event-card'], ul[data-spec='search-results']",
            timeout=6000,
            state="attached"
        )
    except Exception:
        # Rare EB quirk: tweak param ordering or broaden once, then continue
        alt_url = url.replace("&end_date", "&sort=date&end_date")
        try:
            await safe_goto(page, alt_url)
        except Exception:
            pass

    # Load as many cards as possible
    print("🔄 Scrolling to load events on current page…")
    await infinite_scroll(page)

    # Try multiple card selector variants (EB A/B tests DOM)
    card_selector_candidates = [
        "li [data-testid='search-event']",
        "[data-testid='search-event-card']",
        "ul[data-spec='search-results'] li article",
        "article[data-testid*='card']",
    ]
    cards = []
    for sel in card_selector_candidates:
        try:
            found = await page.query_selector_all(sel)
            if found:
                cards = found
                print(f"🧾 Found {len(cards)} event cards with selector: {sel}")
                break
        except Exception:
            continue
    if not cards:
        print("⚠️ No event cards found — page structure may have changed or location filter is empty.")
        return events

    async def extract_from_cards(cards_list):
        local_events = []
        for card in cards_list:
            try:
                # Title variants
                title_el = await card.query_selector("h3, h2, [data-testid='title']")
                title = (await title_el.inner_text()).strip() if title_el else "N/A"

                # Date & location variants
                date_el = await card.query_selector("time, a + p[class*='Typography_'], [data-testid='date']")
                date_text = (await date_el.inner_text()).strip() if date_el else ""

                loc_el = await card.query_selector(
                    "[data-testid='location'], .event-card__location, "
                    "p[class*='Typography_'].Typography_body-md__487rx, p[class*='body-md']"
                )
                location_text = (await loc_el.inner_text()).strip() if loc_el else ""

                # Image variants
                img_el = await card.query_selector("img.event-card-image, img[class*='card'], img[loading]")
                img_url = await img_el.get_attribute("src") if img_el else ""

                # Link variants
                link_el = await card.query_selector("a.event-card-link, a[href*='/e/'], a[href*='/d/']")
                link_raw = await link_el.get_attribute("href") if link_el else ""
                link = normalize_link(link_raw)

                # Price variants
                price_el = await card.query_selector("[data-testid*='price'], div[class*='priceWrapper'] p, .eds-media-card__price")
                price = (await price_el.inner_text()).strip() if price_el else "Free"

                local_events.append({
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
        return local_events

    events.extend(await extract_from_cards(cards))

    # Pagination (if present)
    while True:
        try:
            next_btn = await page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
            if not next_btn:
                print("🛑 No more pages.")
                break
            print("➡️ Going to next page…")
            await next_btn.click()
            await page.wait_for_timeout(1500)
            await page.wait_for_selector(
                "li [data-testid='search-event'], [data-testid='search-event-card']",
                timeout=NAV_TIMEOUT_MS,
                state="attached"
            )
            await infinite_scroll(page)
            new_cards = []
            for sel in card_selector_candidates:
                found = await page.query_selector_all(sel)
                if found:
                    new_cards = found
                    print(f"🧾 Found {len(new_cards)} event cards on this page with selector: {sel}")
                    break
            events.extend(await extract_from_cards(new_cards))
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
        "--disable-blink-features=AutomationControlled",
    ]

    proxy_server = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    proxy_arg = {"server": proxy_server} if proxy_server else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            args=launch_args,
            proxy=proxy_arg  # optional; set HTTP_PROXY/HTTPS_PROXY in secrets if needed
        )

        context = await browser.new_context(
            locale="en-CA",
            timezone_id="America/Toronto",
            user_agent=random.choice(UAS),
            viewport={"width": 1366, "height": 768},
            geolocation={"latitude": 43.6532, "longitude": -79.3832},
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": "en-CA,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        # Light stealth
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', { get: () => ['en-CA','en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
        """)

        page = await context.new_page()
        page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        page.set_default_timeout(NAV_TIMEOUT_MS)

        events = await scrape_eventbrite(page)

        await context.close()
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
