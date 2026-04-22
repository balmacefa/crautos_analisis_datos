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