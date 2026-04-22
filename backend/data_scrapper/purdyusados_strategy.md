# Purdy Usados Scraper Strategy

## Target Site
- **Base URL:** `https://www.purdyusados.com/`
- **Listings Page:** `https://www.purdyusados.com/buscar`
- **Detail Page Pattern:** `https://www.purdyusados.com/auto/{unit_id}`

## Modernization Approach
- **Dynamic Loading:** The site uses a "VER MÁS" (Load More) button. 
- **Tooling:** Playwright (Python).
- **Strategy:** 
    1. Navigate to `/buscar`.
    2. Click "VER MÁS" until all (or target number) of listings are loaded.
    3. Extract all vehicle URLs and basic metadata from the cards.
    4. For each vehicle, visit the detail page to extract full metadata and images.
    5. Save to SQLite via `ScraperRepository`.
    6. Sync to Typesense.

## Metadata to Extract
- `marca` (Brand)
- `modelo` (Model)
- `año` (Year)
- `precio_usd` (Price in USD)
- `precio_crc` (Price in CRC)
- `kilometraje` (Mileage)
- `motor` (Engine CC)
- `tracción` (Traction 4x2/4x4)
- `transmisión` (Transmission)
- `combustible` (Fuel)
- `imagenes` (List of image URLs)
- `imagen_principal` (Main image URL)

## Technical Challenges
- **Infinite Scroll/Load More:** Need to handle the asynchronous loading of more cards.
- **Dynamic Selectors:** Selectors may change; need robust CSS/XPath selectors.
- **Rate Limiting:** Implement reasonable delays between page visits.

## Implementation Details
- **Class:** `PurdyUsadosScraper` in `purdyusados_scrapper.py`.
- **Repository Integration:** Uses `ScraperRepository.mark_url_done`.
- **ID Pattern:** `purdy-{unit_id}`.
