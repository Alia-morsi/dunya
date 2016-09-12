# -*- coding: UTF-8 -*-

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

import os
import json
import data
import docserver
import search
import pysolr
import zipfile
import StringIO

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.safestring import SafeString
from makam import models

# Simple player for Georgi/Istanbul musicians
def makamplayer(request):
    return render(request, "makam/makamplayer.html")

def searchcomplete(request):
    term = request.GET.get("term")
    ret = []
    error = False
    if term:
        try:
            suggestions = search.autocomplete(term)
            ret = []
            for l in suggestions:
                label = l['title_t']
                if 'composer_s' in l:
                    label += ' - ' +l['composer_s']
                if 'artists_s' in l:
                    artists = l['artists_s']
                    if len(artists) > 40:
                        artists = artists[:40] + "..."
                    label += ' - ' + artists
                if 'mbid_s' not in l:
                    l['mbid_s'] = ''

                ret.append({"id": l['object_id_i'], "label": label, "category": l['type_s'], "mbid": l['mbid_s']})
        except pysolr.SolrError:
            error = True
    return HttpResponse(json.dumps(ret), content_type="application/json")

def results(request):
    term = request.GET.get("q")
    ret = {}
    error = False
    if term:
        try:
            suggestions = search.autocomplete(term)
            for l in suggestions:
                doc = {'label': l['title_t'], 'id': l['object_id_i'],}
                if l['type_s'] not in ret:
                    ret[l['type_s']] = []

                if 'mbid_s' not in l:
                    l['mbid_s'] = ''
                if 'composer_s' in l:
                    doc['composer'] = l['composer_s']
                if 'artists_s' in l:
                    doc['artists'] = l['artists_s']

                doc['mbid'] = l['mbid_s']
                ret[l['type_s']].append(doc)
        except pysolr.SolrError:
            error = True
    return render(request, "makam/results.html", {'results': ret, 'error': error})


def main(request):
    q = request.GET.get('q', '')

    s_artist = request.GET.get('artist', '')
    s_perf = request.GET.get('performer', '')
    s_form = request.GET.get('form', '')
    s_makam = request.GET.get('makam', '')
    s_usul = request.GET.get('usul', '')

    artist = ""
    if s_artist and s_artist != '':
        artist = models.Composer.objects.get(id=s_artist)
    perf = ""
    if s_perf and s_perf != '':
        perf = models.Artist.objects.get(id=s_perf)
    form = ""
    if s_form and s_form != '':
        form = models.Form.objects.get(id=s_form)
    usul = ""
    if s_usul and s_usul != '':
        usul = models.Usul.objects.get(id=s_usul)
    makam = ""
    if s_makam and s_makam != '':
        makam = models.Makam.objects.get(id=s_makam)

    url = None
    works = None
    results = None
    if s_artist != '' or s_perf != '' or s_form != '' or s_usul != '' or s_makam != '' or q:
        works, url = get_works_and_url(s_artist, s_form, s_usul, s_makam, s_perf, q)
        if q and q!='':
            url["q"] = "q=" + SafeString(q.encode('utf8'))

        results = len(works) != 0

        paginator = Paginator(works, 25)
        page = request.GET.get('page')
        try:
            works = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            works = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            works = paginator.page(paginator.num_pages)
    if not url:
        url = {
                "q": "q=%s" % SafeString(q.encode('utf8')),
                "usul": "usul=%s" % s_usul,
                "form": "form=%s" % s_form,
                "artist": "artist=%s" % s_artist,
                "makam": "makam=%s" % s_makam,
                "perf": "performer=%s" % s_perf
                }

    ret = {
        'artist': artist,
        'perf': perf,
        'makam': makam,
        'usul': usul,
        'form': form,
        'works': works,
        'results': results,
        'q': q,
        'params': url,
    }
    return render(request, "makam/work_list.html", ret)

