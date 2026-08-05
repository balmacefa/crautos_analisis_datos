# Staff Engineers Reference - Cambios Recientes

Este documento resume los cambios implementados recientemente en el proyecto. Su objetivo es proporcionar una referencia rápida del contexto técnico, problemas solucionados, decisiones arquitectónicas y nuevas implementaciones.

## Infraestructura y Arquitectura

1.  **Refactorización del Scheduler Cron**:
    *   Se eliminó *Ofelia* de los archivos de `docker-compose`.
    *   Se eliminó el `Dockerfile` separado para el proceso de Cron.
    *   El proceso de agendamiento de tareas ("DevOps Job Orchestrator") se fusionó directamente en el contenedor del *scraper*, ejecutándose como un proceso mediante Gunicorn. Esto reduce la complejidad y elimina la necesidad de montar sockets de Docker para disparar contenedores secundarios.
    *   Se agregó documentación específica sobre el orquestador y la definición de trabajos (`cron/devops_job_orchestrator.py`, `job_definitions.py`).

2.  **Robusteza en el Arranque (Startup Scripts)**:
    *   Se añadió creación de directorios y chequeos de integridad PRAGMA de SQLite3 en el `backend/entrypoint.sh` para la creación inicial o reconstrucción correcta de la base de datos de manera atómica.
    *   Para evitar fallos por "Race conditions", se implementó una lógica de *retry* con "exponential backoff" para la creación de la colección y sincronización de datos con **Typesense** (`sync_typesense.py`), asegurando que la sincronización aguarde a que el servidor de búsqueda esté plenamente disponible.
    *   Se solucionaron errores de arranque al añadir dependencias faltantes (`gunicorn`, `flask_session`, `croniter`) a `backend/requirements.txt`.

## Back-End / Scrapers / Base de Datos

1.  **Fiabilidad en Base de Datos de Scraper**:
    *   Implementación de `is_url_done` en `ScraperRepository` para asegurar idoneidad de continuaciones en *EvMarket*. Esto impide que un *scraper* vuelva a procesar la misma URL e incrementa la velocidad y tolerancia a fallos por interrupciones.
    *   El método `mark_url_done` fue modificado para realizar un `UPSERT` en lugar de una simple inserción. Así, URLs descubiertas por los *crawlers* más recientes son insertadas en `car_urls` transparentemente, sin romper *foreign key constraints* y sin necesidad de sembrarlas (*pre-seed*) por anticipado en la base de datos.
    *   Se modificó el scraper de lista de paginación (`scraper_pagination_list.py`) para ignorar "checkpoints" anteriores y siempre iniciar su ejecución desde la página 1.

2.  **Nuevos Endpoints e Insights Analíticos**:
    *   Se añadieron múltiples endpoints bajo `/api/insights/` para potenciar el tablero analítico con estadísticas ricas sobre depreciación, distribución de combustible, distribución de transmisión, oportunidades (Bargains), radios top Precio/Kilometraje y comparación por marcas.
    *   El endpoint `/api/insights/summary` recibió un nuevo campo `last_updated`, derivado directamente usando `MAX(scraped_at)` sobre la tabla de autos, lo que indica visualmente cuándo fue la última vez que la DB cambió efectivamente.

## Front-End (Wrapped-Frontend / Dash)

1.  **Refactorización y UX Móvil**:
    *   La lógica de filtrado de búsquedas de `search/page.jsx` fue abstraída a un componente reusable llamado `SearchSidebar.jsx`.
    *   Se incorporó un menú de "Drawer" o "Hamburguesa" animado (`<AnimatePresence>`) para los filtros y barra de búsqueda en pantallas de dispositivos móviles, logrando eliminar de raíz el excesivo abarrotamiento (*clutter*) visual en dichas pantallas.

2.  **Lógica de Imágenes y Fallback UI**:
    *   Múltiples vistas y tarjetas (e.g., `CarCardV2`) fueron actualizadas para consumir la `imagen_principal` dinámica proveniente de los datos.
    *   Se agregó una política de **Fallback** en cascada: De fallar o faltar la imagen principal, las tarjetas o detalles ahora renderizan `imagenes_secundarias[0]`, y tras agotar las opciones renderizan un *placeholder* genérico (e.g. `/images/car-placeholder.png` o el icono `<Car>` genérico en Dash), usando el evento `onError` del tag `<img>`.
    *   Se crearon test unitarios (TDD) para solidificar la lógica de *fallback*.

3.  **Visualizaciones del Dashboard Analítico**:
    *   El frontend basado en Dash se actualizó para visualizar 4 nuevas tarjetas con "extremos de mercado" (Market extremes) y gráficos de barras apiladas o tartas con las distribuciones por transmisión y tipo de combustible.
    *   Nuevos componentes para mostrar el "Top 10" y una comparación rápida entre marcas. Se unificó el comportamiento en un estado vacío con la ayuda de un helper global `empty_fig()`.
    *   La moneda principal por defecto del panel se estableció en Colones Costarricenses (CRC).
    *   Se implementó un "Banner" superior para mostrar explícitamente y con precisión temporal la última actualización de la base de datos (`last_updated`).
    *   Se implementó un "Collapsible section" que permite ver e interactuar con los datos crudos originales (JSON raw_data) desde el panel de detalles del auto.

## Áreas de Atención
*   Validar la salud en producción de las nuevas implementaciones de `UPSERT` en URLs para el scraper, evitando posibles bloqueos sobre SQLite3.
*   Monitorizar si la lógica de reinicio "Fresh start" impuesta al *scraper* de la lista genera retrasos en el ciclo de finalización o uso innecesario de recursos.
*   En futuras iteraciones, revisar la mantenibilidad de la lógica en el Front-End (particularmente el Drawer para filtros móviles) y refactorizar en base a feedback de usuarios si fuese necesario.
