import os
import asyncio
import html
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import smtplib

# === Calculate Upcoming Friday–Sunday Dates ===
def get_upcoming_weekend_dates():
    today = datetime.today()
    return [today + timedelta(days=10), today + timedelta(days=17)]

# === HTML Output ===
def generate_html(events):
    dates = get_upcoming_weekend_dates()
    title = f"🎉 Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}"
    
    html_output = f"""
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        <table border="1" cellpadding="5" cellspacing="0">
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
                <td>{f'<img src="{html.escape(e["image"])}" width="120">' if e.get('image', '').startswith('http') else ''}</td>
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

# === Eventbrite Scraper ===
async def scrape_eventbrite(page):
    print("🔍 Scraping Eventbrite...")
    events = []
    dates = get_upcoming_weekend_dates()
    start_str = dates[0].strftime("%Y-%m-%d")
    end_str = dates[-1].strftime("%Y-%m-%d")
    url = f"https://www.eventbrite.ca/d/canada--toronto/events/?start_date={start_str}&end_date={end_str}"
    await page.goto(url)

    while True:
        print("🔄 Scrolling to load events on current page...")
        prev_height = 0
        retries = 0
        while retries < 5:
            await page.mouse.wheel(0, 5000)
            await asyncio.sleep(1.2)
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

                date_el = await card.query_selector("a + p.Typography_root__487rx")
                location_el = await card.query_selector(".Typography_root__487rx.Typography_body-md__487rx")
                date_text = (await date_el.inner_text()).strip() if date_el else "N/A"
                location_text = (await location_el.inner_text()).strip() if location_el else "N/A"

                img_el = await card.query_selector("img.event-card-image")
                img_url = await img_el.get_attribute("src") if img_el else ""

                link_el = await card.query_selector("a.event-card-link")
                link = await link_el.get_attribute("href") if link_el else ""

                price_el = await card.query_selector("div[class*='priceWrapper'] p")
                price = (await price_el.inner_text()).strip() if price_el else "Free"

                events.append({
                    "title": title,
                    "date": date_text,
                    "description": location_text,
                    "image": img_url,
                    "url": link,
                    "price": price,
                    "source": "Eventbrite"
                })
            except Exception as e:
                print("⚠️ Error extracting event:", e)

        try:
            next_btn = await page.query_selector('[data-testid="page-next"]:not([aria-disabled="true"])')
            if next_btn:
                print("➡️ Going to next page...")
                await next_btn.click()
                await asyncio.sleep(2)
            else:
                print("🛑 No more pages.")
                break
        except Exception as e:
            print("⚠️ Pagination error:", e)
            break
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events

# === Send Email ===
def send_email_with_attachment(to_email, subject, html_path):
    from_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_PASS")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText("Toronto Weekend Events (Eventbrite Only)", 'plain'))

    with open(html_path, "rb") as file:
        part = MIMEApplication(file.read(), Name="eventbrite_events.html")
        part['Content-Disposition'] = 'attachment; filename="eventbrite_events.html"'
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, app_password)
        server.send_message(msg)
    print("📧 Email sent!")

# === Main Runner ===
async def aggregate_events():
    dates = get_upcoming_weekend_dates()
    print(f"📆 Scraping for: {[d.strftime('%Y-%m-%d') for d in dates]}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        events = await scrape_eventbrite(page)
        await browser.close()

    html_output = generate_html(events)
    with open("eventbrite_events.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("✅ File saved: eventbrite_events.html")

    send_email_with_attachment(
        to_email=os.getenv("EMAIL_TO"),
        subject=f"🎉 Eventbrite - Toronto Weekend Events – {dates[0].strftime('%B %d')}-{dates[-1].strftime('%d, %Y')}",
        html_path="eventbrite_events.html"
    )

if __name__ == "__main__":
    asyncio.run(aggregate_events())
