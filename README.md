# 🎉 Toronto Events Aggregator

This Python script scrapes and compiles a list of **Toronto weekend events** (Friday–Sunday) from five popular sites:

- [BlogTO](https://www.blogto.com/events/)
- [Eventbrite](https://www.eventbrite.ca/)
- [Meetup](https://www.meetup.com/)
- [Ticketmaster](https://www.ticketmaster.ca/)
- [Fever](https://feverup.com/toronto)

It generates an interactive, searchable HTML table and emails the file to you weekly.

---

## 🧠 What It Does

- Aggregates all upcoming **next-weekend** events
- Compiles data into a styled HTML file with:
  - Search + filter + CSV/Excel export
  - Responsive design
  - "🎲 Random Event Picker" button
- Sends the HTML as an **email attachment**

---

## 📦 Requirements

The script uses:

- `playwright`
- `beautifulsoup4`
- Python standard libraries: `asyncio`, `datetime`, `html`, `smtplib`, `email`

Install with:

```bash
pip install -r requirements.txt
playwright install --with-deps
