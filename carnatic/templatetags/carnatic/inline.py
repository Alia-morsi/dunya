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

from django import template
from django.utils.html import format_html, format_html_join, mark_safe

import collections
import carnatic

register = template.Library()

@register.assignment_tag
def work_recordings_with_restricted(work, with_restricted):
    all_recordings = work.recordings()
    restricted = 0
    ret = []
    for r in all_recordings:
        is_b = r.is_restricted()
        if not with_restricted and is_b:
            restricted += 1
        elif with_restricted and is_b:
            ret.append(r)
        elif not is_b:
            ret.append(r)

    return {"recordings": ret, "restricted": restricted}

@register.assignment_tag
def artist_collaborating_artists_with_bootleg(artist, permission):
    coll_artists = artist.collaborating_artists(permission=permission)
    return [{"artist": a, "concerts": c, "bootlegs": b} for a, c, b in coll_artists]

@register.simple_tag
def url_host_and_path(request, url):
    return request.build_absolute_uri(url)

@register.simple_tag
def inline_artist(artist):
    if artist:
        return inline_artist_part(artist)
    else:
        return ""

@register.simple_tag
def inline_artist_list(artists):
    artists = list(artists)
    if len(artists) == 1:
        return inline_artist_part(artists[0])
    elif len(artists) > 1:
        return mark_safe(u", ".join([inline_artist_part(a) for a in artists]))
    else:
        return u"(unknown)"

def inline_artist_part(artist):
    if isinstance(artist, carnatic.models.Artist):
        return format_html(u'<span class="title">{}</span>', artist.name)
    else:
        return artist.name

@register.simple_tag
def inline_concert(concert, bold=False):
    sb = ""
    eb = ""
    if bold:
        sb = "<b>"
        eb = "</b>"
    return format_html(u'<span>%s{}%s</span>' % (sb, eb), concert.title)

@register.simple_tag
def inline_composer(composer):
    return format_html(u'<a href="{}">{}</a>', composer.get_absolute_url(), composer.name)

@register.simple_tag
def inline_recording(recording):
    return format_html(u'<a href="{}">{}</a>', recording.get_absolute_url(), recording.title)

@register.simple_tag
def inline_recording_artist(recording):
    if recording.artist() is not None:
        return recording.artist().name
    return "unknown"

@register.simple_tag
def inline_work(work):
    return work.title

@register.simple_tag
def inline_raaga_list(raagas):
    return mark_safe(u", ".join([inline_raaga(r) for r in raagas]))

@register.simple_tag
def inline_raaga(raaga):
    if raaga:
        return format_html(u'<span title="{}">{}</span>', raaga.common_name.title(), raaga.name.title())
    else:
        return '(unknown)'

@register.simple_tag
def inline_taala_list(taalas):
    return mark_safe(u", ".join(inline_taala(t) for t in taalas))

@register.simple_tag
def inline_taala(taala):
    if taala:
        return format_html(u'<span title="{}">{}</span>', taala.common_name.title(), taala.name.title())
    else:
        return '(unknown)'

@register.simple_tag
def inline_instrument(instrument):
    if not isinstance(instrument, collections.Iterable):
        instrument = [instrument]
    ret = []
    return format_html_join(u", ", u'<a href="{}">{}</a>', ((i.get_absolute_url(), i.name) for i in instrument if i))
