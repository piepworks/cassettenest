from functools import partial
from itertools import groupby
from operator import attrgetter
from .models import Stock

from django.forms.models import ModelChoiceIterator, ModelChoiceField

# GENERAL PURPOSE STUFF
# https://simpleisbetterthancomplex.com/tutorial/2019/01/02/how-to-implement-grouped-model-choice-field.html


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            if isinstance(group, str):
                group = group.title()
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelChoiceField(ModelChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = attrgetter(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError(
                "choices_groupby must either be a str or a callable accepting a single argument"
            )
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)


# VERSION OF THE ABOVE STUFF, BUT TOO FIDDLY TO RECONCILE


class GroupedFilmChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()

        type_choices = dict(Stock._meta.get_field("type").flatchoices)

        for group, objs in groupby(queryset, lambda film: film.stock.type):
            yield (
                type_choices[group],
                [self.choice(obj) for obj in objs],
            )


class GroupedFilmChoiceField(ModelChoiceField):
    def __init__(self, *args, **kwargs):
        self.iterator = partial(GroupedFilmChoiceIterator)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return f"{obj} ({obj.count})"
