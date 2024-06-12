import os
import sqlite3
from contextlib import contextmanager
from dataclasses import astuple, dataclass, field, fields
from datetime import datetime
from uuid import uuid4

import psycopg2
from dotenv import load_dotenv

load_dotenv()
PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PARENT_DIR, 'db.sqlite')

# DB_PATH = os.environ.get('DB_PATH')
DSN = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT'),
    'options': '-c search_path=content',
}
# Добавил проверку для тестов
if DB_PATH is None:
    DB_PATH = 'sqlite_to_postgres/db.sqlite'
if DSN['dbname'] is None:
    DSN = {
        'dbname': 'movies_database',
        'user': 'postgres',
        'password': '123qwe',
        'host': 'postgres',
        'port': 5432,
        'options': '-c search_path=content',
    }


@dataclass
class Person:
    id: uuid4
    full_name: str
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())


@dataclass
class PersonFilmWork:
    id: uuid4
    film_work_id: uuid4
    person_id: uuid4
    role: str
    created: datetime = field(default=datetime.now())


@dataclass
class Genre:
    id: uuid4
    name: str
    description: str
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())


@dataclass
class Filmwork:
    id: uuid4
    title: str
    description: str
    type: str
    creation_date: datetime
    rating: float = field(default=1.0)
    created: datetime = field(default=datetime.now())
    modified: datetime = field(default=datetime.now())
    file_path: str = field(default=None)


@dataclass
class GenreFilmwork:
    id: uuid4
    film_work_id: uuid4
    genre_id: uuid4
    created: datetime.now()


def change_keys_in_data(sqlite_dict: dict):
    true_keys = {
        'created_at': 'created',
        'updated_at': 'modified',
    }
    result_dict = {}

    for key in sqlite_dict.items():
        if key[0] not in true_keys:
            result_dict[key[0]] = sqlite_dict.get(key[0])
        if key[0] == 'description' and sqlite_dict.get(key[0]) is None:
            result_dict[key[0]] = ''
    for sqlite_key in sqlite_dict.items():
        for true_key in true_keys.items():
            if true_key[0] in sqlite_dict:
                result_dict[true_keys[true_key[0]]] = sqlite_dict.get(sqlite_key[0])
    return result_dict


@contextmanager
def conn_context(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def insert_data_to_postgres(sqlite_data, table_name: str, dataclass_main: object):
    table_name = table_name.lower()
    with psycopg2.connect(**DSN) as pg_conn:
        cursor = pg_conn.cursor()
        for sqlite_row in sqlite_data:
            pg_data = dict(sqlite_row)
            changed_pg_data = change_keys_in_data(pg_data)
            dataclass_dict_data = dataclass_main(**dict(changed_pg_data))
            column_names = [field.name for field in fields(dataclass_dict_data)]
            col_count = ', '.join(["%s"] * len(column_names))
            bind_values = cursor.mogrify(
                '({})'.format(col_count), astuple(dataclass_dict_data),
            ).decode("utf-8")
            string_column_names = ", ".join(column_names)
            query = (
                'INSERT INTO content.{} ({}) VALUES {} \
                ON CONFLICT (id) DO NOTHING'.format(
                    table_name, string_column_names, bind_values,
                ),
            )
            cursor.execute(query[0])


def fetch_data_for_pg(table_name: str, dataclass_main: object):
    table_name = table_name.lower()
    with conn_context(DB_PATH) as conn:
        curs = conn.cursor()
        curs.execute('SELECT * FROM {};'.format(table_name))
        while True:
            full_data = curs.fetchmany(50)
            if full_data:
                insert_data_to_postgres(full_data, table_name, dataclass_main)
            else:
                break


if __name__ == '__main__':
    dict_of_parametres = {
        'person': Person,
        'genre': Genre,
        'film_work': Filmwork,
        'genre_film_work': GenreFilmwork,
        'person_film_work': PersonFilmWork,
    }

    for table, class_obj in dict_of_parametres.items():
        fetch_data_for_pg(table, class_obj)
