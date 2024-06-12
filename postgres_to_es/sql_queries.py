sql_changed_ids = """
    SELECT id
    FROM content.{}
    WHERE modified > '{}'
"""

sql_film_ids_on_genre = """
    SELECT fw.id
    FROM content.film_work AS fw
    LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
    WHERE gfw.genre_id IN ({});
"""

sql_film_ids_on_person = """
    SELECT fw.id
    FROM content.film_work AS fw
    LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
    WHERE pfw.person_id IN ({});
"""
sql_films = """
    SELECT 
        fw.id AS fw_id,
        fw.rating AS imdb_rating,
        ARRAY_AGG (DISTINCT g.name) AS genres,
        fw.title,
        fw.description,
        COALESCE ( json_agg( DISTINCT jsonb_build_object( 'id', p.id, 'name', p.full_name ) ) FILTER (WHERE p.id is not null and pfw.role = 'director'), '[]' ) as director,
        ARRAY_AGG (DISTINCT p.full_name) FILTER(WHERE pfw.role = 'actor') AS actors_names,
        ARRAY_AGG  (DISTINCT p.full_name) FILTER(WHERE pfw.role = 'writer') AS writers_names,
        COALESCE ( json_agg( DISTINCT jsonb_build_object( 'id', p.id, 'name', p.full_name ) ) FILTER (WHERE p.id is not null and pfw.role = 'writer'), '[]' ) as writers,     
        COALESCE ( json_agg( DISTINCT jsonb_build_object( 'id', p.id, 'name', p.full_name ) ) FILTER (WHERE p.id is not null and pfw.role = 'actor'), '[]' ) as actors,
        fw.creation_date,
        fw.type,
        fw.created,
        fw.modified
    FROM content.film_work AS fw
    LEFT JOIN content.person_film_work AS pfw ON pfw.film_work_id = fw.id
    LEFT JOIN content.person AS p ON p.id = pfw.person_id
    LEFT JOIN content.genre_film_work AS gfw ON gfw.film_work_id = fw.id
    LEFT JOIN content.genre AS g ON g.id = gfw.genre_id
    WHERE fw.id IN ({})
    GROUP BY fw.id
"""