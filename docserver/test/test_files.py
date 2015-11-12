from django.test import TestCase
from django.http import QueryDict
from django.contrib.auth.models import Permission
from django.contrib import auth

from docserver import forms
from docserver import models
from docserver import util

class SourceFileTest(TestCase):
    def setUp(self):
        permission = Permission.objects.get(codename='read_restricted')
        self.nuser = auth.models.User.objects.create_user("normaluser")

        self.suser = auth.models.User.objects.create_user("user1", "", "pass1")
        self.suser.is_staff = True
        self.suser.save()

        self.ruser = auth.models.User.objects.create_user("restricteduser")
        self.ruser.user_permissions.add(permission)
        self.ruser.save()

        self.col1 = models.Collection.objects.create(collectionid="f33f3f73", name="collection 1", slug="col")
        self.col2 = models.Collection.objects.create(collectionid="f22f2f73", name="collection 2", slug="col2")
        self.col3 = models.Collection.objects.create(collectionid="f33f3f73", name="collection 3", slug="col3")

        self.file_type = models.SourceFileType.objects.create(extension="mp3", name="mp3_file_type", slug="mp3")
        self.file_type2 = models.SourceFileType.objects.create(extension="pdf", name="pdf_file", slug="application/pdf")

        self.doc1 = models.Document.objects.create(title="doc1", external_identifier="111111")
        self.doc2 = models.Document.objects.create(title="doc2", external_identifier="222222")
        self.doc3 = models.Document.objects.create(title="doc3", external_identifier="333333")

        self.doc1.collections.add(self.col1)
        self.doc2.collections.add(self.col2)
        self.doc3.collections.add(self.col3)

        self.sfile1 = models.SourceFile.objects.create(document=self.doc1, file_type=self.file_type, size=1000)
        self.sfile2 = models.SourceFile.objects.create(document=self.doc2, file_type=self.file_type, size=1000)
        self.sfile3 = models.SourceFile.objects.create(document=self.doc3, file_type=self.file_type2, size=1000)

        models.CollectionPermission.objects.create(collection=self.col1, permission="U", source_type=self.file_type2, streamable=False)
        models.CollectionPermission.objects.create(collection=self.col2, permission="R", source_type=self.file_type, streamable=True)
        # Collection 3 doesn't specify permissions, so it's only staff.


    def test_regular_user_access(self):
        # Regular user can access only pdf of collection 1
        self.assertTrue(util.user_has_access(self.nuser, self.doc1, self.file_type2.slug))
        self.assertFalse(util.user_has_access(self.nuser, self.doc2, self.file_type.slug))
        self.assertFalse(util.user_has_access(self.nuser, self.doc2, self.file_type2.slug))
        self.assertFalse(util.user_has_access(self.nuser, self.doc1, self.file_type.slug))
       
    def test_restricted_user_access(self):
        # Restricted users can access only to mp3 of collection 2 and pdf of collection 1
        self.assertTrue(util.user_has_access(self.ruser, self.doc2, self.file_type.slug))
        self.assertTrue(util.user_has_access(self.ruser, self.doc1, self.file_type2.slug))
        self.assertFalse(util.user_has_access(self.ruser, self.doc3, self.file_type.slug))
        self.assertFalse(util.user_has_access(self.ruser, self.doc3, self.file_type2.slug))
        
    def test_staff_user_access(self):
        # Staff users access to mp3 of collection 3 and collection 2 and pdf of collection 1,
        # even if theres in no Permission created they have access too
        self.assertTrue(util.user_has_access(self.suser, self.doc2, self.file_type.slug))
        self.assertTrue(util.user_has_access(self.suser, self.doc3, self.file_type.slug))
        self.assertTrue(util.user_has_access(self.suser, self.doc1, self.file_type2.slug))
        self.assertTrue(util.user_has_access(self.suser, self.doc3, self.file_type2.slug))
        self.assertTrue(util.user_has_access(self.suser, self.doc1, self.file_type.slug))
    
    def test_rate_limit(self):
        # Return rate limit, if user is staff always return False
        self.assertFalse(util.has_rate_limit(self.suser, self.doc3, self.file_type.slug))
        self.assertFalse(util.has_rate_limit(self.ruser, self.doc1, self.file_type2.slug))
        self.assertTrue(util.has_rate_limit(self.ruser, self.doc2, self.file_type.slug))
        self.assertFalse(util.has_rate_limit(self.suser, self.doc2, self.file_type.slug))
