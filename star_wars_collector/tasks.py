from collections import OrderedDict
import dateutil.parser
import os
import petl as etl
import requests

from django.conf import settings

from .models import Collection


def extract_id(url):
    return int(next(s for s in reversed(url.split('/')) if s))


def fetch(collection):
    session = requests.Session()
    folder = settings.MEDIA_ROOT / str(collection.name)
    folder.mkdir(parents=True, exist_ok=True)

    def process_entity(name, processor):
        page, url = 0, f'{settings.SWAPI_URL}{name}/'

        while url:
            response = session.get(url)
            response.raise_for_status()
            json = response.json()

            table = processor(json['results'], page)
            filename = str(folder / f'{name}.csv')
            if page == 0:
                etl.tocsv(table, filename)
            else:
                etl.appendcsv(table, filename)
            url = json['next']
            page += 1

    def process_planets(planets, page):
        planets = [OrderedDict(homeworld_url=d['url'], homeworld_name=d['name']) for d in planets]
        planets = etl.fromdicts(planets)
        return planets

    def process_people(people, page):
        return (
            etl.fromdicts(people)

            # Resolve the `homeworld` field into the homeworld's name - step (1) using field homeworld_name
            .leftjoin(planets, lkey='homeworld', rkey='homeworld_url')

            # Add a `date` column (`%Y-%m-%d`) based on `edited` date
            .addfield('date', lambda row: dateutil.parser.isoparse(row['edited']).strftime('%Y-%m-%d'))
            # row['edited'][:10] may be a bit faster, but is it fully reliable?

            # Fields referencing different resources and date fields other than `date/birth_year` can be dropped
            .cutout('films', 'species', 'vehicles', 'starships', 'created', 'edited', 'url', 'homeworld')

            # Resolve the `homeworld` field into the homeworld's name - step (2) using field homeworld
            .rename('homeworld_name', 'homeworld')
        )

    try:
        process_entity('planets', process_planets)
        planets = etl.fromcsv(str(folder / 'planets.csv'))
        process_entity('people', process_people)
        collection.fetching_status = Collection.FetchingStatus.FINISHED
        collection.save(update_fields=['fetching_status', 'modified'])
        os.rename(str(folder / 'people.csv'), str(settings.MEDIA_ROOT / str(collection.name))+'.csv')
        os.remove(str(folder / 'planets.csv'))
        os.rmdir(str(folder))
    except Exception as e:
        collection.fetching_status = Collection.FetchingStatus.FAILED
        collection.save(update_fields = ['fetching_status', 'modified'])
