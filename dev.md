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



----

https://coolify.io/docs/knowledge-base/environment-variables

Magic Environment Variables
For Docker Compose / Service Stack deployments, Coolify can auto-generate dynamic values using the SERVICE_<TYPE>_<IDENTIFIER> syntax. These let you generate URLs, FQDNs, passwords, and random strings that stay consistent across all services in a stack.

Type	What it generates	Example output
SERVICE_URL_<ID>	A URL based on your wildcard domain	http://app-vgsco4o.example.com
SERVICE_URL_<ID>_3000	URL with proxy routing to a specific port	http://app-vgsco4o.example.com:3000
SERVICE_URL_<ID>=/api	URL with a path appended	http://app-vgsco4o.example.com/api
SERVICE_URL_<ID>_3000=/api	URL with both port routing and path	http://app-vgsco4o.example.com:3000/api
SERVICE_FQDN_<ID>	The FQDN portion of the generated URL	app-vgsco4o.example.com
SERVICE_FQDN_<ID>_3000	FQDN with proxy routing to a specific port	app-vgsco4o.example.com:3000
SERVICE_FQDN_<ID>=/api	FQDN with a path appended	app-vgsco4o.example.com/api
SERVICE_USER_<ID>	A random username string	a8Kd3fR2mNpQ1xYz
SERVICE_PASSWORD_<ID>	A random password (PASSWORD_64 for 64 characters)	G7hkL9mpQ2rT4vXw
SERVICE_BASE64_<ID>	A random base64 string (BASE64_64, BASE64_128 for longer)	x9Yf2KqLm4NpR7TdWb8ZcA1eG3hJ5kM