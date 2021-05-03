# Star Wars Explorer

### Author: Marek


## How to run

	python3 -m venv .venv
	. .venv/bin/activate
	pip install -r requirements.txt
	echo SECRET_KEY=YOUR-SECRET-KEY > .env
	./manage.py migrate
	uvicorn star_wars_explorer.asgi:application
	curl http://127.0.0.1:8000/


## Design related decisions

- Folders:
	- `star_wars_explorer` – Django project
	- `star_wars_collector` – Django application
	- `data` – data files (DB and CSV collections with preprocessed Star Wars data)

- Data model: `star_wars_collector` app ships with a single DB entity – `Collection`.

- Fetching (collection) statuses:
	- `STARTED` – new data download started and not finished yet
	- `FINISHED` – data download successfully finished
	- `FAILED` – data download failed

- Fetching workflow:
	- After fresh installation we start with no data.
	- When the user initiates the `Fetch` action,
		then a new subfolder and a new `Collection` record (in status `STARTED`) are created.
		User is informed about the activity and the `Fetch` button disabled.
		On server an asynchronous fetch task starts and proceed as follows:
		- All `planet` data are fetched (to minimize number of requests as required by spec),
			preprocessed we need only `'id'` and `'name'` attributes of the `planet`
			(in code: `'homeworld'` and `'homeworld_name'`),
			and incrementally saved as `planet.csv` file in the present collection subfolder.
			I assumed that the number of `people` is greater than the number of pages of `planets`
			(and most `planets` are related to some creatures)
			and initial pulling of all planets is reasonable.
			Otherwise cherry-picking (and caching) of only `planets` referenced by `people`, would be a better approach.

		- All `people`'s data are fetched and preprocesed according to the rules given in spec
			as `people.csv` file in the present collection subfolder.

	- When the `Fetch` task successfully finishes then temporary files and folders are removed
		(only `people` list is stored using a file with collection name) and the DB is updated:
		If no errors occurred the present collection fetching status is changed to `FINISHED`, otherwise to `FAILED`.

- I used for development the present LTS Django version (3.2)
	and the `requirements.txt` file refers to it though earlier (3.x) versions probably also work.
	To run asynchronous task (fetch and ETL) on server ASGI is required and for that reason `uvicorn` is used.

- I used SQLite as a DB backend because it is [shipped with modern python][1] and the solution was expected to be simple.

- Templates layout: common `base.html` template is shared between `collection-list.html` and `collection-detail.html` templates.
	They replace `head`, `title` and `content` blocks to present needed content
	(please, distinguish them from HTML 'head' and 'title' tags).
	Bootstrap 4.6 (last stable version) is roughly used for detail layout format (as proposed in spec).

## Some configuration settings:

- `DJANGO_SIMPLE_TASK_WORKERS = 1` — defines how many parallel workers are allowed to run on server
	(when all workers are busy pending tasks are queued though it's volatile and local service)
- `SWAPI_URL = 'https://swapi.py4e.com/api/'` — defines SWAPI endpoint address prefix
- `PAUSE_BEFORE_START_NEW_FETCH = 60` — defines time (seconds) which is required to start new fetch
	even if the previous one is neither `FINISHED` nor `FAILED`

## Potential future improvements:

- Use standard web server, e.g. Apache (now omitted for simplicity)
- Replacement of `SQLite` DB (now used just for simplicity) by server-backed DB, e.g. MySQL (a.k.a. MariaDB) or PostgreSQL,
	which allows to separate DB and web server
- Replacement of `django-simple-task` with Celery (and RabbitMQ or Redis) or with Django Channels (and Redis).
	It should help to have permanent queues (and even distributed, what especially gives the opportunity to separate fetching workers and web server)
- Implement `PAUSE_BEFORE_START_NEW_FETCH` logic in controller - now it's the view-only logic
- Push notification (instead of pull) to all users, when fetching finished (e.g., using websockets) - if the customer confirm it's expected
- Better (e.g. more verbose + logger) error handling, e.g. in the following cases:
	- when fetching data
	- when new folders / files / DB records can not be stored (especially during fetching)
	- when petl processing (e.g. join, aggregation) failed
	- clean up temporary files
- Expose petl defaults in Django setting for further adjustment (e.g. in the production environment)
- Add regression tests
- Add config validation
- Pagination on the 'collection list' page (if the customer confirm my humble opinion that the pagination is required)
- If we can reconfigure SWAPI server (e.g. using the own one) it's reasonable to use big page sizes
	(we need to pull all the rows from the given entities so the pagination just generates overhead)
- Better documentation
- Better CSS






[1]: https://docs.python.org/2.7/whatsnew/2.5.html#the-sqlite3-package
