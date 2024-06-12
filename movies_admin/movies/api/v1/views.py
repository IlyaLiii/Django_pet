from django.db.models.query import QuerySet
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.paginator import Paginator, Page
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView

from movies.models import Filmwork, RoleType
import logging

class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_person_aggregation(self, role: str):
        role = role.lower()
        arrayagg_role = ArrayAgg('personfilmwork__person__full_name', filter=Q(personfilmwork__role=getattr(RoleType, role)), distinct=True)
        return arrayagg_role

    def get_queryset(self):
        queryset: QuerySet = self.model.objects.values().annotate(
            actors=self.get_person_aggregation('actor'),
            directors=self.get_person_aggregation('director'),
            writers=self.get_person_aggregation('writer'),
            genres=ArrayAgg('genres__name', distinct=True)
        )

        return queryset

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class Movies(MoviesApiMixin, BaseListView):
    model = Filmwork
    paginate_by = 50
    ordering = 'title'

    http_method_names = ['get']  # Список методов, которые реализует обработчик

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()

        paginator: Paginator = context['paginator']
        page: Page = context['page_obj']
        page_items: QuerySet = context['object_list']

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            'results': list(page_items),
        }

        return context


class MovieDetail(MoviesApiMixin, BaseDetailView):
    def get_object(self, queryset=None):
        try:
            return self.get_queryset().filter(id=self.kwargs['pk']).get()
        except Filmwork.DoesNotExist as err:
            return {}

    def get_context_data(self, object, **kwargs):
        try:
            context = {
                'results': object,
            }
        except Exception as err:
            logging.error(err)

        return context['results']