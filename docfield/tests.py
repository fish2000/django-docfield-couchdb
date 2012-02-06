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
from docfield.modelfields import CouchAutoField, JSONField, CouchDocLocalField

from pprint import pprint

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

class AutoDocFieldTestManager(DelegateManager):
    __queryset__ = AutoDocFieldTestQuerySet

class ManualDocFieldTestManager(DelegateManager):
    __queryset__ = ManualDocFieldTestQuerySet

class TestModel(models.Model):
    objects = AutoDocFieldTestManager()
    other_objects = ManualDocFieldTestManager()
    id = CouchAutoField(couch=sofaset,
        primary_key=True)
    doc = CouchDocLocalField(couch=sofaset, couch_db=busbench,
        doc_id='pk',
        blank=False, null=False, unique=False,
        default={'yodogg': "Test Model Instance."})

class TestCallableModelField(models.Model):
    id = CouchAutoField(couch=sofaset,
        primary_key=True)
    doc = CouchDocLocalField(couch=sofaset, couch_db=busbench,
        doc_id=lambda tcm: tcm.pk and tcm.pk or sofaset.next_uuid(),
        blank=False, null=False, unique=False,
        default={'yodogg': "Test Callable Model Field."})

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
        ]
        for instance in self.instances:
            instance.save()
    
    def tearDown(self):
        TestModel.objects.all().delete()
        TestCallableModelField.objects.all().delete()
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
    
    def test_callable_fields(self):
        setty = set(d[0] for d in TestCallableModelField.objects.all().values_list('doc'))
        benchley = [doc.keys() for doc in busbench.all_docs().all()]
        benchy = set(reduce(lambda dd,ee: dd+ee, benchley))
        print "SETTY: "
        pprint(setty)
        print ""
        
        print "BENCHY: "
        pprint(benchley)
        print ""
        
        self.assertNotEqual(
            setty,
            benchy)
