```bash
docker compose -f docker-compose.dev.yml down
```

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

```bash
docker compose -f docker-compose.dev.yml exec scraper python -m data_scrapper.run_scraper urls
```

docker compose -f docker-compose.dev.yml  exec scraper python -m db_tools export --format sqlite

docker compose -f docker-compose.dev.yml  restart scraper

docker compose -f docker-compose.dev.yml  logs scraper

docker compose -f docker-compose.dev.yml  exec scraper python -m db_tools.auto_migrate
