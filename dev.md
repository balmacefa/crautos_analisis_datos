```bash
docker compose -f docker-compose.dev.yml down
```

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

```bash
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper urls
```
