import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):

    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class UUIDMixin(models.Model):

    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Genre(UUIDMixin, TimeStampedMixin):

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'genre'
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')


class Type_Choices(models.TextChoices):
    movie = 'MV', _('Movie')
    tv_show = 'TV_S', _('TV-show')

class RoleType(models.TextChoices):
    writer = 'writer', _('сценарист')
    director = 'director', _('режиссер')
    actor = 'actor', _('актер')


class Filmwork(UUIDMixin, TimeStampedMixin):
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    creation_date = models.DateField(auto_now_add=True, null=True)
    rating = models.FloatField(
        _('Rating'),
        null=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    type = models.CharField(
        max_length=20,
        choices=Type_Choices.choices,
    )
    genres = models.ManyToManyField(Genre, through='GenreFilmwork')

    certificate = models.CharField(_('certificate'), max_length=512, blank=True, null=True)
    file_path = models.FileField(_('file'), blank=True, null=True, upload_to='movies/')

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'film_work'
        verbose_name = _('Filmwork')
        verbose_name_plural = _('Filmworks')


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'genre_film_work'


class Gender(models.TextChoices):
    male = 'male', _('male')
    female = 'female', _('female')


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('Full_name'), max_length=255)
    gender = models.TextField(_('gender'), choices=Gender.choices, null=True)

    def __str__(self):
        return self.full_name

    class Meta:
        db_table = 'person'
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')


class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey('Filmwork', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    role = models.CharField(_('профессия'), choices=RoleType.choices, max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.role

    class Meta:
        db_table = 'person_film_work'
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
