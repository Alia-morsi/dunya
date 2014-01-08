# -*- coding: UTF-8 -*-
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q

import social.tagging as tagging
from carnatic.models import *
from carnatic import search
from social.forms import TagSaveForm
import json
import docserver
import collections
import math
import random

def get_filter_items():
    filter_items = [
            Artist.get_filter_criteria(),
            Concert.get_filter_criteria(),
            Instrument.get_filter_criteria(),
            Raaga.get_filter_criteria(),
            Taala.get_filter_criteria()
    ]
    return filter_items

def searchcomplete(request):
    term = request.GET.get("term")
    if term:
        suggestions = search.autocomplete(term)
        ret = [{"id": i, "label": l, "value": l} for i, l in enumerate(suggestions, 1)]
    else:
        ret = []
    return HttpResponse(json.dumps(ret), content_type="application/json")

def main(request):
    qartist = []
    qinstr = []
    qraaga = []
    qtaala = []
    qconcert = []
    if len(request.GET) == 0:
        # We have a 'default' query. If there's no other query we pre-seed it
        # G. N. Balasubramaniam
        qartist = [10]
        # thodi raaga
        qraaga = [55]
    if "a" in request.GET:
        for i in request.GET.getlist("a"):
            qartist.append(int(i))
    if "i" in request.GET:
        for i in request.GET.getlist("i"):
            qinstr.append(int(i))
    if "c" in request.GET:
        for i in request.GET.getlist("c"):
            qconcert.append(int(i))
    if "r" in request.GET:
        for i in request.GET.getlist("r"):
            qraaga.append(int(i))
    if "t" in request.GET:
        for i in request.GET.getlist("t"):
            qtaala.append(int(i))
    if "q" in request.GET:
        query = request.GET.get("q")
        # special case, we have this so we can put a ? in the arglist
        # but it's actually a browse
        if query == "1":
            query = None
    else:
        query = None

    numartists = Artist.objects.filter(dummy=False).count()
    numcomposers = Composer.objects.count()
    numraagas = Raaga.objects.count()
    numtaalas = Taala.objects.count()
    numconcerts = Concert.objects.count()
    numinstruments = Instrument.objects.count()
    numworks = Work.objects.count()

    displayres = []
    querybrowse = False

    if qartist:
        # TODO: If instrument set, only show artists who perform this instrument
        querybrowse = True

        # If raaga or taala is set, make a list to filter concerts by
        rlist = []
        tlist = []
        if qraaga:
            for rid in qraaga:
                ra = Raaga.objects.get(pk=rid)
                rlist.append(ra)
        if qtaala:
            for tid in qtaala:
                ta = Taala.objects.get(pk=tid)
                tlist.append(ta)

        if len(qartist) == 1:
            # If there is one artist selected, show their concerts
            # (optionally filtered by raaga or taala)
            aid = qartist[0]
            art = Artist.objects.get(pk=aid)
            displayres.append(("artist", art))
            if art.main_instrument:
                displayres.append(("instrument", art.main_instrument))
            for ra in rlist:
                displayres.append(("raaga", ra))
            for ta in tlist:
                displayres.append(("taala", ta))
            for c in art.concerts(raagas=rlist, taalas=tlist):
                displayres.append(("concert", c))
        else:
            # Otherwise if more than one artist is selected,
            # show only concerts that all artists perform in
            allconcerts = []
            for aid in qartist:
                art = Artist.objects.get(pk=aid)
                displayres.append(("artist", art))
                if art.main_instrument:
                    displayres.append(("instrument", art.main_instrument))
                thisconcerts = set(art.concerts(raagas=rlist, taalas=tlist))
                allconcerts.append(thisconcerts)
            combinedconcerts = reduce(lambda x, y: x & y, allconcerts)

            for ra in rlist:
                displayres.append(("raaga", ra))
            for ta in tlist:
                displayres.append(("taala", ta))

            for c in list(combinedconcerts):
                displayres.append(("concert", c))

    elif qinstr: # instrument query, but no artist
        querybrowse = True
        # instrument, people
        for iid in qinstr:
            instr = Instrument.objects.get(pk=iid)
            displayres.append(("instrument", instr))
            for p in instr.ordered_performers()[:5]:
                displayres.append(("artist", p.performer))

    elif qraaga:
        querybrowse = True
        # raaga, people
        for rid in qraaga:
            ra = Raaga.objects.get(pk=rid)
            displayres.append(("raaga", ra))
            artists = ra.artists()
            if qinstr:
                # if instrument, only people who play that
                artists = artists.filter(main_instrument__in=qinstr)
            for a in artists[:5]:
                displayres.append(("artist", a))
    elif qtaala:
        querybrowse = True
        # taala, people
        for tid in qtaala[:5]:
            ta = Taala.objects.get(pk=tid)
            displayres.append(("taala", ta))
            percussionists = ta.percussion_artists()
            for a in ta.artists():
                if a not in percussionists:
                    percussionists.append(a)
            # TODO: We could order by percussionists, or by number of times they've
            # performed this taala, or by people with images
            artists = percussionists[:5]
            if qinstr:
                # if instrument, only people who play that
                artists = artists.filter(main_instrument__in=qinstr)
            for a in artists:
                displayres.append(("artist", a))
    elif qconcert:
        querybrowse = True
        # concert, people
        for cid in qconcert:
            con = Concert.objects.get(pk=cid)
            displayres.append(("concert", con))
            artists = con.performers()
            for a in artists:
                displayres.append(("artist", a.performer))
                # if instrument, only people who play that?
    elif query:
        results = search.search(query)
        artists = results.get("artist", [])
        instruments = results.get("instrument", [])
        concerts = results.get("concert", [])
        raagas = results.get("raaga", [])
        taalas = results.get("taala", [])

        displayres = []
        for a in artists:
            displayres.append(("artist", a))
        for i in instruments:
            displayres.append(("instrument", i))
        for c in concerts:
            displayres.append(("concert", c))
        for r in raagas:
            displayres.append(("raaga", r))
        for t in taalas:
            displayres.append(("taala", t))

        numartists = len(artists)
        numraagas = len(raagas)
        numtaalas = len(taalas)
        numconcerts = len(concerts)
        numinstruments = len(instruments)
        results = True
    else:
        results = None

        displayres = []

    if displayres:
        numartists = len([i for i in displayres if i[0] == "artist"])
        numraagas = len([i for i in displayres if i[0] == "raaga"])
        numtaalas = len([i for i in displayres if i[0] == "taala"])
        numconcerts = len([i for i in displayres if i[0] == "concert"])
        numinstruments = len([i for i in displayres if i[0] == "instrument"])

    ret = {"numartists": numartists,
           "filter_items": json.dumps(get_filter_items()),
           "numcomposers": numcomposers,
           "numraagas": numraagas,
           "numtaalas": numtaalas,
           "numconcerts": numconcerts,
           "numworks": numworks,
           "numinstruments": numinstruments,

           "results": displayres,

           "querytext": query,
           "querybrowse": querybrowse,
           "qartist": json.dumps(qartist),
           "qinstr": json.dumps(qinstr),
           "qraaga": json.dumps(qraaga),
           "qtaala": json.dumps(qtaala),
           "qconcert": json.dumps(qconcert)
           }

    return render(request, "carnatic/index.html", ret)

