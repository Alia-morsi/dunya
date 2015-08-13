# Copyright 2013,2014 Music Technology Group - Universitat Pompeu Fabra
#
# This file is part of Dunya
#
# Dunya is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free Software
# Foundation (FSF), either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see http://www.gnu.org/licenses/

from django.db import models
from django_extensions.db.fields import UUIDField
from django.core.urlresolvers import reverse
import django.utils.timezone
from django.apps import apps

import os
import importlib
import json

class StateCarryingManager(models.Manager):
    """ A model manager that also creates a state entry when a
    new object is made. This state object is used to keep track
    of progress on the import.
    """

    def create(self, **kwargs):
        if not self.stateclass or not self.linkname:
            raise ValueError("Need stateclass and linkname set in a subclass")
        if isinstance(self.stateclass, basestring):
            db = apps.get_app_config("dashboard")
            cls = db.get_model(self.stateclass)
        else:
            cls = self.stateclass
        if not cls:
            raise ValueError("Stateclass should be a type that exists")
        baseobject = models.Manager.create(self, **kwargs)
        # Use magic **dict because `linkname' changes between models.
        cls.objects.create(**{self.linkname: baseobject})
        return baseobject

    def get_or_create(self, **kwargs):
        if not self.stateclass or not self.linkname:
            raise ValueError("Need stateclass and linkname set in a subclass")
        if isinstance(self.stateclass, basestring):
            db = apps.get_app_config("dashboard")
            cls = db.get_model(self.stateclass)
        else:
            cls = self.stateclass
        if not cls:
            raise ValueError("Stateclass should be a type that exists")
        baseobject, created = models.Manager.get_or_create(self, **kwargs)
        if created:
            cls.objects.create(**{self.linkname: baseobject})
        return baseobject, created

class CollectionManager(StateCarryingManager):
    stateclass = "CollectionState"
    linkname = "collection"

class CollectionFileManager(StateCarryingManager):
    stateclass = "CollectionFileState"
    linkname = "collectionfile"

class MusicbrainzReleaseManager(StateCarryingManager):
    stateclass = "MusicbrainzReleaseState"
    linkname = "musicbrainzrelease"

class CompletenessChecker(models.Model):
    """ Stores information about modules that have been written to check
    the completeness and consistency of the data that we have stored in
    external sources and the audio files.
    See the dashboard.jobs module for more information
    """
    TYPE_CHOICE = (('r', 'Release'), ('f', 'File'))
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=200)
    templatefile = models.CharField(max_length=200, blank=True, null=True)
    # flag for if this a checker for a single file, or for a whole release
    type = models.CharField(max_length=5, choices=TYPE_CHOICE)

    def __unicode__(self):
        return u"%s (%s / %s)" % (self.name, self.module, self.type)

    def get_instance(self):
        """ Import the class referred to by 'module' and return
        an instance of it """
        mod, clsname = self.module.rsplit(".", 1)
        package = importlib.import_module(mod)
        cls = getattr(package, clsname)
        instance = cls()
        return instance

class CollectionState(models.Model):

    class Meta:
        ordering = ['-state_date']

    collection = models.ForeignKey("Collection")
    STATE_CHOICE = (('n', 'Not started'), ('s', 'Scanning'), ('d', 'Scanned'), ('i', 'Importing'), ('f', 'Finished'), ('e', 'Error'))
    state = models.CharField(max_length=10, choices=STATE_CHOICE, default='n')
    state_date = models.DateTimeField(default=django.utils.timezone.now)

    @property
    def state_name(self):
        return dict(self.STATE_CHOICE)[self.state]

    def __unicode__(self):
        return u"%s (%s)" % (self.state_name, self.state_date)

