# Scraping Strategy: evmarket.cr

This document outlines the technical strategy for crawling and extracting data from `https://evmarket.cr/`, optimized for automated processing.

## 1. Objective
Extract comprehensive automotive market data (EVs/Hybrids) from `evmarket.cr/listings` to populate the `crautos_analisis_datos` system and Typesense index.

## 2. Site Architecture
- **Type**: Server-Side Rendered (SSR). Data is visible in the raw HTML.
- **URL Structure**:
    - **Listing Index**: `https://evmarket.cr/listings`
    - **Pagination**: `https://evmarket.cr/listings?page=N` (e.g., `page=2`, `page=3`).
    - **Detail Page**: `https://evmarket.cr/listing/[item-slug]/` (also supports `listing-details.php?id=[numeric_id]`).

## 3. Crawling Logic

### A. Discovery Layer (Navigation)
1. **Entry Point**: Start at `https://evmarket.cr/listings`.
2. **Page Parsing**:
    - Items are contained in grid elements.
    - Each car has a link to its detail page.
3. **Pagination Strategy**:
    - Detect the total number of items or "Next" button.
    - Loop through `?page=N` until the last page is reached (approx. 11 pages currently).
    - Rate limiting: Use a 1-2 second delay between page requests to avoid WAF triggers.

### B. Extraction Layer (selectors)
Using standard CSS selectors (compatible with BeautifulSoup or Playwright):

| Data Point | Selector / Source | Logic |
| :--- | :--- | :--- |
| **Full Title** | `h2` inside `.listing-title` section | Extract text (e.g., "BYD Yuan Plus 2024"). |
| **Brand/Model/Year** | Parser Logic | Split Title by space. |
| **Price USD** | Text containing `$` | Identify numerical value in price tags. |
| **Price CRC** | Text inside `span` or `()` | Identify value with `₡` symbol. |
| **Technical Specs** | `ul.listing-details li` | Key-Value extraction from `li` labels (Kilometraje, Condición, Combustible, etc.). |
| **Location** | `h5:nth-child(2)` in sidebar | Text under "Ubicación" category. |
| **Images** | `div.gallery img` | Extract `src` attributes (all start with `/uploads/`). |

## 4. Implementation Strategy
- **Service**: Integrated into the existing `backend/data_scrapper`.
- **Driver**: Playwright (Headless) is recommended to handle persistent sessions and easier navigation, although simple `requests` + `BeautifulSoup` would suffice due to SSR.
- **Data Mapping**:
    - Map `Condición` (Nuevo/Usado) to standard Boolean/Enum.
    - Normalize `Kilometraje` (remove units).
    - Ensure `car_id` is stable (use the numeric ID from the URL or a hash of the slug).

## 5. Metadata JSON Structure (Target)
```json
{
  "source": "evmarket.cr",
  "car_id": "ev-375",
  "marca": "Volvo",
  "modelo": "EX30",
  "año": 2025,
  "precio_usd": 37950,
  "informacion_general": {
    "kilometraje": "31 Km",
    "provincia": "San José",
    "transmisión": "Automático"
  },
  "images": ["https://evmarket.cr/uploads/5808067402_375.jpg"]
}
```