def artistsearch(request):
    artists = Artist.objects.filter(dummy=False).order_by('name')
    ret = []
    for a in artists:
        ret.append({"id": a.id, "name": a.name})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def artist(request, artistid):
    artist = get_object_or_404(Artist, pk=artistid)

    inst = artist.instruments()
    ips = InstrumentPerformance.objects.filter(instrument=inst)
    similar_artists = []
    for i in ips:
        if i.performer not in similar_artists:
            similar_artists.append(i.performer)

    if artist.main_instrument and artist.main_instrument.percussion:
        taalamap = {}
        taalacount = collections.Counter()
        taalas = Taala.objects.filter(Q(work__recording__concert__artists=artist) | Q(work__recording__concert__instrumentconcertperformance__performer=artist) | Q(work__recording__instrumentperformance__performer=artist))
        for t in taalas:
            taalacount[t.name] += 1
            if t.name not in taalamap:
                taalamap[t.name] = t
        taalas = []
        for t, count in taalacount.most_common():
            taalas.append((taalamap[t], count))
    else:
        taalas = []
    # vocalist or violinist
    if artist.main_instrument and artist.main_instrument.id in [1, 2]:
        raagamap = {}
        raagacount = collections.Counter()
        raagas = Raaga.objects.filter(Q(work__recording__concert__artists=artist) | Q(work__recording__concert__instrumentconcertperformance__performer=artist) | Q(work__recording__instrumentperformance__performer=artist))
        for r in raagas:
            raagacount[r.name] += 1
            if r.name not in raagamap:
                raagamap[r.name] = r
        raagas = []
        for r, count in raagacount.most_common():
            raagas.append((raagamap[r], count))
    else:
        raagas = []

    tags = tagging.tag_cloud(artistid, "artist")
    musicbrainz = artist.get_musicbrainz_url()
    k = data.models.SourceName.objects.get(name="kutcheris.com")
    w = data.models.SourceName.objects.get(name="Wikipedia")
    kutcheris = None
    wikipedia = None
    kr = artist.references.filter(artist_source_set=k)
    if kr.count():
        kutcheris = kr[0].uri
    wr = artist.references.filter(artist_source_set=w)
    if wr.count():
        wikipedia = wr[0].uri
    desc = artist.description
    if desc and desc.source.source_name == k:
        kutcheris = artist.description.source.uri
    elif desc and desc.source.source_name == w:
        wikipedia = artist.description.source.uri
    kr = artist.references.filter(source_name=k)
    if kr.count() and not kutcheris:
        kutcheris = kr[0].uri
    wr = artist.references.filter(source_name=w)
    if wr.count() and not wikipedia:
        wikipedia = wr[0].uri

    # Sample is the first track of any of their concerts (Vignesh, Dec 9)
    concerts = artist.concerts()
    sample = None
    if concerts:
        tracks = concerts[0].tracks.all()
        if tracks:
            sample = tracks[0]

    ret = {"filter_items": json.dumps(get_filter_items()),
    	   "artist": artist,
           "form": TagSaveForm(),
            "objecttype": "artist",
            "objectid": artist.id,
            "tags": tags,
            "similar_artists": similar_artists,
            "raagas": raagas,
            "taalas": taalas,
            "sample": sample,
            "mb": musicbrainz,
            "kutcheris": kutcheris,
            "wiki": wikipedia
    }

    return render(request, "carnatic/artist.html", ret)

