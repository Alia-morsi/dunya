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

from docserver import models
import compmusic
import tempfile
import os
import subprocess
import json
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
class NoFileException(Exception):
    pass

class TooManyFilesException(Exception):
    pass

def docserver_add_mp3(collectionid, releaseid, fpath, recordingid):
    meta = compmusic.file_metadata(fpath)
    mp3type = models.SourceFileType.objects.get_by_slug("mp3")
    title = meta["meta"].get("title")

    try:
        doc = models.Document.objects.get_by_external_id(recordingid)
        docserver_add_sourcefile(doc.pk, mp3type.pk, fpath)
    except models.Document.DoesNotExist:
        docserver_add_document(collectionid, mp3type.pk, title, fpath, recordingid)

def docserver_add_document(collection_id, filetype_id, title, path, external_identifier=None):
    """ Add a document.
        Arguments:
          filetype: a SourceFileType
    """
    collection = models.Collection.objects.get(collectionid=collection_id)
    document = models.Document.objects.create(title=title)
    document.collections.add(collection)
    if external_identifier:
        document.external_identifier = external_identifier
        document.save()
    docserver_add_sourcefile(document.pk, filetype_id, path)

def _write_to_disk(file, filepath):
    """ write the file object `file` to disk at `filepath'"""

    size = 0
    try:
        with open(filepath, 'wb') as dest:
            for chunk in file.chunks():
                size += len(chunk)
                dest.write(chunk)
    except IOError as e:
        raise
    return size

def docserver_upload_and_save_file(document_id, sft_id, file):
    document = models.Document.objects.get(id=document_id)
    sft = models.SourceFileType.objects.get(id=sft_id)

    root = document.get_root_dir()

    mbid = document.external_identifier
    mb = mbid[:2]
    slug = sft.slug
    ext = sft.extension
    subdir = sft.stype
    filedir = os.path.join(mb, mbid, slug)
    datadir = os.path.join(root, subdir, filedir)

    try:
        os.makedirs(datadir)
    except OSError:
        print "Error making directory", datadir
        pass

    filename = "%s-%s.%s" % (mbid, slug, ext)
    filepath = os.path.join(datadir, filename)

    size = _write_to_disk(file, filepath)

    return docserver_add_sourcefile(document_id, sft_id, filepath)

def docserver_add_sourcefile(document_id, sft_id, path):
    """ Add a file to the given document. If a file with the given filetype
        already exists for the document just update the path and size. """
    document = models.Document.objects.get(pk=document_id)
    sft = models.SourceFileType.objects.get(pk=sft_id)

    size = os.stat(path).st_size
    root_directory = os.path.join(document.get_root_dir(), sft.stype)
    if path.startswith(root_directory):
        # If the path is absolute, remove it
        path = path[len(root_directory):]
    if path.startswith("/"):
        path = path[1:]

    sf, created = models.SourceFile.objects.get_or_create(document=document, file_type=sft,
            defaults={"path":path, "size": size})
    if not created:
        sf.path = path
        sf.size = size
        sf.save()
    return sf, created

def docserver_get_wav_filename(documentid):
    """ Return a tuple (filename, created) containing the filename
        of a wave file for this document. If created is True, it means
        the file was generated on demand and you must delete it when
        you're finished. Otherwise it's from the docserver
    """
    try:
        filename = docserver_get_filename(documentid, "wav", "wave")
        if not os.path.exists(filename):
            raise NoFileException("Wave file doesn't exist")
        return filename, False
    except:  # Error getting file because it's not in the db or it doesn't exist
        print "Error getting file, calculating again"
        mp3filename = docserver_get_filename(documentid, "mp3")
        fp, tmpname = tempfile.mkstemp(".wav")
        os.close(fp)
        proclist = ["lame", "--decode", mp3filename, tmpname]
        p = subprocess.Popen(proclist)
        p.communicate()
        return tmpname, True

def docserver_get_url(documentid, slug, subtype=None, part=None, version=None):
    part = _docserver_get_part(documentid, slug, subtype, part, version)
    url = part.get_absolute_url()
    return url

def docserver_get_mp3_url(documentid):
    part = _docserver_get_part(documentid, "mp3")
    url = part.get_absolute_url("ds-download-mp3")
    return url

def docserver_get_filename(documentid, slug, subtype=None, part=None, version=None):
    part = _docserver_get_part(documentid, slug, subtype, part, version)
    full_path = part.fullpath
    return full_path

