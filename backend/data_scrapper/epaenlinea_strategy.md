# EPA en Línea (cr.epaenlinea.com) — Scraper Strategy

**Status: UNVALIDATED — best-effort draft.** This is the first source of the
open-data pivot beyond cars ("Ferretería EPA Costa Rica" — construction, home
improvement and decoration products). Unlike the existing car scrapers, this
document was **not** produced by driving a real browser against the site: the
sandbox this was authored in has its outbound network access blocked for
`cr.epaenlinea.com` (both the session's egress proxy and the hosted WebFetch
tool received `403`, which looks like anti-bot protection rather than a
temporary outage). Everything below is inferred from search-engine snippets
and generic patterns common to hardware-store e-commerce sites in the region.
**Do not enable `epa` in the production cron schedule until someone with real
network access has run the "Recon Checklist" below and corrected the
selectors.**

## 1. Site Structure & Navigation (known facts)

- **Base URL**: `https://cr.epaenlinea.com/`
- Confirmed real pages (from search engine indexing, not fetched directly):
  - `https://cr.epaenlinea.com/catalogo.html` — "Descubra los productos del mes"
  - `https://cr.epaenlinea.com/productos.html` — general product listing
  - `https://cr.epaenlinea.com/amarre.html` — category: lingas de amarre y cuerdas
  - `https://cr.epaenlinea.com/rodines.html` — category: rodines para muebles/sillas/carga
  - `https://cr.epaenlinea.com/tiendas/epa.html` — physical store listing
  - `https://cr.epaenlinea.com/preguntas-frecuentes` — FAQ
  - `https://empresas.cr.epaenlinea.com/` — a separate B2B subdomain (out of
    scope for the pilot)
- **URL pattern**: category pages appear to be `/<slug>.html` at the domain
  root (no `/categoria/` prefix seen). Product detail URLs were not observed
  directly; assume a similarly flat `/<product-slug>.html` or `/<slug>-p-<id>.html`
  pattern until confirmed.
- Prices are listed in Costa Rican colones (₡), unlike the car sources which
  are mostly USD.

## 2. Pilot Scope

Per project decision, the first pass is a **pilot**: only 2 known categories,
few pages each — enough to validate the end-to-end pipeline (URL discovery →
detail scrape → SQLite → Typesense), not a full catalog crawl.

```python
PILOT_CATEGORY_PATHS = ["/rodines.html", "/amarre.html"]
```

## 3. CSS Selectors — best-effort guesses (NEEDS VALIDATION)

No real HTML was inspected. The scraper implementation therefore tries a
cascade of common patterns instead of a single hard-coded selector, mirroring
the defensive style already used in `purdyusados_scrapper.py` /
`veinsa_scrapper.py` for sites that turned out to need fallbacks. Candidates
tried, in order:

- **Product card / link (listing page)**: any `a[href$=".html"]` inside a
  product-grid-looking container (`.product`, `.product-item`,
  `.vtex-product-summary`, `.item`, `[data-product]`), excluding known
  non-product links (`/tiendas/`, `/preguntas-frecuentes`, `catalogo.html`,
  `productos.html`).
- **Pagination**: numbered pagination (`a.page-link`, `.pagination a`) or a
  `?page=N` / `?p=N` query-string fallback.
- **Product name (detail page)**: first `h1`.
- **Price (detail page)**: first element containing `₡` (colón sign) near the
  top of the page — tried on common containers (`.price`, `.product-price`,
  `[itemprop="price"]`) before falling back to a full-page text regex
  `₡\s*[\d.,]+`.
- **SKU**: text near "SKU" / "Código" labels, or the URL slug as a fallback.
- **Category / breadcrumb**: `.breadcrumb a`, `nav[aria-label="breadcrumb"] a`.
- **Description**: `.product-description`, `#description`, or the first `p`
  after the `h1`.
- **Images**: `img` tags inside a gallery-looking container
  (`.product-images`, `.gallery`, `.swiper-slide img`), same approach as
  `veinsa_scrapper.py`.

## 4. Extraction & Normalization Strategy

- **Product ID Prefix**: `epa-`
- **Product ID Extraction**: last path segment of the URL, slugified.
- **Structured Data Model** (generic — see `product_details` table, not the
  car-specific `car_details` schema):

```json
{
  "nombre": "string",
  "categoria": "string",
  "subcategoria": "string|null",
  "marca": "string|null",
  "sku": "string|null",
  "precio_crc": "float",
  "precio_usd": "float|null",
  "disponibilidad": "string|null",
  "descripcion": "string|null",
  "especificaciones": {"key": "value"},
  "images": ["string"],
  "imagen_principal": "string"
}
```

- **Source**: `"EpaEnLinea"`

## 5. Recon Checklist (for whoever runs this with real access)

1. Load `https://cr.epaenlinea.com/rodines.html` in a real browser (or a
   Playwright session that isn't blocked) and confirm whether it's SSR or a
   JS-rendered SPA.
2. Capture the actual CSS selectors for: product card link, price, pagination
   controls, and detail-page fields listed above.
3. Confirm the real product detail URL pattern (flat `.html` vs `/p/` vs
   query-string IDs).
4. Check `robots.txt` (`https://cr.epaenlinea.com/robots.txt`) for any
   disallowed paths before scaling past the pilot.
5. Update `epaenlinea_scrapper.py` selectors and this document, then remove
   the "UNVALIDATED" warning.
6. Only then move `epa` from manual-trigger-only (see `job_definitions.py`)
   into a scheduled cron entry.

## 6. Technical Challenges (anticipated)

- **Anti-bot protection**: the site returned `403` to at least one automated
  fetch attempt during research. The scraper should use a real browser
  (Playwright, already the pattern for this project) with a realistic
  `user_agent`, and a polite delay between requests — but may still need
  additional measures (cookies/session warm-up) once tested for real.
- **Currency**: prices are in ₡ (CRC), not $ — the price parser must not
  assume a `$` sign like the car scrapers do.
