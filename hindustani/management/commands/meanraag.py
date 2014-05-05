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

from django.core.management.base import BaseCommand, CommandError
import collections

import numpy as np

from hindustani import models
from docserver import util
from compmusic.extractors.similaritylib import raaga

class Command(BaseCommand):
    help = "Calculate mean pitch profile of all raags"

    def calc_profile(self, raag, recordings):
        average = raaga.Raaga()
        pitches = []
        tonics = []
        for r in recordings:
            mbid = r.mbid
            pitch = util.docserver_get_json(mbid, "pitch", "pitch")
            tonic = util.docserver_get_contents(mbid, "ctonic", "tonic")
            tonic = float(tonic)
            npp = np.array(pitch)
            pitches.append(npp)
            tonics.append(tonic)

        average.compute_average_hist_data(pitches, tonics)
        average.generate_image("%s.png" % raag.common_name)

    def handle(self, *args, **options):
        recordings = models.Recording.objects.all()
        recmap = collections.defaultdict(list)
        for r in recordings:
            if r.raags.count() == 1:
                raag = r.raags.get()
                recmap[raag].append(r)
        for raag, recordings in recmap.items():
            self.calc_profile(raag, recordings)




