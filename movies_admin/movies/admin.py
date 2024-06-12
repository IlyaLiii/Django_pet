from django.contrib import admin
from .models import Genre, Filmwork, GenreFilmwork, Person, PersonFilmwork


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):

    search_fields = ('name',)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):

    inlines = (GenreFilmworkInline,)
    list_display = ('title', 'type', 'creation_date', 'rating')
    list_filter = ('type', 'genres')
    search_fields = ('title', 'description', 'id')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ('full_name',)


@admin.register(PersonFilmwork)
class PersonFilmworkAdmin(admin.ModelAdmin):

    list_display = ('film_work', 'person', 'role')

    search_fields = ('role', 'film_work', 'person')
