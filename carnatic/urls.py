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

from django.conf.urls import url
from django.views.generic.base import TemplateView

from carnatic import views

uuid_match = r'(?P<uuid>[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
name_match = r'(?:/(?P<name>[\w-]+))?'
title_match = r'(?:/(?P<title>[\w-]+))?'

urlpatterns = [
    url(r'^$', views.main, name='carnatic-main'),
    url(r'^info$',
        TemplateView.as_view(template_name="carnatic/info.html"), name='carnatic-info'),

    url(r'^formedit/%s$' % (uuid_match, ), views.formconcert, name='carnatic-formconcert'),
    url(r'^formedit$', views.formedit, name='carnatic-formedit'),

    url(r'^searchcomplete$', views.searchcomplete, name='carnatic-searchcomplete'),
    url(r'^search$', views.recordings_search, name='carnatic-search'),

    url(r'^recording/(?P<recordingid>\d+)%s$' % (title_match, ), views.recordingbyid, name='carnatic-recordingbyid'),
    url(r'^recording/%s%s$' % (uuid_match, title_match), views.recording, name='carnatic-recording'),

    url(r'filters.json$', views.filters, name='carnatic-filters'),
]
