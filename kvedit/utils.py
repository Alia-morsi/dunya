from kvedit.models import Field, Item, Category 

def upload_kvdata(cat_name, items_dic):   
    category, created = Category.objects.get_or_create(name=cat_name)
    # Select the items with the same id
    existing_items = Item.objects.filter(ref__in=items_dic.keys(), category=category)
    for item in existing_items:
        for field in items_dic[item.ref]:
            old_field = item.fields.filter(key=field.key)
            # If the old Fields have the same key, override the value unless they have been already modified
            if len(old_field) == 1 and old_field[0].value != field.value and not old_field[0].modified:
                old_field[0].value = field.value
                old_field[0].save()
            elif len(old_field) == 0:
                field.item = item
                field.save()
        del items_dic[item.ref]
    # Save the new Fields and Items
    for ref, fields in items_dic.iteritems():
        item = Item(ref=ref)
        item.category = category
        item.save()
        for field in fields:
            field.item = item
            field.save()