class Collection(models.Model):
    AUDIO_DIR = 'audio'
    objects = CollectionManager()

    id = UUIDField(primary_key=True)
    name = models.CharField(max_length=200)
    last_updated = models.DateTimeField(default=django.utils.timezone.now)
    root_directory = models.CharField(max_length=255)

    # The Completeness Checkers to run on this collection
    checkers = models.ManyToManyField(CompletenessChecker)
    # If we want to import this collection to main Dunya
    do_import = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.id)

    def state_colour(self):
        curr = self.get_current_state()
        if curr:
            if curr.state == "n":
                return "red"
            elif curr.state == "s":
                return "yellow"
            elif curr.state == "f":
                return "green"
        return "rscan_and_linked"

    def get_current_state(self):
        return self.collectionstate_set.all()[0]

    def has_previous_state(self):
        return self.collectionstate_set.count() > 1

    def get_previous_states(self):
        return self.collectionstate_set.all()[1:]

    def update_state(self, state):
        CollectionState.objects.create(collection=self, state=state)

    def set_state_importing(self):
        self.update_state('i')

    def set_state_finished(self):
        self.update_state('f')

    def set_state_scanning(self):
        """ Mark this collection as having its importer started. """
        self.update_state('s')

    def set_state_scanned(self):
        self.update_state('d')

    def set_state_error(self):
        self.update_state('e')

    def status_can_finish(self):
        """ See if this collection's import can finish.
        An import can finish if all its children directories have finished.
        """
        for rel in self.musicbrainzrelease_set.all():
            relstate = rel.get_current_state()
            if relstate.state != 'f':
                return False
        return True

    def get_absolute_url(self):
        return reverse("dashboard-collection", args=[str(self.id)])

    def add_log_message(self, message):
        return CollectionLogMessage.objects.create(collection=self, message=message)

class CollectionLogMessage(models.Model):
    """ A message that a completeness checker can add to a Collection """

    class Meta:
        ordering = ['-datetime']

    collection = models.ForeignKey(Collection)
    message = models.TextField()
    datetime = models.DateTimeField(default=django.utils.timezone.now)

    def __unicode__(self):
        return u"%s - %s" % (self.collection.name, self.datetime)

class MusicbrainzReleaseState(models.Model):
    """ Indicates the procesing state of a release. A release has finished
    processing when all files it is part of have finished.
    """

    class Meta:
        ordering = ['-state_date']

    musicbrainzrelease = models.ForeignKey("MusicbrainzRelease")
    STATE_CHOICE = (('n', 'Not started'), ('i', 'Importing'), ('f', 'Finished'), ('e', 'Error'))
    state = models.CharField(max_length=10, choices=STATE_CHOICE, default='n')
    state_date = models.DateTimeField(default=django.utils.timezone.now)

    @property
    def state_name(self):
        return dict(self.STATE_CHOICE)[self.state]

    def __unicode__(self):
        return u"%s (%s)" % (self.state_name, self.state_date)

class MusicbrainzRelease(models.Model):
    class Meta:
        unique_together = ('mbid', 'collection')

    objects = MusicbrainzReleaseManager()

    mbid = UUIDField()
    collection = models.ForeignKey(Collection)
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, blank=True, null=True)
    # If a release has ignore set, we do not try and import it
    ignore = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s (%s)" % (self.title, self.id)

    def all_files(self):
        ret = []
        for directory in self.collectiondirectory_set.all():
            ret.extend(directory.collectionfile_set.all())
        return ret

    def get_absolute_url(self):
        return reverse("dashboard-release", args=[str(self.pk)])

    def matched_paths(self):
        r = []
        for m in self.collectiondirectory_set.all():
            r.append(m.short_path())
        return r

    def update_state(self, state):
        MusicbrainzReleaseState.objects.create(musicbrainzrelease=self, state=state)

    def set_state_importing(self):
        """ Set the state of the release to 'importing'. Also sets
        the state of all files that are part of this release
        to importing too
        """
        self.update_state('i')
        for f in CollectionFile.objects.filter(directory__musicbrainzrelease=self):
            f.set_state_importing()

    def set_state_finished(self):
        self.update_state('f')

    def set_state_error(self):
        self.update_state('e')

    def get_current_state(self):
        return self.musicbrainzreleasestate_set.all()[0]

    def has_previous_state(self):
        return self.musicbrainzreleasestate_set.count() > 1

    def get_previous_states(self):
        return self.musicbrainzreleasestate_set.all()[1:]

    def get_latest_checker_results(self):
        # for each checker, get one result ordered by date
        ret = []
        for ch in CompletenessChecker.objects.filter(type='r'):
            results = self.musicbrainzreleaseresult_set.filter(checker=ch).all()
            if len(results):
                ret.append(results[0])
        return ret

    def get_rest_results_for_checker(self, checkerid):
        # order by date
        return self.musicbrainzreleaseresult_set.filter(checker__id=checkerid)[1:]

    def add_log_message(self, message, checker=None):
        return MusicbrainzReleaseLogMessage.objects.create(musicbrainzrelease=self, checker=checker, message=message)