def filter_directory(request):
    elem = request.GET.get('elem', None)

    q = request.GET.get('q', None)

    artist = request.GET.get('artist', '')
    perf = request.GET.get('performer', '')
    form = request.GET.get('form', '')
    makam = request.GET.get('makam', '')
    usul = request.GET.get('usul', '')

    works, url = get_works_and_url(artist, form, usul, makam, perf, q, elem)
    if q and q!='':
        url["q"] = "q=" + SafeString(q.encode('utf8'))

    if elem == "makam":
        elems = models.Makam.objects.filter(work__in=works.all()).order_by('name').distinct()
    elif elem == "form":
        elems = models.Form.objects.filter(work__in=works.all()).order_by('name').distinct()
    elif elem == "usul":
        elems = models.Usul.objects.filter(work__in=works.all()).order_by('name').distinct()
    elif elem == "artist":
        elems = models.Composer.objects.filter(works__in=works.all()).order_by('name').distinct() | \
            models.Composer.objects.filter(lyric_works__in=works.all()).order_by('name').distinct()
    elif elem == "performer":
        e_perf = models.Artist.objects.all()
        elems = e_perf.order_by('name').distinct()
        e_perf = models.Artist.objects.filter(instrumentperformance__recording__recordingwork__work__in=works.all()).distinct() | \
                 models.Artist.objects.filter(recording__recordingwork__work__in=works.all()).distinct()

    return  render(request, "makam/display_directory.html", {"elem": elem, "elems": elems, "params": url})

def get_works_and_url(artist, form, usul, makam, perf, q, elem=None):
    works = models.Work.objects
    url = {}
    if q and q!='':
        ids = list(models.Work.objects.unaccent_get(q).values_list('pk', flat=True))
        works = works.filter(pk__in=ids) | works.filter(recording__title__contains=q)

    if elem != "artist":
        if artist and artist != '':
            works = works.filter(composers=artist) | works.filter(lyricists=artist)
        url["artist"] = "artist=" + artist
    if elem != "form":
        if form and form != '':
            works = works.filter(form=form)
        url["form"] = "form=" + form
    if elem != "usul":
        if usul and usul != '':
            works = works.filter(usul=usul)
        url["usul"] = "usul=" + usul
    if elem != "makam":
        if makam and makam != '':
            works = works.filter(makam=makam)
        url["makam"] = "makam=" + makam
    if elem != "performer":
        if perf and perf != '':
            works = works.filter(recordingwork__recording__instrumentperformance__artist=perf) | \
                    works.filter(recordingwork__recording__release__artists=perf)
        url["perf"] = "performer=" + perf

    works = works.distinct().order_by('title')
    return works, url


def work_score(request, uuid, title=None):
    work = None
    works = models.Work.objects.filter(mbid=uuid)
    if len(works):
        work = works[0]

    scoreurl = "/document/by-id/%s/score?v=0.1&subtype=score&part=1" % uuid
    phraseurl = "/document/by-id/%s/segmentphraseseg?v=0.1&subtype=segments" % uuid
    indexmapurl = "/document/by-id/%s/score?v=0.1&subtype=indexmap" % uuid

    return render(request, "makam/work_score.html", {
            "work": work,
            "phraseurl": phraseurl,
            "scoreurl": scoreurl,
            "indexmapurl": indexmapurl,
        })

def basic_lyric_alignment(request, uuid, title=None):
    recording = models.Recording()
    recording.title = "碧云天黄花地西风紧” 《西厢记》（崔莺莺）"
    recordingmbid = uuid
    mbid = uuid
    try:
        lyricsalignurl = docserver.util.docserver_get_url(mbid, "lyrics-align", "alignedLyricsSyllables", 1, version="0.1")
    except docserver.util.NoFileException:
        lyricsalignurl = None
    try:
        audio = docserver.util.docserver_get_mp3_url(mbid)
    except docserver.util.NoFileException:
        audio = None
    ret = {
           "recording": recording,
           "objecttype": "recording",
           "audio": audio,
           "mbid": mbid,
           "lyricsalignurl": lyricsalignurl,
           "recordinglengthfmt": "5:29",
           "recordinglengthseconds": "329",
    }
    return render(request, "makam/basic_lyric_alignment.html", ret)




