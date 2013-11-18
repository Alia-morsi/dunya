import pysolr
from django.conf import settings
import collections

from carnatic import models

solr = pysolr.Solr(settings.SOLR_URL)
def search(name):
    name = name.lower()
    query = "doctype_s:search AND title_t:(%s)" % name
    results = solr.search(query, rows=100)
    ret = collections.defaultdict(list)
    klass_map = {"instrument": models.Instrument,
                 "raaga": models.Raaga,
                 "taala": models.Taala,
                 "concert": models.Concert,
                 "artist": models.Artist,
                 "work": models.Work,
                 "composer": models.Composer}
    for d in results.docs:
        type = d["type_s"]
        id = d["object_id_i"]
        id = int(id)
        klass = klass_map.get(type)
        if klass:
            instance = klass.objects.get(pk=id)
            ret[type].append(instance)
    return ret

def get_concerts_with_raagas(raagas):
    if not isinstance(raagas, list):
        raagas = [raagas]
    raagas = " ".join(raagas)
    query = "doctype_s:concertsimilar AND raaga_is:(%s)" % raagas
    results = solr.search(query, rows=100)
    ret = []
    for d in results.docs:
        concertid = d["concertid_i"]
        ret.append(models.Concert.objects.get(pk=concertid))
    return ret

def get_concerts_with_taalas(taalas):
    if not isinstance(taalas, list):
        taalas = [taalas]
    taalas = " ".join(taalas)
    query = "doctype_s:concertsimilar AND taala_is:(%s)" % taalas
    results = solr.search(query, rows=100)
    ret = []
    for d in results.docs:
        concertid = d["concertid_i"]
        ret.append(models.Concert.objects.get(pk=concertid))
    return ret

def get_concerts_with_works(works):
    if not isinstance(works, list):
        works = [works]
    works = " ".join(works)
    query = "doctype_s:concertsimilar AND work_is:(%s)" % works
    results = solr.search(query, rows=100)
    ret = []
    for d in results.docs:
        concertid = d["concertid_i"]
        ret.append(models.Concert.objects.get(pk=concertid))
    return ret
