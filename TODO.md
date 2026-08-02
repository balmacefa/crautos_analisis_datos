LLM Please INCLUDE dev.md on this conversation


1- We want to explore this new source of scrawwraler.
https://evmarket.cr/ [DONE]

2- add a new wraller for thsi new source. we need to investigate first the html structure, and investigate http request to identify a the best crawler strategy . [DONE]
2.1 - Ones this is completed, create a n llm document , this is not going to be used by humann, only for LLM to understand the code and the strategy and structure of the web ite and navegation strategy. [DONE]
2.2 The objective is to crawller the entire website, https://evmarket.cr/listings [DONE]
,
https://evmarket.cr/listings?page=2 [DONE]

2.3 Extract all possible metadata from each car, includeing images urls, and any other details please. [DONE]

3. [DONE] create a new cron job similar to the current one and run it once to populate the database with the new source. Make sure to include a way to differentiate the new source from the current one, and also include a way to update the new source in the future.
4. [DONE] combines the data so typesense query combines both source. standerize tand normalize the data.
5. [DONE] Store the data con sqlite tables and sync with typesense.
6. [DONE] write unit, functional and integration tests for this new crawler and cron job.
7. [DONE] Integrate tests into CI/CD pipeline (GitHub Actions).

### Usados Cori (usadoscori.com) [DONE]
- [x] Research & Strategy Doc.
- [x] Scraper Implementation.
- [x] Integration & Staggered Cron.
- [x] Unit Testing.

### Veinsa Usados (veinsausados.com) [DONE]
- [x] Research & Strategy Doc.
- [x] Scraper Implementation.
- [x] Integration & Staggered Cron.
- [x] Unit Testing.

### [DONE] https://www.purdyusados.com/
- [x] Research & Strategy Doc.
- [x] Scraper Implementation.
- [x] Integration with run_scraper.

## Open-Data Pivot: beyond cars, any Costa Rica product [IN PROGRESS]

Goal: grow this from a cars-only marketplace scraper into an open-data
initiative covering any product sold on Costa Rican websites, incrementally
— without breaking the existing car pipeline/API/frontend.

Approach taken (additive, not a rewrite):
- [x] New generic `product_urls` / `product_details` tables in
      `backend/data_scrapper/repository.py`, parallel to the car tables, with
      their own status tracking, soft-deletes, and a `products` Typesense
      collection sync (mirrors the car sync pattern).
- [x] First source: EPA en Línea (`cr.epaenlinea.com`, Ferretería EPA Costa
      Rica) — `epaenlinea_scrapper.py` + `epaenlinea_strategy.md`.
      **Selectors are UNVALIDATED** — outbound access to the site was
      blocked (403) from the sandbox this was built in, so this needs a
      recon pass with real browser access before it's trusted or scheduled
      (see the strategy doc's Recon Checklist).
- [x] Wired into `run_scraper.py` as the `epa` command and into
      `job_definitions.py` as a manual-trigger-only job (no cron schedule
      yet, same pattern as `validate`).
- [x] Unit tests: `tests/test_epaenlinea_scrapper.py`,
      `tests/test_product_repository.py`, plus `run_scraper epa` coverage in
      `tests/test_run_scraper.py`.

Not done yet (deliberately out of scope for this first increment):
- [ ] Validate `epaenlinea_scrapper.py` selectors against the live site and
      remove the "UNVALIDATED" warning.
- [ ] Promote `epa` from manual-only to a scheduled cron entry once validated.
- [ ] Expand beyond the 2-category pilot to the full EPA catalog.
- [ ] Generalize the API (`backend/api/`) to serve generic products, not just
      cars — new `/products` endpoints, Pydantic models, etc.
- [ ] Generalize/extend the frontend to browse non-car products.
- [ ] Add more Costa Rica sources beyond EPA (e.g. other retail/hardware/
      grocery/electronics sites) once the generic pipeline is proven.