class MusicbrainzReleaseLogMessage(models.Model):
    """ A message that a completeness checker can add to a MusicbrainzRelease """

    class Meta:
        ordering = ['-datetime']

    musicbrainzrelease = models.ForeignKey(MusicbrainzRelease)
    checker = models.ForeignKey(CompletenessChecker, blank=True, null=True)
    message = models.TextField()
    datetime = models.DateTimeField(default=django.utils.timezone.now)

    def __unicode__(self):
        return u"%s: %s" % (self.datetime, self.message)

class CollectionDirectory(models.Model):
    """ A directory inside the file tree for a collection that has releases
    in it. This usually corresponds to a single CD. This means a MusicbrainzRelease
    may have more than 1 CollectionDirectory """

    collection = models.ForeignKey(Collection)
    musicbrainzrelease = models.ForeignKey(MusicbrainzRelease, blank=True, null=True)
    path = models.CharField(max_length=500)

    @property
    def full_path(self):
        return os.path.join(self.collection.root_directory, self.path)

    def __unicode__(self):
        return u"From collection %s, release %s, path on disk %s" % (
            self.collection,
            self.musicbrainzrelease, self.path)

    def short_path(self):
        if len(self.path) < 60:
            return self.path
        else:
            return u"%s\u2026%s" % (self.path[:30], self.path[-30:])

    def get_absolute_url(self):
        return reverse('dashboard-directory', args=[int(self.id)])

    def add_log_message(self, message, checker=None):
        return CollectionDirectoryLogMessage.objects.create(collectiondirectory=self, checker=checker, message=message)

    def get_file_list(self):
        return self.collectionfile_set.order_by('name').all()

class CollectionDirectoryLogMessage(models.Model):
    """ A message that a completeness checker can add to a CollectionDirectory """

    class Meta:
        ordering = ['-datetime']

    collectiondirectory = models.ForeignKey(CollectionDirectory)
    checker = models.ForeignKey(CompletenessChecker, blank=True, null=True)
    message = models.TextField()
    datetime = models.DateTimeField(default=django.utils.timezone.now)

    def __unicode__(self):
        return u"%s: %s" % (self.datetime, self.message)

class CollectionFileState(models.Model):
    """ Indicates the processing state of a single file.
    a file has finished processing when all `file' consistency
    checkers have completed (regardless of if they are good or bad). """

    class Meta:
        ordering = ['-state_date']

    collectionfile = models.ForeignKey("CollectionFile")
    STATE_CHOICE = (('n', 'Not started'), ('i', 'Importing'), ('f', 'Finished'), ('e', 'Error'))
    state = models.CharField(max_length=10, choices=STATE_CHOICE, default='n')
    state_date = models.DateTimeField(default=django.utils.timezone.now)

    @property
    def state_name(self):
        return dict(self.STATE_CHOICE)[self.state]

    def __unicode__(self):
        return u"%s (%s)" % (self.state_name, self.state_date)

