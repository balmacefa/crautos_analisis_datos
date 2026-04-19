# Corimotors Usados (usadoscori.com) - Scraper Strategy

This document outlines the strategy for scraping `usadoscori.com`.

## 1. Site Structure & Navigation

- **Base URL**: `https://usadoscori.com/`
- **Catalog URL**: `https://usadoscori.com/catalog/filtro/`
- **Navigation Type**: Paged results (Standard Bitrix CMS).
- **Pagination**: Numbered list at the bottom or "Show More" button (if many items exist). Currently the inventory is small enough (6 items) that pagination may not be active.

## 2. CSS Selectors (Listings Page)

- **Listing Container**: `div.product-item`
- **Link to Detail**: `a.product-item-image-wrapper` (relative href)
- **Preview Title**: `div.product-item-title a`
- **Preview Price**: `.product-item-price-current`

## 3. CSS Selectors (Detail Page)

- **Main Container**: `.product-item-detail-container`
- **Title**: `h1.product-item-detail-title` (Format: "MARCA MODELO AÑO")
- **Price**: `.product-item-detail-price-current`
- **Property List**: `.product-item-detail-properties`
  - Each item is a `.product-item-detail-properties-item`
  - Name: `.product-item-detail-properties-item-name`
  - Value: `.product-item-detail-properties-item-value`
- **Identification Fields**:
  - **Marca**: Found in properties or extracted from title.
  - **Modelo**: Found in properties or extracted from title.
  - **Año**: Found in properties (label "Año") or extracted from title.
  - **Kilometraje**: Label "Recorrido" or "Kilometraje".
  - **Transmisión**: Label "Transmisión".
  - **Combustible**: Often labeled as "Motor" or "Combustible".
- **Images**:
  - Primary: `.product-item-detail-slider-image img`
  - Gallery: `.product-item-detail-slider-container img`

## 4. Normalization Strategy

- **Car ID Prefix**: `cori-`
- **Currency**: Normalize everything to USD if possible, or store original strings.
- **Kilometraje**: Convert "30,000 km" to integer `30000`.
- **Source Differentiation**: Mark data source as "usadoscori".

## 5. Implementation Notes

- Use Playwright for robustness, although SSR might allow for simple HTTP requests.
- Handle relative URLs by joining with the Base URL.
- Implement a similar retry and logging pattern as used in `evmarket_scrapper.py`.
