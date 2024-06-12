import json
import os
import time
from contextlib import closing
from datetime import datetime

import psycopg2
import requests
from dotenv import load_dotenv
from helper import backoff, logger
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor
from requests.exceptions import RequestException
from sql_queries import (
    sql_changed_ids,
    sql_film_ids_on_genre,
    sql_film_ids_on_person,
    sql_films,
)
from state_storage import JsonFileStorage, State

load_dotenv()
ES_SOCKET = os.getenv('ES_SOCKET')

class PostgresExtractor:
    def __init__(self, connection: connection):
        self.conn = connection

    def extract_film_ids(self, query: str, batch_size=50):
        try:
            with self.conn.cursor() as self.curs:
                self.curs.execute(query)
                while True:
                    records = self.curs.fetchmany(size=batch_size)
                    if not records:
                        break
                    films_id = set()
                    for record in records:
                        films_id.add(dict(record)["id"])
                    yield films_id
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")

    def extract_film_ids_based_in_filmwork(self, state_value: str):
        TABLE = "film_work"
        sql_query = sql_changed_ids.format(TABLE, state_value)

        try:
            with self.conn.cursor() as self.curs:
                self.curs.execute(sql_query)
                records = self.curs.fetchone()
                if not records:
                    return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")

        sql_query = sql_film_ids_on_genre.format(sql_query)
        return self.extract_film_ids(sql_query)

    def extract_film_ids_based_in_genres(self, state_value: str):
        TABLE = "genre"
        sql_subquery = sql_changed_ids.format(TABLE, state_value)

        try:
            with self.conn.cursor() as self.curs:
                self.curs.execute(sql_subquery)
                records = self.curs.fetchone()
                if not records:
                    return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")

        sql_query = sql_film_ids_on_genre.format(sql_subquery)
        return self.extract_film_ids(sql_query)

    def extract_film_ids_based_on_person(self, state_value: str):
        TABLE = "person"
        sql_subquery = sql_changed_ids.format(TABLE, state_value)

        try:
            with self.conn.cursor() as self.curs:
                self.curs.execute(sql_subquery)
                records = self.curs.fetchone()
                if not records:
                    return None
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")

        sql_query = sql_film_ids_on_person.format(sql_subquery)
        return self.extract_film_ids(sql_query)

    def check_changed_films(self, state_value):
        changed_filmwork_ids = set()

        films_based_on_movies = self.extract_film_ids_based_in_filmwork(state_value)
        if films_based_on_movies:
            for film_ids_set in films_based_on_movies:
                changed_filmwork_ids = changed_filmwork_ids.union(film_ids_set)

        films_based_on_genres = self.extract_film_ids_based_in_genres(state_value)

        if films_based_on_genres:
            for film_ids_set in films_based_on_genres:
                changed_filmwork_ids = changed_filmwork_ids.union(film_ids_set)

        films_based_on_persons = self.extract_film_ids_based_on_person(state_value)

        if films_based_on_persons:
            for film_ids_set in films_based_on_persons:
                changed_filmwork_ids = changed_filmwork_ids.union(film_ids_set)

        if len(changed_filmwork_ids) == 0:
            return None
        return changed_filmwork_ids

    def extract_data(self, changed_filmwork_ids: set[str], batch_size=50):
        sql_query_films = sql_films.format("'" + "','".join(changed_filmwork_ids) + "'")

        try:
            with self.conn.cursor() as self.curs:
                self.curs.execute(sql_query_films)
                while True:
                    records = self.curs.fetchmany(size=batch_size)
                    if not records:
                        break
                    yield records
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")


