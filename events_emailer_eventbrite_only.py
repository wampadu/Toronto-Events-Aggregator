import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from bs4 import BeautifulSoup  # (kept if you later parse detail pages)
from datetime import datetime, timedelta
import html
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import random
import time

# =========================
# Date helpers (2 target dates)
# =========================
def get_upcoming_weekend_dates():
    """
    Current behavior: return two dates used as [start, end].
    If you want Fri–Sun, change this to compute those 3 days and return [fri, sun].
    """
    today = datetime.today()
    return [today + timedelta(days=10), today + timedelta(days=17)]

# =========================
# HTML output
# =========================
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    html_output = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/buttons/2.4.1/css/buttons.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/responsive/2.5.0/css/responsive.dataTables.min.css">
        <link rel="stylesheet" href="https://cdn.datatables.net/searchbuilder/1.5.0/css/searchBuilder.dataTables.min.css">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border: 1px solid #ccc; vertical-align: top; }}
            img {{ max-width: 150px; height: auto; border-radius: 10px; }}
            .dtsb-title {{ display: none; }}
            button {{ background-color: black !important; color: white !important; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <table id="events">
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

        <!-- jQuery + DataTables JS -->
        <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.html5.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.print.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.1/js/buttons.colVis.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/pdfmake.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.68/vfs_fonts.js"></script>
        <script src="https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js"></script>
        <script src="https://cdn.datatables.net/searchbuilder/1.5.0/js/dataTables.searchBuilder.min.js"></script>

        <script>
        function addFancyRandomEventButtonBelowH1() {
                const dt = $('#events').DataTable();
                if (!dt) return console.warn("⚠️ DataTable not ready.");
                let shownIndices = [];
                try { dt.buttons('.random-event').remove(); } catch (e) {}
                dt.button().add(null, {
                        text: '🎲 Random Event Picker',
                        className: 'random-event btn btn-outline-primary',
                        action: function () {
                                const rowsArr = dt.rows({ search: 'applied' }).nodes().toArray();
                                if (!rowsArr.length) return alert("No visible events to pick from.");
                                if (shownIndices.length >= rowsArr.length) { shownIndices = []; }
                                let randIndex;
                                do { randIndex = Math.floor(Math.random() * rowsArr.length); } while (shownIndices.includes(randIndex));
                                shownIndices.push(randIndex);
                                const row = rowsArr[randIndex];
                                const linkEl = row.querySelector("td:nth-child(2) a");
                                const imgEl  = row.querySelector("td:nth-child(1) img");
                                const title = linkEl?.textContent.trim() || "No title";
                                const href  = linkEl?.href || "#";
                                const image = imgEl?.src || "";
                                document.getElementById('random-event-card')?.remove();
                                const card = document.createElement("div");
                                card.id = "random-event-card";
                                card.style = `
                                        border: 1px solid #ccc; border-left: 5px solid #007acc;
                                        padding: 16px; margin-top: 20px; max-width: 600px;
                                        border-radius: 8px; position: relative; background: #f9f9f9;
                                        font-family: sans-serif;
                                `;
                                card.innerHTML = `
                                        <button style="
                                                position: absolute; top: 8px; right: 10px; background: transparent;
                                                border: none; font-size: 20px; cursor: pointer; color: #999;"
                                                onclick="document.getElementById('random-event-card').remove()">×</button>
                                        <h3 style="margin: 0 0 10px">🎯 Your Random Pick:</h3>
                                        <a href="${href}" target="_blank" style="font-size: 16px; font-weight: bold; color: #007acc;">${title}</a>
                                        ${image ? `<div><img src="${image}" style="margin-top: 10px; max-width: 100%; border-radius: 6px;" /></div>` : ''}
                                `;
                                const h1 = document.querySelector("h1");
                                if (h1) h1.insertAdjacentElement("afterend", card);
                        }
                });
        }

        (function waitForTableAndUpgrade(retries = 10) {
          const tableEl = document.querySelector("#events");
          if (!tableEl || !tableEl.querySelector("thead")) {
            if (retries > 0) return setTimeout(() => waitForTableAndUpgrade(retries - 1), 500);
            else return console.warn("❌ Table not found.");
          }
          if ($.fn.DataTable.isDataTable("#events")) $('#events').DataTable().destroy();
          if (!tableEl.querySelector("tfoot")) {
            const tfoot = tableEl.querySelector("thead").cloneNode(true);
            tfoot.querySelectorAll("th").forEach(cell => cell.innerHTML = "");
            tableEl.appendChild(tfoot);
          }
          $('#events').DataTable({
            responsive: true,
            paging: false,
            ordering: true,
            info: false,
            dom: 'QBfrtip',
            buttons: ['csv', 'excel'],
            searchBuilder: { columns: true },
            columnDefs: [{ targets: -1, orderable: false }],
            initComplete: function () {
              this.api().columns().every(function () {
                const input = document.createElement("input");
                input.placeholder = "Filter...";
                input.style.width = "100%";
                $(input).appendTo($(this.footer()).empty())
                  .on("keyup change clear", function () {
                    this.search(this.value).draw();
                  }.bind(this));
              });
              addFancyRandomEventButtonBelowH1();
            }
          });
        })();
        </script>
    </body>
    </html>
    """
    return html_output

# =========================
# Email
# =========================
def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")  # Gmail App Password

    if isinstance(to_email, str):
        to_emails = [email.strip() for email in to_email.split(",")]
    else:
        to_emails = list(to_email)

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText("open your 'Toronto Weekend Events' HTML file and book an event 2 weeks from now for your social life.", 'plain'))

    with open(html_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="weekend_events_toronto.html")
        part['Content-Disposition'] = 'attachment; filename="weekend_events_toronto.html"'
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg, from_addr=from_email, to_addrs=to_emails)
    print("📧 Email sent!")

# =========================
# Playwright helpers
# =========================
STEALTH_INIT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
"""

BLOCK_URL_PARTS = [
    "googletagmanager", "google-analytics", "doubleclick",
    "hotjar", "segment", "optimizely", "braze", "mixpanel",
    "facebook", "snap", "tiktok", "bing.com/collect", "bat.bing",
    "scorecardresearch", "app.link"
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

async def safe_goto(page, url, max_retries=3, base_timeout=90000):
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=base_timeout)
            return
        except PWTimeoutError as e:
            last_err = e
            print(f"⏳ goto timeout (attempt {attempt}/{max_retries}). Backing off...")
            await asyncio.sleep(2 * attempt)
        except Exception as e:
            last_err = e
            print(f"⚠️ goto error (attempt {attempt}/{max_retries}): {e}")
            await asyncio.sleep(2 * attempt)
    raise last_err

async def accept_cookies_if_present(page):
    # Eventbrite often uses OneTrust
    selectors = [
        "#onetrust-accept-btn-handler",
        "button[aria-label='Accept All']",
        "button:has-text('Accept All')",
        "[data-testid='onetrust-accept-btn-handler']",
    ]
    for sel in selectors:
        try:
            btn = await page.query_selector(sel)
            if btn:
                await btn.click()
                await asyncio.sleep(0.5)
                print("🍪 Accepted cookies.")
                return
        except:
            pass

async def infinite_scroll(page, max_idle_rounds=5, wheel_px=4000, max_total_rounds=40):
    prev_height = 0
    idle_rounds = 0
    total_rounds = 0
    while idle_rounds < max_idle_rounds and total_rounds < max_total_rounds:
        try:
            await page.mouse.wheel(0, wheel_px)
        except:
            # mouse may not exist in headless; use window.scrollBy as fallback
            await page.evaluate("window.scrollBy(0, 4000)")
        await asyncio.sleep(1.2)
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            idle_rounds += 1
        else:
            idle_rounds = 0
            prev_height = curr_height
        total_rounds += 1

# =========================
# Scraper
# =========================
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")

    # CA Toronto main search with explicit start/end
    url = (
        "https://www.eventbrite.ca/d/canada--toronto/events/"
        f"?start_date={start_str}&end_date={end_str}"
    )

    await safe_goto(page, url)

    # Handle cookie/consent if shown
    await accept_cookies_if_present(page)

    # Let critical content load
    await asyncio.sleep(2.0)

    # Try to ensure location is Toronto. If a location control exists, consider clicking it.
    # (Kept minimal to avoid fragility; your earlier runs showed manual dropdown might be needed.)
    # Optional: TODO add robust location set if Eventbrite shows a location modal.

    # Progressive infinite scroll to load most cards
    print("🔄 Scrolling to load events...")
    await infinite_scroll(page)

    # Gather cards; try multiple selector fallbacks due to frequent A/B tests
    card_selectors = [
        "li [data-testid='search-event']",              # your original
        "[data-testid='search-event-card']",            # alt
        "ul[data-spec='search-results'] li article",    # generic
        "article[data-testid*='card']"                  # very generic fallback
    ]

    cards = []
    for sel in card_selectors:
        cards = await page.query_selector_all(sel)
        if cards:
            print(f"🧾 Found {len(cards)} event cards with selector: {sel}")
            break
    if not cards:
        print("⚠️ No cards found. The page structure may have changed.")
        return events

    # Extract data
    for card in cards:
        try:
            # Title variants
            title_el = await card.query_selector("h3, h2, [data-testid='title']")
            title = (await title_el.inner_text()).strip() if title_el else "N/A"

            # Date & location variants (EB uses Typography classes that change frequently)
            date_el = await card.query_selector("time, a + p, [data-testid='date']")
            date_text = (await date_el.inner_text()).strip() if date_el else ""

            loc_el = await card.query_selector("[data-testid='location'], .event-card__location, .Typography_body-md__487rx")
            location_text = (await loc_el.inner_text()).strip() if loc_el else ""

            # Image variants
            img_el = await card.query_selector("img.event-card-image, img[loading], img")
            img_url = await img_el.get_attribute("src") if img_el else ""

            # Link variants
            link_el = await card.query_selector("a.event-card-link, a[href*='/e/'], a[href*='/d/']")
            link = await link_el.get_attribute("href") if link_el else ""
            if link and link.startswith("/"):
                link = "https://www.eventbrite.ca" + link

            # Price variants
            price_el = await card.query_selector("[data-testid*='price'], [class*='price'], .eds-media-card__price")
            price = (await price_el.inner_text()).strip() if price_el else "Free"

            events.append({
                "title": title or "N/A",
                "date": date_text,
                "description": location_text,
                "image": img_url or "",
                "url": link or "",
                "price": price or "",
                "source": "Eventbrite"
            })
        except Exception as e:
            print("⚠️ Error extracting an event card:", e)

    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

# =========================
# Main
# =========================
async def aggregate_events():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    all_events = []

    proxy_server = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or None
    # e.g., set in GH Actions secrets if you have one:
    # HTTP_PROXY=http://user:pass@host:port

    async with async_playwright() as p:
        chrome = p.chromium

        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        browser = await chrome.launch(
            headless=True,                 # headless in CI
            args=launch_args,
        )

        context_args = {
            "user_agent": UA,
            "viewport": {"width": 1366, "height": 768},
            "locale": "en-CA",
            "timezone_id": "America/Toronto",
            "geolocation": {"latitude": 43.6532, "longitude": -79.3832},  # Toronto
            "permissions": ["geolocation"],
        }
        if proxy_server:
            # Playwright python proxy must be passed on launch, not context.
            # Here we only read env to hint setup; for true proxy support,
            # pass {"server": proxy_server} to launch(proxy=...) above in Playwright >=1.40.
            pass

        context = await browser.new_context(**context_args)
        await context.add_init_script(STEALTH_INIT)

        # Block analytics/ads noise to speed up load (don’t block images/css/html/js)
        async def route_handler(route):
            url = route.request.url
            if any(part in url for part in BLOCK_URL_PARTS):
                return await route.abort()
            return await route.continue_()
        await context.route("**/*", route_handler)

        page = await context.new_page()
        page.set_default_timeout(90000)

        events = await scrape_eventbrite(page)
        all_events.extend(events)

        await context.close()
        await browser.close()

    # De-duplicate by normalized title
    seen = set()
    deduped = []
    for ev in all_events:
        key = (ev.get("title","").strip().lower())
        if key and key not in seen:
            seen.add(key)
            deduped.append(ev)

    html_output = generate_html(deduped)
    out_path = "weekend_events_toronto.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"✅ File saved: {out_path}")

    # Email
    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO"),
        subject=f"🎉 Eventbrite Only - Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path=out_path
    )

if __name__ == "__main__":
    asyncio.run(aggregate_events())
