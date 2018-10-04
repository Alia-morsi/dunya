from django.db import models

import data.models
from jingju import managers


class JingjuStyle(object):
    def get_style(self):
        return "jingju"

    def get_object_map(self, key):
        return {
            "performance": RecordingInstrumentalist,
            "release": Release,
            "artist": Artist,
            "recording": Recording,
            "work": Work,
            "instrument": Instrument
        }[key]


class Recording(JingjuStyle, data.models.BaseModel):
    class Meta:
        ordering = ['id']

    title = models.CharField(max_length=200, blank=True, null=True)
    mbid = models.UUIDField(blank=True, null=True)
    work = models.ForeignKey('Work', null=True, on_delete=models.CASCADE)
    performers = models.ManyToManyField('Artist')
    instrumentalists = models.ManyToManyField('Artist', through='RecordingInstrumentalist',
                                              related_name='instrumentalist')
    shengqiangbanshi = models.ManyToManyField('ShengqiangBanshi')
    objects = managers.CollectionRecordingManager()

    def __str__(self):
        return u"%s" % (self.title)


class RecordingInstrumentalist(JingjuStyle, models.Model):
    recording = models.ForeignKey('Recording', on_delete=models.CASCADE)
    artist = models.ForeignKey('Artist', on_delete=models.CASCADE)
    instrument = models.ForeignKey('Instrument', on_delete=models.CASCADE)


class Artist(data.models.Artist):
    alias = models.CharField(max_length=200, blank=True, null=True)
    role_type = models.ForeignKey('RoleType', blank=True, null=True, on_delete=models.CASCADE)
    instrument = models.ForeignKey('Instrument', blank=True, null=True, related_name='jingju', on_delete=models.CASCADE)
    objects = managers.ArtistManager()

    class Meta:
        ordering = ['id']


class ArtistAlias(data.models.ArtistAlias):
    pass


class Instrument(data.models.Instrument):
    class Meta:
        ordering = ['id']


class RecordingRelease(models.Model):
    recording = models.ForeignKey('Recording', on_delete=models.CASCADE)
    release = models.ForeignKey('Release', on_delete=models.CASCADE)
    sequence = models.IntegerField(blank=True, null=True)

    # The number that the track comes in the concert. Numerical 1-n
    track = models.IntegerField(blank=True, null=True)
    # The disc number. 1-n
    disc = models.IntegerField(blank=True, null=True)
    # The track number within this disc. 1-n
    disctrack = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ("track",)

    def __str__(self):
        return u"%s: %s from %s" % (self.track, self.recording, self.release)


class Work(JingjuStyle, data.models.BaseModel):
    class Meta:
        ordering = ['id']

    title = models.CharField(max_length=200, blank=True, null=True)
    mbid = models.UUIDField(blank=True, null=True)
    score = models.ForeignKey('Score', blank=True, null=True, on_delete=models.CASCADE)
    play = models.ForeignKey('Play', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return u"%s" % self.title


class Release(JingjuStyle, data.models.Release):
    class Meta:
        ordering = ['id']

    recordings = models.ManyToManyField('Recording', through='RecordingRelease')
    collection = models.ForeignKey('data.Collection', blank=True, null=True, on_delete=models.CASCADE)
    objects = managers.CollectionReleaseManager()


class RoleType(data.models.BaseModel):
    name = models.CharField(max_length=100)
    transliteration = models.CharField(max_length=100)
    uuid = models.UUIDField()


class Play(data.models.BaseModel):
    title = models.CharField(max_length=100)
    uuid = models.UUIDField(blank=True, null=True)


class Score(data.models.BaseModel):
    name = models.CharField(max_length=100)
    uuid = models.UUIDField(blank=True, null=True)


class ShengqiangBanshi(data.models.BaseModel):
    name = models.CharField(max_length=100)
