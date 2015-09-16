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

import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.forms.models import inlineformset_factory

from forms import JsonForm, FieldForm, ItemForm
from kvedit.models import Category, Field, Item
from docserver.util import docserver_upload_and_save_file, docserver_create_document
from django.core.files.base import ContentFile

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff)
def edit_item(request, item_id, cat_id):
    message = ""
    item = Item.objects.get(ref=item_id, category__id=cat_id)
    FieldSet = inlineformset_factory(Item, Field, form=FieldForm, fields=('key','value','modified'), can_delete=False, extra=0)
    if request.method == 'POST':
        item_form = ItemForm(request.POST, instance=item)
        form = FieldSet(request.POST, instance = item)
        if item_form.is_valid() and form.is_valid():
            item_form.save()
            form.save()
            # Re-make the form with the item from the database so
            # that `modified` is set if it was changed
            item = Item.objects.get(ref=item_id, category__id=cat_id)
            form = FieldSet(instance=item)
            item_form = ItemForm(instance=item)
            message = "Item successfully saved."
            if item.verified and item.category.source_file_type and item.category.collection:
                if item.fields.filter(key="name").exists():
                    name = item.fields.get(key="name").value
                else:
                    name = item.ref
                document = docserver_create_document(item.category.collection.collectionid,
                                                     item.ref,
                                                     name)
                docserver_upload_and_save_file(document.id,
                                               item.category.source_file_type.id,
                                               ContentFile(item.to_json()))
                message += " SourceFile uploaded."
    else:
        item_form = ItemForm(instance=item)
        form = FieldSet(instance = item)
    return render(request, 'kvedit/edit.html', {'item_form':item_form, 'form': form, 'item': item, "message": message})

@user_passes_test(is_staff)
def items(request, cat_id):
    category = Category.objects.get(id=cat_id)
    items = category.items.all()
    return render(request, "kvedit/items.html", {"category": category, "items": items})


@user_passes_test(is_staff)
def categories(request):
    categories = Category.objects.order_by("-name").all()
    message = ""
    success_cat = None
    if request.method == 'POST':
        form = JsonForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            success_cat = Category.objects.get(name=form.cleaned_data['category'])
            message = "Json file successfully uploaded"
    else:
        form = JsonForm()
    return render(request, 'kvedit/categories.html', {'success_cat': success_cat, 'form': form, 'message': message, "categories": categories})
