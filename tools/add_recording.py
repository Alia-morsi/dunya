#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."))

from dunya import settings
from django.core.management import setup_environ
setup_environ(settings)

from data.models import *

import musicbrainzngs as mb
mb.set_useragent("Dunya", "0.1")
mb.set_rate_limit(False)

import pprint

import logging
logging.basicConfig(level=logging.INFO)

def import_release(mbid):
    rel = mb.get_release_by_id(mbid, includes=["artists","recordings"])
    rel = rel["release"]

    mbid = rel["id"]
    logging.info("Adding release %s" % mbid)
    try:
        concert = Concert.objects.get(mbid=mbid)
    except Concert.DoesNotExist:
        concert = Concert(mbid=mbid, title=rel["title"])
        concert.save()
        for a in rel["artist-credit"]:
            artistid = a["artist"]["id"]
            artist = add_and_get_artist(artistid)
            logging.info("  artist: %s" % artist)
            concert.artists.add(artist)
    recordings = []
    for medium in rel["medium-list"]:
        for track in medium["track-list"]:
            recordings.append(track["recording"]["id"])
    for recid in recordings:
        recording = add_and_get_recording(recid)
        concert.tracks.add(recording)


def add_and_get_artist(artistid):
    try:
        artist = Artist.objects.get(mbid=artistid)
    except Artist.DoesNotExist:
        logging.info("  adding artist %s" % (artistid, ))
        a = mb.get_artist_by_id(artistid)["artist"]
        artist = Artist(name=a["name"], mbid=artistid)
        if a.get("type") == "Person":
            artist.artist_type = "P"
        elif a.get("type") == "Group":
            artist.artist_type = "G"
        if a.get("gender") == "Male":
            artist.gender = "M"
        elif a.get("gender") == "Female":
            artist.gender = "F"
        artist.save()
    return artist

def _get_raaga(taglist):
    for t in taglist:
        name = t["name"].lower()
        if "raaga" in name:
            return name.replace("raaga", "")
    return None

def _get_taala(taglist):
    for t in taglist:
        name = t["name"].lower()
        if "taala" in name:
            return name.replace("taala", "")
    return None

def add_and_get_recording(recordingid):
    try:
        rec = Recording.objects.get(mbid=recordingid)
    except Recording.DoesNotExist:
        logging.info("  adding recording %s" % (recordingid,))
        mbrec = mb.get_recording_by_id(recordingid, includes=["tags", "work-rels", "artist-rels"])
        mbrec = mbrec["recording"]
        raaga = _get_raaga(mbrec["tag-list"])
        taala = _get_taala(mbrec["tag-list"])
        mbwork = None
        for work in mbrec.get("work-relation-list", []):
            if work["type"] == "performance":
                mbwork = add_and_get_work(work["target"], raaga, taala)
        rec = Recording(mbid=recordingid, work=mbwork)
        rec.length = mbrec.get("length")
        rec.title = mbrec["title"]
        rec.save()
        for perf in mbrec.get("artist-relation-list", []):
            if perf["type"] == "vocal":
                artistid = perf["target"]
                is_lead = "lead" in perf["attribute-list"]
                add_performance(recordingid, artistid, "vocal", is_lead)
            elif perf["type"] == "instrument":
                artistid = perf["target"]
                attrs = perf.get("attrribute-list", [])
                is_lead = False
                if "lead" in attrs:
                    is_lead = "True"
                    attrs.remove("lead")
                inst = perf["attribute-list"][0]
                add_performance(recordingid, artistid, inst, is_lead)
    return rec

def add_and_get_work(workid, raaga, taala):
    try:
        w = Work.objects.get(mbid=workid)
    except Work.DoesNotExist:
        r = add_and_get_raaga(raaga)
        t = add_and_get_taala(taala)
        mbwork = mb.get_work_by_id(workid, includes=["artist-rels"])["work"]
        w = Work(title=mbwork["title"], mbid=workid, raaga=r, taala=t)
        w.save()
        for artist in mbwork.get("artist-relation-list", []):
            if artist["type"] == "composer":
                composer = add_and_get_composer(artist["target"])
                w.composer = composer
                w.save()
            elif artist["type"] == "lyricist":
                pass
    return w

def add_and_get_composer(artistid):
    try:
        composer = Composer.objects.get(mbid=artistid)
    except Composer.DoesNotExist:
        logging.info("  adding composer %s" % (artistid, ))
        a = mb.get_artist_by_id(artistid)["artist"]
        composer = Composer(name=a["name"], mbid=artistid)
        if a.get("gender") == "Male":
            composer.gender = "M"
        elif a.get("gender") == "Female":
            composer.gender = "F"
        composer.save()
    return composer

def add_and_get_raaga(raaganame):
    if raaganame is None:
        return None
    try:
        raaga = Raaga.objects.get(name=raaganame)
    except Raaga.DoesNotExist:
        raaga = Raaga()
        raaga.name = raaganame
        raaga.save()
    return raaga

def add_and_get_taala(taalaname):
    if taalaname is None:
        return None
    try:
        taala = Taala.objects.get(name=taalaname)
    except Taala.DoesNotExist:
        taala = Taala()
        taala.name = taalaname
        taala.save()
    return taala

def add_performance(recordingid, artistid, instrument, is_lead):
    logging.info("  Adding performance...")
    artist = add_and_get_artist(artistid)
    instrument = add_and_get_instrument(instrument)
    recording = Recording.objects.get(mbid=recordingid)
    perf = InstrumentPerformance(recording=recording, instrument=instrument, performer=artist, lead=is_lead)
    perf.save()

def add_and_get_instrument(instname):
    try:
        inst = Instrument.objects.get(name=instname)
    except Instrument.DoesNotExist:
        logging.info("  adding instrument %s" % (instname,))
        inst = Instrument()
        inst.name = instname
        inst.save()
    return inst

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: %s <release_mbid>" % (sys.argv[0], )
    else:
        import_release(sys.argv[1])

