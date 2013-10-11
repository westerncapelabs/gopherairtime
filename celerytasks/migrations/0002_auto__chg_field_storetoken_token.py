# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'StoreToken.token'
        db.alter_column(u'celerytasks_storetoken', 'token', self.gf('django.db.models.fields.CharField')(max_length=150))

    def backwards(self, orm):

        # Changing field 'StoreToken.token'
        db.alter_column(u'celerytasks_storetoken', 'token', self.gf('django.db.models.fields.CharField')(max_length=120))

    models = {
        u'celerytasks.storetoken': {
            'Meta': {'object_name': 'StoreToken'},
            'expire_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['celerytasks']