class Transformer:

    def transform_record(self, record):
        transform_record = {
            "id": str(record[0]),
            "imgb_rating": record[1],
            "genre": record[2],
            "title": record[3],
            "description": record[4],
        }
        dict_with_actors_and_writers = {}

        if len(record[5]) == 0:
            dict_with_actors_and_writers.update({"director": []})

        elif len(record[5]) == 1:
            dict_with_actors_and_writers.update({"director": record[5][0]['name']})


        if record[6] is None:
            dict_with_actors_and_writers.update({"actors_names": ''})
        else:
            dict_with_actors_and_writers.update({"actors_names": record[6]})

        if record[7] is None:
            dict_with_actors_and_writers.update({"writers_names": ''})
        else:
            dict_with_actors_and_writers.update({"writers_names": record[7]})


        if len(record[8]) == 0:
            dict_with_actors_and_writers.update({"actors": []})
        else:
            dict_with_actors_and_writers.update({"actors": record[9]})

        if len(record[9]) == 0:
            dict_with_actors_and_writers.update({"writers": []})
        else:
            dict_with_actors_and_writers.update({"writers": record[9]})

        transform_record.update(dict_with_actors_and_writers)

        return transform_record

    def transform_batch_records(self, batch_records):
        transformed_batch_records = ""

        for record in batch_records:
            transformed_record = self.transform_record(record)
            # record_id = transformed_record.get('id')

            row_before_record = {"index": {"_index": "movies", "_id": None}}
            row_before_record["index"]["_id"] = str(transformed_record.get('id'))
            row_before_record = json.dumps(row_before_record)
            print(row_before_record)
            transformed_record = json.dumps(self.transform_record(record))
            print(transformed_record)
            transformed_batch_records += (
                row_before_record + "\n" + transformed_record + "\n"
            )
            print(type(transformed_batch_records))

        return transformed_batch_records.encode("utf-8")


class ElasticsearchLoader:
    def check_schema_movies_exist(self):
        r = requests.get(f"{ES_SOCKET}/movies/_mapping")
        if r.status_code != 200:
            try:
                es_movies_schema_path = os.path.join(
                    os.path.dirname(__file__), "config/es_schema_movies.json"
                )
                es_movies_schema = json.load(open(es_movies_schema_path, "r"))
                requests.put(
                    f"{ES_SOCKET}/movies",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(es_movies_schema),
                )
                logger.info("Elasticsearch schema movies is created")
            except Exception as e:
                logger.error(f"{self.__class__.__name__}: {e}")

    def save_data(self, batch_records):
        try:
            r = requests.post(
                f"{ES_SOCKET}/_bulk",
                headers={"Content-Type": "application/json"},
                data=batch_records,
            )

            response = json.loads(r.text)
            if response["errors"] == True:
                for item in response["items"]:
                    if item["index"]["status"] != 200:
                        logger.error(
                            f"status: {item['index']['status']}, error_type: {item['index']['error']['type']}"
                        )
                raise RequestException("mapper_parsing_exeption")
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: {e}")


def run_etl_process(pg_conn: connection):
    extractor = PostgresExtractor(pg_conn)
    transformer = Transformer()
    loader = ElasticsearchLoader()

    state_value = state.get_state(key="last_update")

    if not state_value:
        state_value = datetime(1950, 1, 1).isoformat(sep=" ", timespec="microseconds")

    new_state_value = datetime.now().isoformat(sep=" ", timespec="microseconds")

    changed_filmwork_ids = extractor.check_changed_films(state_value)

    if not changed_filmwork_ids:
        logger.info("All data is up to date")
    else:
        all_records = extractor.extract_data(changed_filmwork_ids)
        loader.check_schema_movies_exist()

        for batch_records in all_records:
            transformed_batch_records = transformer.transform_batch_records(
                batch_records
            )
            print(batch_records)
            loader.save_data(transformed_batch_records)

    # state.set_state(key="last_update", value=new_state_value)

    logger.info(f'synchronize is completed on {state.get_state("last_update")}')


if __name__ == "__main__":
    pg_dsn = {'dbname': os.getenv('DB_NAME'),
              'user': os.getenv('DB_USER'),
              'password': os.getenv('DB_PASS'),
              'host': os.getenv('DB_HOST'),
              'port': os.getenv('DB_PORT'),
            }

    state_storage_file_path = os.path.join(
        os.path.dirname(__file__), "state_storage/state_storage.json"
    )
    state_storage = JsonFileStorage(state_storage_file_path)
    state = State(state_storage)

    @backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def make_connections_to_postgres_and_elasticsearch():
        r = requests.get(ES_SOCKET)
        if r.status_code == 200:
            logger.info("ElasticSearch is available")
        with closing(psycopg2.connect(**pg_dsn, cursor_factory=DictCursor)) as pg_conn:
            logger.info("Postgres is connected")
            run_etl_process(pg_conn)
    while True:
        try:
            make_connections_to_postgres_and_elasticsearch()
        except ConnectionError:
            logger.error("ETL process is interrupted")