def lyric_alignment(request, uuid, title=None):
    recording = get_object_or_404(models.Recording, mbid=uuid)
    mbid = recording.mbid

    intervalsurl = "/score?v=0.1&subtype=intervals"
    scoreurl = "/score?v=0.1&subtype=score&part=1"
    indexmapurl = "/score?v=0.1&subtype=indexmap"
    documentsurl = "/document/by-id/"
    phraseurl = "/segmentphraseseg?v=0.1&subtype=segments"

    try:
        wave = docserver.util.docserver_get_url(mbid, "makamaudioimages", "waveform8", 1, version=0.2)
    except docserver.util.NoFileException:
        wave = None
    try:
        spec = docserver.util.docserver_get_url(mbid, "makamaudioimages", "spectrum8", 1, version=0.2)
    except docserver.util.NoFileException:
        spec = None
    try:
        small = docserver.util.docserver_get_url(mbid, "makamaudioimages", "smallfull", version=0.2)
    except docserver.util.NoFileException:
        small = None
    try:
        audio = docserver.util.docserver_get_mp3_url(mbid)
    except docserver.util.NoFileException:
        audio = None

    try:
        akshara = docserver.util.docserver_get_contents(mbid, "rhythm", "aksharaPeriod", version=settings.FEAT_VERSION_RHYTHM)
        akshara = str(round(float(akshara), 3) * 1000)
    except docserver.util.NoFileException:
        akshara = None
    try:
        pitchtrackurl = docserver.util.docserver_get_url(mbid, "tomatodunya", "pitch", version="0.1")
    except docserver.util.NoFileException:
        pitchtrackurl = "/document/by-id/%s/%s?subtype=%s&v=%s" % (mbid, "tomatodunya", "pitch", "0.1")

    try:
        notesalignurl = docserver.util.docserver_get_url(mbid, "lyrics-align", "alignedLyricsSyllables", 1, version="0.1")
    except docserver.util.NoFileException:
        notesalignurl = None

    try:
        histogramurl = docserver.util.docserver_get_url(mbid, "correctedpitchmakam", "histogram", 1, version="0.2")
    except docserver.util.NoFileException:
        histogramurl = None

    try:
        notemodelsurl = docserver.util.docserver_get_url(mbid, "correctedpitchmakam", "notemodels", 1, version="0.2")
    except docserver.util.NoFileException:
        notemodelsurl = None

    try:
        sectionsurl = docserver.util.docserver_get_url(mbid, "scorealign", "sectionlinks", 1, version="0.2")
    except docserver.util.NoFileException:
        sectionsurl = None

    try:
        max_pitch = docserver.util.docserver_get_json(mbid, "dunyapitchmakam", "pitchmax", 1, version="0.2")
        min_pitch = max_pitch['min']
        max_pitch = max_pitch['max']
    except docserver.util.NoFileException:
        max_pitch = None
        min_pitch = None
    try:
        tonicurl = docserver.util.docserver_get_url(mbid, "tonictempotuning", "tonic", 1, version="0.1")
    except docserver.util.NoFileException:
        tonicurl = None
    try:
        ahenkurl = docserver.util.docserver_get_url(mbid, "correctedpitchmakam", "ahenk", 1, version="0.2")
    except docserver.util.NoFileException:
        ahenkurl = None

    try:
        worksurl = docserver.util.docserver_get_url(mbid, "correctedpitchmakam", "works_intervals", 1, version="0.2")
    except docserver.util.NoFileException:
        worksurl = None

    ret = {
           "recording": recording,
           "objecttype": "recording",
           "objectid": recording.id,
           "waveform": wave,
           "spectrogram": spec,
           "smallimage": small,
           "audio": audio,
           "tonicurl": tonicurl,
           "akshara": akshara,
           "mbid": mbid,
           "pitchtrackurl": pitchtrackurl,
           "worklist": recording.worklist(),
           "scoreurl": scoreurl,
           "indexmapurl": indexmapurl,
           "sectionsurl": sectionsurl,
           "notesalignurl": notesalignurl,
           "intervalsurl": intervalsurl,
           "documentsurl": documentsurl,
           "histogramurl": histogramurl,
           "notemodelsurl": notemodelsurl,
           "max_pitch": max_pitch,
           "min_pitch": min_pitch,
           "worksurl": worksurl,
           "phraseurl": phraseurl,
           "ahenkurl": ahenkurl
    }
    return render(request, "makam/lyric_alignment.html", ret)

def recordings_urls(include_img_and_bin=True):
    ret = {
            "notesalignurl": [("jointanalysis", "notes", 1, "0.1")],
            "pitchtrack": [("jointanalysis", "pitch", 1, "0.1"),
                ('audioanalysis', 'pitch', 1, '0.1')],
            "tempourl": [("jointanalysis", "tempo", 1, "0.1")],
            "histogramurl": [("jointanalysis", "pitch_distribution", 1, "0.1")],
            "pitch_distributionurl": [("audioanalysis", "pitch_distribution", 1, "0.1")],
            "notemodelsurl": [("jointanalysis", "note_models", 1, "0.1"),
                ("audioanalysis", "note_models", 1, "0.1")],
            "sectionsurl": [("jointanalysis", "sections", 1, "0.1")],
            "tonicurl": [( "jointanalysis", "tonic", 1, "0.1")],
            "ahenkurl": [("jointanalysis", "transposition", 1, "0.1")],
            "worksurl": [("jointanalysis", "works_intervals", 1, "0.1")],
            "melodic_progression": [("jointanalysis", "melodic_progression", 1,
                "0.1")],
            "waveform": [("makamaudioimages", "waveform8", 1, 0.3)],
            "smallimage": [("makamaudioimages", "smallfull", 1, 0.3)],
 }
    if include_img_and_bin:
        ret["spectrogram"] = [("makamaudioimages", "spectrum8", 1, 0.3)]
        ret["pitchtrackurl"] = [("tomatodunya", "pitch", 1, "0.1")]

    return ret