def _docserver_get_part(documentid, slug, subtype=None, part=None, version=None):
    try:
        doc = models.Document.objects.get(external_identifier=documentid)
    except models.Document.DoesNotExist:
        raise NoFileException("Cannot find a document with id %s" % documentid)
    try:
        sourcetype = models.SourceFileType.objects.get_by_slug(slug)
    except models.SourceFileType.DoesNotExist:
        sourcetype = None
    if doc and sourcetype:
        files = doc.sourcefiles.filter(file_type=sourcetype)
        if len(files) == 0:
            raise NoFileException("Looks like a sourcefile, but I can't find one")
        else:
            return files[0]

    try:
        module = models.Module.objects.get(slug=slug)
    except models.Module.DoesNotExist:
        raise NoFileException("Cannot find a module with type %s" % slug)
    moduleversions = module.versions
    if version:
        moduleversions = moduleversions.filter(version=version)
    else:
        moduleversions = moduleversions.order_by("-date_added")
    if len(moduleversions):
        dfs = None
        for mv in moduleversions:
            # go through all the versions until we find a file of that version
            dfs = doc.derivedfiles.filter(module_version=mv).all()
            if subtype:
                dfs = dfs.filter(outputname=subtype)
            if dfs.count() > 0:
                # We found some files, break
                break
        if dfs.count() > 1:
            raise TooManyFilesException("Found more than 1 subtype for this module but you haven't specified what you want")
        elif dfs.count() == 1:
            # Double-check if subtypes match. This is to catch the case where we
            # have only one subtype for a type but we don't specify it in the
            # query. By 'luck' we will get the right subtype, but this doesn't
            # preclude the default subtype changing in a future version.
            # Explicit is better than implicit
            derived = dfs.get()
            if derived.outputname != subtype:
                raise NoFileException("This module has only one subtype which you must specify (%s)" % (derived.outputname, ))
            # Select the part.
            # If the file has many parts and ?part is not set then it's an error
            parts = derived.parts
            if part:
                try:
                    part = int(part)
                    parts = parts.filter(part_order=part)
                except ValueError:
                    raise NoFileException("Invalid part")
            else:
                parts = parts.all()
            if parts.count() > 1:
                raise TooManyFilesException("Found more than 1 part without part set")
            elif parts.count() == 1:
                return parts[0]
            else:
                raise NoFileException("No parts on this file")
        else:
            # If no files, or none with this version
            msg = "No derived files with this type/subtype"
            if version:
                msg += " or version"
            raise NoFileException(msg)
    else:
        raise NoFileException("No known versions for this module")

def docserver_get_contents(documentid, slug, subtype=None, part=None, version=None):
    try:
        return open(docserver_get_filename(documentid, slug, subtype, part, version), "rb").read()
    except IOError:
        raise NoFileException

def docserver_get_json(documentid, slug, subtype=None, part=None, version=None):
    try:
        contents = open(docserver_get_filename(documentid, slug, subtype, part, version), "rb").read()
        return json.loads(contents)
    except IOError:
        raise NoFileException

def get_user_permissions(user):
    permission = ["U"]
    if user.is_staff:
        permission = ["S", "R", "U"]
    elif user.has_perm('docserver.access_restricted_file'):
        permission = ["R", "U"]
    return permission

def user_has_access(user, document, file_type_slug):
    '''
    Returns True if the user has access to the source_file, this is made through
    the related collection.
    If the user is_staff also returns True.
    Also returns True if there is no Source File with that slug but there is a Module.
    file_type_slug is the slug of the file SourceFileType.
    '''
    user_permissions = get_user_permissions(user)
    if user.is_staff:
        return True
    try:
        sourcetype = models.SourceFileType.objects.get_by_slug(file_type_slug)
    except models.SourceFileType.DoesNotExist:
        sourcetype = None
    if not sourcetype:
        try:
            module = models.Module.objects.get(slug=file_type_slug)
            return True
        except models.Module.DoesNotExist:
            return False

    return models.CollectionPermission.objects.filter(
            collection__in=document.collections.all(),
            source_type=sourcetype,
            permission__in=user_permissions).count() != 0

def has_rate_limit(user, document, file_type_slug):
    '''
    Returns True if the user has access to the source_file with rate limit,
    but if the user is staff always returns False
    file_type_slug is the slug of the file SourceFileType.
    In the case where there is no CollectionPermission element we return
    False, because it corresponds to a Module slug
    '''
    user_permissions = get_user_permissions(user)
    if user.is_staff:
        return False
    try:
        c = models.CollectionPermission.objects.get(
            collection__in=document.collections.all(),
            source_type__slug=file_type_slug,
            permission__in=user_permissions)
        return c.streamable
    except ObjectDoesNotExist, e:
         return False

