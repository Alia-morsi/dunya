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
from django.contrib import admin

admin.site.register(models.Collection)
admin.site.register(models.Document)
admin.site.register(models.SourceFileType)
admin.site.register(models.SourceFile)
admin.site.register(models.DerivedFile)
admin.site.register(models.DerivedFilePart)
admin.site.register(models.EssentiaVersion)
admin.site.register(models.Module)
admin.site.register(models.ModuleVersion)

