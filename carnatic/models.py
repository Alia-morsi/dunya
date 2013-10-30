from django.db import models
from django.core.urlresolvers import reverse

import data.models
import managers
import filters
import random


class CarnaticStyle(object):
    def get_style(self):
        return "carnatic"
    def get_object_map(self, key):
        return {"performance": InstrumentPerformance,
                "concertperformance": InstrumentConcertPerformance,
                "concert": Concert,
                "composer": Composer,
                "artist": Artist,
                "recording": Recording,
                "work": Work,
                "instrument": Instrument
                }[key]

class GeographicRegion(CarnaticStyle, models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class MusicalSchool(CarnaticStyle, models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

class Artist(CarnaticStyle, data.models.Artist):
    state = models.ForeignKey(GeographicRegion, blank=True, null=True)
    gurus = models.ManyToManyField("Artist", related_name="students")
    hidden = models.BooleanField(default=False)

    def instruments(self):
        insts = []
        for perf in self.instrumentperformance_set.all():
            if perf.instrument.name not in insts:
                insts.append(perf.instrument)
        if insts:
            return insts[0]
        else:
            return None

    def similar_artists(self):
        pass

    def concerts(self):
        ret = []
        ret.extend(self.primary_concerts.all())
        for concert, perf in self.performances():
            if concert not in ret:
                ret.append(concert)
        return ret

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-artist-search'),
               "name": "Artist",
               "data": [filters.School().object, filters.Region().object, filters.Generation().object]
              }
        return ret

class Language(CarnaticStyle, models.Model):
    name = models.CharField(max_length=50)

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

class LanguageAlias(CarnaticStyle, models.Model):
    name = models.CharField(max_length=50)
    language = models.ForeignKey(Language, related_name="aliases")

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

class Sabbah(CarnaticStyle, models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

class Concert(CarnaticStyle, data.models.Concert):
    sabbah = models.ForeignKey(Sabbah, blank=True, null=True)

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-concert-search'),
               "name": "Concert",
               "data": [filters.Venue().object, filters.Instrument().object]
              }
        return ret

class RaagaAlias(models.Model):
    name = models.CharField(max_length=50)
    raaga = models.ForeignKey("Raaga", related_name="aliases")

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

class Form(models.Model):
    name = models.CharField(max_length=50)

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

class FormAlias(models.Model):
    name = models.CharField(max_length=50)
    form = models.ForeignKey(Form, related_name="aliases")

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

class Raaga(data.models.BaseModel):
    missing_image = "raaga.png"

    name = models.CharField(max_length=50)

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-raaga-search'),
               "name": "Raaga",
               "data": [filters.Text().object]
              }
        return ret

    def get_absolute_url(self):
        return reverse('carnatic-raaga', args=[str(self.id)])

    def works(self):
        return self.work_set.distinct().all()

    def composers(self):
        return Composer.objects.filter(work__raaga=self).distinct()

    def artists(self):
        return Artist.objects.filter(primary_concerts__tracks__work__raaga=self).distinct()

class TaalaAlias(models.Model):
    name = models.CharField(max_length=50)
    taala = models.ForeignKey("Taala", related_name="aliases")

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name


# similarity matrix. key: a taala id, val: an ordered list of similarities (taala ids)
# We fill in 'above' and 'below' the diagonal - e.g. 1: 2,3 / 2: 1
taala_similar = {1: [5], 3: [7, 11, 10], 4: [8, 9], 5: [1], 6: [2],
        7: [3, 11, 10], 8: [4, 9], 2: [6], 9: [8, 4], 10: [7, 3], 11: [7, 3]}

