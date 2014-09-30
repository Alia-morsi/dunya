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

from django import forms

from docserver import models
from docserver import jobs

class EssentiaVersionForm(forms.ModelForm):
    class Meta:
        model = models.EssentiaVersion
        fields = ["version", "sha1", "date_added"]

class ModuleEditForm(forms.ModelForm):
    class Meta:
        model = models.Module
        fields = ["collections"]
        widgets = {'collections': forms.CheckboxSelectMultiple()}

class ModuleForm(forms.Form):
    module = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(ModuleForm, self).__init__(*args, **kwargs)

        choices = []
        for checker in models.Collection.objects.all():
            choices.append((checker.pk, checker.name))

        self.fields['collections'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=choices)

    def clean_module(self):
        modulepath = self.cleaned_data.get('module')
        instance = jobs._get_module_instance_by_path(modulepath)
        if not instance:
            raise forms.ValidationError("The specified module doesn't exist")
        if models.Module.objects.filter(slug=instance.__slug__).exists():
            raise forms.ValidationError("A module with this slug (%s) already exists" % instance.__slug__)


    class Meta:
        fields = []
