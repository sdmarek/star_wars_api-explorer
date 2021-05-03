from uuid import uuid4
from django.db import models
from django.utils.timezone import now


class Collection(models.Model):
    FetchingStatus = models.IntegerChoices('FetchingStatus', 'STARTED FINISHED FAILED')

    name = models.CharField(max_length=36, default=uuid4, unique=True, blank=False, editable=False)
    created = models.DateTimeField(auto_now_add=True, blank=False, editable=False)
    modified = models.DateTimeField(auto_now=True, blank=False, editable=False)
    fetching_status = models.IntegerField(default=FetchingStatus.STARTED, choices=FetchingStatus.choices, blank=False, editable=False)

    def age(self):
        return (now() - self.created).total_seconds()
