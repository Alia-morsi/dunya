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

import pysolr
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Load data in the database to solr'
    solr_m = pysolr.Solr(settings.SOLR_URL + "/makam")
    solr_c = pysolr.Solr(settings.SOLR_URL + "/carnatic")
    solr_h = pysolr.Solr(settings.SOLR_URL + "/hindustani")

    def handle(self, *args, **options):
        self.solr_c.delete(q="*:*")
        self.solr_c.commit()
        self.solr_m.delete(q="*:*")
        self.solr_m.commit()
        self.solr_h.delete(q="*:*")
        self.solr_h.commit()
