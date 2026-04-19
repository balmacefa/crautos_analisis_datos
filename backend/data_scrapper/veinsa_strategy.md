# Veinsa Usados (veinsausados.com) - Scraper Strategy

This document outlines the strategy for scraping `veinsausados.com`.

## 1. Site Structure & Navigation

- **Base URL**: `https://veinsausados.com/`
- **Catalog URL**: `https://veinsausados.com/buscador?search=true`
- **Navigation Type**: Paged results with a numeric pagination bar.
- **Rendering**: Client-Side Rendered (CSR). Navigation involves dynamic loading.
- **Pagination Controls**:
  - Pages: `button.pagination-number`
  - Next: `button.pagination-btn--next`
  - Active: `button.pagination-number.active`

## 2. CSS Selectors (Listings Page)

- **Listing Item (Card)**: The site uses a grid of containers. Each card contains an `h3` and several `p` tags.
- **Link to Detail**: The `h3` title is clickable, or just construct `/detalle/[slug]-[id]` if possible.
- **Title**: `h3` (e.g., "CITROEN C-ELYSEE")
- **Brand**: `p` (immediately after `h3`)
- **Year & Trans**: `p` (e.g., "2016 · AUTOMATICA")
- **Price**: `small` (e.g., "$ 7,900")

## 3. CSS Selectors (Detail Page)

- **Title Block**: `h1` contains the name; year is usually in parentheses next to it.
- **Technical Specs**:
  - Labels: `p` or `span` containing "Kilometraje", "Combustible", "Motor", "Transmisión".
  - Values: The following text sibling or child.
- **Images**:
  - Gallery thumbnails are available.
  - Main image: A large `img` in the hero section.

## 4. Extraction & Normalization Strategy

- **Car ID Prefix**: `veinsa-`
- **Car ID Extraction**: Extract the ID from the tail of the URL (e.g., `/detalle/citroen-c-elysee-12345` -> `veinsa-12345`).
- **Data Model**:
  - **Marca**: Extracted from card `p` or detail view.
  - **Modelo**: Extracted from title.
  - **Año**: Integer from the `2016 · AUTOMATICA` string or title.
  - **Precio**: Convert "$ 7,900" to USD string.
  - **Kilometraje**: Extract numbers from "54,000 km".
- **Source**: "veinsausados"

## 5. Technical Challenges (CSR)

- **Loading Spinners**: Must wait for the "Cargando..." overlay to disappear.
- **Pagination**: Clicking "Next" might not reload the page. Use `page.wait_for_selector` for new content or check the pagination active state.
- **Wait Times**: Use `wait_until="networkidle"` or `domcontentloaded` + explicit waits for the grid to appear.
