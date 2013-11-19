from django.db import models

from compmusic.fuzzy import stringDuplicates

class FuzzySearchManager(models.Manager):
    def fuzzy(self, name):
        name = name.lower()
        try:
            self.model.objects.get(name__iexact=name)
        except self.model.DoesNotExist:
            items = self.model.objects.all()
            names = [i.name.lower() for i in items]
            dups = stringDuplicates.stringDuplicates(name, names, stripped=True)
            if len(dups) != 1:
                raise self.model.DoesNotExist()
            n = dups[0]
            for i in items:
                if i.name.lower() == n.lower():
                    return i
            raise Exception("Whoops")

