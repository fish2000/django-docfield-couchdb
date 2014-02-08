#!/usr/bin/env python
# encoding: utf-8
"""

Execute this file to run the tests. At the moment,
they will have a freakout and halt unless a Couch
instance is running on your default port and we can
connect to it with impunity.

"""

import settings as docfield_settings
from django.conf import settings
if not settings.configured:
    settings.configure(**docfield_settings.__dict__)

from django.test import TestCase
from django.db import models
from delegate import DelegateManager, DelegateQuerySet, delegate
from docfield.modelfields import CouchID, CouchAutoField, CouchDocLocalField

if __name__ == "__main__":
    from django.core.management import call_command
    call_command('test', 'docfield',
        settings='docfield.settings',
        interactive=False, traceback=True, verbosity=2)
    import shutil, sys
    tempdata = docfield_settings.tempdata
    print "Deleting test data: %s" % tempdata
    shutil.rmtree(tempdata)
    sys.exit(0)

import couchdbkit
sofaset = couchdbkit.Server()
busbench = sofaset.get_or_create_db('test_docfield')

class AutoDocFieldTestQuerySet(DelegateQuerySet):
    def yodogg(self):
        return self.filter(doc__icontains="yo dogg")
    def iheardyoulike(self, whatiheardyoulike):
        return self.filter(doc__icontains=whatiheardyoulike)

class ManualDocFieldTestQuerySet(models.query.QuerySet):
    @delegate
    def queryinyourquery(self):
        return self.filter(doc__icontains="yo dogg")
    def iheardyoulike(self, whatiheardyoulike):
        return self.filter(doc__icontains=whatiheardyoulike)

class NormalDjangoPrimaryKeyFieldTestQuerySet(DelegateQuerySet):
    def yodogg(self):
        return self.filter(doc__icontains="yo dogg")
    def iheardyoulike(self, whatiheardyoulike):
        return self.filter(doc__icontains=whatiheardyoulike)

class AutoDocFieldTestManager(DelegateManager):
    __queryset__ = AutoDocFieldTestQuerySet

class ManualDocFieldTestManager(DelegateManager):
    __queryset__ = ManualDocFieldTestQuerySet

class NormalDjangoPrimaryKeyFieldTestManager(DelegateManager):
    __queryset__ = NormalDjangoPrimaryKeyFieldTestQuerySet

class TestModel(models.Model):
    objects = AutoDocFieldTestManager()
    other_objects = ManualDocFieldTestManager()
    id = CouchAutoField(couch=sofaset)
    doc = CouchDocLocalField(
        couch=sofaset,
        couch_db=busbench,
        blank=False, null=False, unique=False,
        default={'yodogg': "Test Model Instance."})

class TestCallableModelField(models.Model):
    id = CouchAutoField(couch=sofaset)
    doc = CouchDocLocalField(
        couch=sofaset,
        couch_db=busbench,
        doc_id=lambda model_obj: model_obj.pk or sofaset.next_uuid(),
        blank=False, null=False, unique=False,
        default={'yodogg': "Test Callable Model Field."})

class TestModelWithNormalDjangoPrimaryKey(models.Model):
    """ This also tests the default database handles (per settings.py) """
    objects = NormalDjangoPrimaryKeyFieldTestManager()
    couch_id = CouchID()
    doc = CouchDocLocalField(
        doc_id='couch_id',
        blank=False, null=False, unique=False,
        default={'yodogg': "Test Model Instance."})

class DocFieldTests(TestCase):
    def setUp(self):
        self.instances = [
            TestModel(doc=dict(yodogg='hello, dogg.')),
            TestModel(doc=dict(yodogg='Oh wow, is that *dog*??! no way.')),
            TestModel(),
            TestModel(),
            TestCallableModelField(doc=dict(yodogg='hello, dogg.', ooga='booga')),
            TestCallableModelField(doc=dict(yodogg='hello, dogg.', fuckyes='eat shit.')),
            TestCallableModelField(),
            TestCallableModelField(),
            TestModelWithNormalDjangoPrimaryKey(doc=dict(yodogg='hello, dogg.', ooga='booga')),
            TestModelWithNormalDjangoPrimaryKey(doc=dict(yodogg='hello, dogg.', fuckyes='eat shit.')),
            TestModelWithNormalDjangoPrimaryKey(),
            TestModelWithNormalDjangoPrimaryKey(),
        ]
        for instance in self.instances:
            instance.save()
    
    def tearDown(self):
        TestModel.objects.all().delete()
        TestCallableModelField.objects.all().delete()
        TestModelWithNormalDjangoPrimaryKey.objects.all().delete()
        busbench.delete_docs(
            busbench.all_docs().all())
    
    def test_manual_docfield(self):
        self.assertTrue(hasattr(TestModel.other_objects, 'queryinyourquery'))
        self.assertFalse(hasattr(TestModel.other_objects, 'iheardyoulike'))
        self.assertEqual(
            TestModel.other_objects.queryinyourquery().count(),
            TestModel.other_objects.all().queryinyourquery().count())
    
    def test_manual_docfield_querysets(self):
        comparator = [repr(q) for q in TestModel.other_objects.all().queryinyourquery()]
        self.assertQuerysetEqual(
            TestModel.other_objects.queryinyourquery(),
            comparator)
        self.assertQuerysetEqual(
            TestModel.other_objects.all().queryinyourquery(),
            comparator)
    
    def test_automatic_docfield(self):
        self.assertTrue(hasattr(TestModel.objects, 'yodogg'))
        self.assertTrue(hasattr(TestModel.objects, 'iheardyoulike'))
        self.assertEqual(
            TestModel.objects.yodogg().count(),
            TestModel.objects.all().yodogg().count())
        self.assertEqual(
            TestModel.objects.iheardyoulike('yo dogg').count(),
            TestModel.objects.all().iheardyoulike('yo dogg').count())
    
    def test_automatic_docfield_querysets(self):
        comparator = [repr(q) for q in TestModel.objects.all().yodogg()]
        self.assertQuerysetEqual(
            TestModel.objects.yodogg(),
            comparator)
        self.assertQuerysetEqual(
            TestModel.objects.all().yodogg(),
            comparator)
    
    def test_non_primary_key_couchid_field(self):
        comparator = [repr(q) for q in TestModelWithNormalDjangoPrimaryKey.objects.all().yodogg()]
        self.assertQuerysetEqual(
            TestModelWithNormalDjangoPrimaryKey.objects.yodogg(),
            comparator)
        self.assertQuerysetEqual(
            TestModelWithNormalDjangoPrimaryKey.objects.all().yodogg(),
            comparator)
        for comparible in comparator:
            self.assertTrue(comparible.couch_id is not None)
    
    def test_callable_fields(self):
        import json
        
        set_models = set(json.loads(d['doc'])['_id'] for d in TestModel.objects.all().values('doc'))
        set_callable_field_models = set(json.loads(d['doc'])['_id'] for d in TestCallableModelField.objects.all().values('doc'))
        set_non_pk_models = set(json.loads(d['doc'])['_id'] for d in TestModelWithNormalDjangoPrimaryKey.objects.all().values('doc'))
        couchdb_set = set([doc['id'] for doc in busbench.all_docs().all() if doc.get('id', None)])
        
        self.assertTrue(len(couchdb_set) > 0)
        self.assertTrue(set_models.issubset(couchdb_set))
        self.assertTrue(set_callable_field_models.issubset(couchdb_set))
        self.assertTrue(set_non_pk_models.issubset(couchdb_set))
