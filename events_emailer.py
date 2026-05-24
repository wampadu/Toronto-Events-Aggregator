async def scrape_blogto(page):
    print("🔍 Scraping BlogTO...")
    try:
        await page.goto("https://www.blogto.com/events/", timeout=30000)
    except Exception as e:
        print(f"❌ Failed to navigate to BlogTO: {e}")
        return []
    
    target_days = get_upcoming_weekend_dates()
    events, seen = [], set()

    # Try to wait for initial page load - be more flexible with selectors
    try:
        await page.wait_for_selector(".event-info-box", timeout=5000)
    except:
        print("⚠️ Initial event-info-box not found, will try to load events via date picker...")

    for day in target_days:
        try:
            selector = f'button[data-pika-year="{day.year}"][data-pika-month="{day.month - 1}"][data-pika-day="{day.day}"]'
            date_btn = await page.query_selector(selector)
            
            if not date_btn:
                print(f"⚠️ Date button not found for {day.strftime('%Y-%m-%d')}: {selector}")
                continue
            
            print(f"📅 Clicking date: {day.strftime('%Y-%m-%d')}")
            await date_btn.click()
            
            # Wait for events to load after clicking the date
            await page.wait_for_timeout(3000)
            
            # Try multiple selectors in case the structure changed
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            # Try different selectors
            cards = soup.select(".event-info-box")
            if not cards:
                print(f"⚠️ No .event-info-box found, trying alternative selectors...")
                cards = soup.select("[class*='event']")
            
            print(f"📦 Found {len(cards)} event cards for {day.strftime('%Y-%m-%d')}")
            
            for card in cards:
                try:
                    # Try main selector
                    title_el = card.select_one(".event-info-box-title-link")
                    if not title_el:
                        # Try alternative
                        title_el = card.select_one("a")
                    
                    if not title_el:
                        continue
                    
                    title = title_el.text.strip()
                    if not title or title in seen:
                        continue
                    
                    seen.add(title)

                    date_text = ""
                    date_el = card.select_one(".event-info-box-date")
                    if date_el:
                        date_text = date_el.text.strip()

                    desc = ""
                    desc_el = card.select_one(".event-info-box-description")
                    if desc_el:
                        desc = desc_el.text.strip()

                    image = ""
                    img_el = card.select_one(".event-info-box-image")
                    if img_el and img_el.has_attr("src"):
                        image = img_el["src"]

                    url = title_el.get('href', '#')

                    events.append({
                        "title": title,
                        "date": f"{day.strftime('%A %B %d')} {date_text}" if date_text else day.strftime('%A %B %d'),
                        "description": desc,
                        "image": image,
                        "url": url,
                        "price": "N/A",
                        "source": "BlogTO"
                    })

                except Exception as e:
                    print(f"⚠️ Error parsing card: {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Error on {day.strftime('%Y-%m-%d')}: {e}")
            continue
    
    print(f"✅ Finished scraping. Found {len(events)} events.")
    return events