class CollectionFile(models.Model):
    """ A single audio file in the collection. A file is part of a
    collection directory.
    If the directory is matched to a MusicbrainzRelease, then a CollectionFile
    can also have an optional recordingid set, which references the musicbrainz
    recording id of the file.
    """
    objects = CollectionFileManager()

    name = models.CharField(max_length=255)
    directory = models.ForeignKey(CollectionDirectory)
    recordingid = UUIDField(null=True, blank=True)
    filesize = models.IntegerField(blank=True, null=True)

    @property
    def path(self):
        """ Absolute path """
        return os.path.join(
            self.directory.collection.root_directory,
            self.directory.path, self.name)

    @property
    def relativepath(self):
        """ Path relative to the collection root """
        return os.path.join(self.directory.path, self.name)

    def __unicode__(self):
        return u"%s (from %s)" % (self.name, self.directory.musicbrainzrelease)

    def update_state(self, state):
        CollectionFileState.objects.create(collectionfile=self, state=state)

    def set_state_importing(self):
        self.update_state('i')

    def set_state_finished(self):
        self.update_state('f')

    def set_state_error(self):
        self.update_state('e')

    def get_current_state(self):
        return self.collectionfilestate_set.all()[0]

    def has_previous_state(self):
        return self.collectionfilestate_set.count() > 1

    def get_previous_states(self):
        return self.collectionfilestate_set.all()[1:]

    def add_log_message(self, message, checker=None):
        return CollectionFileLogMessage.objects.create(collectionfile=self, checker=checker, message=message)

    def get_absolute_url(self):
        return reverse('dashboard-file', args=[int(self.id)])

    def get_latest_checker_results(self):
        # for each checker, get the most recent result
        ret = []
        for ch in CompletenessChecker.objects.filter(type='f'):
            results = self.collectionfileresult_set.filter(checker=ch)
            if len(results):
                ret.append(results[0])
        return ret

    def get_rest_results_for_checker(self, checkerid):
        # order by date
        return self.collectionfileresult_set.filter(checker__id=checkerid)[1:]

class CollectionFileLogMessage(models.Model):
    """ A message that a completeness checker can add to a CollectionFile """

    class Meta:
        ordering = ['-datetime']

    collectionfile = models.ForeignKey(CollectionFile)
    checker = models.ForeignKey(CompletenessChecker, blank=True, null=True)
    message = models.TextField()
    datetime = models.DateTimeField(default=django.utils.timezone.now)

class CollectionFileResult(models.Model):
    """ The result of running a single completeness checker
    on a single file. The a completeness checker either returns
    True or False.
    """

    class Meta:
        ordering = ['-datetime']

    RESULT_CHOICE = (('g', 'Good'), ('b', 'Bad'))
    datetime = models.DateTimeField(default=django.utils.timezone.now)
    collectionfile = models.ForeignKey(CollectionFile)
    checker = models.ForeignKey(CompletenessChecker)
    result = models.CharField(max_length=10, choices=RESULT_CHOICE)
    data = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u"%s testing %s: %s" % (self.checker.name, self.collectionfile.name, self.result)

    def get_result_icon(self):
        icons = {"g": "tick.png",
                 "b": "cross.png"
                 }
        return icons[self.result]

    @property
    def data_object(self):
        if self.data:
            return json.loads(self.data)
        else:
            return {}

class MusicbrainzReleaseResult(models.Model):
    """ The result of running a single completeness checker
    on a single release. The a completeness checker either returns
    True or False.
    """

    class Meta:
        ordering = ['-datetime']

    RESULT_CHOICE = (('g', 'Good'), ('b', 'Bad'))
    datetime = models.DateTimeField(default=django.utils.timezone.now)
    musicbrainzrelease = models.ForeignKey(MusicbrainzRelease, blank=True, null=True)
    checker = models.ForeignKey(CompletenessChecker)
    result = models.CharField(max_length=10, choices=RESULT_CHOICE)
    data = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u"%s testing %s: %s" % (self.checker.name, self.musicbrainzrelease.title, self.result)

    def get_result_icon(self):
        icons = {"g": "tick.png",
                 "b": "cross.png"
                 }
        return icons[self.result]

    @property
    def data_object(self):
        if self.data:
            return json.loads(self.data)
        else:
            return {}