def composer(request, composerid):
    composer = get_object_or_404(Composer, pk=composerid)
    recordings = []
    for w in composer.work_set.all():
        recordings.extend(w.recording_set.all())
        break
    ret = {"composer": composer,
		   "tracks": recordings,
		   "filter_items": json.dumps(get_filter_items())}

    return render(request, "carnatic/composer.html", ret)

def concertsearch(request):
    concerts = Concert.objects.all().order_by('title')
    ret = []
    for c in concerts:
        ret.append({"id": c.id, "title": c.title})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def concert(request, concertid):
    concert = get_object_or_404(Concert, pk=concertid)
    images = concert.images.all()
    if images:
        image = images[0].image.url
    else:
        image = "/media/images/noconcert.jpg"
    tracks = concert.tracks.all()
    sample = None
    if tracks:
        sample = tracks[:1]

    tags = tagging.tag_cloud(concertid, "concert")

    # Other similar concerts
    similar = concert.get_similar()

    # Raaga in
    ret = {"filter_items": json.dumps(get_filter_items()),
           "concert": concert,
	   "form": TagSaveForm(),
	   "objecttype": "concert",
	   "objectid": concert.id,
	   "tags": tags,
       "image": image,
       "sample": sample,
       "similar_concerts": similar
       }

    return render(request, "carnatic/concert.html", ret)