class Taala(data.models.BaseModel):
    missing_image = "taala.png"

    name = models.CharField(max_length=50)

    objects = managers.FuzzySearchManager()

    def __unicode__(self):
        return self.name

    def get_similar(self):
        if self.pk in taala_similar:
            return [Taala.objects.get(pk=id) for id in taala_similar[self.pk]]
        else:
            return []

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-taala-search'),
               "name": "Taala",
               "data": [filters.Text().object]
              }
        return ret

    def get_absolute_url(self):
        return reverse('carnatic-taala', args=[str(self.id)])

    def works(self):
        return self.work_set.distinct().all()

    def composers(self):
        return Composer.objects.filter(work__taala=self).distinct()

    def artists(self):
        return Artist.objects.filter(primary_concerts__tracks__work__taala=self).distinct()

    def percussion_artists(self):
        return Artist.objects.filter(primary_concerts__tracks__work__taala=self, main_instrument__percussion=True).distinct()

class Work(CarnaticStyle, data.models.Work):
    raaga = models.ManyToManyField('Raaga', through="WorkRaaga")
    taala = models.ManyToManyField('Taala', through="WorkTaala")
    form = models.ForeignKey('Form', blank=True, null=True)
    language = models.ForeignKey('Language', blank=True, null=True)

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-work-search'),
               "name": "Composition",
               "data": [filters.Form().object, filters.Language().object, filters.WorkDate().object]
              }
        return ret

class WorkRaaga(models.Model):
    work = models.ForeignKey('Work')
    raaga = models.ForeignKey('Raaga')
    sequence = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s, seq %d %s" % (self.work, self.sequence, self.raaga)

class WorkTaala(models.Model):
    work = models.ForeignKey('Work')
    taala = models.ForeignKey('Taala')
    sequence = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s, seq %d %s" % (self.work, self.sequence, self.taala)

class WorkAttribute(CarnaticStyle, data.models.WorkAttribute):
    pass

class WorkAttributeType(CarnaticStyle, data.models.WorkAttributeType):
    pass

class WorkAttributeTypeValue(CarnaticStyle, data.models.WorkAttributeTypeValue):
    pass

class Recording(CarnaticStyle, data.models.Recording):

    def raaga(self):
        if self.work:
            rs = self.work.raaga.all()
            if rs:
                return rs[0]
        return None

    def taala(self):
        if self.work:
            ts = self.work.taala.all()
            if ts:
                return ts[0]
        return None

class InstrumentAlias(CarnaticStyle, data.models.InstrumentAlias):
    objects = managers.FuzzySearchManager()

class Instrument(CarnaticStyle, data.models.Instrument):
    objects = managers.FuzzySearchManager()

    def description(self):
        return "The description of an instrument"

    def performers(self):
        IPClass = self.get_object_map("performance")
        performances = IPClass.objects.filter(instrument=self).distinct()
        ret = []
        artists = []
        for p in performances:
            if p.performer not in artists:
                ret.append(p)
                artists.append(p.performer)

        # TODO: This might be slow getting 2 sets of performances and doing tests
        ICPClass = self.get_object_map("concertperformance")
        performances = ICPClass.objects.filter(instrument=self).distinct()
        for p in performances:
            if p.performer not in artists:
                ret.append(p)
                artists.append(p.performer)

        return ret

    def references(self):
        pass

    def samples(self):
        IPClass = self.get_object_map("performance")
        performances = list(IPClass.objects.filter(instrument=self).all())
        random.shuffle(performances)
        perf = performances[:2]
        return [p.recording for p in perf]

    @classmethod
    def get_filter_criteria(cls):
        ret = {"url": reverse('carnatic-instrument-search'),
               "name": "Instrument",
               "data": [filters.Text().object]
              }
        return ret

class InstrumentPerformance(CarnaticStyle, data.models.InstrumentPerformance):
    pass

class InstrumentConcertPerformance(CarnaticStyle, data.models.InstrumentConcertPerformance):
    pass

class Composer(CarnaticStyle, data.models.Composer):
    state = models.ForeignKey(GeographicRegion, blank=True, null=True)
    def raagas(self):
        return Raaga.objects.filter(work__composer=self).all()

    def taalas(self):
        return Taala.objects.filter(work__composer=self).all()

class Location(CarnaticStyle, data.models.Location):
    pass

