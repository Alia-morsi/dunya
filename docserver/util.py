from docserver import models
import compmusic

def docserver_add_mp3(collectionid, releaseid, fpath, recordingid):
    meta = compmusic.file_metadata(fpath)
    # TODO: We assume it's MP3 for now.
    mp3type = models.FileType.objects.get(extension="mp3")
    title = meta["meta"].get("title")

    try:
        doc = docserver.models.Document.objects.get_by_external_id(recordingid)
        docserver_add_file(doc.id, mp3type, fpath)
    except docserver.models.Document.DoesNotExist:
        docserver_add_document(collectionid, mp3type, title, fpath, recordingid)

def docserver_add_document(collection_id, filetype, title, path, alt_id=None):
    collection = models.Collection.objects.get(pk=collection_id)
    document = models.Document.objects.create(collection=collection, title=title)
    if alt_id:
        document.external_identifier = alt_id
        document.save()
    docserver_add_file(document.id, filetype, path)

def docserver_add_file(document_id, ftype, path):
    document = models.Document.objects.get(pk=document_id)
    file = models.File.objects.create(document=document, file_type=ftype, path=path)

def docserver_add_contents(collection_id, document_id, fileytpe, title, contents):
    collection = models.Collection.objects.get(pk=collection_id)