def recording(request, recordingid):
    recording = get_object_or_404(Recording, pk=recordingid)
    show_sim = request.GET.get("s")

    tags = tagging.tag_cloud(recordingid, "recording")

    try:
        wave = docserver.util.docserver_get_url(recording.mbid, "audioimages", "waveform32", 1)
    except docserver.util.NoFileException:
        wave = None
    try:
        spec = docserver.util.docserver_get_url(recording.mbid, "audioimages", "spectrum32", 1)
    except docserver.util.NoFileException:
        spec = None
    try:
        small = docserver.util.docserver_get_url(recording.mbid, "audioimages", "smallfull")
    except docserver.util.NoFileException:
        small = None
    try:
        audio = docserver.util.docserver_get_mp3_url(recording.mbid)
    except docserver.util.NoFileException:
        audio = None
    try:
        tonic = docserver.util.docserver_get_contents(recording.mbid, "ctonic", "tonic")
        notenames = ["A", "A♯", "B", "C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯"]
        tonic = round(float(tonic), 2)
        thebin = (12 * math.log(tonic/440.0) / math.log(2)) % 12
        thebin = int(math.round(thebin))
        tonic = str(tonic)
        if thebin <= 11 and thebin >= 0:
            tonicname = notenames[thebin]
        else:
            print "bin is", thebin, "weird"
            print tonic
            tonicname = ""
    except docserver.util.NoFileException:
        tonic = None
        tonicname = None
    try:
        akshara = docserver.util.docserver_get_contents(recording.mbid, "rhythm", "aksharaPeriod")
        akshara = str(round(float(akshara), 3) * 1000)
    except docserver.util.NoFileException:
        akshara = None

    try:
        pitchtrackurl = docserver.util.docserver_get_url(recording.mbid, "normalisedpitch", "packedpitch")
        histogramurl = docserver.util.docserver_get_url(recording.mbid, "normalisedpitch", "drawhistogram")
        rhythmurl = docserver.util.docserver_get_url(recording.mbid, "rhythm", "aksharaTicks")
        aksharaurl = docserver.util.docserver_get_url(recording.mbid, "rhythm", "APcurve")
    except docserver.util.NoFileException:
        pitchtrackurl = None
        histogramurl = None
        rhythmurl = None
        aksharaurl = None

    similar_mbids = search.similar_recordings(recording.mbid)
    similar = []
    for m in similar_mbids:
        rec = Recording.objects.get(mbid=m[0])
        similar.append(rec)

    concert = recording.concert_set.get()
    tracks = list(concert.tracks.all())
    recordingpos = tracks.index(recording)
    nextrecording = None
    prevrecording = None
    if recordingpos > 0:
        prevrecording = tracks[recordingpos-1]
    if recordingpos+1 < len(tracks):
        nextrecording = tracks[recordingpos+1]
    mbid = recording.mbid

    ret = {"filter_items": json.dumps(get_filter_items()),
    	   "recording": recording,
           "form": TagSaveForm(),
            "objecttype": "recording",
            "objectid": recording.id,
            "tags": tags,
            "waveform": wave,
            "spectrogram": spec,
            "smallimage": small,
            "audio": audio,
            "tonic": tonic,
            "tonicname": tonicname,
            "akshara": akshara,
            "mbid": mbid,
            "nextrecording": nextrecording,
            "prevrecording": prevrecording,
            "pitchtrackurl": pitchtrackurl,
            "histogramurl": histogramurl,
            "rhythmurl": rhythmurl,
            "aksharaurl": aksharaurl,
            "similar": similar,
            "show_similar": show_sim,
    }

    return render(request, "carnatic/recording.html", ret)

def worksearch(request):
    works = Work.objects.all()
    ret = []
    for w in works:
        ret.append({"id": w.id, "title": w.title})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def work(request, workid):
    work = get_object_or_404(Work, pk=workid)

    tags = tagging.tag_cloud(workid, "work")
    tracks = work.recording_set.all()
    if len(tracks):
        sample = random.sample(tracks, 1)
    else:
        sample = None


    ret = {"filter_items": json.dumps(get_filter_items()),
           "work": work,
           "form": TagSaveForm(),
            "objecttype": "work",
            "objectid": work.id,
			"sample": sample,
            "tags": tags,
    }
    return render(request, "carnatic/work.html", ret)

def taalasearch(request):
    taalas = Taala.objects.all().order_by('name')
    ret = []
    for t in taalas:
        ret.append({"id": t.id, "name": t.name})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def taala(request, taalaid):
    taala = get_object_or_404(Taala, pk=taalaid)

    similar = taala.get_similar()
    tracks = taala.recordings(10)
    if len(tracks):
        tracks = random.sample(tracks, 1)

    ret = {"taala": taala,
           "tracks": tracks,
           "similar": similar
          }
    return render(request, "carnatic/taala.html", ret)

def raagasearch(request):
    raagas = Raaga.objects.all().order_by('name')
    ret = []
    for r in raagas:
        ret.append({"id": r.id, "name": r.name})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def raaga(request, raagaid):
    raaga = get_object_or_404(Raaga, pk=raagaid)
    similar = raaga.get_similar()
    tracks = raaga.recordings(10)
    if len(tracks):
        tracks = random.sample(tracks, 1)

    ret = {"raaga": raaga,
           "tracks": tracks,
           "similar": similar
    }
    return render(request, "carnatic/raaga.html", ret)

def instrumentsearch(request):
    instruments = Instrument.objects.all().order_by('name')
    ret = []
    for i in instruments:
        ret.append({"id": i.id, "name": i.name})
    return HttpResponse(json.dumps(ret), content_type="application/json")

def instrument(request, instrumentid):
    instrument = get_object_or_404(Instrument, pk=instrumentid)
    samples = instrument.samples(10)
    sample = None
    if samples:
        sample = samples[0]
    ret = {"instrument": instrument,
           "tracks": sample,
           "filter_items": json.dumps(get_filter_items())
          }

    return render(request, "carnatic/instrument.html", ret)
