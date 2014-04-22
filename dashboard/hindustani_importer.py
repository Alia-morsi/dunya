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

from django.db.models import Q

from dashboard.log import logger
from dashboard import release_importer
import compmusic

import hindustani
import data

class HindustaniReleaseImporter(release_importer.ReleaseImporter):
    _ArtistClass = hindustani.models.Artist
    _ArtistAliasClass = hindustani.models.ArtistAlias
    _ComposerClass = hindustani.models.Composer
    _ComposerAliasClass = hindustani.models.ComposerAlias
    _ReleaseClass = hindustani.models.Release
    _RecordingClass = hindustani.models.Recording
    _InstrumentClass = hindustani.models.Instrument
    _WorkClass = hindustani.models.Work


    def _link_release_recording(self, release, recording, trackorder):
        if not release.tracks.filter(pk=recording.pk).exists():
            hindustani.models.ReleaseRecording.objects.create(
                    release=release, recording=recording, track=trackorder)

    def _join_recording_and_works(self, recording, works):
        # A hindustani recording can have many works
        if self.overwrite:
            hindustani.models.WorkTime.objects.filter(recording=recording).delete()

        sequence = 1
        for w in works:
            hindustani.models.WorkTime.objects.create(work=w, recording=recording, sequence=sequence)
            sequence += 1

    def _apply_tags(self, recording, work, tags):
        raags = self._get_raag_tags(tags)
        taals = self._get_taal_tags(tags)
        layas = self._get_laya_tags(tags)
        forms = self._get_form_tags(tags)

        if self.overwrite:
            hindustani.models.RecordingTaal.objects.filter(recording=recording).delete()
            hindustani.models.RecordingLaya.objects.filter(recording=recording).delete()
            hindustani.models.RecordingRaag.objects.filter(recording=recording).delete()
            hindustani.models.RecordingForm.objects.filter(recording=recording).delete()

        for l in layas:
            lpos = l[0]
            lob = self._get_laya(l[1])
            if lob:
                hindustani.models.RecordingLaya.objects.create(recording=recording, laya=lob, sequence=lpos)
            else:
                print "couldn't find a laya", l

        for t in taals:
            tpos = t[0]
            tob = self._get_taal(t[1])
            if tob:
                hindustani.models.RecordingTaal.objects.create(recording=recording, taal=tob, sequence=tpos)
            else:
                print "couldn't find a taal", t


        for r in raags:
            rpos = r[0]
            rob = self._get_raag(r[1])
            if rob:
                hindustani.models.RecordingRaag.objects.create(recording=recording, raag=rob, sequence=rpos)
            else:
                print "could't find a raag", r

        for f in forms:
            fpos = f[0]
            fob = self._get_form(f[1])
            if fob:
                hindustani.models.RecordingForm.objects.create(recording=recording, form=fob, sequence=fpos)
            else:
                print "couldn't find a form", f

    def _get_raag_tags(self, taglist):
        ret = []
        for t in taglist:
            name = t["name"].lower()
            if compmusic.tags.has_raag(name):
                parsed = compmusic.tags.parse_raag(name)
                if parsed and parsed[0]:
                    ret.append(parsed)
        return ret

    def _get_taal_tags(self, taglist):
        ret = []
        for t in taglist:
            name = t["name"].lower()
            if compmusic.tags.has_taal(name):
                parsed = compmusic.tags.parse_taal(name)
                if parsed and parsed[0]:
                    ret.append(parsed)
        return ret

    def _get_laya_tags(self, taglist):
        ret = []
        for t in taglist:
            name = t["name"].lower()
            if compmusic.tags.has_laya(name):
                parsed = compmusic.tags.parse_laya(name)
                if parsed and parsed[0]:
                    ret.append(parsed)
        return ret

    def _get_form_tags(self, taglist):
        ret = []
        for t in taglist:
            name = t["name"].lower()
            if compmusic.tags.has_hindustani_form(name):
                parsed = compmusic.tags.parse_hindustani_form(name)
                if parsed and parsed[0]:
                    ret.append(parsed)
        return ret

    def _get_raag(self, rname):
        try:
            return hindustani.models.Raag.objects.get(Q(name__iexact=rname) | Q(common_name__iexact=rname))
        except hindustani.models.Raag.DoesNotExist:
            try:
                al = hindustani.models.RaagAlias.objects.get(name__iexact=rname)
                return al.raag
            except hindustani.models.RaagAlias.DoesNotExist:
                return None

    def _get_taal(self, tname):
        try:
            return hindustani.models.Taal.objects.get(Q(name__iexact=tname) | Q(common_name__iexact=tname))
        except hindustani.models.Taal.DoesNotExist:
            try:
                al = hindustani.models.TaalAlias.objects.get(name__iexact=tname)
                return al.taal
            except hindustani.models.TaalAlias.DoesNotExist:
                return None

    def _get_form(self, fname):
        try:
            return hindustani.models.Form.objects.get(Q(name__iexact=fname) | Q(common_name__iexact=fname))
        except hindustani.models.Form.DoesNotExist:
            try:
                al = hindustani.models.FormAlias.objects.get(name__iexact=fname)
                return al.form
            except hindustani.models.FormAlias.DoesNotExist:
                return None

    def _get_laya(self, lname):
        try:
            return hindustani.models.Laya.objects.get(Q(name__iexact=lname) | Q(common_name__iexact=lname))
        except hindustani.models.Laya.DoesNotExist:
            try:
                al = hindustani.models.LayaAlias.objects.get(name__iexact=lname)
                return al.laya
            except hindustani.models.LayaAlias.DoesNotExist:
                return None

    def get_instrument(self, instname):
        try:
            return hindustani.models.Instrument.objects.get(name__iexact=instname)
        except hindustani.models.Instrument.DoesNotExist:
            return None

    def _add_recording_performance(self, recordingid, artistid, instrument, is_lead):
        logger.info("  Adding recording performance...")
        artist = self.add_and_get_artist(artistid)
        # Musicbrainz calls it 'vocals', but we want it to be 'voice'
        if instrument == "vocals":
            instrument = "voice"
        instrument = self.get_instrument(instrument)
        if instrument:
            recording = hindustani.models.Recording.objects.get(mbid=recordingid)
            perf = hindustani.models.InstrumentPerformance(recording=recording, instrument=instrument, performer=artist, lead=is_lead)
            perf.save()

    def _add_release_performance(self, releaseid, artistid, instrument, is_lead):
        logger.info("  Adding concert performance to all tracks...")
        release = hindustani.models.Release.objects.get(mbid=releaseid)
        for t in release.tracks.all():
            self._add_recording_performance(t.mbid, artistid, instrument, is_lead)