def recording(request, uuid, title=None):
    recording = get_object_or_404(models.Recording, mbid=uuid)
    start_time = request.GET.get("start", 0)
    mbid = recording.mbid

    intervalsurl = "/score?v=0.2&subtype=intervals"
    scoreurl = "/score?v=0.2&subtype=score&part=1"
    documentsurl = "/document/by-id/"
    phraseurl = "/segmentphraseseg?v=0.1&subtype=segments"

    try:
        audio = docserver.util.docserver_get_mp3_url(mbid)
    except docserver.util.NoFileException:
        audio = None

    try:
        max_pitch = docserver.util.docserver_get_json(mbid, "tomatodunya", "pitchmax", 1, version="0.1")
        min_pitch = max_pitch['min']
        max_pitch = max_pitch['max']
    except docserver.util.NoFileException:
        max_pitch = None
        min_pitch = None

    ret = {
           "recording": recording,
           "objecttype": "recording",
           "objectid": recording.id,
           "audio": audio,
           "mbid": mbid,
           "worklist": recording.worklist(),
           "scoreurl": scoreurl,
           "intervalsurl": intervalsurl,
           "documentsurl": documentsurl,
           "max_pitch": max_pitch,
           "min_pitch": min_pitch,
           "phraseurl": phraseurl,
           "start_time": start_time
    }

    urls = recordings_urls()
    for u in urls.keys():
        for option in urls[u]:
            try:
                success_content = docserver.util.docserver_get_url(mbid, option[0], option[1],
                        option[2], version=option[3])
                ret[u] = success_content
                break
            except docserver.util.NoFileException:
                ret[u] = None

    return render(request, "makam/recording.html", ret)

def download_derived_files(request, uuid, title=None):
    recording = get_object_or_404(models.Recording, mbid=uuid)
    mbid = recording.mbid

    filenames = []

    urls = recordings_urls(False)

    for w in recording.works.all():
        document = docserver.models.Document.objects.filter(external_identifier=w.mbid)
        if len(document) == 1:
            files = document[0].derivedfiles.filter(outputname='score',
                    module_version__version="0.2")

            if len(files) == 1:
                for n in range(files[0].numparts):
                    filenames.append(docserver.util.docserver_get_filename(w.mbid,
                        'score', 'score', n+1, '0.2'))
            score = document[0].sourcefiles.filter(file_type__extension='xml')
            if len(score) == 1:
                filenames.append(score[0].fullpath)

    for u in urls.keys():
        for option in urls[u]:
            try:
                filenames.append(docserver.util.docserver_get_filename(mbid, option[0], option[1],
                        option[2], version=option[3]))
                break
            except docserver.util.NoFileException:
                pass

    zip_subdir = "derivedfiles_%s" % mbid
    zip_filename = "%s.zip" % zip_subdir

    s = StringIO.StringIO()
    zf = zipfile.ZipFile(s, "w")
    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        # Replace name fonly for smallfull case
        zip_path = os.path.join(zip_subdir, fname.replace('smallfull',
            'melodic_progression'))

        # Add file, at correct path
        zf.write(fpath, zip_path)
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


def symbtr(request, uuid):
    """ The symbtr view returns the data of this item from
    the docserver, except sets a download hint for the browser
    and sets the filename to be the symbtr name """

    sym = get_object_or_404(models.SymbTr, uuid=uuid)
    types = ("txt", "midi", "pdf", "xml", "mu2")
    fmt = request.GET.get("format", "txt")
    if fmt not in types:
        return HttpResponseBadRequest("Unknown format parameter")

    slug = "symbtr%s" % fmt
    filetype = get_object_or_404(docserver.models.SourceFileType, slug=slug)
    filename = "%s.%s" % (sym.name, filetype.extension)
    response = docserver.views.download_external(request, uuid, slug)
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response
