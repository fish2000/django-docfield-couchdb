#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
django-docfield-couchdb/docfield/modelfields.py

Created by FI$H 2000 on 2011-08-02.
Copyright (c) 2011 Objects In Space And Time, LLC. All rights reserved.

"""

import types
import couchdbkit
import simplejson as json

from django.conf import settings
from django.db import models
from django.utils import simplejson as json
from django.core import exceptions, validators
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import ugettext_lazy as _

COUCH_ID_LENGTH = 32


class CouchID(models.Field):
    
    __metaclass__ = models.SubfieldBase
    description = _("CouchDB Document ID: 32-Character UUID String Hex-Encoded Representation")
    
    def __init__(self, name=None, *args, **kwargs):
        self.couch = kwargs.pop('couch',
            getattr(settings, 'DEFAULT_COUCH', couchdbkit.Server()))
        
        kwargs['max_length'] = COUCH_ID_LENGTH
        kwargs['editable'] = False      # NO TOUCHING!!
        kwargs['blank'] = True
        kwargs['unique'] = True
        
        super(CouchID, self).__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length))
    
    def to_python(self, value):
        if value is None:
            return self.couch.next_uuid()
        if len(str(value)) == COUCH_ID_LENGTH:
            return str(value)
        else:
            msg = self.error_messages['invalid'] % (
                "%s value length should be %s instead of %s" % (
                    self.__class__.__name__,
                    COUCH_ID_LENGTH, len(str(value))))
            raise exceptions.ValidationError(msg)
    
    def validate(self, value, model_instance):
        if len(str(value)) == COUCH_ID_LENGTH:
            return super(CouchID, self).validate(value, model_instance)
        else:
            msg = self.error_messages['invalid'] % (
                "%s value length should be %s instead of %s" % (
                    self.__class__.__name__,
                    COUCH_ID_LENGTH, len(str(value))))
            raise exceptions.ValidationError(msg)
    
    def get_internal_type(self):
        return "CharField"
    
    def get_prep_value(self, value):
        if value is None:
            return None
        return self.to_python(value)

    def db_type(self, connection=None):
        if connection and connection.vendor in ("postgresql",):
            return 'UUID'
        return 'CHAR(%s)' % (self.max_length,)

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        if add and not value:
            # get a new UUID from the Couch server.
            value = self.couch.next_uuid()
            setattr(model_instance, self.attname, value)
        return value
    
    def formfield(self, **kwargs):
        defaults = { 'max_length': self.max_length, }
        defaults.update(kwargs)
        return super(CouchAutoField, self).formfield(**defaults)
    
    def south_field_triple(self):
        """ Returns a suitable description of this field for South. """
        from south.modelsinspector import introspector
        field_class = "docfield.modelfields.CouchAutoField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)


class CouchAutoField(CouchID, models.AutoField):
    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True    # Always
        super(CouchAutoField, self).__init__(*args, **kwargs)
    
    def get_internal_type(self):
        return "AutoField"


class JSONField(models.TextField):
    """ JSONField is a TextField that stores Python tree values as JSON strings. """

    __metaclass__ = models.SubfieldBase
    description = _("Python Dictionary Structure Serialized as a String")

    def to_python(self, value):
        """ Convert the value to JSON from the string stored in the database. """
        if value == "":
            return None
        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value, connection):
        """ Convert the object to a JSON string before saving. """
        if not value or value == "":
            return None
        if isinstance(value, (dict, list)):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONField, self).get_db_prep_save(value, connection)

    def value_to_string(self, obj):
        """ Return unicode data (for now) suitable for serialization. """
        return self.get_db_prep_value(self._get_val_from_obj(obj))
    

class CouchDocLocalField(JSONField):
    
    __metaclass__ = models.SubfieldBase
    description = _("")
    
    def __init__(self, *args, **kwargs):
        """
        
        The doc_id kwarg can be:
            *) a callable -- it will receive a reference to the 
               model instance on which its CouchDocLocalField is defined;
               it should yield a Couch-worthy _id UUID string --
               existent or otherwise.
            *) a string, containing the name of a CouchAutoField
               from which to draw the _id.
            *) a string, containing a hard-coded _id UUID --
               this will force the CouchDocLocalFields' model instances
               to share the same _id; each model instance will
               have unique _rev values instead.
            *) no value -- in which case the CouchDocLocalField will
               check its dict for an '_id' field, and failing that,
               try the model's pk field as its _id.
        
        """
        self.couch = kwargs.pop('couch',
            getattr(settings, 'DEFAULT_COUCH',
                couchdbkit.Server()))
        self.couch_db = kwargs.pop('couch_db',
            getattr(settings, 'DEFAULT_COUCH_DB', None))
        
        self.doc_id = kwargs.pop('doc_id', None)
        super(CouchDocLocalField, self).__init__(*args, **kwargs)
        
        
    def to_couch(self, value, model_instance):
        
        
        print "CHECKING OUT DOC: %s" % value
        
        
        if not value or value == "":
            value = {}
        
        elif isinstance(value, (unicode, basestring)):
            # has it been pre-JSONified? round-trip it to check.
            try:
                value = eval(value)
            except (SyntaxError, ValueError):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError, err:
                    msg = "Invalid string assigned to CouchDocLocalField: %s (%s)" % (value, err)
                    raise exceptions.ValidationError(msg)
        
        elif not isinstance(value, (dict, list)):
            if hasattr(value, 'to_python'):
                value = value.to_python()
            elif hasattr(value, 'to_json'):
                pass # couchdbkit API will deal w/ this
            
            else:
                msg = "Unserializable value assigned to CouchDocLocalField: %s (%s)" % (value, err)
                raise exceptions.ValidationError(msg)
        
        doc_id = self.doc_id
        _id = None
        
        if callable(doc_id):
            _id = doc_id(model_instance)
        else:
            _id = getattr(model_instance, doc_id, doc_id)
        if not _id:
            if isinstance(value, dict):
                _id = value.get('_id',
                    value.get('doc_id', None))
        if not _id:
            if isinstance(model_instance._meta.pk, CouchAutoField):
                _id = model_instance.pk
        
        value['_id'] = _id
        
        
        print "DOC FIT FOR COUCH???: %s" % value
        
        
        return value
    
    def pre_save(self, model_instance, add):
        value = self.to_couch(getattr(
            model_instance, self.attname, None), model_instance)
        if add and not value.get('_id', None):
            value['_id'] = self.couch.next_uuid()
        
        setattr(model_instance, self.attname, value)
        
        print "ABOUT TO SAVE DOC: %s" % value
        
        self.couch_db.save_doc(value)
        return value
    
    def to_python(self, value):
        value = super(CouchDocLocalField, self).to_python(value)
        if '_id' in value:
            self.doc_id = value.pop('_id')
        if '_rev' in value:
            del value['_rev']
        return value
        
