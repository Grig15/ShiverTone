# ShiverTone - Reverb Scraper
# v0.2 - Scrape sold listings from Reverb

import asyncio
import json
import re
import sys
import os
from datetime import datetime


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from playwright.async_api import async_playwright
from database.models import get_connection


async def scrape_reverb_sold(search_term: str, max_pages: int = 3):
    """
    Scrape sold listings from Reverb for a given search term.
    Stores results in the database.
    """
    print(f"\n🎸 ShiverTone Scraper — Searching Reverb for: '{search_term}'")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        for page_num in range(1, max_pages + 1):
            url = (
                f"https://reverb.com/marketplace"
                f"?query={search_term.replace(' ', '%20')}"
                f"&product_type=effects-and-pedals"
                f"&show_only_sold=true"
                f"&page={page_num}"
            )
            print(f"  📄 Scraping page {page_num}: {url}")

            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(3000)

                listings = await page.evaluate('''() => {
                    const items = [];
                    const cards = document.querySelectorAll('.rc-listing-card');

                    cards.forEach(card => {
                        const titleEl = card.querySelector('.rc-listing-card__title-element');
                        const priceEl = card.querySelector('.rc-listing-card__price');
                        const conditionEl = card.querySelector('.rc-listing-card__condition');
                        const imgEl = card.querySelector('.rc-listing-card__thumbnail img');
                        const linkEl = card.querySelector('.rc-listing-card__title-element');

                        if (titleEl) {
                            // Get only the first price found, ignore original/shipping text
                            let priceText = '';
                            if (priceEl) {
                                const priceSpan = priceEl.querySelector('span[class*="price"]') || priceEl;
                                priceText = priceSpan.innerText.split('\\n')[0].trim();
                            }

                            items.push({
                                title: titleEl.innerText.trim(),
                                price: priceText,
                                condition: conditionEl ? conditionEl.innerText.trim() : 'unknown',
                                thumbnail: imgEl ? imgEl.src : null,
                                url: linkEl ? 'https://reverb.com' + linkEl.getAttribute('href') : null
                            });
                        }
                    });
                    return items;
                }''')

                print(f"  ✅ Found {len(listings)} listings on page {page_num}")
                results.extend(listings)

                # Be polite — don't hammer the server
                await page.wait_for_timeout(2000)

            except Exception as e:
                print(f"  ❌ Error on page {page_num}: {e}")
                continue

        await browser.close()

    # Save to database
    if results:
        saved = save_listings(results, search_term)
        print(f"\n💾 Saved {saved} listings to database")
    else:
        print("\n⚠️  No listings found")

    return results


# Keywords that indicate clones, kits, modern builds
CLONE_KEYWORDS = [
    'clone', 'kit', 'pcb', 'build your own', 'handmade',
    'replica', 'boutique', 'mood machine',
    'pedal pcb', 'byoc', 'diy', 'vero', 'stripboard',
    'raygun', 'stronzo', 'sentimental animal', 'noody'
]

# Modern years to exclude
MODERN_YEARS = [str(year) for year in range(2000, 2030)]

def is_vintage_original(title: str) -> bool:
    """
    Returns True if listing looks like a vintage original.
    Returns False if it looks like a clone, kit, or modern build.
    """
    title_lower = title.lower()

    # Check clone keywords
    for keyword in CLONE_KEYWORDS:
        if keyword in title_lower:
            return False

    # Check for modern years in title
    for year in MODERN_YEARS:
        if year in title:
            return False

    return True
def parse_price(price_str: str) -> float:
    """Extract the final/sold price from messy price strings."""
    try:
        if not price_str:
            return 0.0

        # If contains 'now', take the price after 'now'
        if 'now' in price_str.lower():
            price_str = price_str.lower().split('now')[-1]

        # Take first line only
        price_str = price_str.split('\n')[0]

        # Extract all numbers with decimals
        numbers = re.findall(r'\d+\.?\d*', price_str.replace(',', ''))

        if numbers:
            price = float(numbers[0])
            # Sanity check
            if 0 < price < 100000:
                return price
        return 0.0
    except:
        return 0.0


def save_listings(listings: list, search_term: str) -> int:
    """Save scraped listings to database."""
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0

    for listing in listings:
        try:
            price_raw = listing.get('price', '0')
            price = parse_price(price_raw)

            if price <= 0:
                continue

            # Filter out clones and modern builds
            if not is_vintage_original(listing.get('title', '')):
                print(f"  🚫 Filtered: {listing.get('title')}")
                continue

            cursor.execute('''
                           INSERT INTO sold_listings
                           (title, sale_price, condition, platform, listing_url, thumbnail_url, sale_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               listing.get('title'),
                               price,
                               listing.get('condition', 'unknown'),
                               'reverb',
                               listing.get('url'),
                               listing.get('thumbnail'),
                               datetime.now().isoformat()
                           ))
            saved += 1

        except Exception as e:
            print(f"  ⚠️  Could not save listing: {e}")
            continue

    conn.commit()
    conn.close()
    return saved


async def main():
    """Test the scraper."""
    search_term = input("Search Reverb for: ")
    results = await scrape_reverb_sold(search_term, max_pages=3)

    print(f"\n📊 Results preview:")
    for r in results[:5]:
        print(f"  • {r.get('title')} — {r.get('price')}")


if __name__ == "__main__":
    asyncio.run(main())